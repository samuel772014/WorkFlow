export type HandoffPhase = 'idle' | 'summarizing' | 'clearing' | 'error'

declare module 'claude-code' {
  interface PluginState {
    handoff: { percent: number | null; phase: HandoffPhase; error: string | null }
  }
}
