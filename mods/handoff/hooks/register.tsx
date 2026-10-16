import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { HandoffPhase } from '../types'

const percent = atom({ plugin: 'handoff', key: 'percent' } as const, null)
const phase = atom({ plugin: 'handoff', key: 'phase' } as const, 'idle')
const error = atom({ plugin: 'handoff', key: 'error' } as const, null)

const SHOW_AT = 70

export const SUMMARY_PROMPT = `請為這段對話寫一份交接摘要，讓一個完全沒有看過這段對話的新 session 可以直接接手。用繁體中文、Markdown，依序包含以下章節：

## 目前的目標
## 已完成
## 尚未完成（依優先順序）
## 改過的檔案（完整路徑，每個附一句說明改了什麼）
## 注意事項（使用者的裁決與偏好、踩過的坑、不可做的事、待確認問題）

只寫事實，不要推測；沒有內容的章節寫「無」。直接輸出摘要本身，不要前言或結語。`

const pad = (n: number) => String(n).padStart(2, '0')

export const stamp = (d: Date) =>
  `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`

const setPhase = ($: EngineInterface, p: HandoffPhase, message: string | null = null) =>
  Promise.all([update($, phase, () => p), update($, error, () => message)])

const measure = async ($: EngineInterface) => {
  const { context } = await $.session.usage()
  await update($, percent, () => context.percent ?? null)
}

export const runHandoff = async ($: EngineInterface) => {
  if ((await read($, phase)) === 'summarizing' || (await read($, phase)) === 'clearing') return
  await setPhase($, 'summarizing')
  try {
    const reply = await $.model.fork({ prompt: SUMMARY_PROMPT })
    if (!reply.isAnswered) {
      await setPhase($, 'error', `摘要產生失敗：${reply.reason}`)
      return
    }
    const summary = reply.text.trim()
    const path = `.claude/handoff/handoff-${stamp(new Date())}.md`
    await $.fs.write(path, `${summary}\n`)

    await setPhase($, 'clearing')
    await $.command.run({ command: 'clear' })

    const first = `以下是上一段對話的交接摘要（已存於 ${path}），請讀完後接續工作：\n\n${summary}`
    await setPhase($, 'idle')
    await update($, percent, () => null)
    await $.prompt.submit({ text: first, asUser: true })
  } catch (err) {
    await setPhase($, 'error', `交接失敗：${err instanceof Error ? err.message : String(err)}`)
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    await measure($).catch(() => undefined)
    return result
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    await measure($).catch(() => undefined)
    return result
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const pct = await read($, percent)
    const p = await read($, phase)
    const message = await read($, error)
    const isBusy = p === 'summarizing' || p === 'clearing'
    const isDue = pct !== null && pct >= SHOW_AT

    if (e.props.hasSurvey || (!isDue && !isBusy && p !== 'error')) {
      return next(e)
    }

    const { Box, Button, Text } = $.ui.resolve(e)
    // 保留其他 mod（如 usage-band）在同一條帶上畫的內容
    const below = await next(e)

    if (isBusy) {
      return (
        <Box flexDirection="column">
          {below}
          <Text color="yellow">{p === 'summarizing' ? '交接中：正在寫交接摘要…' : '交接中：清空對話並開新對話…'}</Text>
        </Box>
      )
    }

    return (
      <Box flexDirection="column">
        {below}
        <Box>
          {p === 'error' ? (
            <Text color="red">{message} </Text>
          ) : (
            <Text color="yellow">Context 已用 {Math.round(pct ?? 0)}%，建議交接 </Text>
          )}
          <Button key="handoff" label={p === 'error' ? '重試交接' : '交接'} onPress={() => runHandoff($)} />
        </Box>
      </Box>
    )
  })
}
