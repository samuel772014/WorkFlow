import { expect, test } from 'claude-code/testing'

const BAND = {
  plugin: 'agent-progress-bar',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: true, maxRows: 10, bodyColumns: 100 },
} as const

test('背景作業：Agent、背景指令、Monitor 都計入，通知與對帳會結束', async ($, on) => {
  let n = 0
  on('agent.spawn', () => ({ model: 'haiku', agentId: `a${++n}` }))
  on('tool.call', { tool: 'Bash' }, () => ({ result: { stdout: '', stderr: '', interrupted: false, backgroundTaskId: 'b1' } }) as never)
  on('tool.call', { tool: 'Monitor' }, () => ({ result: { taskId: 'm1', timeoutMs: 0 } }) as never)
  on('turn.complete', () => ({ text: '' }))
  on('prompt.submit', ($, e) => ({ text: e.text }))
  on('classic.Stop', () => ({}) as never)
  on('ui.status', () => ({ value: undefined }))
  on('ui.render', { component: 'AbovePrompt' }, () => ({ type: 'engine', ref: 0 }) as never)

  await $.agent.spawn({ prompt: 'x', description: '查欄位', subagentType: 'Explore' })
  await $.tool.call({ tool: 'Bash', command: 'sleep 30', description: '等待 30 秒', run_in_background: true } as never)
  await $.tool.call({ tool: 'Monitor', description: '監看 build', timeout_ms: 1000, command: 'x' } as never)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface } as never)
    expect(await ui.find({ type: 'Text', text: /0\/3 \(0%\)/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /執行中 3/ })).toBeDefined()
    expect((await ui.find({ type: 'Text', text: /◐ \[指令\] 等待 30 秒/ }))?.props.color).toBe('error')
    expect(await ui.find({ type: 'Text', text: /◐ \[監看\] 監看 build/ })).toBeDefined()
    await ui.unmount()
  }

  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' } as never)

  // 背景指令完成通知
  await $.prompt.submit({
    text: '<task-notification><task-id>b1</task-id><status>completed</status></task-notification>',
    wait: false,
    origin: { kind: 'task-notification' },
  } as never)
  expect((await ui.find({ type: 'Text', text: /✔ \[指令\] 等待 30 秒/ }))?.props.color).toBe('success')

  // 子代理完成
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 't1', agentId: 'a1', reason: 'answer' })
  expect(await ui.find({ type: 'Text', text: /2\/3/ })).toBeDefined()

  // 對帳：app 回報沒有執行中的 m1，另有一個漏追的 shell
  await $.classic.Stop({
    stop_hook_active: false,
    background_tasks: [{ id: 'x9', type: 'shell', status: 'running', description: 'npm run dev' }],
  } as never)
  expect(await ui.find({ type: 'Text', text: /✔ \[監看\] 監看 build/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /◐ \[指令\] npm run dev/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /3\/4 .*執行中 1/ })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: /執行中 1/ })).toBeDefined()

  // 收合／展開
  await ui.press({ key: 'toggle' })
  expect(await ui.find({ type: 'Text', text: /npm run dev/ })).toBeUndefined()
  await ui.press({ key: 'toggle' })
  expect(await ui.find({ type: 'Text', text: /npm run dev/ })).toBeDefined()

  // 還有執行中的作業時，使用者送出訊息不清空
  await $.prompt.submit({ text: '繼續', wait: false } as never)
  expect(await ui.find({ type: 'Text', text: /npm run dev/ })).toBeDefined()
})
