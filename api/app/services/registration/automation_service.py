"""
注册自动化服务核心实现

处理用户注册后的完整自动化流程：
1. 创建默认会话
2. 通过AI Gateway触发Dify Agent生成欢迎消息
3. 通知顾问团队有新客户
"""
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.chat import Conversation, Message
from app.db.uuid_utils import conversation_id, message_id
from app.schemas.chat import ConversationInfo, MessageInfo
from app.services.ai.ai_gateway_service import get_ai_gateway_service
from app.services.chat.chat_service import ChatService
from app.services.broadcasting_factory import create_broadcasting_service
from .consultant_notifier import ConsultantNotifier

logger = logging.getLogger(__name__)


class RegistrationAutomationService:
    """注册自动化服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_gateway = get_ai_gateway_service(db)
        
    async def handle_user_registration(self, user_id: str, user_info: Dict[str, Any]):
        """
        处理用户注册后的自动化流程
        
        Args:
            user_id: 用户ID
            user_info: 用户信息
        """
        try:
            logger.info(f"开始处理用户注册自动化: user_id={user_id}")
            
            # 第一步：创建默认会话
            conversation = await self._create_default_conversation(user_id)
            if not conversation:
                logger.error(f"创建默认会话失败: user_id={user_id}")
                return
            
            logger.info(f"默认会话创建成功: user_id={user_id}, conversation_id={conversation.id}")
            
            # 第二步：触发Dify Agent生成欢迎消息
            welcome_message = await self._trigger_welcome_message(user_id, conversation.id, user_info)
            if welcome_message:
                logger.info(f"欢迎消息生成成功: user_id={user_id}, message_id={welcome_message.id}")
            else:
                logger.warning(f"欢迎消息生成失败，使用默认消息: user_id={user_id}")
                # 创建默认欢迎消息
                await self._create_default_welcome_message(user_id, conversation.id)
            
            # 第三步：通知顾问团队
            await self._notify_consultants(user_id, conversation.id, user_info)
            
            logger.info(f"用户注册自动化完成: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"用户注册自动化失败: user_id={user_id}, error={e}", exc_info=True)
            # 失败时至少尝试创建一个基本会话
            try:
                await self._create_fallback_conversation(user_id)
            except Exception as fallback_error:
                logger.error(f"创建失败回退会话也失败: user_id={user_id}, error={fallback_error}")
    
    async def _create_default_conversation(self, user_id: str) -> Optional[ConversationInfo]:
        """创建默认会话"""
        try:
            # 创建会话
            conversation_data = {
                "id": conversation_id(),
                "customer_id": user_id,
                "status": "active",
                "ai_enabled": True,  # 启用AI功能
                "assigned_consultant_id": None,  # 暂未分配顾问
                "title": "欢迎咨询",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            conversation = Conversation(**conversation_data)
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            
            # 转换为响应模型
            from app.schemas.chat import ConversationInfo
            return ConversationInfo.from_model(conversation)
            
        except Exception as e:
            logger.error(f"创建默认会话失败: user_id={user_id}, error={e}")
            self.db.rollback()
            return None
    
    async def _trigger_welcome_message(self, user_id: str, conversation_id: str, user_info: Dict[str, Any]) -> Optional[MessageInfo]:
        """触发Dify Agent生成欢迎消息"""
        try:
            # 构建用户档案信息传递给AI Gateway
            user_profile = {
                "user_id": user_id,
                "username": user_info.get("username", ""),
                "email": user_info.get("email", ""),
                "roles": user_info.get("roles", []),
                "is_new_user": True,
                "source": "registration_automation",
                "registration_time": datetime.now().isoformat()
            }
            
            # 构建欢迎消息生成的prompt
            welcome_prompt = f"""新用户刚刚注册了我们的医美咨询平台，请为用户生成一条个性化的欢迎消息。

用户信息：
- 用户名：{user_info.get('username', '新用户')}
- 主要角色：{user_info.get('roles', ['customer'])[0] if user_info.get('roles') else 'customer'}
- 注册时间：刚刚注册

请生成一条温馨、专业的欢迎消息，包含：
1. 欢迎词
2. 平台简介
3. 服务说明
4. 引导用户开始咨询

请确保消息友好、专业，符合医美行业的特点。"""
            
            # 通过AI Gateway调用Dify Agent
            response = await self.ai_gateway.customer_service_chat(
                message=welcome_prompt,
                user_id=user_id,
                session_id=conversation_id,
                conversation_history=[],
                user_profile=user_profile
            )
            
            if response and hasattr(response, 'success') and response.success:
                # 创建消息记录
                message_data = {
                    "id": message_id(),
                    "conversation_id": conversation_id,
                    "content": {
                        "type": "text",
                        "text": response.content
                    },
                    "message_type": "text",
                    "sender_id": "system",
                    "sender_type": "ai",
                    "is_important": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                message = Message(**message_data)
                self.db.add(message)
                self.db.commit()
                self.db.refresh(message)
                
                # 广播消息给用户
                await self._broadcast_welcome_message(conversation_id, message_data)
                
                from app.schemas.chat import MessageInfo
                return MessageInfo.from_model(message)
            else:
                logger.warning(f"AI Gateway返回失败: user_id={user_id}, error={getattr(response, 'error_message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"触发欢迎消息失败: user_id={user_id}, error={e}", exc_info=True)
            return None
    
    async def _create_default_welcome_message(self, user_id: str, conversation_id: str) -> Optional[MessageInfo]:
        """创建默认欢迎消息（fallback）"""
        try:
            default_message = """🌟 欢迎来到安美智享！

我是您的专属AI咨询助手，很高兴为您服务！

✨ 在这里，您可以：
• 咨询医美项目和方案
• 获得专业的美容建议
• 与资深顾问对话交流
• 了解最新的美容资讯

💬 请随时告诉我您的需求，我会为您提供最专业的帮助。如需人工服务，我们的顾问也会很快为您安排！

祝您美丽每一天！ 💕"""
            
            message_data = {
                "id": message_id(),
                "conversation_id": conversation_id,
                "content": {
                    "type": "text",
                    "text": default_message
                },
                "message_type": "text",
                "sender_id": "system",
                "sender_type": "system",
                "is_important": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            message = Message(**message_data)
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            # 广播消息
            await self._broadcast_welcome_message(conversation_id, message_data)
            
            from app.schemas.chat import MessageInfo
            return MessageInfo.from_model(message)
            
        except Exception as e:
            logger.error(f"创建默认欢迎消息失败: user_id={user_id}, error={e}")
            return None
    
    async def _broadcast_welcome_message(self, conversation_id: str, message_data: Dict[str, Any]):
        """广播欢迎消息"""
        try:
            # 获取广播服务
            broadcasting_service = await create_broadcasting_service(self.db)
            
            # 广播消息到会话
            await broadcasting_service.broadcast_message(
                conversation_id=conversation_id,
                message_data=message_data
            )
            
            logger.debug(f"欢迎消息已广播: conversation_id={conversation_id}")
            
        except Exception as e:
            logger.error(f"广播欢迎消息失败: conversation_id={conversation_id}, error={e}")
    
    async def _notify_consultants(self, user_id: str, conversation_id: str, user_info: Dict[str, Any]):
        """通知顾问团队有新客户"""
        try:
            notifier = ConsultantNotifier(self.db)
            await notifier.notify_new_customer(user_id, conversation_id, user_info)
            
            logger.info(f"顾问通知已发送: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"通知顾问失败: user_id={user_id}, error={e}")
    
    async def _create_fallback_conversation(self, user_id: str):
        """创建失败回退会话（最基本的会话）"""
        try:
            simple_conversation = Conversation(
                id=conversation_id(),
                customer_id=user_id,
                status="active",
                ai_enabled=False,  # 失败时禁用AI
                title="咨询会话",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.db.add(simple_conversation)
            self.db.commit()
            
            logger.info(f"失败回退会话创建成功: user_id={user_id}, conversation_id={simple_conversation.id}")
            
        except Exception as e:
            logger.error(f"创建失败回退会话失败: user_id={user_id}, error={e}")


async def handle_registration_automation(user_id: str, user_info: Dict[str, Any]):
    """
    注册自动化主入口函数
    
    这个函数会被FastAPI的BackgroundTasks调用
    """
    from app.db.base import get_db
    
    db = next(get_db())
    
    try:
        automation_service = RegistrationAutomationService(db)
        await automation_service.handle_user_registration(user_id, user_info)
        
    except Exception as e:
        logger.error(f"注册自动化处理失败: user_id={user_id}, error={e}", exc_info=True)
        
    finally:
        try:
            db.close()
        except:
            pass 