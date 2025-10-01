"""
会话聚合根 - 领域层
包含会话的业务逻辑和验证规则
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.common.infrastructure.db.uuid_utils import conversation_id


class Conversation:
    """会话聚合根"""
    
    def __init__(
        self,
        id: str,
        title: str,
        owner_id: str,
        chat_mode: str = "single",
        is_active: bool = True,
        is_archived: bool = False,
        message_count: int = 0,
        unread_count: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ):
        self._id = id
        self._title = title
        self._owner_id = owner_id
        self._chat_mode = chat_mode
        self._is_active = is_active
        self._is_archived = is_archived
        self._message_count = message_count
        self._unread_count = unread_count
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()
        self._is_pinned = False
        self._pinned_at = None
        self._last_message_at = None
        self._assigned_consultant_id = None
        self._is_ai_controlled = False
        self._extra_metadata = extra_metadata or {}
        
        # 验证业务规则
        self._validate()
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def title(self) -> str:
        return self._title
    
    @property
    def owner_id(self) -> str:
        return self._owner_id
    
    @property
    def chat_mode(self) -> str:
        return self._chat_mode
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    @property
    def is_archived(self) -> bool:
        return self._is_archived
    
    @property
    def message_count(self) -> int:
        return self._message_count
    
    @property
    def unread_count(self) -> int:
        return self._unread_count
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def is_pinned(self) -> bool:
        return self._is_pinned
    
    @property
    def pinned_at(self) -> Optional[datetime]:
        return self._pinned_at
    
    @property
    def last_message_at(self) -> Optional[datetime]:
        return self._last_message_at
    
    @property
    def assigned_consultant_id(self) -> Optional[str]:
        return self._assigned_consultant_id
    
    @property
    def is_ai_controlled(self) -> bool:
        return self._is_ai_controlled
    
    @property
    def extra_metadata(self) -> Dict[str, Any]:
        return self._extra_metadata
    
    def _validate(self) -> None:
        """验证业务规则"""
        if not self._title.strip():
            raise ValueError("会话标题不能为空")
        
        if not self._owner_id:
            raise ValueError("会话所有者ID不能为空")
        
        if self._chat_mode not in ["single", "group"]:
            raise ValueError("无效的会话类型")
        
        if self._message_count < 0:
            raise ValueError("消息数不能为负数")
        
        if self._unread_count < 0:
            raise ValueError("未读数不能为负数")
    
    def update_title(self, new_title: str) -> None:
        """更新会话标题"""
        if not new_title.strip():
            raise ValueError("会话标题不能为空")
        
        self._title = new_title.strip()
        self._updated_at = datetime.now()
    
    def pin(self) -> None:
        """置顶会话"""
        self._is_pinned = True
        self._pinned_at = datetime.now()
        self._updated_at = datetime.now()
    
    def unpin(self) -> None:
        """取消置顶会话"""
        self._is_pinned = False
        self._pinned_at = None
        self._updated_at = datetime.now()
    
    def archive(self) -> None:
        """归档会话"""
        self._is_archived = True
        self._is_active = False
        self._updated_at = datetime.now()
    
    def unarchive(self) -> None:
        """取消归档会话"""
        self._is_archived = False
        self._is_active = True
        self._updated_at = datetime.now()
    
    def assign_consultant(self, consultant_id: str) -> None:
        """分配顾问"""
        self._assigned_consultant_id = consultant_id
        self._updated_at = datetime.now()
    
    def unassign_consultant(self) -> None:
        """取消分配顾问"""
        self._assigned_consultant_id = None
        self._updated_at = datetime.now()
    
    def set_ai_controlled(self, is_ai_controlled: bool) -> None:
        """设置AI控制状态"""
        self._is_ai_controlled = is_ai_controlled
        self._updated_at = datetime.now()
    
    def increment_message_count(self) -> None:
        """增加消息数"""
        self._message_count += 1
        self._last_message_at = datetime.now()
        self._updated_at = datetime.now()
    
    def update_unread_count(self, count: int) -> None:
        """更新未读数"""
        if count < 0:
            raise ValueError("未读数不能为负数")
        
        self._unread_count = count
        self._updated_at = datetime.now()
    
    def increment_unread_count(self) -> None:
        """增加未读数"""
        self._unread_count += 1
        self._updated_at = datetime.now()
    
    def reset_unread_count(self) -> None:
        """重置未读数"""
        self._unread_count = 0
        self._updated_at = datetime.now()
    
    def update_extra_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新附加元数据"""
        self._extra_metadata = metadata or {}
        self._updated_at = datetime.now()
    
    @classmethod
    def create(
        cls,
        title: str,
        owner_id: str,
        chat_mode: str = "single",
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> "Conversation":
        """创建新会话"""
        return cls(
            id=conversation_id(),
            title=title,
            owner_id=owner_id,
            chat_mode=chat_mode,
            extra_metadata=extra_metadata
        )
