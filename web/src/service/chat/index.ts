/**
 * 聊天模块统一导出
 * 提供所有聊天相关的服务接口
 */

// 导出类型定义
export type * from './types';
export { AI_INFO, SYSTEM_INFO, CACHE_TIME } from './types';

// 导出状态管理
export { ChatStateManager, chatState } from './state';

// 导出API服务
export { ChatApiService } from './api';

// 导出WebSocket管理
export { ChatWebSocketManager, chatWebSocket } from './websocket'; 