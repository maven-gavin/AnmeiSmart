"""
WebSocket连接管理器 - 专注于连接管理和消息广播
"""
from typing import Dict, List, Any, Optional
from fastapi import WebSocket
import logging
import asyncio
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
        self._is_closed = False
    
    async def send_json(self, data: Dict[str, Any]) -> bool:
        """发送JSON消息"""
        if self._is_closed:
            return False
            
        try:
            await self.websocket.send_json(data)
            self.last_ping = datetime.now()  # 更新最后活动时间
            return True
        except Exception as e:
            logger.error(f"发送消息失败: user_id={self.user_id}, 错误={e}")
            return False
    
    async def close(self, code: int = 1000):
        """关闭连接"""
        if self._is_closed:
            return
            
        try:
            await self.websocket.close(code)
            self._is_closed = True
        except Exception as e:
            logger.error(f"关闭连接失败: user_id={self.user_id}, 错误={e}")
    
    @property
    def is_connected(self) -> bool:
        """检查连接是否仍然活跃"""
        return not self._is_closed


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 异步锁，确保并发安全
        self._lock = asyncio.Lock()
        # 按会话ID组织的连接
        self._connections_by_conversation: Dict[str, List[WebSocketConnection]] = {}
        # 按用户ID组织的连接
        self._connections_by_user: Dict[str, List[WebSocketConnection]] = {}
        # 所有连接的映射
        self._all_connections: Dict[WebSocket, WebSocketConnection] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, conversation_id: str) -> WebSocketConnection:
        """建立WebSocket连接"""
        async with self._lock:
            try:
                await websocket.accept()
            except Exception as e:
                logger.error(f"接受WebSocket连接失败: user_id={user_id}, 错误={e}")
                raise
            
            # 检查是否已存在相同用户的连接（可选：断开旧连接）
            existing_connections = [
                conn for conn in self._connections_by_user.get(user_id, [])
                if conn.conversation_id == conversation_id and conn.is_connected
            ]
            
            if existing_connections:
                logger.info(f"用户 {user_id} 在会话 {conversation_id} 中已有连接，断开旧连接")
                for old_conn in existing_connections:
                    await self.disconnect(old_conn.websocket)
            
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
            try:
                event = create_user_event(
                    EventTypes.WS_CONNECT,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    connection_time=connection.connected_at.isoformat()
                )
                await event_bus.publish_async(event)
            except Exception as e:
                logger.error(f"发布连接事件失败: user_id={user_id}, 错误={e}")
            
            return connection
    
    async def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        async with self._lock:
            if websocket not in self._all_connections:
                return
            
            connection = self._all_connections[websocket]
            user_id = connection.user_id
            conversation_id = connection.conversation_id
            
            try:
                # 主动关闭WebSocket连接
                await connection.close()
            except Exception as e:
                logger.warning(f"关闭WebSocket连接时出错: user_id={user_id}, 错误={e}")
            
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
        
        # 发布断开事件（在锁外执行，避免阻塞）
        try:
            event = create_user_event(
                EventTypes.WS_DISCONNECT,
                user_id=user_id,
                conversation_id=conversation_id,
                disconnect_time=datetime.now().isoformat()
            )
            await event_bus.publish_async(event)
        except Exception as e:
            logger.error(f"发布断开事件失败: user_id={user_id}, 错误={e}")
    
    async def broadcast_to_conversation(self, conversation_id: str, message: Dict[str, Any], exclude_user: Optional[str] = None):
        """向会话中的所有用户广播消息"""
        if conversation_id not in self._connections_by_conversation:
            logger.warning(f"尝试广播到不存在的会话: {conversation_id}")
            return
        
        connections = self._connections_by_conversation[conversation_id].copy()  # 创建副本避免修改原列表
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
        
        # 清理断开的连接（使用更安全的方式）
        for connection in disconnected_connections:
            try:
                await self.disconnect(connection.websocket)
            except Exception as e:
                logger.error(f"清理断开连接时出错: user_id={connection.user_id}, 错误={e}")
        
        logger.info(f"广播完成: 成功={success_count}, 失败={len(disconnected_connections)}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """向指定用户发送消息
        
        Args:
            user_id: 用户ID
            message: 要发送的消息字典
            
        Returns:
            bool: 是否至少有一个连接成功发送消息
        """
        # 输入参数验证
        if not user_id or not message:
            logger.warning(f"无效参数: user_id={user_id}, message={message}")
            return False
        
        # 获取用户连接（使用锁保护）
        async with self._lock:
            if user_id not in self._connections_by_user:
                logger.warning(f"用户未连接: {user_id}")
                return False
            
            connections = self._connections_by_user[user_id].copy()
        
        if not connections:
            logger.warning(f"用户 {user_id} 没有活跃连接")
            return False
        
        logger.info(f"向用户 {user_id} 发送消息，连接数: {len(connections)}")
        
        success_count = 0
        failed_connections = []
        
        for connection in connections:
            # 检查连接状态
            if not connection.is_connected:
                logger.warning(f"连接已关闭: user_id={user_id}, conversation_id={connection.conversation_id}")
                failed_connections.append(connection)
                continue
            
            try:
                success = await connection.send_json(message)
                if success:
                    success_count += 1
                    logger.debug(f"消息发送成功: user_id={user_id}, conversation_id={connection.conversation_id}")
                else:
                    failed_connections.append(connection)
                    logger.warning(f"消息发送失败: user_id={user_id}, conversation_id={connection.conversation_id}")
            except Exception as e:
                logger.error(f"发送消息时出错: user_id={user_id}, conversation_id={connection.conversation_id}, 错误={e}")
                failed_connections.append(connection)
        
        # 清理失败的连接
        for connection in failed_connections:
            try:
                await self.disconnect(connection.websocket)
            except Exception as e:
                logger.error(f"断开失败连接时出错: user_id={user_id}, 错误={e}")
        
        logger.info(f"用户 {user_id} 消息发送完成: 成功={success_count}, 失败={len(failed_connections)}")
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
    
    def get_connection_count(self, conversation_id: Optional[str] = None) -> int:
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
        
        # 创建副本避免在遍历过程中修改字典
        async with self._lock:
            connections = list(self._all_connections.values())
        
        for connection in connections:
            success = await connection.send_json(ping_message)
            if success:
                connection.last_ping = datetime.now()
            else:
                disconnected_connections.append(connection)
        
        # 清理断开的连接（使用更安全的方式）
        for connection in disconnected_connections:
            try:
                await self.disconnect(connection.websocket)
            except Exception as e:
                logger.error(f"清理断开连接时出错: user_id={connection.user_id}, 错误={e}")
    
    async def cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """清理超时的非活跃连接"""
        cutoff_time = datetime.now().timestamp() - (timeout_minutes * 60)
        inactive_connections = []
        
        async with self._lock:
            for connection in self._all_connections.values():
                if connection.last_ping.timestamp() < cutoff_time:
                    inactive_connections.append(connection)
        
        logger.info(f"发现 {len(inactive_connections)} 个非活跃连接，开始清理")
        
        for connection in inactive_connections:
            try:
                await self.disconnect(connection.websocket)
            except Exception as e:
                logger.error(f"清理非活跃连接时出错: user_id={connection.user_id}, 错误={e}")
        
        logger.info(f"非活跃连接清理完成")


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager() 