"""
AI回复服务 - 基于AI Gateway的新架构实现

使用统一的AI Gateway调用AI能力，支持多提供商自动切换和降级。
"""
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.models.chat import Message, Conversation
from app.core.events import event_bus, EventTypes, Event
from .message_service import MessageService
from app.schemas.chat import MessageInfo
from app.services.ai.ai_gateway_service import get_ai_gateway_service

logger = logging.getLogger(__name__)


class AIResponseService:
    """AI回复服务类"""
    
    def __init__(self, db: Session):
        self.db: Session = db
        self.message_service: MessageService = MessageService(db)
        
        # 订阅消息事件
        event_bus.subscribe_async(EventTypes.CHAT_MESSAGE_RECEIVED, self.handle_message_event)
    
    async def handle_message_event(self, event: Event):
        """根据事件判断是否需要AI回复，如果需要则生成AI回复，保存并广播"""
        if await self.should_ai_reply(event):
            # 从事件数据中获取消息内容
            content = event.data.get("content", "")
            await self.generate_ai_response(event.conversation_id, content)
    
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
            return True
        except Exception as e:
            logger.error(f"判断AI回复条件失败: {e}")
            return False
    
    async def generate_ai_response(self, conversation_id: str, user_message: str):
        """生成AI回复 - 使用AI Gateway"""
        AI_SENDER_ID = "ai_system"
        AI_SENDER_TYPE = "ai"
        
        try:
            logger.info(f"开始生成AI回复: conversation_id={conversation_id}, user_message={user_message}")
            
            # 获取会话历史
            history = self.get_conversation_history(conversation_id)
            
            # 获取用户档案信息
            user_profile = await self._get_user_profile_from_conversation(conversation_id)
            
            # 使用AI Gateway生成回复
            ai_gateway = get_ai_gateway_service(self.db)
            ai_response = await ai_gateway.customer_service_chat(
                message=user_message,
                user_id=self._get_user_id_from_conversation(conversation_id),
                session_id=conversation_id,
                conversation_history=history
            )
            
            # 检查AI响应是否成功
            if not ai_response.success:
                logger.error(f"AI回复生成失败: {ai_response.error_message}")
                await self.create_error_message(conversation_id, ai_response.error_message or "AI服务暂时不可用")
                return
            
            # 创建AI回复消息
            ai_message = await self.message_service.create_message(
                conversation_id=conversation_id,
                content={"text": ai_response.content},  # 使用新的消息格式
                message_type="text",
                sender_id=AI_SENDER_ID,
                sender_type=AI_SENDER_TYPE
            )
            
            logger.info(f"AI回复生成成功: message_id={ai_message.id}, provider={ai_response.provider.value}")
            
            # 发布AI回复事件
            from app.core.events import create_message_event
            event = create_message_event(
                conversation_id=conversation_id,
                user_id="ai_system",
                content=ai_response.content,
                message_type="text",
                sender_type=AI_SENDER_TYPE,
                message_id=ai_message.id
            )
            event.type = EventTypes.AI_RESPONSE_GENERATED
            await event_bus.publish_async(event)
            
        except Exception as e:
            logger.error(f"AI回复生成失败: conversation_id={conversation_id}, 错误={e}")
            await self.create_error_message(conversation_id, str(e))
    
    async def _get_user_profile_from_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """从会话中获取用户档案信息"""
        try:
            conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conversation and conversation.customer_id:
                # 这里可以从Customer表获取用户档案信息
                # 暂时返回基本信息
                return {"user_type": "customer", "conversation_id": conversation_id}
            return None
        except Exception as e:
            logger.error(f"获取用户档案失败: {e}")
            return None
    
    def _get_user_id_from_conversation(self, conversation_id: str) -> str:
        """从会话中获取用户ID"""
        try:
            conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conversation and conversation.customer_id:
                return conversation.customer_id
            return f"anonymous_{conversation_id}"
        except Exception as e:
            logger.error(f"获取用户ID失败: {e}")
            return f"anonymous_{conversation_id}"
    
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
                sender_id=None,
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
                sender_id=None,
                sender_type="system"
            )
        except Exception as e:
            logger.error(f"创建错误消息失败: {e}")
    
    async def force_ai_response(self, conversation_id: str, prompt: str) -> Optional[MessageInfo]:
        """强制生成AI回复（用于手动触发）"""
        try:
            logger.info(f"强制生成AI回复: conversation_id={conversation_id}")
            
            # 获取会话历史
            history = self.get_conversation_history(conversation_id)
            
            # 获取AI服务实例
            from app.services.ai import get_ai_service
            ai_service = get_ai_service(self.db)
            
            # 生成AI回复
            ai_response = await ai_service.get_response(prompt, history)
            
            # 创建AI回复消息
            ai_message = await self.message_service.create_message(
                conversation_id=conversation_id,
                content=ai_response.get("content", "无法生成回复"),
                message_type="text",
                sender_id=None,
                sender_type="ai"
            )
            
            return MessageInfo.from_model(ai_message)
            
        except Exception as e:
            logger.error(f"强制AI回复失败: {e}")
            return None