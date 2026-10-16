import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { UsageSnapshot } from '../types'

const snapshot = atom({ plugin: 'usage-band', key: 'snapshot' } as const, null)

const RED_AT = 80

const pad = (n: number) => String(n).padStart(2, '0')

export const formatReset = (iso?: string): string | undefined => {
  if (!iso) return undefined
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return undefined
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const capture = async ($: EngineInterface) => {
  const usage = await $.session.usage()
  const five = usage.rateLimits.find(r => r.kind === 'five_hour')
  const week = usage.rateLimits.find(r => r.kind === 'seven_day')
  const next: UsageSnapshot = {
    context: usage.context.percent,
    fiveHour: five?.percentUsed,
    fiveHourResetsAt: five?.resetsAt,
    week: week?.percentUsed,
  }
  await update($, snapshot, () => next)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    await capture($).catch(() => undefined)
    return result
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    await capture($).catch(() => undefined)
    return result
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const snap = await read($, snapshot)
    if (e.props.hasSurvey || snap === null) {
      return next(e)
    }

    const { Box, Text } = $.ui.resolve(e)
    const item = (label: string, pct: number | undefined, suffix = '') => {
      const isHot = pct !== undefined && pct >= RED_AT
      const value = pct === undefined ? '—' : `${Math.round(pct)}%`
      return isHot ? (
        <Text color="red" bold>
          {label} {value}
          {suffix}
        </Text>
      ) : (
        <Text dimColor>
          {label} {value}
          {suffix}
        </Text>
      )
    }
    const reset = formatReset(snap.fiveHourResetsAt)
    const sep = <Text dimColor>  │  </Text>

    return (
      <Box>
        {item('Context', snap.context)}
        {sep}
        {item('5h', snap.fiveHour, reset ? ` (${reset} 重置)` : '')}
        {sep}
        {item('本週', snap.week)}
      </Box>
    )
  })
}
