import { atom, read, update } from 'claude-code'
import type { EngineInterface, PromptOrigin, Register } from 'claude-code'

import type { AgentRun, RunKind, RunStatus } from '../types'

const runs = atom({ plugin: 'agent-progress-bar', key: 'runs' } as const, [] as AgentRun[])
const isCollapsed = atom({ plugin: 'agent-progress-bar', key: 'isCollapsed' } as const, false)

const WIDTH = 20
const ICON = { running: '◐', done: '✔', failed: '✗' } as const
// 成功=綠，未完成與失敗=紅
const COLOR = { running: 'error', done: 'success', failed: 'error' } as const
const KIND_LABEL: Record<RunKind, string> = { agent: 'Agent', shell: '指令', monitor: '監看', other: '作業' }

// 視為「使用者自己送出」的提示來源；通知、子代理回報等不算
const HUMAN_ORIGINS: ReadonlySet<PromptOrigin['kind']> = new Set(['composer', 'bridge', 'sdk'])

function counts(list: AgentRun[]) {
  const running = list.filter(r => r.status === 'running').length
  const finished = list.length - running
  const done = list.filter(r => r.status === 'done').length
  const failed = list.filter(r => r.status === 'failed').length
  const pct = list.length === 0 ? 0 : Math.round((finished / list.length) * 100)
  return { running, finished, done, failed, pct }
}

function filledCells(done: number, total: number): number {
  return total === 0 ? 0 : Math.round((done / total) * WIDTH)
}

function oneLine(text: string, max: number): string {
  const flat = text.replace(/\s+/g, ' ').trim()
  return flat.length > max ? `${flat.slice(0, max - 1)}…` : flat
}

function summary(list: AgentRun[]): string {
  const { running, finished, failed, pct } = counts(list)
  const filled = filledCells(finished, list.length)
  return `背景作業 ${'█'.repeat(filled)}${'░'.repeat(WIDTH - filled)} ${finished}/${list.length} (${pct}%) 執行中 ${running}${failed ? ` ✗${failed}` : ''}`
}

async function refreshStatus($: EngineInterface) {
  const list = await read($, runs)
  $.ui.status(list.length === 0 ? undefined : summary(list))
}

// 新增一筆執行中的作業，並自動展開
async function addRun($: EngineInterface, run: Omit<AgentRun, 'status'>) {
  await update($, runs, list => [...list.filter(r => r.id !== run.id), { ...run, status: 'running' }])
  await update($, isCollapsed, () => false)
  await refreshStatus($)
}

// 標記結束；全部成功完成就自動收合
async function finishRun($: EngineInterface, id: string, status: Exclude<RunStatus, 'running'>) {
  const list = await update($, runs, all =>
    all.map(r => (r.id === id && r.status === 'running' ? { ...r, status } : r)),
  )
  if (list.length > 0 && list.every(r => r.status === 'done')) {
    await update($, isCollapsed, () => true)
  }
  await refreshStatus($)
}

function kindOf(type: string): RunKind {
  if (type === 'subagent') return 'agent'
  if (type === 'shell') return 'shell'
  if (type === 'monitor') return 'monitor'
  return 'other'
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await refreshStatus($)
    return next(e)
  })

  // 子代理啟動
  on('agent.spawn', async ($, e, next) => {
    const result = await next(e)
    if (result.agentId !== undefined && result.teammateId === undefined) {
      await addRun($, {
        id: result.agentId,
        kind: 'agent',
        description: e.description || e.subagentType,
        type: e.subagentType,
      })
    }
    return result
  }).catch(($, e, next) => next(e))

  // 背景 shell 指令（run_in_background、Ctrl+B、逾時轉背景）
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const ran = await next(e)
    const id = ran.deny === undefined && ran.isError !== true ? ran.result?.backgroundTaskId : undefined
    if (id !== undefined) {
      await addRun($, { id, kind: 'shell', description: oneLine(e.description ?? e.command, 60), type: 'Bash' })
    }
    return ran
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: 'PowerShell' }, async ($, e, next) => {
    const ran = await next(e)
    const id = ran.deny === undefined && ran.isError !== true ? ran.result?.backgroundTaskId : undefined
    if (id !== undefined) {
      await addRun($, { id, kind: 'shell', description: oneLine(e.description ?? e.command, 60), type: 'PowerShell' })
    }
    return ran
  }).catch(($, e, next) => next(e))

  // 背景監看
  on('tool.call', { tool: 'Monitor' }, async ($, e, next) => {
    const ran = await next(e)
    const id = ran.deny === undefined && ran.isError !== true ? ran.result?.taskId : undefined
    if (id !== undefined) {
      await addRun($, { id, kind: 'monitor', description: oneLine(e.description, 60), type: 'Monitor' })
    }
    return ran
  }).catch(($, e, next) => next(e))

  // 子代理那一輪結束：標記完成或失敗
  on('turn.complete', async ($, e, next) => {
    if (e.agentId !== undefined) {
      await finishRun($, e.agentId, e.reason === 'answer' ? 'done' : 'failed')
    }
    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    // 背景作業結束的通知：<task-id>…</task-id> <status>…</status>
    if (e.origin?.kind === 'task-notification') {
      const id = /<task-id>([^<]+)<\/task-id>/.exec(e.text)?.[1]
      const status = /<status>([^<]+)<\/status>/.exec(e.text)?.[1]
      if (id !== undefined && status !== undefined && status !== 'running') {
        await finishRun($, id, status === 'completed' ? 'done' : 'failed')
      }
    }

    // 使用者自己送出新提示時，若上一批全部結束就清空
    const isHuman = e.origin === undefined || HUMAN_ORIGINS.has(e.origin.kind)
    const list = await read($, runs)
    if (isHuman && list.length > 0 && list.every(r => r.status !== 'running')) {
      await update($, runs, () => [])
      $.ui.status(undefined)
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  // 每輪結束時與 app 的「執行中背景作業」清單對帳：補上漏追的，結束沒收到通知的標記完成
  on('classic.Stop', async ($, e, next) => {
    const inFlight = e.background_tasks
    if (inFlight !== undefined) {
      const live = new Set(inFlight.map(t => t.id))
      const list = await read($, runs)
      const known = new Set(list.map(r => r.id))
      for (const t of inFlight) {
        if (!known.has(t.id) && t.type !== 'subagent') {
          await addRun($, {
            id: t.id,
            kind: kindOf(t.type),
            description: oneLine(t.description || t.command || t.type, 60),
            type: t.type,
          })
        }
      }
      for (const r of list) {
        if (r.status === 'running' && r.kind !== 'agent' && !live.has(r.id)) {
          await finishRun($, r.id, 'done')
        }
      }
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  // 輸入框上方的進度帶：總進度條 + 每項作業一行，可收合／展開
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const list = await read($, runs)
    if (e.props.hasSurvey || list.length === 0) {
      return next(e)
    }

    const { Box, Button, Text } = $.ui.resolve(e)
    const collapsed = await read($, isCollapsed)
    const { running, finished, done, failed, pct } = counts(list)
    const greenCells = filledCells(done, list.length)
    const rows = list.slice(-Math.max(1, e.props.maxRows - 2))

    return (
      <Box flexDirection="column">
        <Box>
          <Text bold>{'背景作業 '}</Text>
          <Text color="success">{'█'.repeat(greenCells)}</Text>
          <Text color="error">{'░'.repeat(WIDTH - greenCells)}</Text>
          <Text bold>{` ${finished}/${list.length} (${pct}%)`}</Text>
          <Text bold color={running > 0 ? 'error' : 'success'}>{`  執行中 ${running}`}</Text>
          {failed > 0 && <Text color="error">{` ✗${failed}`}</Text>}
          <Text>{' '}</Text>
          <Button
            key="toggle"
            label={collapsed ? '展開' : '收合'}
            onPress={() => update($, isCollapsed, v => !v)}
          />
        </Box>
        {!collapsed &&
          rows.map(r => (
            <Text key={r.id} color={COLOR[r.status]}>
              {`${ICON[r.status]} [${KIND_LABEL[r.kind]}] ${r.description} (${r.type})`}
            </Text>
          ))}
      </Box>
    )
  })
}
