import { expect, mock, test } from 'claude-code/testing'

test('AskUserQuestion 的權限事件不覆蓋「需要你裁決」；其他工具顯示「等待你核准」', async ($, on) => {
  mock.clock(on)
  const pushed: string[] = []
  on('tool.call', { tool: 'PushNotification' }, ($, e) => {
    pushed.push(e.message)
    return { result: 'sent' } as never
  })
  on('classic.PermissionRequest', () => ({}) as never)
  on('ui.status', () => ({ value: undefined }))

  await $.classic.PermissionRequest({ tool_name: 'AskUserQuestion', tool_input: {} } as never)
  expect(pushed.length).toBe(0)

  await $.classic.PermissionRequest({ tool_name: 'Bash', tool_input: {} } as never)
  expect(pushed.at(-1)).toMatch(/等待你核准：Bash/)
})
