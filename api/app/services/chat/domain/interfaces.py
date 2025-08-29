"""
领域层抽象接口 - 遵循依赖倒置原则
定义仓储和应用服务的抽象接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.schemas.chat import MessageInfo, ConversationInfo, MessageCreateRequest, CreateTextMessageRequest


class IMessageRepository(ABC):
    """消息仓储抽象接口"""
    
    @abstractmethod
    async def save(self, message: Any) -> Any:
        """保存消息"""
        pass
    
    @abstractmethod
    async def get_by_id(self, message_id: str) -> Optional[Any]:
        """根据ID获取消息"""
        pass
    
    @abstractmethod
    async def get_conversation_messages(self, conversation_id: str, skip: int = 0, limit: int = 100) -> List[Any]:
        """获取会话消息"""
        pass
    
    @abstractmethod
    async def mark_as_read(self, message_id: str) -> bool:
        """标记消息为已读"""
        pass
    
    @abstractmethod
    async def mark_as_important(self, message_id: str, is_important: bool) -> bool:
        """标记消息为重点"""
        pass


class IConversationRepository(ABC):
    """会话仓储抽象接口"""
    
    @abstractmethod
    async def save(self, conversation: Any) -> Any:
        """保存会话"""
        pass
    
    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Optional[Any]:
        """根据ID获取会话"""
        pass
    
    @abstractmethod
    async def get_user_conversations(self, user_id: str, user_role: str, skip: int = 0, limit: int = 100) -> List[Any]:
        """获取用户参与的会话列表"""
        pass
    
    @abstractmethod
    async def exists_by_title_and_owner(self, title: str, owner_id: str) -> bool:
        """检查用户是否已有同名会话"""
        pass
    
    @abstractmethod
    async def get_last_message(self, conversation_id: str) -> Optional[Any]:
        """获取会话的最后一条消息"""
        pass
    
    @abstractmethod
    async def get_unread_count(self, conversation_id: str, user_id: str) -> int:
        """获取用户在指定会话中的未读消息数"""
        pass
    
    @abstractmethod
    async def get_last_messages(self, conversation_ids: List[str]) -> Dict[str, Any]:
        """批量获取会话的最后消息"""
        pass
    
    @abstractmethod
    async def get_unread_counts(self, conversation_ids: List[str], user_id: str) -> Dict[str, int]:
        """批量获取会话的未读数"""
        pass
    
    @abstractmethod
    async def delete(self, conversation_id: str) -> bool:
        """删除会话"""
        pass





class IChatApplicationService(ABC):
    """聊天应用服务抽象接口"""
    
    @abstractmethod
    async def create_conversation_use_case(self, title: str, owner_id: str, conversation_type: str, auto_assign_consultant: bool) -> ConversationInfo:
        """创建会话用例"""
        pass
    
    @abstractmethod
    def get_conversations_use_case(self, user_id: str, user_role: str, skip: int = 0, limit: int = 100) -> List[ConversationInfo]:
        """获取用户会话列表用例"""
        pass
    
    @abstractmethod
    def get_conversation_by_id_use_case(self, conversation_id: str, user_id: str, user_role: str) -> Optional[ConversationInfo]:
        """获取指定会话用例"""
        pass
    
    @abstractmethod
    async def send_message_use_case(self, conversation_id: str, content: Any, message_type: str, sender_id: str, sender_type: str) -> MessageInfo:
        """发送消息用例"""
        pass


class IConversationDomainService(ABC):
    """会话领域服务抽象接口"""
    
    @abstractmethod
    async def create_conversation(self, title: str, owner_id: str, conversation_type: str = "single") -> Any:
        """创建会话 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def update_conversation(self, conversation: Any, updates: Dict[str, Any]) -> Any:
        """更新会话 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def verify_access(self, conversation_id: str, user_id: str, user_role: str) -> bool:
        """验证用户对会话的访问权限 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def verify_ownership(self, conversation_id: str, user_id: str) -> bool:
        """验证用户是否为会话所有者 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def archive_conversation(self, conversation_id: str, user_id: str) -> Any:
        """归档会话 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def pin_conversation(self, conversation_id: str, user_id: str, is_pinned: bool) -> Any:
        """置顶/取消置顶会话 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def increment_message_count(self, conversation_id: str) -> Optional[Any]:
        """增加会话消息数 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def mark_as_read(self, conversation_id: str, user_id: str) -> Optional[Any]:
        """标记会话为已读 - 领域逻辑"""
        pass


class IMessageDomainService(ABC):
    """消息领域服务抽象接口"""
    
    @abstractmethod
    async def create_text_message(self, conversation_id: str, text: str, sender_id: str, sender_type: str) -> Any:
        """创建文本消息 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def create_media_message(self, conversation_id: str, media_url: str, media_name: str, mime_type: str, sender_id: str, sender_type: str, text: Optional[str] = None) -> Any:
        """创建媒体消息 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def create_system_message(self, conversation_id: str, event_type: str, event_data: Dict[str, Any]) -> Any:
        """创建系统消息 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def create_structured_message(self, conversation_id: str, card_type: str, title: str, data: Dict[str, Any], sender_id: str, sender_type: str) -> Any:
        """创建结构化消息 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def mark_as_read(self, message_id: str) -> bool:
        """标记消息为已读 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def mark_as_important(self, message_id: str, is_important: bool) -> bool:
        """标记/取消标记消息为重点 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def add_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """添加反应 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def remove_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """移除反应 - 领域逻辑"""
        pass

