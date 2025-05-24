"""
WebSocket连接管理器 - 专注于连接管理和消息广播
"""
from typing import Dict, List, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime

from .events import event_bus, EventTypes, create_user_event, create_system_event

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """WebSocket连接封装"""
    
    def __init__(self, websocket: WebSocket, user_id: str, conversation_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.connected_at = datetime.now()
        self.last_ping = datetime.now()
    
    async def send_json(self, data: Dict[str, Any]):
        """发送JSON消息"""
        try:
            await self.websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"发送消息失败: user_id={self.user_id}, 错误={e}")
            return False
    
    async def close(self, code: int = 1000):
        """关闭连接"""
        try:
            await self.websocket.close(code)
        except Exception as e:
            logger.error(f"关闭连接失败: user_id={self.user_id}, 错误={e}")


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 按会话ID组织的连接
        self._connections_by_conversation: Dict[str, List[WebSocketConnection]] = {}
        # 按用户ID组织的连接
        self._connections_by_user: Dict[str, List[WebSocketConnection]] = {}
        # 所有连接的映射
        self._all_connections: Dict[WebSocket, WebSocketConnection] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, conversation_id: str) -> WebSocketConnection:
        """建立WebSocket连接"""
        await websocket.accept()
        
        connection = WebSocketConnection(websocket, user_id, conversation_id)
        
        # 添加到各种映射中
        self._all_connections[websocket] = connection
        
        if conversation_id not in self._connections_by_conversation:
            self._connections_by_conversation[conversation_id] = []
        self._connections_by_conversation[conversation_id].append(connection)
        
        if user_id not in self._connections_by_user:
            self._connections_by_user[user_id] = []
        self._connections_by_user[user_id].append(connection)
        
        logger.info(f"WebSocket连接已建立: user_id={user_id}, conversation_id={conversation_id}")
        
        # 发布连接事件
        event = create_user_event(
            EventTypes.WS_CONNECT,
            user_id=user_id,
            conversation_id=conversation_id,
            connection_time=connection.connected_at.isoformat()
        )
        await event_bus.publish_async(event)
        
        return connection
    
    async def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket not in self._all_connections:
            return
        
        connection = self._all_connections[websocket]
        user_id = connection.user_id
        conversation_id = connection.conversation_id
        
        # 从各种映射中移除
        del self._all_connections[websocket]
        
        if conversation_id in self._connections_by_conversation:
            if connection in self._connections_by_conversation[conversation_id]:
                self._connections_by_conversation[conversation_id].remove(connection)
            if not self._connections_by_conversation[conversation_id]:
                del self._connections_by_conversation[conversation_id]
        
        if user_id in self._connections_by_user:
            if connection in self._connections_by_user[user_id]:
                self._connections_by_user[user_id].remove(connection)
            if not self._connections_by_user[user_id]:
                del self._connections_by_user[user_id]
        
        logger.info(f"WebSocket连接已断开: user_id={user_id}, conversation_id={conversation_id}")
        
        # 发布断开事件
        event = create_user_event(
            EventTypes.WS_DISCONNECT,
            user_id=user_id,
            conversation_id=conversation_id,
            disconnect_time=datetime.now().isoformat()
        )
        await event_bus.publish_async(event)
    
    async def broadcast_to_conversation(self, conversation_id: str, message: Dict[str, Any], exclude_user: str = None):
        """向会话中的所有用户广播消息"""
        if conversation_id not in self._connections_by_conversation:
            logger.warning(f"尝试广播到不存在的会话: {conversation_id}")
            return
        
        connections = self._connections_by_conversation[conversation_id]
        logger.info(f"广播消息到会话 {conversation_id}, 连接数: {len(connections)}")
        
        disconnected_connections = []
        success_count = 0
        
        for connection in connections:
            # 排除指定用户
            if exclude_user and connection.user_id == exclude_user:
                continue
            
            success = await connection.send_json(message)
            if success:
                success_count += 1
            else:
                disconnected_connections.append(connection)
        
        # 清理断开的连接
        for connection in disconnected_connections:
            await self.disconnect(connection.websocket)
        
        logger.info(f"广播完成: 成功={success_count}, 失败={len(disconnected_connections)}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """向指定用户发送消息"""
        if user_id not in self._connections_by_user:
            logger.warning(f"用户未连接: {user_id}")
            return False
        
        connections = self._connections_by_user[user_id]
        success_count = 0
        
        for connection in connections:
            success = await connection.send_json(message)
            if success:
                success_count += 1
        
        return success_count > 0
    
    def get_conversation_users(self, conversation_id: str) -> List[str]:
        """获取会话中的所有用户ID"""
        if conversation_id not in self._connections_by_conversation:
            return []
        
        return [conn.user_id for conn in self._connections_by_conversation[conversation_id]]
    
    def get_user_conversations(self, user_id: str) -> List[str]:
        """获取用户参与的所有会话ID"""
        if user_id not in self._connections_by_user:
            return []
        
        return [conn.conversation_id for conn in self._connections_by_user[user_id]]
    
    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self._connections_by_user
    
    def get_connection_count(self, conversation_id: str = None) -> int:
        """获取连接数"""
        if conversation_id:
            return len(self._connections_by_conversation.get(conversation_id, []))
        return len(self._all_connections)
    
    async def ping_all(self):
        """向所有连接发送心跳"""
        ping_message = {
            "action": "ping",
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected_connections = []
        
        for connection in self._all_connections.values():
            success = await connection.send_json(ping_message)
            if success:
                connection.last_ping = datetime.now()
            else:
                disconnected_connections.append(connection)
        
        # 清理断开的连接
        for connection in disconnected_connections:
            await self.disconnect(connection.websocket)


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager() 