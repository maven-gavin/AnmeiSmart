"""
聊天应用服务 - 应用层
负责编排聊天相关的用例，整合会话和消息管理
遵循DDD分层架构的应用层职责
"""
import logging
from typing import List, Optional, Dict, Any, Union

from app.identity_access.infrastructure.db.user import User
from app.chat.schemas.chat import (
    ConversationInfo, MessageInfo, ConversationCreate,
    MessageCreateRequest, CreateTextMessageRequest, CreateMediaMessageRequest,
    CreateSystemEventRequest, CreateStructuredMessageRequest, AppointmentCardData
)
from app.chat.domain.interfaces import (
    IConversationRepository, IMessageRepository, IChatApplicationService,
    IConversationDomainService, IMessageDomainService
)
from app.chat.domain.entities.conversation import Conversation
from app.chat.domain.entities.message import Message
from app.chat.converters.conversation_converter import ConversationConverter
from app.chat.converters.message_converter import MessageConverter
from app.websocket.broadcasting_service import BroadcastingService

logger = logging.getLogger(__name__)


class ChatApplicationService(IChatApplicationService):
    """聊天应用服务 - 整合会话和消息管理"""

    def __init__(
        self,
        conversation_repository: IConversationRepository,
        message_repository: IMessageRepository,
        conversation_domain_service: IConversationDomainService,
        message_domain_service: IMessageDomainService,
        broadcasting_service: Optional[BroadcastingService] = None
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.conversation_domain_service = conversation_domain_service
        self.message_domain_service = message_domain_service
        self.broadcasting_service = broadcasting_service

    def get_user_role(self, user: User) -> str:
        """获取用户的当前角色"""
        if hasattr(user, '_active_role') and user._active_role:
            return user._active_role
        elif user.roles:
            return user.roles[0].name
        else:
            return 'customer'

    # ============ 会话相关用例 ============

    async def create_conversation_use_case(
        self,
        title: str,
        owner_id: str,
        chat_mode: str = "single",
        auto_assign_consultant: bool = True
    ) -> ConversationInfo:
        """创建会话用例"""
        try:
            logger.info(
                f"创建会话: title={title}, owner_id={owner_id}, type={chat_mode}")

            # 1. 调用领域服务创建会话
            conversation = await self.conversation_domain_service.create_conversation(
                title=title,
                owner_id=owner_id,
                chat_mode=chat_mode
            )

            # 2. 保存到仓储
            saved_conversation = await self.conversation_repository.save(conversation)

            # 3. 创建欢迎消息
            welcome_text = "欢迎来到安美智享！我是您的AI助手，有什么可以帮助您的吗？"
            welcome_message = await self.message_domain_service.create_system_message(
                conversation_id=str(saved_conversation.id),
                event_type="welcome",
                event_data={"message": welcome_text}
            )

            # 4. 保存欢迎消息
            await self.message_repository.save(welcome_message)

            logger.info(f"会话创建成功: id={saved_conversation.id}")

            # 5. 转换为响应Schema
            conversation_info = ConversationConverter.to_response(
                saved_conversation)
            if conversation_info is None:
                raise ValueError("会话转换失败")
            return conversation_info

        except ValueError as e:
            logger.error(f"创建会话失败: {e}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"创建会话时发生未知错误: {e}")
            raise Exception("创建会话失败")

    async def create_conversation(self, request: ConversationCreate, owner_id: str) -> ConversationInfo:
        """创建会话用例 - 兼容接口"""
        return await self.create_conversation_use_case(
            title=request.title,
            owner_id=owner_id,
            chat_mode=request.chat_mode
        )

    async def get_conversations_use_case(
        self,
        user_id: str,
        user_role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConversationInfo]:
        """获取用户会话列表用例"""
        try:
            logger.info(f"应用服务：获取会话列表 - user_id={user_id}, role={user_role}")

            # 1. 从仓储获取会话列表
            conversations = await self.conversation_repository.get_user_conversations(
                user_id=user_id,
                user_role=user_role,
                skip=skip,
                limit=limit
            )

            # 2. 获取最后消息和未读数
            conversation_ids = [str(conv.id) for conv in conversations]
            last_messages_with_senders = await self.conversation_repository.get_last_messages(conversation_ids)
            unread_counts = await self.conversation_repository.get_unread_counts(conversation_ids, user_id)

            # 3. 转换为响应Schema列表
            return ConversationConverter.to_list_response(
                conversations=conversations,
                last_messages_with_senders=last_messages_with_senders,
                unread_counts=unread_counts
            )

        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            raise Exception("获取会话列表失败")

    async def get_conversations(self, user_id: str, user_role: str, skip: int = 0, limit: int = 100) -> List[ConversationInfo]:
        """获取用户会话列表用例 - 兼容接口"""
        return await self.get_conversations_use_case(user_id, user_role, skip, limit)

    async def get_conversation_by_id_use_case(
        self,
        conversation_id: str,
        user_id: str,
        user_role: str
    ) -> Optional[ConversationInfo]:
        """获取指定会话用例"""
        try:
            logger.info(
                f"应用服务：获取会话 - conversation_id={conversation_id}, user_id={user_id}")

            # 1. 验证访问权限
            if not await self.conversation_domain_service.verify_access(conversation_id, user_id, user_role):
                return None

            # 2. 从仓储获取会话
            conversation = await self.conversation_repository.get_by_id(conversation_id)
            if not conversation:
                return None

            # 3. 获取最后消息
            last_message, sender_user, sender_digital_human = await self.conversation_repository.get_last_message_with_sender(conversation_id)

            # 4. 获取未读数
            unread_count = await self.conversation_repository.get_unread_count(conversation_id, user_id)

            # 5. 转换为响应Schema
            conversation_info = ConversationConverter.to_response(
                conversation=conversation,
                last_message=last_message,
                unread_count=unread_count,
                sender_user=sender_user,
                sender_digital_human=sender_digital_human
            )
            return conversation_info

        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            raise Exception("获取会话失败")

    async def get_conversation_by_id(self, conversation_id: str, user_id: str, user_role: str) -> Optional[ConversationInfo]:
        """获取指定会话用例 - 兼容接口"""
        return await self.get_conversation_by_id_use_case(conversation_id, user_id, user_role)

    async def update_conversation(self, conversation_id: str, user_id: str, updates: dict) -> Optional[ConversationInfo]:
        """更新会话用例"""
        logger.info(
            f"应用服务：更新会话 - conversation_id={conversation_id}, user_id={user_id}")

        # 1. 验证访问权限
        if not await self.conversation_domain_service.verify_ownership(conversation_id, user_id):
            raise ValueError("无权限修改此会话")

        # 2. 获取会话
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            return None

        # 3. 应用更新
        updated_conversation = await self.conversation_domain_service.update_conversation(conversation, updates)

        # 4. 保存更新后的会话
        saved_conversation = await self.conversation_repository.save(updated_conversation)

        # 5. 转换为响应模型
        conversation_info = ConversationConverter.to_response(
            saved_conversation)
        if conversation_info is None:
            raise ValueError("会话转换失败")
        return conversation_info

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """删除会话用例"""
        logger.info(
            f"应用服务：删除会话 - conversation_id={conversation_id}, user_id={user_id}")

        # 1. 验证访问权限
        if not await self.conversation_domain_service.verify_ownership(conversation_id, user_id):
            raise ValueError("无权限删除此会话")

        # 2. 执行删除
        return await self.conversation_repository.delete(conversation_id)

    # ============ 消息相关用例 ============

    async def send_message_use_case(
        self,
        conversation_id: str,
        content: Union[str, Dict[str, Any]],
        message_type: str,
        sender_id: str,
        sender_type: str
    ) -> MessageInfo:
        """发送消息用例"""
        try:
            # 1. 验证会话存在和权限
            conversation = await self.conversation_repository.get_by_id(conversation_id)
            if not conversation:
                raise ValueError(f"会话不存在: {conversation_id}")

            if not self._verify_conversation_access(conversation, sender_id, sender_type):
                raise ValueError(f"会话不存在或无权访问: {conversation_id}")

            # 2. 确保content是字典格式
            if isinstance(content, str):
                content = {"text": content}

            # 3. 创建消息
            message = Message(
                id="",  # 由仓储生成
                conversation_id=conversation_id,
                content=content,
                message_type=message_type,
                sender_id=sender_id,
                sender_type=sender_type,
                is_important=False,
                reply_to_message_id=None,
                extra_metadata={}
            )

            # 4. 保存消息
            saved_message = await self.message_repository.save(message)

            # 5. 更新会话消息数
            updated_conversation = await self.conversation_domain_service.increment_message_count(conversation_id)
            if updated_conversation:
                await self.conversation_repository.save(updated_conversation)

            # 6. 广播消息
            if self.broadcasting_service:
                try:
                    message_info = MessageConverter.to_response(saved_message)
                    if message_info:
                        await self.broadcasting_service.broadcast_message(
                            conversation_id=conversation_id,
                            message_data=message_info.dict(),
                            exclude_user_id=sender_id
                        )
                        logger.info(f"消息广播成功: message_id={saved_message.id}")
                except Exception as e:
                    logger.error(
                        f"消息广播失败: message_id={saved_message.id}, error={e}")

            # 7. 转换为响应Schema
            message_info = MessageConverter.to_response(saved_message)
            if message_info is None:
                raise ValueError("消息转换失败")
            return message_info

        except ValueError as e:
            logger.error(f"发送消息失败: {e}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"发送消息时发生未知错误: {e}")
            raise Exception("发送消息失败")

    async def create_message_use_case(
        self,
        conversation_id: str,
        request: MessageCreateRequest,
        sender: User
    ) -> MessageInfo:
        """创建通用消息用例"""
        try:
            # 1. 创建领域实体
            message = Message(
                id="",  # 由仓储生成
                conversation_id=conversation_id,
                content=request.content,
                message_type=request.type,
                sender_id=str(sender.id),
                sender_type=self.get_user_role(sender),
                is_important=request.is_important or False,
                reply_to_message_id=request.reply_to_message_id,
                extra_metadata=request.extra_metadata
            )

            # 2. 保存到仓储
            saved_message = await self.message_repository.save(message)

            # 3. 转换为响应Schema
            message_info = MessageConverter.to_response(saved_message)
            if message_info is None:
                raise ValueError("消息转换失败")
            return message_info

        except ValueError as e:
            logger.error(f"创建消息失败: {e}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"创建消息时发生未知错误: {e}")
            raise Exception("创建消息失败")

    async def create_text_message_use_case(
        self,
        conversation_id: str,
        request: CreateTextMessageRequest,
        sender: User
    ) -> MessageInfo:
        """创建文本消息用例"""
        try:
            # 1. 使用领域服务创建文本消息
            message = await self.message_domain_service.create_text_message(
                conversation_id=conversation_id,
                text=request.text,
                sender_id=str(sender.id),
                sender_type=self.get_user_role(sender)
            )

            # 2. 保存到仓储
            saved_message = await self.message_repository.save(message)

            # 3. 转换为响应Schema
            message_info = MessageConverter.to_response(saved_message)
            if message_info is None:
                raise ValueError("消息转换失败")
            return message_info

        except ValueError as e:
            logger.error(f"创建文本消息失败: {e}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"创建文本消息时发生未知错误: {e}")
            raise Exception("创建文本消息失败")

    async def create_media_message_use_case(
        self,
        conversation_id: str,
        request: CreateMediaMessageRequest,
        sender: User
    ) -> MessageInfo:
        """创建媒体消息用例"""
        try:
            # 1. 使用领域服务创建媒体消息
            message = await self.message_domain_service.create_media_message(
                conversation_id=conversation_id,
                media_url=request.media_url,
                media_name=request.media_name,
                mime_type=request.mime_type,
                sender_id=str(sender.id),
                sender_type=self.get_user_role(sender),
                text=request.text
            )

            # 2. 保存到仓储
            saved_message = await self.message_repository.save(message)

            # 3. 转换为响应Schema
            message_info = MessageConverter.to_response(saved_message)
            if message_info is None:
                raise ValueError("消息转换失败")
            return message_info

        except ValueError as e:
            logger.error(f"创建媒体消息失败: {e}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"创建媒体消息时发生未知错误: {e}")
            raise Exception("创建媒体消息失败")

    async def create_system_event_message_use_case(
        self,
        conversation_id: str,
        request: CreateSystemEventRequest,
        sender: User
    ) -> MessageInfo:
        """创建系统事件消息用例"""
        try:
            # 1. 权限检查
            from app.identity_access.deps.permission_deps import is_user_admin
            if not await is_user_admin(sender):
                raise PermissionError("只有管理员可以创建系统事件消息")

            # 2. 使用领域服务创建系统事件消息
            message = await self.message_domain_service.create_system_message(
                conversation_id=conversation_id,
                event_type=request.event_type,
                event_data=request.event_data or {}
            )

            # 3. 保存到仓储
            saved_message = await self.message_repository.save(message)

            # 4. 转换为响应Schema
            message_info = MessageConverter.to_response(saved_message)
            if message_info is None:
                raise ValueError("消息转换失败")
            return message_info

        except PermissionError:
            raise PermissionError("只有管理员可以创建系统事件消息")
        except ValueError as e:
            logger.error(f"创建系统事件消息失败: {e}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"创建系统事件消息时发生未知错误: {e}")
            raise Exception("创建系统事件消息失败")

    async def create_structured_message_use_case(
        self,
        conversation_id: str,
        request: CreateStructuredMessageRequest,
        sender: User
    ) -> MessageInfo:
        """创建结构化消息用例"""
        try:
            # 1. 使用领域服务创建结构化消息
            message = await self.message_domain_service.create_structured_message(
                conversation_id=conversation_id,
                card_type=request.card_type,
                title=request.title,
                data=request.data,
                sender_id=str(sender.id),
                sender_type=self.get_user_role(sender)
            )

            # 2. 保存到仓储
            saved_message = await self.message_repository.save(message)

            # 3. 转换为响应Schema
            message_info = MessageConverter.to_response(saved_message)
            if message_info is None:
                raise ValueError("消息转换失败")
            return message_info

        except ValueError as e:
            logger.error(f"创建结构化消息失败: {e}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"创建结构化消息时发生未知错误: {e}")
            raise Exception("创建结构化消息失败")

    async def create_appointment_confirmation_use_case(
        self,
        conversation_id: str,
        appointment_data: AppointmentCardData,
        sender: User
    ) -> MessageInfo:
        """创建预约确认消息用例"""
        try:
            # 1. 权限检查
            user_role = self.get_user_role(sender)
            if user_role not in ["consultant", "doctor"]:
                raise PermissionError("只有顾问或医生可以发送预约确认")

            # 2. 创建预约卡片内容
            content = {
                "card_type": "appointment",
                "title": "预约确认",
                "subtitle": f"您的{appointment_data.service_name}预约",
                "data": appointment_data.dict(),
                "components": [],
                "actions": {}
            }

            # 3. 创建领域实体
            message = Message(
                id="",  # 由仓储生成
                conversation_id=conversation_id,
                content=content,
                message_type="structured",
                sender_id=str(sender.id),
                sender_type=self.get_user_role(sender),
                is_important=True,  # 预约消息通常标记为重要
                reply_to_message_id=None,
                extra_metadata={}
            )

            # 4. 保存到仓储
            saved_message = await self.message_repository.save(message)

            # 5. 转换为响应Schema
            message_info = MessageConverter.to_response(saved_message)
            if message_info is None:
                raise ValueError("消息转换失败")
            return message_info

        except PermissionError:
            raise PermissionError("只有顾问或医生可以发送预约确认")
        except ValueError as e:
            logger.error(f"创建预约确认失败: {e}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"创建预约确认时发生未知错误: {e}")
            raise Exception("创建预约确认失败")

    async def get_conversation_messages_use_case(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[MessageInfo]:
        """获取会话消息列表用例"""
        try:
            # 1. 从仓储获取消息列表及发送者信息
            messages, sender_users, sender_digital_humans = await self.message_repository.get_conversation_messages_with_senders(
                conversation_id=conversation_id,
                skip=skip,
                limit=limit
            )

            # 2. 转换为响应Schema列表
            return MessageConverter.to_list_response(messages, sender_users, sender_digital_humans)

        except Exception as e:
            logger.error(f"获取消息列表失败: {e}")
            raise Exception("获取消息列表失败")

    async def mark_message_as_read_use_case(self, message_id: str) -> bool:
        """标记消息为已读用例"""
        try:
            # 1. 调用领域服务标记消息为已读
            success = await self.message_domain_service.mark_as_read(message_id)
            return success

        except Exception as e:
            logger.error(f"标记消息为已读失败: {e}")
            raise Exception("标记消息为已读失败")

    async def mark_message_as_important_use_case(
        self,
        message_id: str,
        is_important: bool
    ) -> bool:
        """标记消息为重点用例"""
        try:
            # 1. 调用领域服务标记消息为重点
            success = await self.message_domain_service.mark_as_important(message_id, is_important)
            return success

        except Exception as e:
            logger.error(f"标记消息为重点失败: {e}")
            raise Exception("标记消息为重点失败")

    async def add_reaction_use_case(self, message_id: str, user_id: str, emoji: str) -> bool:
        """添加反应用例"""
        try:
            # 1. 调用领域服务添加反应
            success = await self.message_domain_service.add_reaction(message_id, user_id, emoji)
            return success

        except Exception as e:
            logger.error(f"添加反应失败: {e}")
            raise Exception("添加反应失败")

    async def remove_reaction_use_case(self, message_id: str, user_id: str, emoji: str) -> bool:
        """移除反应用例"""
        try:
            # 1. 调用领域服务移除反应
            success = await self.message_domain_service.remove_reaction(message_id, user_id, emoji)
            return success

        except Exception as e:
            logger.error(f"移除反应失败: {e}")
            raise Exception("移除反应失败")

    async def broadcast_message_safe(
        self,
        conversation_id: str,
        message_info: MessageInfo,
        sender_id: str
    ) -> None:
        """安全地广播消息"""
        try:
            if self.broadcasting_service:
                await self.broadcasting_service.broadcast_message(
                    conversation_id=conversation_id,
                    message_data=message_info.dict(),
                    exclude_user_id=sender_id
                )
                logger.info(
                    f"消息广播成功: conversation_id={conversation_id}, message_id={message_info.id}")
        except Exception as e:
            logger.error(f"广播消息失败: {e}")
            # 不抛出异常，因为消息已经成功创建

    def _verify_conversation_access(
        self,
        conversation: Conversation,
        user_id: str,
        user_role: str
    ) -> bool:
        """验证用户对会话的访问权限"""
        # 会话所有者可以访问
        if str(conversation.owner_id) == user_id:
            return True

        # 管理员可以访问所有会话
        from app.identity_access.deps.permission_deps import is_user_admin
        if await is_user_admin(user):
            return True

        # 其他情况需要检查参与者关系
        # 这里简化处理，实际应该查询参与者表
        return False
