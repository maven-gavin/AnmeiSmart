"""
会话聚合根 - 领域层
包含会话的业务逻辑和验证规则
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from app.common.infrastructure.db.uuid_utils import conversation_id


@dataclass
class ConversationEntity:
    """会话聚合根"""
    
    id: str
    title: str
    ownerId: str
    chatMode: str = "single"
    isActive: bool = True
    isArchived: bool = False
    messageCount: int = 0
    unreadCount: int = 0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    isPinned: bool = False
    pinnedAt: Optional[datetime] = None
    lastMessageAt: Optional[datetime] = None
    assignedConsultantId: Optional[str] = None
    isAiControlled: bool = False
    extraMetadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """验证业务规则"""
        self.createdAt = self.createdAt or datetime.utcnow()
        self.updatedAt = self.updatedAt or datetime.utcnow()
        if self.extraMetadata is None:
            self.extraMetadata = {}
        
        if not self.title or not self.title.strip():
            raise ValueError("会话标题不能为空")
        
        if not self.ownerId:
            raise ValueError("会话所有者ID不能为空")
        
        if self.chatMode not in {"single", "group"}:
            raise ValueError("无效的会话类型")
        
        if self.messageCount < 0:
            raise ValueError("消息数不能为负数")
        
        if self.unreadCount < 0:
            raise ValueError("未读数不能为负数")
    
    def update_title(self, new_title: str) -> None:
        """更新会话标题"""
        if not new_title or not new_title.strip():
            raise ValueError("会话标题不能为空")
        
        self.title = new_title.strip()
        self.updatedAt = datetime.utcnow()
    
    def pin(self) -> None:
        """置顶会话"""
        self.isPinned = True
        self.pinnedAt = datetime.utcnow()
        self.updatedAt = datetime.utcnow()
    
    def unpin(self) -> None:
        """取消置顶会话"""
        self.isPinned = False
        self.pinnedAt = None
        self.updatedAt = datetime.utcnow()
    
    def archive(self) -> None:
        """归档会话"""
        self.isArchived = True
        self.isActive = False
        self.updatedAt = datetime.utcnow()
    
    def unarchive(self) -> None:
        """取消归档会话"""
        self.isArchived = False
        self.isActive = True
        self.updatedAt = datetime.utcnow()
    
    def assign_consultant(self, consultant_id: str) -> None:
        """分配顾问"""
        self.assignedConsultantId = consultant_id
        self.updatedAt = datetime.utcnow()
    
    def unassign_consultant(self) -> None:
        """取消分配顾问"""
        self.assignedConsultantId = None
        self.updatedAt = datetime.utcnow()
    
    def set_ai_controlled(self, is_ai_controlled: bool) -> None:
        """设置AI控制状态"""
        self.isAiControlled = is_ai_controlled
        self.updatedAt = datetime.utcnow()
    
    def increment_message_count(self) -> None:
        """增加消息数"""
        self.messageCount += 1
        self.lastMessageAt = datetime.utcnow()
        self.updatedAt = datetime.utcnow()
    
    def update_unread_count(self, count: int) -> None:
        """更新未读数"""
        if count < 0:
            raise ValueError("未读数不能为负数")
        
        self.unreadCount = count
        self.updatedAt = datetime.utcnow()
    
    def increment_unread_count(self) -> None:
        """增加未读数"""
        self.unreadCount += 1
        self.updatedAt = datetime.utcnow()
    
    def reset_unread_count(self) -> None:
        """重置未读数"""
        self.unreadCount = 0
        self.updatedAt = datetime.utcnow()
    
    def update_extra_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新附加元数据"""
        self.extraMetadata = metadata or {}
        self.updatedAt = datetime.utcnow()
    
    @classmethod
    def create(
        cls,
        title: str,
        ownerId: Optional[str] = None,
        *,
        owner_id: Optional[str] = None,
        chatMode: str = "single",
        chat_mode: Optional[str] = None,
        extraMetadata: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> "ConversationEntity":
        """创建新会话"""
        resolved_owner_id = ownerId if ownerId is not None else owner_id
        if resolved_owner_id is None:
            raise ValueError("会话所有者ID不能为空")
        
        return cls(
            id=conversation_id(),
            title=title,
            ownerId=resolved_owner_id,
            chatMode=chatMode if chatMode is not None else (chat_mode or "single"),
            extraMetadata=extraMetadata if extraMetadata is not None else extra_metadata
        )
    
    # 兼容旧的蛇形命名访问
    @property
    def owner_id(self) -> str:
        return self.ownerId
    
    @owner_id.setter
    def owner_id(self, value: str) -> None:
        self.ownerId = value
    
    @property
    def chat_mode(self) -> str:
        return self.chatMode
    
    @chat_mode.setter
    def chat_mode(self, value: str) -> None:
        self.chatMode = value
    
    @property
    def is_active(self) -> bool:
        return self.isActive
    
    @is_active.setter
    def is_active(self, value: bool) -> None:
        self.isActive = value
    
    @property
    def is_archived(self) -> bool:
        return self.isArchived
    
    @is_archived.setter
    def is_archived(self, value: bool) -> None:
        self.isArchived = value
    
    @property
    def message_count(self) -> int:
        return self.messageCount
    
    @message_count.setter
    def message_count(self, value: int) -> None:
        self.messageCount = value
    
    @property
    def unread_count(self) -> int:
        return self.unreadCount
    
    @unread_count.setter
    def unread_count(self, value: int) -> None:
        self.unreadCount = value
    
    @property
    def created_at(self) -> datetime:
        return self.createdAt
    
    @created_at.setter
    def created_at(self, value: datetime) -> None:
        self.createdAt = value
    
    @property
    def updated_at(self) -> datetime:
        return self.updatedAt
    
    @updated_at.setter
    def updated_at(self, value: datetime) -> None:
        self.updatedAt = value
    
    @property
    def is_pinned(self) -> bool:
        return self.isPinned
    
    @property
    def pinned_at(self) -> Optional[datetime]:
        return self.pinnedAt
    
    @property
    def last_message_at(self) -> Optional[datetime]:
        return self.lastMessageAt
    
    @last_message_at.setter
    def last_message_at(self, value: Optional[datetime]) -> None:
        self.lastMessageAt = value
    
    @property
    def assigned_consultant_id(self) -> Optional[str]:
        return self.assignedConsultantId
    
    @property
    def is_ai_controlled(self) -> bool:
        return self.isAiControlled
    
    @property
    def extra_metadata(self) -> Dict[str, Any]:
        return self.extraMetadata
    
    @extra_metadata.setter
    def extra_metadata(self, value: Dict[str, Any]) -> None:
        self.extraMetadata = value or {}
    
    def __str__(self) -> str:
        return (
            f"ConversationEntity(id={self.id}, title={self.title}, ownerId={self.ownerId}, "
            f"chatMode={self.chatMode}, isActive={self.isActive}, isArchived={self.isArchived}, "
            f"messageCount={self.messageCount}, unreadCount={self.unreadCount}, "
            f"createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
    
    def __repr__(self) -> str:
        return (
            f"ConversationEntity(id={self.id}, title={self.title}, ownerId={self.ownerId}, "
            f"chatMode={self.chatMode}, isActive={self.isActive}, isArchived={self.isArchived}, "
            f"messageCount={self.messageCount}, unreadCount={self.unreadCount}, "
            f"isPinned={self.isPinned}, pinnedAt={self.pinnedAt}, lastMessageAt={self.lastMessageAt}, "
            f"assignedConsultantId={self.assignedConsultantId}, isAiControlled={self.isAiControlled}, "
            f"extraMetadata={self.extraMetadata}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
