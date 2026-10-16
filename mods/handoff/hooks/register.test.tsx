import { expect, test } from 'claude-code/testing'

const usageAt = (percent: number) => () => ({
  value: { startedAt: 0, context: { tokens: 1, window: 100, percent }, rateLimits: [] },
})
const DONE = { answer: 'ok', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer' } as const
const PROPS = { hasSurvey: false, isWorking: false, maxRows: 10 } as never
const emptyBand = ($: any, e: any) => {
  const { Box } = $.ui.resolve(e)
  return <Box />
}

test('未達 70% 不出現按鈕', async ($, on) => {
  on('session.usage', usageAt(50))
  on('ui.render', emptyBand)
  on('turn.complete', () => ({ text: 'ok' }))
  await $.turn.complete(DONE)
  const ui = await $.ui.mount({ plugin: 'handoff', surface: 'terminal', component: 'AbovePrompt', props: PROPS })
  expect(await ui.find({ key: 'handoff' })).toBeUndefined()
})

test('達 70% 出現按鈕，按下：摘要→存檔→清空→送出摘要', async ($, on) => {
  const calls: string[] = []
  let written = ''
  let submitted = ''
  on('session.usage', usageAt(72))
  on('ui.render', emptyBand)
  on('turn.complete', () => ({ text: 'ok' }))
  on('model.fork', () => (calls.push('fork'), { value: { isAnswered: true, text: '## 目前的目標\n測試', usage: {} } }) as never)
  on('fs.write', (_$, e: any) => (calls.push('write'), (written = String(e.path ?? e[0] ?? '')), { value: undefined }) as never)
  on('command.run', (_$, e) => (calls.push(`/${e.command}`), {}))
  on('prompt.submit', (_$, e) => (calls.push('submit'), (submitted = e.text), { text: e.text }))

  await $.turn.complete(DONE)
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ plugin: 'handoff', surface, component: 'AbovePrompt', props: PROPS })
    expect(await ui.find({ key: 'handoff' })).toBeDefined()
    expect(JSON.stringify(await ui.drawn())).toMatch(/已用.*72.*%/)
  }

  const ui = await $.ui.mount({ plugin: 'handoff', surface: 'terminal', component: 'AbovePrompt', props: PROPS })
  await ui.press({ key: 'handoff' })

  expect(calls).toEqual(['fork', 'write', '/clear', 'submit'])
  expect(submitted).toContain('## 目前的目標')
  expect(submitted).toContain('.claude/handoff/handoff-')
  console.log('written:', written)
})
