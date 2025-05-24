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

logger = logging.getLogger(__name__)


class AIResponseService:
    """AI回复服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.message_service = MessageService(db)
        self.ai_service = get_ai_service()
        
        # 订阅消息事件
        event_bus.subscribe_async(EventTypes.CHAT_MESSAGE_RECEIVED, self.handle_message_event)
    
    async def handle_message_event(self, event: Event):
        """处理消息事件，决定是否需要AI回复"""
        try:
            # 只处理用户消息
            if event.data.get("sender_type") != "user":
                return
            
            conversation_id = event.conversation_id
            user_id = event.user_id
            content = event.data.get("content", "")
            
            logger.info(f"处理AI回复请求: conversation_id={conversation_id}, user_id={user_id}")
            
            # 检查是否需要AI回复
            should_reply = await self.should_ai_reply(conversation_id, user_id)
            
            if should_reply:
                await self.generate_ai_response(conversation_id, content)
            else:
                logger.info(f"跳过AI回复: conversation_id={conversation_id}")
                
        except Exception as e:
            logger.error(f"处理AI回复事件失败: {e}")
    
    async def should_ai_reply(self, conversation_id: str, user_id: str) -> bool:
        """判断是否应该生成AI回复"""
        # 这里可以实现复杂的逻辑来决定是否需要AI回复
        # 例如：检查会话设置、用户偏好、顾问在线状态等
        
        # 简化版：默认总是回复
        # 实际项目中可以根据以下条件判断：
        # 1. 会话是否启用了AI
        # 2. 是否有人工顾问在线
        # 3. 用户是否明确要求AI回复
        # 4. 消息类型是否适合AI回复
        
        return True
    
    async def generate_ai_response(self, conversation_id: str, user_message: str):
        """生成AI回复"""
        try:
            logger.info(f"开始生成AI回复: conversation_id={conversation_id}")
            
            # 获取会话历史
            history = self.get_conversation_history(conversation_id)
            
            # 设置超时时间
            timeout = 10.0
            
            # 生成AI回复
            ai_response = await asyncio.wait_for(
                self.ai_service.get_response(user_message, history),
                timeout=timeout
            )
            
            # 创建AI回复消息
            ai_message = await self.message_service.create_message(
                conversation_id=conversation_id,
                content=ai_response.get("content", "抱歉，我暂时无法回复"),
                message_type="text",
                sender_id="ai",
                sender_type="ai"
            )
            
            logger.info(f"AI回复生成成功: message_id={ai_message.id}")
            
            # 发布AI回复事件
            from app.core.events import create_message_event
            event = create_message_event(
                conversation_id=conversation_id,
                user_id="ai",
                content=ai_message.content,
                message_type="text",
                sender_type="ai",
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
    
    async def force_ai_response(self, conversation_id: str, prompt: str) -> Optional[Message]:
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
            
            return ai_message
            
        except Exception as e:
            logger.error(f"强制AI回复失败: {e}")
            return None
    
    def set_ai_enabled(self, conversation_id: str, enabled: bool):
        """设置会话的AI启用状态"""
        # 这里可以实现会话级别的AI开关
        # 可以存储在数据库的会话配置中
        pass
    
    def get_ai_status(self, conversation_id: str) -> Dict[str, Any]:
        """获取AI状态信息"""
        return {
            "enabled": True,  # 从数据库或配置中获取
            "model": "default",
            "response_time_avg": 2.5,  # 平均响应时间
            "success_rate": 0.95  # 成功率
        } 