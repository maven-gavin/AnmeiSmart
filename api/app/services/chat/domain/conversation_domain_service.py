"""
会话领域服务 - 领域层
负责核心业务逻辑，领域规则，领域事件
遵循DDD分层架构的领域层职责
"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.services.chat.domain.interfaces import IConversationRepository, IConversationDomainService
from app.services.chat.domain.entities.conversation import Conversation

logger = logging.getLogger(__name__)


class ConversationDomainService(IConversationDomainService):
    """会话领域服务 - 核心业务逻辑"""

    def __init__(self, conversation_repository: IConversationRepository):
        self.conversation_repository = conversation_repository

    async def create_conversation(
        self,
        title: str,
        owner_id: str,
        chat_mode: str = "single"
    ) -> Conversation:
        """创建会话 - 领域逻辑"""
        logger.info(f"领域服务：创建会话 - title={title}, owner_id={owner_id}")

        # 领域规则验证
        if not title or not title.strip():
            raise ValueError("会话标题不能为空")

        if not owner_id:
            raise ValueError("会话所有者不能为空")

        # 检查用户是否已有同名会话
        if await self.conversation_repository.exists_by_title_and_owner(title.strip(), owner_id):
            raise ValueError(f"会话标题 '{title}' 已存在")

        # 使用领域实体的工厂方法创建会话
        conversation = Conversation.create(
            title=title.strip(),
            owner_id=owner_id,
            chat_mode=chat_mode
        )

        # 发布领域事件
        self._add_domain_event("conversation_created", {
            "conversation_id": str(conversation.id),
            "owner_id": owner_id,
            "title": title,
            "chat_mode": chat_mode
        })

        return conversation

    async def update_conversation(self, conversation: Conversation, updates: Dict[str, Any]) -> Conversation:
        """更新会话 - 领域逻辑"""
        logger.info(f"领域服务：更新会话 - conversation_id={conversation.id}")

        # 应用更新
        for field, value in updates.items():
            if field == "title" and hasattr(conversation, "update_title"):
                conversation.update_title(value)
            elif field == "is_pinned" and hasattr(conversation, "pin" if value else "unpin"):
                if value:
                    conversation.pin()
                else:
                    conversation.unpin()
            elif field == "is_archived" and hasattr(conversation, "archive" if value else "unarchive"):
                if value:
                    conversation.archive()
                else:
                    conversation.unarchive()
            elif hasattr(conversation, field):
                setattr(conversation, f"_{field}", value)

        # 发布领域事件
        self._add_domain_event("conversation_updated", {
            "conversation_id": str(conversation.id),
            "updated_fields": list(updates.keys())
        })

        return conversation  # 返回修改后的实体，由应用服务保存

    async def verify_access(self, conversation_id: str, user_id: str, user_role: str) -> bool:
        """验证用户对会话的访问权限 - 领域逻辑"""
        logger.info(
            f"领域服务：验证访问权限 - conversation_id={conversation_id}, user_id={user_id}, role={user_role}")

        # 从仓储获取会话
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            return False

        # 领域规则：用户可以访问自己参与的会话（包括第一位参与者和其他参与者）
        if await self.conversation_repository.is_user_participant(conversation_id, user_id):
            return True

        return False

    async def verify_ownership(self, conversation_id: str, user_id: str) -> bool:
        """验证用户是否为会话所有者 - 领域逻辑"""
        logger.info(
            f"领域服务：验证所有权 - conversation_id={conversation_id}, user_id={user_id}")

        # 从仓储获取会话
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            return False

        return str(conversation.owner_id) == user_id

    async def archive_conversation(self, conversation_id: str, user_id: str) -> Conversation:
        """归档会话 - 领域逻辑"""
        logger.info(
            f"领域服务：归档会话 - conversation_id={conversation_id}, user_id={user_id}")

        # 验证权限
        if not await self.verify_ownership(conversation_id, user_id):
            raise PermissionError("只有会话所有者可以归档会话")

        # 从仓储获取会话
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError("会话不存在")

        # 执行归档操作
        conversation.archive()

        # 发布领域事件
        self._add_domain_event("conversation_archived", {
            "conversation_id": str(conversation.id),
            "archived_by": user_id
        })

        return conversation  # 返回修改后的实体，由应用服务保存

    async def pin_conversation(self, conversation_id: str, user_id: str, is_pinned: bool) -> Conversation:
        """置顶/取消置顶会话 - 领域逻辑"""
        logger.info(
            f"领域服务：置顶会话 - conversation_id={conversation_id}, user_id={user_id}, is_pinned={is_pinned}")

        # 验证权限
        if not await self.verify_ownership(conversation_id, user_id):
            raise PermissionError("只有会话所有者可以置顶会话")

        # 从仓储获取会话
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError("会话不存在")

        # 执行置顶操作
        if is_pinned:
            conversation.pin()
        else:
            conversation.unpin()

        # 发布领域事件
        self._add_domain_event("conversation_pin_changed", {
            "conversation_id": str(conversation.id),
            "is_pinned": is_pinned,
            "changed_by": user_id
        })

        return conversation  # 返回修改后的实体，由应用服务保存

    async def increment_message_count(self, conversation_id: str) -> Optional[Conversation]:
        """增加会话消息数 - 领域逻辑"""
        logger.info(f"领域服务：增加消息数 - conversation_id={conversation_id}")

        # 从仓储获取会话
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            logger.warning(f"会话不存在，无法增加消息数: {conversation_id}")
            return None

        # 增加消息数
        conversation.increment_message_count()

        # 发布领域事件
        self._add_domain_event("conversation_message_count_incremented", {
            "conversation_id": str(conversation.id),
            "new_message_count": conversation.message_count
        })

        return conversation  # 返回修改后的实体，由应用服务保存

    async def mark_as_read(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """标记会话为已读 - 领域逻辑"""
        logger.info(
            f"领域服务：标记已读 - conversation_id={conversation_id}, user_id={user_id}")

        # 从仓储获取会话
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            logger.warning(f"会话不存在，无法标记已读: {conversation_id}")
            return None

        # 重置未读数
        conversation.reset_unread_count()

        # 发布领域事件
        self._add_domain_event("conversation_marked_as_read", {
            "conversation_id": str(conversation.id),
            "read_by": user_id
        })

        return conversation  # 返回修改后的实体，由应用服务保存

    def _add_domain_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """添加领域事件 - 内部方法"""
        # 这里可以集成事件总线或消息队列
        logger.info(f"领域事件：{event_type} - {event_data}")

        # TODO: 发布到事件总线
        # await event_bus.publish(event_type, event_data)
