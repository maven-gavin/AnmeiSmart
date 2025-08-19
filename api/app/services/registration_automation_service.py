import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.chat.chat_service import ChatService
from app.services.broadcasting_service import BroadcastingService
from app.services.broadcasting_factory import get_broadcasting_service_dependency
from app.services.ai.ai_gateway_service import AIGatewayService
# MCP功能已重构，暂时注释相关功能
# from app.mcp.services import MCPToolExecutionService
from app.db.models.user import User
from app.db.models.chat import Conversation, Message
from app.schemas.chat import ConversationCreate, MessageCreate
import secrets

logger = logging.getLogger(__name__)

class RegistrationAutomationService:
    """用户注册自动化服务 - 集成MCP和Agent"""

    def __init__(self, db: Session):
        self.db = db
        self.chat_service = ChatService()
        # MCP服务已重构，暂时使用简化实现
        # self.mcp_execution = MCPToolExecutionService(db)

    async def handle_user_registration(self, user_id: str, user_info: dict) -> bool:
        """
        处理用户注册后的自动化流程
        
        Args:
            user_id: 用户ID
            user_info: 用户信息
            
        Returns:
            bool: 是否成功完成自动化流程
        """
        try:
            logger.info(f"开始用户注册自动化流程: user_id={user_id}")
            
            # 1. 创建默认会话
            conversation = await self._create_default_conversation(user_id)
            if not conversation:
                logger.error(f"创建默认会话失败: user_id={user_id}")
                return False
            
            # 2. 通过MCP获取用户信息进行分析
            user_analysis = await self._analyze_user_through_mcp(user_id)
            
            # 3. 生成个性化欢迎消息
            welcome_message = await self._generate_welcome_message(
                user_id, conversation.id, user_analysis
            )
            
            # 4. 保存欢迎消息
            if welcome_message:
                await self._save_welcome_message(conversation.id, welcome_message)
            
            # 5. 通知顾问有新客户
            await self._notify_consultants(user_id, conversation.id)
            
            logger.info(f"用户注册自动化流程完成: user_id={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"用户注册自动化流程失败: user_id={user_id}, error={e}")
            return False

    async def _create_default_conversation(self, user_id: str) -> Optional[Conversation]:
        """创建默认会话"""
        try:
            conversation_data = ConversationCreate(
                customer_id=user_id,
                title="欢迎咨询",
                ai_enabled=True,
                status="active"
            )
            
            conversation = await self.chat_service.create_conversation(
                self.db, conversation_data
            )
            
            logger.info(f"默认会话创建成功: user_id={user_id}, conversation_id={conversation.id}")
            return conversation
            
        except Exception as e:
            logger.error(f"创建默认会话失败: user_id={user_id}, error={e}")
            return None

    async def _analyze_user_through_mcp(self, user_id: str) -> Dict[str, Any]:
        """通过MCP工具分析用户"""
        try:
            # MCP服务已重构，暂时使用基础分析
            # TODO: 集成新的MCP工具执行服务
            
            # 查询用户基础信息
            user = self.db.query(User).filter(User.id == user_id).first()
            
            analysis_result = {
                "user_profile": {
                    "user_id": user_id,
                    "username": user.username if user else "新用户",
                    "roles": user.roles if user else ["customer"],
                    "is_new_user": True
                },
                "customer_analysis": {
                    "customer_segment": "新注册用户",
                    "behavior_pattern": "探索期",
                    "engagement_level": "新用户"
                },
                "service_info": {
                    "services": "全套医美咨询服务",
                    "recommendation": "建议先进行初步咨询"
                },
                "analysis_source": "simplified",
                "registration_time": datetime.now().isoformat()
            }
            
            logger.info(f"简化用户分析完成: user_id={user_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"用户分析失败: user_id={user_id}, error={e}")
            # 返回基础分析结果
            return {
                "user_profile": {"user_id": user_id, "is_new_user": True},
                "customer_analysis": {"customer_segment": "新用户"},
                "service_info": {"services": "基础咨询服务"},
                "analysis_source": "fallback"
            }

    async def _generate_welcome_message(self, user_id: str, conversation_id: str, 
                                      user_analysis: Dict[str, Any]) -> Optional[str]:
        """生成个性化欢迎消息"""
        try:
            # 构建给Agent的上下文信息
            context_prompt = self._build_welcome_context(user_analysis)
            
            # 通过AI Gateway调用Agent
            ai_gateway = AIGatewayService(self.db)
            
            response = await ai_gateway.customer_service_chat(
                message=context_prompt,
                user_id=user_id,
                session_id=conversation_id,
                conversation_history=[],
                user_profile={
                    "is_new_user": True,
                    "source": "registration_automation",
                    "analysis": user_analysis
                }
            )
            
            if response.success and response.content:
                logger.info(f"Agent欢迎消息生成成功: user_id={user_id}")
                return response.content
            else:
                logger.warning(f"Agent欢迎消息生成失败，使用默认消息: user_id={user_id}")
                return self._get_default_welcome_message(user_id)
                
        except Exception as e:
            logger.error(f"生成欢迎消息失败: user_id={user_id}, error={e}")
            return self._get_default_welcome_message(user_id)

    def _build_welcome_context(self, user_analysis: Dict[str, Any]) -> str:
        """构建欢迎消息的上下文"""
        user_profile = user_analysis.get("user_profile", {})
        customer_analysis = user_analysis.get("customer_analysis", {})
        
        context = f"""
新用户刚刚注册，请生成个性化欢迎消息。

用户信息：
- 用户ID: {user_profile.get('user_id', '未知')}
- 用户类型: {user_profile.get('roles', ['客户'])}
- 注册时间: {user_analysis.get('registration_time', '刚刚')}

客户画像分析：
- 客户细分: {customer_analysis.get('customer_segment', '新用户')}
- 行为模式: {customer_analysis.get('behavior_pattern', '探索期')}
- 参与度: {customer_analysis.get('engagement_level', '未知')}

请生成一个温馨、专业的欢迎消息，介绍我们的医美咨询服务，并鼓励用户提出问题。
消息应该：
1. 友好热情，体现专业性
2. 简洁明了，不超过150字
3. 包含服务介绍和咨询邀请
4. 体现个性化关怀
        """
        
        return context.strip()

    def _get_default_welcome_message(self, user_id: str) -> str:
        """默认欢迎消息模板"""
        return f"""
欢迎来到安美智享！🌟

我是您的专属AI咨询助手，很高兴为您服务。我们提供专业的医美咨询服务，包括：

• 个性化美容方案设计
• 专业治疗建议
• 风险评估与安全指导
• 术后护理指导

您可以随时向我咨询任何关于医美的问题，我会根据您的具体情况提供专业建议。

有什么想了解的吗？我来为您详细介绍！😊
        """.strip()

    async def _save_welcome_message(self, conversation_id: str, message_content: str) -> bool:
        """保存欢迎消息到数据库"""
        try:
            message_data = MessageCreate(
                conversation_id=conversation_id,
                sender_type="ai",
                sender_id="system",
                type="text",
                content={
                    "text": message_content,
                    "source": "registration_automation",
                    "generated_at": datetime.now().isoformat()
                }
            )
            
            message = await self.chat_service.create_message(self.db, message_data)
            
            logger.info(f"欢迎消息保存成功: conversation_id={conversation_id}, message_id={message.id}")
            return True
            
        except Exception as e:
            logger.error(f"保存欢迎消息失败: conversation_id={conversation_id}, error={e}")
            return False

    async def _notify_consultants(self, user_id: str, conversation_id: str) -> bool:
        """通知顾问有新客户"""
        try:
            broadcasting_service = await get_broadcasting_service_dependency(self.db)
            
            # 获取在线顾问列表
            online_consultants = await self._get_online_consultants()
            
            notification_data = {
                "type": "new_customer_registration",
                "title": "新客户注册",
                "message": "新客户已注册并开始咨询，等待顾问服务",
                "customer_id": user_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "action": "claim_customer",
                "priority": "normal"
            }
            
            # 发送实时通知给在线顾问
            success_count = 0
            for consultant_id in online_consultants:
                try:
                    await broadcasting_service.send_direct_message(
                        user_id=consultant_id,
                        message_data=notification_data
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"发送顾问通知失败: consultant_id={consultant_id}, error={e}")
            
            # 如果没有在线顾问，发送推送通知
            if not online_consultants:
                all_consultants = await self._get_all_consultants()
                for consultant_id in all_consultants:
                    try:
                        await broadcasting_service._send_push_notification(
                            user_id=consultant_id,
                            notification_data={
                                "title": "新客户等待服务",
                                "body": "有新客户注册，请及时响应",
                                "conversation_id": conversation_id,
                                "data": notification_data
                            }
                        )
                    except Exception as e:
                        logger.error(f"发送推送通知失败: consultant_id={consultant_id}, error={e}")
            
            logger.info(f"顾问通知发送完成: user_id={user_id}, 成功通知={success_count}个顾问")
            return success_count > 0 or len(online_consultants) == 0
            
        except Exception as e:
            logger.error(f"通知顾问失败: user_id={user_id}, error={e}")
            return False

    async def _get_online_consultants(self) -> list:
        """获取在线顾问列表"""
        try:
            # TODO: 实现获取在线顾问的逻辑
            # 这里可以查询WebSocket连接状态或者从缓存中获取在线用户
            online_consultants = []
            
            # 查询具有顾问角色的在线用户
            consultants = self.db.query(User).filter(
                User.roles.contains(["consultant"]),
                User.is_active == True
            ).all()
            
            # 简化实现：假设部分顾问在线
            for consultant in consultants[:2]:  # 模拟前2个顾问在线
                online_consultants.append(consultant.id)
            
            return online_consultants
            
        except Exception as e:
            logger.error(f"获取在线顾问失败: error={e}")
            return []

    async def _get_all_consultants(self) -> list:
        """获取所有顾问列表"""
        try:
            consultants = self.db.query(User).filter(
                User.roles.contains(["consultant"]),
                User.is_active == True
            ).all()
            
            return [consultant.id for consultant in consultants]
            
        except Exception as e:
            logger.error(f"获取所有顾问失败: error={e}")
            return []

# 异步任务函数
async def handle_registration_automation(user_id: str, user_info: dict) -> bool:
    """
    注册自动化主任务函数
    
    Args:
        user_id: 用户ID
        user_info: 用户信息
        
    Returns:
        bool: 是否成功完成
    """
    db = next(get_db())
    try:
        automation_service = RegistrationAutomationService(db)
        return await automation_service.handle_user_registration(user_id, user_info)
    except Exception as e:
        logger.error(f"注册自动化任务失败: user_id={user_id}, error={e}")
        return False
    finally:
        db.close() 