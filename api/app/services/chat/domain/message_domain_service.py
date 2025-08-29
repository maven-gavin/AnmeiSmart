"""
消息领域服务 - 领域层
负责核心业务逻辑，领域规则，领域事件
遵循DDD分层架构的领域层职责
"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.services.chat.domain.interfaces import IMessageRepository, IMessageDomainService
from app.services.chat.domain.entities.message import Message

logger = logging.getLogger(__name__)


class MessageDomainService(IMessageDomainService):
    """消息领域服务 - 核心业务逻辑"""
    
    def __init__(self, message_repository: IMessageRepository):
        self.message_repository = message_repository
    
    async def create_text_message(
        self,
        conversation_id: str,
        text: str,
        sender_id: str,
        sender_type: str
    ) -> Message:
        """创建文本消息 - 领域逻辑"""
        logger.info(f"领域服务：创建文本消息 - conversation_id={conversation_id}, sender_id={sender_id}")
        
        # 领域规则验证
        if not text or not text.strip():
            raise ValueError("消息内容不能为空")
        
        if not conversation_id:
            raise ValueError("会话ID不能为空")
        
        if not sender_id:
            raise ValueError("发送者ID不能为空")
        
        # 使用领域实体的工厂方法创建文本消息
        message = Message.create_text_message(
            conversation_id=conversation_id,
            text=text.strip(),
            sender_id=sender_id,
            sender_type=sender_type
        )
        
        # 发布领域事件
        self._add_domain_event("text_message_created", {
            "message_id": str(message.id),
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "sender_type": sender_type
        })
        
        return message
    
    async def create_media_message(
        self,
        conversation_id: str,
        media_url: str,
        media_name: str,
        mime_type: str,
        sender_id: str,
        sender_type: str,
        text: Optional[str] = None
    ) -> Message:
        """创建媒体消息 - 领域逻辑"""
        logger.info(f"领域服务：创建媒体消息 - conversation_id={conversation_id}, sender_id={sender_id}")
        
        # 领域规则验证
        if not media_url:
            raise ValueError("媒体URL不能为空")
        
        if not media_name:
            raise ValueError("媒体名称不能为空")
        
        if not mime_type:
            raise ValueError("MIME类型不能为空")
        
        if not conversation_id:
            raise ValueError("会话ID不能为空")
        
        if not sender_id:
            raise ValueError("发送者ID不能为空")
        
        # 使用领域实体的工厂方法创建媒体消息
        message = Message.create_media_message(
            conversation_id=conversation_id,
            media_url=media_url,
            media_name=media_name,
            mime_type=mime_type,
            sender_id=sender_id,
            sender_type=sender_type,
            text=text
        )
        
        # 发布领域事件
        self._add_domain_event("media_message_created", {
            "message_id": str(message.id),
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "sender_type": sender_type,
            "media_type": mime_type
        })
        
        return message
    
    async def create_system_message(
        self,
        conversation_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Message:
        """创建系统消息 - 领域逻辑"""
        logger.info(f"领域服务：创建系统消息 - conversation_id={conversation_id}, event_type={event_type}")
        
        # 领域规则验证
        if not conversation_id:
            raise ValueError("会话ID不能为空")
        
        if not event_type:
            raise ValueError("事件类型不能为空")
        
        # 使用领域实体的工厂方法创建系统消息
        message = Message.create_system_event_message(
            conversation_id=conversation_id,
            event_type=event_type,
            status="sent",
            event_data=event_data
        )
        
        # 发布领域事件
        self._add_domain_event("system_message_created", {
            "message_id": str(message.id),
            "conversation_id": conversation_id,
            "event_type": event_type
        })
        
        return message
    
    async def create_structured_message(
        self,
        conversation_id: str,
        card_type: str,
        title: str,
        data: Dict[str, Any],
        sender_id: str,
        sender_type: str
    ) -> Message:
        """创建结构化消息 - 领域逻辑"""
        logger.info(f"领域服务：创建结构化消息 - conversation_id={conversation_id}, card_type={card_type}")
        
        # 领域规则验证
        if not conversation_id:
            raise ValueError("会话ID不能为空")
        
        if not card_type:
            raise ValueError("卡片类型不能为空")
        
        if not title:
            raise ValueError("标题不能为空")
        
        if not data:
            raise ValueError("数据不能为空")
        
        if not sender_id:
            raise ValueError("发送者ID不能为空")
        
        # 创建结构化消息内容
        content = {
            "card_type": card_type,
            "title": title,
            "data": data
        }
        
        # 创建消息
        message = Message(
            id="",  # 由仓储生成
            conversation_id=conversation_id,
            content=content,
            message_type="structured",
            sender_id=sender_id,
            sender_type=sender_type,
            is_important=False,
            reply_to_message_id=None,
            extra_metadata={}
        )
        
        # 发布领域事件
        self._add_domain_event("structured_message_created", {
            "message_id": str(message.id),
            "conversation_id": conversation_id,
            "card_type": card_type,
            "sender_id": sender_id
        })
        
        return message
    
    async def mark_as_read(self, message_id: str) -> bool:
        """标记消息为已读 - 领域逻辑"""
        logger.info(f"领域服务：标记消息已读 - message_id={message_id}")
        
        # 从仓储获取消息
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            logger.warning(f"消息不存在，无法标记已读: {message_id}")
            return False
        
        # 标记为已读
        message.mark_as_read()
        
        # 发布领域事件
        self._add_domain_event("message_marked_as_read", {
            "message_id": message_id
        })
        
        return True
    
    async def mark_as_important(self, message_id: str, is_important: bool) -> bool:
        """标记消息为重点 - 领域逻辑"""
        logger.info(f"领域服务：标记消息重点 - message_id={message_id}, is_important={is_important}")
        
        # 从仓储获取消息
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            logger.warning(f"消息不存在，无法标记重点: {message_id}")
            return False
        
        # 标记为重点
        message.mark_as_important(is_important)
        
        # 发布领域事件
        self._add_domain_event("message_importance_changed", {
            "message_id": message_id,
            "is_important": is_important
        })
        
        return True
    
    async def add_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """添加反应 - 领域逻辑"""
        logger.info(f"领域服务：添加反应 - message_id={message_id}, user_id={user_id}, emoji={emoji}")
        
        # 从仓储获取消息
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            logger.warning(f"消息不存在，无法添加反应: {message_id}")
            return False
        
        # 添加反应
        success = message.add_reaction(user_id, emoji)
        
        if success:
            # 发布领域事件
            self._add_domain_event("message_reaction_added", {
                "message_id": message_id,
                "user_id": user_id,
                "emoji": emoji
            })
        
        return success
    
    async def remove_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """移除反应 - 领域逻辑"""
        logger.info(f"领域服务：移除反应 - message_id={message_id}, user_id={user_id}, emoji={emoji}")
        
        # 从仓储获取消息
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            logger.warning(f"消息不存在，无法移除反应: {message_id}")
            return False
        
        # 移除反应
        success = message.remove_reaction(user_id, emoji)
        
        if success:
            # 发布领域事件
            self._add_domain_event("message_reaction_removed", {
                "message_id": message_id,
                "user_id": user_id,
                "emoji": emoji
            })
        
        return success
    
    def _add_domain_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """添加领域事件 - 内部方法"""
        # 这里可以集成事件总线或消息队列
        logger.info(f"领域事件：{event_type} - {event_data}")
        
        # TODO: 发布到事件总线
        # await event_bus.publish(event_type, event_data)
