import { atom, read, update } from 'claude-code'
import type { EngineInterface, PromptOrigin, Register } from 'claude-code'

import type { Alert, AlertKind } from '../types'

const alert = atom({ plugin: 'attention-alert', key: 'alert' } as const, null as Alert | null)

// 執行中的工具呼叫：tool_use_id → 工具名稱
const pending = new Map<string, string>()

// 需要使用者回應的兩種狀態
const WAITING: ReadonlySet<AlertKind> = new Set(['ask', 'permission'])

const STYLE = {
  ask: { icon: '⚠', title: '需要你裁決', bg: 'error' },
  permission: { icon: '⚠', title: '等待你核准', bg: 'warning' },
  done: { icon: '✔', title: '工作完成，等你下一步', bg: 'success' },
  error: { icon: '✗', title: '工作中斷（發生錯誤）', bg: 'error' },
} as const

// 視為「使用者自己送出」的提示來源；通知、子代理回報等不算
const HUMAN_ORIGINS: ReadonlySet<PromptOrigin['kind']> = new Set(['composer', 'bridge', 'sdk'])

function isPluginTree(node: unknown): boolean {
  return typeof node === 'object' && node !== null && (node as { type?: unknown }).type !== 'engine'
}

function oneLine(text: string, max: number): string {
  const flat = text.replace(/\s+/g, ' ').trim()
  return flat.length > max ? `${flat.slice(0, max - 1)}…` : flat
}

function hhmm(ms: number): string {
  const d = new Date(ms)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 設定提醒、狀態列，並推播到手機（使用者正在看畫面時系統會自動略過）
async function raise($: EngineInterface, kind: AlertKind, text: string) {
  const at = hhmm(await $.clock.now())
  await update($, alert, () => ({ kind, text, at }))
  $.ui.status(`${STYLE[kind].icon} ${STYLE[kind].title}`)

  const message = oneLine(`${STYLE[kind].title}${text ? `：${text}` : ''}`, 180)
  try {
    await $.tool.call({ tool: 'PushNotification', message, status: 'proactive' })
  } catch {
    // 推播失敗（未連 Remote Control 等）不影響畫面提醒
  }
}

async function clear($: EngineInterface, only?: ReadonlySet<AlertKind>) {
  const current = await read($, alert)
  if (current !== null && (only === undefined || only.has(current.kind))) {
    await update($, alert, () => null)
    $.ui.status(undefined)
  }
}

export const register: Register = on => {
  // AskUserQuestion：問題出現時提醒，回答後清除
  on('tool.call', { tool: 'AskUserQuestion' }, async ($, e, next) => {
    const first = e.questions[0]
    await raise($, 'ask', first ? oneLine(first.question, 120) : '')
    try {
      return await next(e)
    } finally {
      await clear($, WAITING)
    }
  }).catch(($, e, next) => next(e))

  // 權限核准對話框：出現時提醒
  on('classic.PermissionRequest', async ($, e, next) => {
    // AskUserQuestion 也會走這裡，已由上面的「需要你裁決」處理
    if (e.tool_name === 'AskUserQuestion') {
      return next(e)
    }
    // 對話框出現時輸入框上方的色塊會被蓋住，改在對話框下方加一行提示
    const id = [...pending].reverse().find(([, tool]) => tool === e.tool_name)?.[0]
    if (id !== undefined) {
      try {
        $.ui.notice(id, `⚠ 等待你核准：${e.tool_name}`)
      } catch {
        // 對話框尚未開啟時會被拒絕，略過
      }
    }
    await raise($, 'permission', e.tool_name)
    return next(e)
  }).catch(($, e, next) => next(e))

  // 記下執行中的工具呼叫，讓核准對話框找得到自己的 tool_use_id；跑完（含核准已回應）就清除「等待核准」
  on('tool.call', async ($, e, next) => {
    pending.set(e.tool_use_id, e.tool)
    try {
      return await next(e)
    } finally {
      pending.delete(e.tool_use_id)
      if (e.tool !== 'PushNotification') {
        await clear($, new Set(['permission']))
      }
    }
  }).catch(($, e, next) => next(e))

  // 主迴圈一輪結束：完成或錯誤（使用者自己中斷不提醒）
  on('turn.complete', async ($, e, next) => {
    if (e.agentId === undefined) {
      if (e.reason === 'answer') {
        await raise($, 'done', oneLine(e.answer, 100))
      } else if (e.reason === 'error' || e.reason === 'refusal') {
        await raise($, 'error', '')
      } else {
        await clear($)
      }
    }
    return next(e)
  })

  // 使用者自己送出新訊息就清除
  on('prompt.submit', async ($, e, next) => {
    if (e.origin === undefined || HUMAN_ORIGINS.has(e.origin.kind)) {
      await clear($)
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  // 選擇題對話框會取代輸入框上方區域，把紅色標題放進對話框頂端
  on('ui.render', { component: 'AskUserQuestion' }, async ($, e, next) => {
    const dialog = await next(e)
    const { Box, Text } = $.ui.resolve(e)

    return (
      <Box flexDirection="column">
        <Text bold color="inverseText" backgroundColor="error">
          {' ⚠ 需要你裁決 '}
        </Text>
        {dialog}
      </Box>
    )
  }).catch(($, e, next) => next(e))

  // 輸入框上方的醒目色塊，疊在其他 mod（如 agent-progress-bar）的內容上方
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const current = await read($, alert)
    if (e.props.hasSurvey || current === null) {
      return next(e)
    }

    const { Box, Button, Text } = $.ui.resolve(e)
    const s = STYLE[current.kind]
    // 其他 mod 畫的內容才疊上；app 自己的空白區塊（engine 節點）不能放進樹裡
    const beneath = await next(e)
    const below = isPluginTree(beneath) ? beneath : null

    return (
      <Box flexDirection="column">
        <Box>
          <Text bold color="inverseText" backgroundColor={s.bg}>
            {` ${s.icon} ${s.title}  ${current.at} `}
          </Text>
          <Text>{' '}</Text>
          {!WAITING.has(current.kind) && (
            <Button key="dismiss" label="知道了" onPress={() => clear($)} />
          )}
        </Box>
        {current.text !== '' && <Text color={s.bg}>{`  ${current.text}`}</Text>}
        {below}
      </Box>
    )
  })
}
