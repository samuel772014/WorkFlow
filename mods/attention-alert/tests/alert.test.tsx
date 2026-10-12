import { expect, mock, test } from 'claude-code/testing'

const BAND = {
  plugin: 'attention-alert',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 80 },
} as const

test('完成／裁決時顯示醒目色塊並推播', async ($, on) => {
  mock.clock(on, { now: Date.UTC(2026, 9, 12, 6, 30) })
  const pushed: string[] = []
  on('tool.call', { tool: 'PushNotification' }, ($, e) => {
    pushed.push(e.message)
    return { result: 'sent' } as never
  })
  on('tool.call', { tool: 'AskUserQuestion' }, () => ({ result: 'ok' }) as never)
  on('turn.complete', () => ({ text: '' }))
  on('prompt.submit', ($, e) => ({ text: e.text }))
  on('ui.status', () => ({ value: undefined }))
  on('ui.render', { component: 'AbovePrompt' }, () => ({ type: 'engine', ref: 0 }) as never)

  // 主迴圈完成 → 綠色「工作完成」
  await $.turn.complete({ answer: '全部改好了', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer' })
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface } as never)
    const head = await ui.find({ type: 'Text', text: /工作完成/ })
    expect(head?.props.backgroundColor).toBe('success')
    expect(await ui.find({ type: 'Text', text: /全部改好了/ })).toBeDefined()
    await ui.unmount()
  }
  expect(pushed.at(-1)).toMatch(/工作完成.*：全部改好了/)

  // 子代理完成不提醒
  const before = pushed.length
  await $.turn.complete({ answer: 'x', durationMs: 1, isAborted: false, turnId: 't2', agentId: 'a1', reason: 'answer' })
  expect(pushed.length).toBe(before)

  // 「知道了」可關掉
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' } as never)
  await ui.press({ key: 'dismiss' })
  expect(await ui.find({ type: 'Text', text: /工作完成/ })).toBeUndefined()

  // AskUserQuestion 回答後清除，並有推播
  await $.tool.call({
    tool: 'AskUserQuestion',
    questions: [{ question: '要用哪個方案？', header: '方案', multiSelect: false, options: [{ label: 'A', description: 'a' }, { label: 'B', description: 'b' }] }],
  } as never)
  expect(pushed.at(-1)).toMatch(/需要你裁決：要用哪個方案/)
  expect(await ui.find({ type: 'Text', text: /需要你裁決/ })).toBeUndefined()

  // 錯誤結束 → 紅色
  await $.turn.complete({ answer: '', durationMs: 1, isAborted: false, turnId: 't3', reason: 'error' })
  expect((await ui.find({ type: 'Text', text: /工作中斷/ }))?.props.backgroundColor).toBe('error')

  // 使用者送出新訊息 → 清除
  await $.prompt.submit({ text: '繼續', wait: false } as never)
  expect(await ui.find({ type: 'Text', text: /工作中斷/ })).toBeUndefined()
})
