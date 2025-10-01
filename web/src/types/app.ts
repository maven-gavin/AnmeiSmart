export type AppIconType = 'image' | 'emoji'

/**
 * App modes
 */
export const AppModes = ['advanced-chat', 'agent-chat', 'chat', 'completion', 'workflow'] as const
export type AppMode = typeof AppModes[number]
