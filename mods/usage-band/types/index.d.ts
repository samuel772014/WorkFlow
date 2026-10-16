export type UsageSnapshot = {
  context?: number
  fiveHour?: number
  fiveHourResetsAt?: string
  week?: number
}

declare module 'claude-code' {
  interface PluginState {
    'usage-band': { snapshot: UsageSnapshot | null }
  }
}
