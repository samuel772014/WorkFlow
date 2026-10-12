export type AgentRunStatus = 'running' | 'done' | 'failed'
export type AgentRun = { id: string; description: string; type: string; status: AgentRunStatus }

declare module 'claude-code' {
  interface PluginState {
    'agent-progress-bar': { runs: AgentRun[]; isCollapsed: boolean }
  }
}
