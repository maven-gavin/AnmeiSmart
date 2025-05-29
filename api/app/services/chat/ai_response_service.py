"""
AI回复服务 - 处理AI自动回复逻辑
"""
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.models.chat import Message, Conversation
from app.services.ai import get_ai_service
from app.core.events import event_bus, EventTypes, Event
from .message_service import MessageService
from app.schemas.chat import MessageInfo

logger = logging.getLogger(__name__)


class AIResponseService:
    """AI回复服务类"""
    
    def __init__(self, db: Session):
        self.db: Session = db
        self.message_service: MessageService = MessageService(db)
        self.ai_service = get_ai_service()
        
        # 订阅消息事件
        event_bus.subscribe_async(EventTypes.CHAT_MESSAGE_RECEIVED, self.handle_message_event)
    
    async def handle_message_event(self, event: Event):
        """根据事件判断是否需要AI回复，如果需要则生成AI回复，保存并广播"""
        if await self.should_ai_reply(event):
            await self.generate_ai_response(event.conversation_id, event.content)
    
    async def should_ai_reply(self, event) -> bool:
        """判断是否应该生成AI回复，event需包含conversation_id, user_id, sender_type等"""
        try:
            conversation_id = event.conversation_id
            sender_type = getattr(event, 'sender_type', event.data.get('sender_type', None))
            # 1. 仅客户消息触发AI
            if sender_type not in ["customer"]:
                logger.info(f"非客户消息，不触发AI: sender_type={sender_type}")
                return False
            # 2. 检查会话是否存在且为AI控制
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if not conversation.is_ai_controlled:
                logger.info(f"会话已被顾问接管，不生成AI回复: {conversation_id}")
                return False
        except Exception as e:
            logger.error(f"判断AI回复条件失败: {e}")
            return False
    
    async def generate_ai_response(self, conversation_id: str, user_message: str):
        """生成AI回复"""
        AI_SENDER_ID = "ai"
        AI_SENDER_TYPE = "ai"
        try:
            logger.info(f"开始生成AI回复: conversation_id={conversation_id}, user_message={user_message}")
            
            # 获取会话历史
            history = self.get_conversation_history(conversation_id)
            
            # 设置超时时间
            timeout = 5.0
            
            # 生成AI回复
            ai_response = await asyncio.wait_for(
                self.ai_service.get_response(user_message, history),
                timeout=timeout
            )
            
            # 类型检查
            if not isinstance(ai_response, dict):
                logger.error(f"AI服务返回格式错误: {ai_response}")
                await self.create_error_message(conversation_id, "AI服务返回格式错误")
                return
            
            # 创建AI回复消息
            ai_message = await self.message_service.create_message(
                conversation_id=conversation_id,
                content=ai_response.get("content", "抱歉，我暂时无法回复"),
                message_type="text",
                sender_id=AI_SENDER_ID,
                sender_type=AI_SENDER_TYPE
            )
            
            logger.info(f"AI回复生成成功: message_id={ai_message.id}")
            
            # 发布AI回复事件
            from app.core.events import create_message_event
            event = create_message_event(
                conversation_id=conversation_id,
                user_id=AI_SENDER_ID,
                content=ai_message.content,
                message_type="text",
                sender_type=AI_SENDER_TYPE,
                message_id=ai_message.id
            )
            event.type = EventTypes.AI_RESPONSE_GENERATED
            await event_bus.publish_async(event)
            
        except asyncio.TimeoutError:
            logger.error(f"AI回复生成超时: conversation_id={conversation_id}")
            await self.create_timeout_message(conversation_id)
            
        except Exception as e:
            logger.error(f"AI回复生成失败: conversation_id={conversation_id}, 错误={e}")
            await self.create_error_message(conversation_id, str(e))
    
    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取会话历史用于AI上下文"""
        messages = self.message_service.get_recent_messages(conversation_id, limit)
        
        history = []
        for message in messages:
            history.append({
                "content": message.content,
                "sender_type": message.sender_type,
                "timestamp": message.timestamp.isoformat()
            })
        
        return history
    
    async def create_timeout_message(self, conversation_id: str):
        """创建超时错误消息"""
        try:
            await self.message_service.create_message(
                conversation_id=conversation_id,
                content="AI响应超时，请稍后再试",
                message_type="text",
                sender_id="system",
                sender_type="system"
            )
        except Exception as e:
            logger.error(f"创建超时消息失败: {e}")
    
    async def create_error_message(self, conversation_id: str, error_msg: str):
        """创建错误消息"""
        try:
            await self.message_service.create_message(
                conversation_id=conversation_id,
                content=f"生成回复时出错: {error_msg}",
                message_type="text",
                sender_id="system",
                sender_type="system"
            )
        except Exception as e:
            logger.error(f"创建错误消息失败: {e}")
    
    async def force_ai_response(self, conversation_id: str, prompt: str) -> Optional[MessageInfo]:
        """强制生成AI回复（用于手动触发）"""
        try:
            logger.info(f"强制生成AI回复: conversation_id={conversation_id}")
            history = self.get_conversation_history(conversation_id)
            ai_response = await self.ai_service.get_response(prompt, history)
            ai_message = await self.message_service.create_message(
                conversation_id=conversation_id,
                content=ai_response.get("content", "无法生成回复"),
                message_type="text",
                sender_id="ai",
                sender_type="ai"
            )
            return MessageInfo.from_model(ai_message)
        except Exception as e:
            logger.error(f"强制AI回复失败: {e}")
            return None