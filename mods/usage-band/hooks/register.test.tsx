import { expect, test } from 'claude-code/testing'

test('turn.complete 後顯示三項，>=80% 變紅', async ($, on) => {
  on('session.usage', () => ({ value: {
    startedAt: 0,
    context: { tokens: 1000, window: 200000, percent: 42 },
    rateLimits: [
      { kind: 'five_hour', percentUsed: 85.5, resetsAt: '2026-10-16T10:30:00Z' },
      { kind: 'seven_day', percentUsed: 30 },
    ],
  } }))
  on('ui.render', () => null as never)
  on('turn.complete', () => ({ text: 'ok' }))

  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer' })

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({
      plugin: 'usage-band',
      surface,
      component: 'AbovePrompt',
      props: { hasSurvey: false, isWorking: false, maxRows: 10 } as never,
    })
    const tree = JSON.stringify(await ui.drawn())
    expect(tree).toContain('Context')
    expect(tree).toContain('42%')
    expect(tree).toContain('86%')
    expect(tree).toContain('重置')
    expect(tree).toContain('30%')
    const hot = await ui.find({ type: 'Text', text: /5h/ })
    expect(JSON.stringify(hot)).toContain('red')
    const cool = await ui.find({ type: 'Text', text: /本週/ })
    expect(JSON.stringify(cool)).not.toContain('red')
  }
})
