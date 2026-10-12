export type AlertKind = 'ask' | 'permission' | 'done' | 'error'
export type Alert = { kind: AlertKind; text: string; at: string }

declare module 'claude-code' {
  interface PluginState {
    'attention-alert': { alert: Alert | null }
  }
}
