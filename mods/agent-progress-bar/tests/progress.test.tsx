import { expect, test } from 'claude-code/testing'

const BAND = {
  plugin: 'agent-progress-bar',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: true, maxRows: 10, bodyColumns: 80 },
} as const

test('進度帶：顏色、收合展開、全部完成自動收合', async ($, on) => {
  let n = 0
  on('agent.spawn', () => ({ model: 'haiku', agentId: `a${++n}` }))
  on('turn.complete', () => ({ text: '' }))
  on('prompt.submit', ($, e) => ({ text: e.text }))
  on('ui.status', () => ({ value: undefined }))
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Box } = $.ui.resolve(e)
    return <Box />
  })

  await $.agent.spawn({ prompt: 'x', description: '查欄位', subagentType: 'Explore' })
  await $.agent.spawn({ prompt: 'y', description: '寫API', subagentType: 'general-purpose' })
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't1', agentId: 'a1', reason: 'answer' })
  // 子代理回報以通知形式送入，不應清空
  await $.prompt.submit({ text: 'done', wait: false, origin: { kind: 'task-notification' } } as never)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface } as never)
    expect(await ui.find({ type: 'Text', text: /1\/2 \(50%\)/ })).toBeDefined()
    expect((await ui.find({ type: 'Text', text: /✔ 查欄位/ }))?.props.color).toBe('success')
    expect((await ui.find({ type: 'Text', text: /◐ 寫API/ }))?.props.color).toBe('error')
    await ui.unmount()
  }

  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' } as never)
  await ui.press({ key: 'toggle' })
  expect(await ui.find({ type: 'Text', text: /寫API/ })).toBeUndefined()
  await ui.press({ key: 'toggle' })
  expect(await ui.find({ type: 'Text', text: /寫API/ })).toBeDefined()

  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't2', agentId: 'a2', reason: 'answer' })
  expect(await ui.find({ type: 'Text', text: /2\/2 \(100%\)/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /寫API/ })).toBeUndefined()
})
