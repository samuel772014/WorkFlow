import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

const turns = atom({ plugin: 'retro-button', key: 'turns' } as const, 0)
const isHidden = atom({ plugin: 'retro-button', key: 'isHidden' } as const, false)
const isRetroDone = atom({ plugin: 'retro-button', key: 'isRetroDone' } as const, false)

export const register: Register = on => {
  // 每完成一輪工作就累計，有工作過才顯示按鈕
  on('turn.complete', async ($, e, next) => {
    await update($, turns, n => n + 1)

    return next(e)
  })

  // 使用者自己打 /retro 也視為已回顧
  on('command.run', { command: 'retro' }, async ($, e, next) => {
    await update($, isRetroDone, () => true)

    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const isQuiet =
      e.props.hasSurvey ||
      e.props.isWorking ||
      (await read($, turns)) === 0 ||
      (await read($, isHidden)) ||
      (await read($, isRetroDone))

    if (isQuiet) {
      return next(e)
    }

    const { Box, Button, Text } = $.ui.resolve(e)

    return (
      <Box>
        <Text dimColor>Session 要結束了嗎？ </Text>
        <Button
          key="retro"
          label="回顧此 session (/retro)"
          onPress={async () => {
            await update($, isRetroDone, () => true)
            try {
              await $.command.run({ command: 'retro' })
            } catch {
              await update($, isRetroDone, () => false)
              $.ui.toast('找不到 /retro 指令，請確認 .claude/skills/retro 存在')
            }
          }}
        />
        <Text> </Text>
        <Button key="hide" label="隱藏" onPress={() => update($, isHidden, () => true)} />
      </Box>
    )
  })
}
