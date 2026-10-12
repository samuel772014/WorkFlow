import { expect, test } from 'claude-code/testing'

test('選擇題對話框頂端加上紅色「需要你裁決」', async ($, on) => {
  on('ui.render', { component: 'AskUserQuestion' }, () => ({ type: 'engine', ref: 0 }) as never)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({
      plugin: 'attention-alert',
      surface,
      component: 'AskUserQuestion',
      props: { tool: 'AskUserQuestion', questions: [] },
    } as never)
    expect((await ui.find({ type: 'Text', text: /需要你裁決/ }))?.props.backgroundColor).toBe('error')
    await ui.unmount()
  }
})
