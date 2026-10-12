import { atom, read, update } from 'claude-code'
import type { EngineInterface, PromptOrigin, Register } from 'claude-code'

import type { AgentRun } from '../types'

const runs = atom({ plugin: 'agent-progress-bar', key: 'runs' } as const, [] as AgentRun[])
const isCollapsed = atom({ plugin: 'agent-progress-bar', key: 'isCollapsed' } as const, false)

const WIDTH = 20
const ICON = { running: '◐', done: '✔', failed: '✗' } as const
// 成功=綠，未完成與失敗=紅
const COLOR = { running: 'error', done: 'success', failed: 'error' } as const

// 視為「使用者自己送出」的提示來源；通知、子代理回報等不算
const HUMAN_ORIGINS: ReadonlySet<PromptOrigin['kind']> = new Set(['composer', 'bridge', 'sdk'])

function counts(list: AgentRun[]) {
  const finished = list.filter(r => r.status !== 'running').length
  const done = list.filter(r => r.status === 'done').length
  const failed = list.filter(r => r.status === 'failed').length
  const pct = list.length === 0 ? 0 : Math.round((finished / list.length) * 100)
  return { finished, done, failed, pct }
}

function filledCells(done: number, total: number): number {
  return total === 0 ? 0 : Math.round((done / total) * WIDTH)
}

function summary(list: AgentRun[]): string {
  const { finished, failed, pct } = counts(list)
  const filled = filledCells(finished, list.length)
  return `Agents ${'█'.repeat(filled)}${'░'.repeat(WIDTH - filled)} ${finished}/${list.length} (${pct}%)${failed ? ` ✗${failed}` : ''}`
}

async function refreshStatus($: EngineInterface) {
  const list = await read($, runs)
  $.ui.status(list.length === 0 ? undefined : summary(list))
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await refreshStatus($)
    return next(e)
  })

  // 子代理啟動：記錄一筆 running，並自動展開
  on('agent.spawn', async ($, e, next) => {
    const result = await next(e)
    if (result.agentId === undefined || result.teammateId !== undefined) {
      return result
    }

    const run: AgentRun = {
      id: result.agentId,
      description: e.description || e.subagentType,
      type: e.subagentType,
      status: 'running',
    }
    await update($, runs, list => [...list.filter(r => r.id !== run.id), run])
    await update($, isCollapsed, () => false)
    await refreshStatus($)

    return result
  }).catch(($, e, next) => next(e))

  // 子代理那一輪結束：標記完成或失敗；全部成功完成就自動收合
  on('turn.complete', async ($, e, next) => {
    if (e.agentId !== undefined) {
      const status = e.reason === 'answer' ? 'done' : 'failed'
      const list = await update($, runs, all =>
        all.map(r => (r.id === e.agentId && r.status === 'running' ? { ...r, status } : r)),
      )
      if (list.length > 0 && list.every(r => r.status === 'done')) {
        await update($, isCollapsed, () => true)
      }
      await refreshStatus($)
    }

    return next(e)
  })

  // 使用者自己送出新提示時，若上一批全部結束就清空
  on('prompt.submit', async ($, e, next) => {
    const isHuman = e.origin === undefined || HUMAN_ORIGINS.has(e.origin.kind)
    const list = await read($, runs)
    if (isHuman && list.length > 0 && list.every(r => r.status !== 'running')) {
      await update($, runs, () => [])
      $.ui.status(undefined)
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  // 輸入框上方的進度帶：總進度條 + 每個 agent 一行，可收合／展開
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const list = await read($, runs)
    if (e.props.hasSurvey || list.length === 0) {
      return next(e)
    }

    const { Box, Button, Text } = $.ui.resolve(e)
    const collapsed = await read($, isCollapsed)
    const { finished, done, failed, pct } = counts(list)
    const greenCells = filledCells(done, list.length)
    const rows = list.slice(-Math.max(1, e.props.maxRows - 2))

    return (
      <Box flexDirection="column">
        <Box>
          <Text bold>{'Agents '}</Text>
          <Text color="success">{'█'.repeat(greenCells)}</Text>
          <Text color="error">{'░'.repeat(WIDTH - greenCells)}</Text>
          <Text bold>{` ${finished}/${list.length} (${pct}%)`}</Text>
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
              {`${ICON[r.status]} ${r.description} [${r.type}]`}
            </Text>
          ))}
      </Box>
    )
  })
}
