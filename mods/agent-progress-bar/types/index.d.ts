export type RunStatus = 'running' | 'done' | 'failed'
export type RunKind = 'agent' | 'shell' | 'monitor' | 'other'
export type AgentRun = { id: string; kind: RunKind; description: string; type: string; status: RunStatus }

declare module 'claude-code' {
  interface PluginState {
    'agent-progress-bar': { runs: AgentRun[]; isCollapsed: boolean }
  }
}
