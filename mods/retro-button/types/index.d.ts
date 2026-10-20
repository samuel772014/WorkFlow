export type RetroCount = number

declare module 'claude-code' {
  interface PluginState {
    'retro-button': { turns: number; isHidden: boolean; isRetroDone: boolean }
  }
}
