"""
消息广播服务 - 处理WebSocket消息的广播逻辑
"""
from typing import Dict, Any
import logging
from datetime import datetime

from app.core.websocket_manager import websocket_manager
from app.core.events import event_bus, EventTypes, Event

logger = logging.getLogger(__name__)


class MessageBroadcaster:
    """消息广播服务"""
    
    def __init__(self):
        # 订阅需要广播的事件
        event_bus.subscribe_async(EventTypes.CHAT_MESSAGE_SENT, self.broadcast_message)
        event_bus.subscribe_async(EventTypes.AI_RESPONSE_GENERATED, self.broadcast_ai_response)
        event_bus.subscribe_async(EventTypes.CHAT_TYPING, self.broadcast_typing_status)
        event_bus.subscribe_async(EventTypes.CHAT_READ, self.broadcast_read_status)
        event_bus.subscribe_async(EventTypes.SYSTEM_NOTIFICATION, self.broadcast_system_notification)
    
    async def broadcast_message(self, event: Event):
        """广播普通消息"""
        try:
            conversation_id = event.conversation_id
            if not conversation_id:
                logger.warning("消息事件缺少conversation_id")
                return
            
            message_data = {
                "action": "message",
                "data": {
                    "id": event.data.get("message_id"),
                    "content": event.data.get("content"),
                    "type": event.data.get("message_type", "text"),
                    "sender_id": event.user_id,
                    "sender_type": event.data.get("sender_type", "user"),
                    "is_read": False,
                    "is_important": event.data.get("is_important", False)
                },
                "conversation_id": conversation_id,
                "timestamp": event.timestamp.isoformat()
            }
            
            await websocket_manager.broadcast_to_conversation(
                conversation_id, 
                message_data,
                exclude_user=event.user_id  # 不发送给发送者自己
            )
            
            logger.info(f"消息已广播: conversation_id={conversation_id}, sender={event.user_id}")
            
        except Exception as e:
            logger.error(f"广播消息失败: {e}")
    
    async def broadcast_ai_response(self, event: Event):
        """广播AI回复"""
        try:
            conversation_id = event.conversation_id
            if not conversation_id:
                logger.warning("AI回复事件缺少conversation_id")
                return
            
            ai_message_data = {
                "action": "message",
                "data": {
                    "id": event.data.get("message_id"),
                    "content": event.data.get("content"),
                    "type": event.data.get("message_type", "text"),
                    "sender_id": "ai",
                    "sender_type": "ai",
                    "is_read": False,
                    "is_important": False
                },
                "conversation_id": conversation_id,
                "timestamp": event.timestamp.isoformat()
            }
            
            await websocket_manager.broadcast_to_conversation(
                conversation_id, 
                ai_message_data
            )
            
            logger.info(f"AI回复已广播: conversation_id={conversation_id}")
            
        except Exception as e:
            logger.error(f"广播AI回复失败: {e}")
    
    async def broadcast_typing_status(self, event: Event):
        """广播正在输入状态"""
        try:
            conversation_id = event.conversation_id
            if not conversation_id:
                return
            
            typing_data = {
                "action": "typing",
                "data": {
                    "is_typing": event.data.get("is_typing", False)
                },
                "sender_id": event.user_id,
                "conversation_id": conversation_id,
                "timestamp": event.timestamp.isoformat()
            }
            
            await websocket_manager.broadcast_to_conversation(
                conversation_id,
                typing_data,
                exclude_user=event.user_id
            )
            
        except Exception as e:
            logger.error(f"广播输入状态失败: {e}")
    
    async def broadcast_read_status(self, event: Event):
        """广播已读状态"""
        try:
            conversation_id = event.conversation_id
            if not conversation_id:
                return
            
            read_data = {
                "action": "read",
                "data": {
                    "message_ids": event.data.get("message_ids", [])
                },
                "sender_id": event.user_id,
                "conversation_id": conversation_id,
                "timestamp": event.timestamp.isoformat()
            }
            
            await websocket_manager.broadcast_to_conversation(
                conversation_id,
                read_data,
                exclude_user=event.user_id
            )
            
        except Exception as e:
            logger.error(f"广播已读状态失败: {e}")
    
    async def broadcast_system_notification(self, event: Event):
        """广播系统通知"""
        try:
            conversation_id = event.conversation_id
            
            notification_data = {
                "action": "system",
                "data": {
                    "message": event.data.get("message"),
                    "type": event.data.get("type", "info")
                },
                "conversation_id": conversation_id,
                "timestamp": event.timestamp.isoformat()
            }
            
            if conversation_id:
                # 广播到特定会话
                await websocket_manager.broadcast_to_conversation(
                    conversation_id,
                    notification_data
                )
            else:
                # 全局广播（如果需要的话）
                # 这里可以实现全局广播逻辑
                pass
            
        except Exception as e:
            logger.error(f"广播系统通知失败: {e}")
    
    async def broadcast_user_status(self, user_id: str, conversation_id: str, status: str):
        """广播用户状态变化"""
        try:
            status_data = {
                "action": "user_status",
                "data": {
                    "user_id": user_id,
                    "status": status  # online, offline, typing, etc.
                },
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket_manager.broadcast_to_conversation(
                conversation_id,
                status_data,
                exclude_user=user_id
            )
            
        except Exception as e:
            logger.error(f"广播用户状态失败: {e}")
    
    async def send_direct_message(self, user_id: str, message: Dict[str, Any]) -> bool:
        """向特定用户发送直接消息"""
        try:
            return await websocket_manager.send_to_user(user_id, message)
        except Exception as e:
            logger.error(f"发送直接消息失败: {e}")
            return False


# 全局消息广播器实例
message_broadcaster = MessageBroadcaster() 