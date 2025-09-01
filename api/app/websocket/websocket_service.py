"""
统一WebSocket服务 - 整合连接管理和消息广播
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.websocket.distributed_connection_manager import DistributedConnectionManager
from app.core.websocket.events import event_bus, EventTypes, Event
from app.websocket.broadcasting_service import BroadcastingService
from .websocket_handler import websocket_handler

logger = logging.getLogger(__name__)


class WebSocketService:
    """
    统一WebSocket服务
    - 整合连接管理和消息广播
    - 提供统一的WebSocket接口
    - 支持事件驱动的消息处理
    """
    
    def __init__(self, connection_manager: DistributedConnectionManager, broadcasting_service: BroadcastingService):
        self.connection_manager = connection_manager
        self.broadcasting_service = broadcasting_service
        self.websocket_handler = websocket_handler
        
        # 订阅事件，自动处理消息广播
        self._setup_event_handlers()
        
        logger.info("WebSocket服务已初始化")
    
    def _setup_event_handlers(self):
        """设置事件处理器"""
        # 订阅消息事件，自动广播
        event_bus.subscribe_async(EventTypes.CHAT_MESSAGE_SENT, self._handle_message_event)
        event_bus.subscribe_async(EventTypes.CHAT_TYPING, self._handle_typing_event)
        event_bus.subscribe_async(EventTypes.CHAT_READ, self._handle_read_event)
        event_bus.subscribe_async(EventTypes.SYSTEM_NOTIFICATION, self._handle_system_event)
    
    async def _handle_message_event(self, event: Event):
        """处理消息事件"""
        try:
            conversation_id = event.conversation_id
            if not conversation_id:
                logger.warning("消息事件缺少conversation_id")
                return
            
            # 构造消息数据
            message_data = {
                "id": event.data.get("message_id"),
                "content": event.data.get("content"),
                "type": event.data.get("message_type", "text"),
                "sender_id": event.user_id,
                "sender_type": event.data.get("sender_type", "user"),
                "timestamp": event.timestamp,
                "is_read": False,
                "is_important": event.data.get("is_important", False)
            }
            
            # 使用广播服务发送消息
            await self.broadcasting_service.broadcast_message(
                conversation_id=conversation_id,
                message_data=message_data,
                exclude_user_id=event.user_id
            )
            
        except Exception as e:
            logger.error(f"处理消息事件失败: {e}")
    
    async def _handle_typing_event(self, event: Event):
        """处理输入状态事件"""
        try:
            conversation_id = event.conversation_id
            if not conversation_id:
                return
            
            # 检查user_id是否存在
            if not event.user_id:
                logger.warning("输入状态事件缺少user_id")
                return
            
            is_typing = event.data.get("is_typing", False)
            
            await self.broadcasting_service.broadcast_typing_status(
                conversation_id=conversation_id,
                user_id=event.user_id,
                is_typing=is_typing
            )
            
        except Exception as e:
            logger.error(f"处理输入状态事件失败: {e}")
    
    async def _handle_read_event(self, event: Event):
        """处理已读状态事件"""
        try:
            conversation_id = event.conversation_id
            if not conversation_id:
                return
            
            # 检查user_id是否存在
            if not event.user_id:
                logger.warning("已读状态事件缺少user_id")
                return
            
            message_ids = event.data.get("message_ids", [])
            
            await self.broadcasting_service.broadcast_read_status(
                conversation_id=conversation_id,
                user_id=event.user_id,
                message_ids=message_ids
            )
            
        except Exception as e:
            logger.error(f"处理已读状态事件失败: {e}")
    
    async def _handle_system_event(self, event: Event):
        """处理系统事件"""
        try:
            conversation_id = event.conversation_id
            
            notification_data = {
                "title": event.data.get("title", "系统通知"),
                "message": event.data.get("message", ""),
                "type": event.data.get("type", "info")
            }
            
            if conversation_id:
                await self.broadcasting_service.broadcast_system_notification(
                    conversation_id=conversation_id,
                    notification_data=notification_data
                )
            
        except Exception as e:
            logger.error(f"处理系统事件失败: {e}")
    
    async def connect_user(self, user_id: str, websocket, metadata: Optional[Dict[str, Any]] = None, connection_id: Optional[str] = None) -> bool:
        """连接用户"""
        return await self.connection_manager.connect(user_id, websocket, metadata, connection_id)
    
    async def disconnect_user(self, websocket) -> None:
        """断开用户连接"""
        await self.connection_manager.disconnect(websocket)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """向用户发送消息"""
        result = await self.connection_manager.send_to_user(user_id, message)
        return bool(result)
    
    async def send_to_device(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """向特定设备发送消息"""
        result = await self.connection_manager.send_to_device(connection_id, message)
        return bool(result)
    
    async def send_to_device_type(self, user_id: str, device_type: str, message: Dict[str, Any]) -> bool:
        """向用户的特定设备类型发送消息"""
        result = await self.connection_manager.send_to_device_type(user_id, device_type, message)
        return bool(result)
    
    async def handle_websocket_message(self, data: Dict[str, Any], user_id: str, conversation_id: str) -> Dict[str, Any]:
        """处理WebSocket消息"""
        return await self.websocket_handler.handle_websocket_message(data, user_id, conversation_id)
    
    async def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return await self.connection_manager.is_user_online(user_id)
    
    async def get_online_users(self) -> List[str]:
        """获取在线用户列表"""
        users = await self.connection_manager.get_online_users()
        return list(users)
    
    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户设备信息"""
        return self.connection_manager.get_user_devices(user_id)
    
    async def broadcast_message(self, conversation_id: str, message_data: Dict[str, Any], exclude_user_id: Optional[str] = None):
        """广播消息到会话"""
        await self.broadcasting_service.broadcast_message(conversation_id, message_data, exclude_user_id)
    
    async def broadcast_typing_status(self, conversation_id: str, user_id: str, is_typing: bool):
        """广播输入状态"""
        await self.broadcasting_service.broadcast_typing_status(conversation_id, user_id, is_typing)
    
    async def broadcast_read_status(self, conversation_id: str, user_id: str, message_ids: List[str]):
        """广播已读状态"""
        await self.broadcasting_service.broadcast_read_status(conversation_id, user_id, message_ids)
    
    async def broadcast_system_notification(self, conversation_id: str, notification_data: Dict[str, Any], target_user_ids: Optional[List[str]] = None):
        """广播系统通知"""
        await self.broadcasting_service.broadcast_system_notification(conversation_id, notification_data, target_user_ids)
    
    async def send_direct_message(self, user_id: str, message_data: Dict[str, Any]):
        """发送直接消息"""
        await self.broadcasting_service.send_direct_message(user_id, message_data)
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return self.connection_manager.get_local_connection_count()
    
    def get_user_count(self) -> int:
        """获取用户数"""
        return self.connection_manager.get_local_user_count()
