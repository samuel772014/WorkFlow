import { expect, test } from 'claude-code/testing'

const PROPS = { hasSurvey: false, isWorking: false, maxRows: 10 }

for (const surface of ['terminal', 'desktop'] as const) {
  test(`${surface}: 有工作過才顯示按鈕，按下執行 /retro 後隱藏`, async ($, on) => {
    const ran: string[] = []
    on('command.run', ($, e) => {
      ran.push(e.command)
      return { text: '' }
    })
    on('turn.complete', () => ({ text: '' }))
    on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
      const { Box } = $.ui.resolve(e)
      return h(Box, { key: 'engine' })
    })
    const mount = () => $.ui.mount({ plugin: 'retro-button', surface, component: 'AbovePrompt', props: PROPS })

    const before = await mount()
    expect(await before.find({ key: 'retro' })).toBeUndefined()
    await before.unmount()

    await $.turn.complete({ reason: 'answer' } as never)
    const ui = await mount()
    expect(await ui.find({ key: 'retro' })).toBeDefined()

    await ui.press({ key: 'retro' })
    expect(ran).toEqual(['retro'])
    expect(await ui.find({ key: 'retro' })).toBeUndefined()
  })
}
