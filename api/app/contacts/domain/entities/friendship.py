"""
好友关系聚合根
Contact领域的核心聚合，管理好友关系的生命周期和业务规则
"""
from typing import List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from app.contacts.domain.value_objects import FriendshipStatus, InteractionRecord


class FriendshipStatus(Enum):
    """好友关系状态值对象"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    DELETED = "deleted"


@dataclass
class InteractionRecord:
    """交互记录值对象"""
    interaction_type: str
    interaction_time: datetime
    metadata: dict = field(default_factory=dict)


class Friendship:
    """好友关系聚合根"""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        friend_id: str,
        status: FriendshipStatus = FriendshipStatus.PENDING,
        nickname: Optional[str] = None,
        remark: Optional[str] = None,
        is_starred: bool = False,
        is_muted: bool = False,
        is_pinned: bool = False,
        is_blocked: bool = False,
        verification_message: Optional[str] = None,
        source: str = "manual",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self._id = id
        self._user_id = user_id
        self._friend_id = friend_id
        self._status = status
        self._nickname = nickname
        self._remark = remark
        self._is_starred = is_starred
        self._is_muted = is_muted
        self._is_pinned = is_pinned
        self._is_blocked = is_blocked
        self._verification_message = verification_message
        self._source = source
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()
        
        # 聚合内部状态
        self._tags: Set[str] = set()  # 标签ID集合
        self._groups: Set[str] = set()  # 分组ID集合
        self._interaction_count = 0
        self._last_interaction_at: Optional[datetime] = None
        self._interaction_records: List[InteractionRecord] = []
        
        # 领域事件
        self._domain_events: List[object] = []
    
    # ============ 属性访问器 ============
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def user_id(self) -> str:
        return self._user_id
    
    @property
    def friend_id(self) -> str:
        return self._friend_id
    
    @property
    def status(self) -> FriendshipStatus:
        return self._status
    
    @property
    def nickname(self) -> Optional[str]:
        return self._nickname
    
    @property
    def remark(self) -> Optional[str]:
        return self._remark
    
    @property
    def is_starred(self) -> bool:
        return self._is_starred
    
    @property
    def is_muted(self) -> bool:
        return self._is_muted
    
    @property
    def is_pinned(self) -> bool:
        return self._is_pinned
    
    @property
    def is_blocked(self) -> bool:
        return self._is_blocked
    
    @property
    def verification_message(self) -> Optional[str]:
        return self._verification_message
    
    @property
    def source(self) -> str:
        return self._source
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def interaction_count(self) -> int:
        return self._interaction_count
    
    @property
    def last_interaction_at(self) -> Optional[datetime]:
        return self._last_interaction_at
    
    @property
    def tags(self) -> Set[str]:
        return self._tags.copy()
    
    @property
    def groups(self) -> Set[str]:
        return self._groups.copy()
    
    @property
    def interaction_records(self) -> List[InteractionRecord]:
        return self._interaction_records.copy()
    
    @property
    def domain_events(self) -> List[object]:
        return self._domain_events.copy()
    
    # ============ 领域方法 ============
    
    def accept_friendship(self) -> None:
        """接受好友请求"""
        if self._status != FriendshipStatus.PENDING:
            raise ValueError("只能接受待处理的好友请求")
        
        self._status = FriendshipStatus.ACCEPTED
        self._updated_at = datetime.utcnow()
        self._last_interaction_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipAcceptedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id
        ))
    
    def reject_friendship(self) -> None:
        """拒绝好友请求"""
        if self._status != FriendshipStatus.PENDING:
            raise ValueError("只能拒绝待处理的好友请求")
        
        self._status = FriendshipStatus.REJECTED
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipRejectedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id
        ))
    
    def block_friend(self) -> None:
        """拉黑好友"""
        if self._status == FriendshipStatus.BLOCKED:
            raise ValueError("好友已经被拉黑")
        
        self._status = FriendshipStatus.BLOCKED
        self._is_blocked = True
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipBlockedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id
        ))
    
    def unblock_friend(self) -> None:
        """取消拉黑"""
        if self._status != FriendshipStatus.BLOCKED:
            raise ValueError("好友未被拉黑")
        
        self._status = FriendshipStatus.ACCEPTED
        self._is_blocked = False
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipUnblockedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id
        ))
    
    def delete_friendship(self) -> None:
        """删除好友关系"""
        self._status = FriendshipStatus.DELETED
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipDeletedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id
        ))
    
    def update_nickname(self, nickname: Optional[str]) -> None:
        """更新昵称"""
        if nickname and len(nickname.strip()) > 100:
            raise ValueError("昵称不能超过100个字符")
        
        self._nickname = nickname.strip() if nickname else None
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipNicknameUpdatedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id,
            nickname=self._nickname
        ))
    
    def update_remark(self, remark: Optional[str]) -> None:
        """更新备注"""
        self._remark = remark
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipRemarkUpdatedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id,
            remark=self._remark
        ))
    
    def toggle_star(self) -> None:
        """切换星标状态"""
        self._is_starred = not self._is_starred
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipStarToggledEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id,
            is_starred=self._is_starred
        ))
    
    def toggle_mute(self) -> None:
        """切换免打扰状态"""
        self._is_muted = not self._is_muted
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipMuteToggledEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id,
            is_muted=self._is_muted
        ))
    
    def toggle_pin(self) -> None:
        """切换置顶状态"""
        self._is_pinned = not self._is_pinned
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipPinToggledEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id,
            is_pinned=self._is_pinned
        ))
    
    def add_tag(self, tag_id: str) -> None:
        """添加标签"""
        if tag_id in self._tags:
            raise ValueError("标签已存在")
        
        self._tags.add(tag_id)
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipTagAddedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id,
            tag_id=tag_id
        ))
    
    def remove_tag(self, tag_id: str) -> None:
        """移除标签"""
        if tag_id not in self._tags:
            raise ValueError("标签不存在")
        
        self._tags.remove(tag_id)
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipTagRemovedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id,
            tag_id=tag_id
        ))
    
    def add_to_group(self, group_id: str) -> None:
        """添加到分组"""
        if group_id in self._groups:
            raise ValueError("已在分组中")
        
        self._groups.add(group_id)
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipGroupAddedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id,
            group_id=group_id
        ))
    
    def remove_from_group(self, group_id: str) -> None:
        """从分组移除"""
        if group_id not in self._groups:
            raise ValueError("不在分组中")
        
        self._groups.remove(group_id)
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(FriendshipGroupRemovedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id,
            group_id=group_id
        ))
    
    def record_interaction(self, interaction_type: str, metadata: Optional[dict] = None) -> None:
        """记录交互"""
        if self._status != FriendshipStatus.ACCEPTED:
            raise ValueError("只能与已接受的好友记录交互")
        
        self._interaction_count += 1
        self._last_interaction_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
        
        # 创建交互记录
        interaction_record = InteractionRecord(
            interaction_type=interaction_type,
            interaction_time=datetime.utcnow(),
            metadata=metadata or {}
        )
        self._interaction_records.append(interaction_record)
        
        # 发布领域事件
        self._add_domain_event(FriendshipInteractionRecordedEvent(
            friendship_id=self._id,
            user_id=self._user_id,
            friend_id=self._friend_id,
            interaction_type=interaction_type,
            interaction_count=self._interaction_count
        ))
    
    # ============ 业务规则验证 ============
    
    def can_interact(self) -> bool:
        """检查是否可以交互"""
        return self._status == FriendshipStatus.ACCEPTED and not self._is_blocked
    
    def is_active(self) -> bool:
        """检查是否为活跃状态"""
        return self._status == FriendshipStatus.ACCEPTED
    
    def is_pending(self) -> bool:
        """检查是否为待处理状态"""
        return self._status == FriendshipStatus.PENDING
    
    def is_blocked(self) -> bool:
        """检查是否被拉黑"""
        return self._status == FriendshipStatus.BLOCKED or self._is_blocked
    
    # ============ 工厂方法 ============
    
    @classmethod
    def create(
        cls,
        user_id: str,
        friend_id: str,
        verification_message: Optional[str] = None,
        source: str = "manual"
    ) -> "Friendship":
        """创建好友关系"""
        if user_id == friend_id:
            raise ValueError("不能与自己建立好友关系")
        
        if not user_id or not friend_id:
            raise ValueError("用户ID和好友ID不能为空")
        
        # 生成ID（实际实现中应该使用UUID生成器）
        import uuid
        friendship_id = str(uuid.uuid4())
        
        return cls(
            id=friendship_id,
            user_id=user_id,
            friend_id=friend_id,
            status=FriendshipStatus.PENDING,
            verification_message=verification_message,
            source=source
        )
    
    # ============ 私有方法 ============
    
    def _add_domain_event(self, event: object) -> None:
        """添加领域事件"""
        self._domain_events.append(event)
    
    def clear_domain_events(self) -> None:
        """清除领域事件"""
        self._domain_events.clear()


# ============ 领域事件定义 ============

@dataclass
class FriendshipAcceptedEvent:
    friendship_id: str
    user_id: str
    friend_id: str


@dataclass
class FriendshipRejectedEvent:
    friendship_id: str
    user_id: str
    friend_id: str


@dataclass
class FriendshipBlockedEvent:
    friendship_id: str
    user_id: str
    friend_id: str


@dataclass
class FriendshipUnblockedEvent:
    friendship_id: str
    user_id: str
    friend_id: str


@dataclass
class FriendshipDeletedEvent:
    friendship_id: str
    user_id: str
    friend_id: str


@dataclass
class FriendshipNicknameUpdatedEvent:
    friendship_id: str
    user_id: str
    friend_id: str
    nickname: Optional[str]


@dataclass
class FriendshipRemarkUpdatedEvent:
    friendship_id: str
    user_id: str
    friend_id: str
    remark: Optional[str]


@dataclass
class FriendshipStarToggledEvent:
    friendship_id: str
    user_id: str
    friend_id: str
    is_starred: bool


@dataclass
class FriendshipMuteToggledEvent:
    friendship_id: str
    user_id: str
    friend_id: str
    is_muted: bool


@dataclass
class FriendshipPinToggledEvent:
    friendship_id: str
    user_id: str
    friend_id: str
    is_pinned: bool


@dataclass
class FriendshipTagAddedEvent:
    friendship_id: str
    user_id: str
    friend_id: str
    tag_id: str


@dataclass
class FriendshipTagRemovedEvent:
    friendship_id: str
    user_id: str
    friend_id: str
    tag_id: str


@dataclass
class FriendshipGroupAddedEvent:
    friendship_id: str
    user_id: str
    friend_id: str
    group_id: str


@dataclass
class FriendshipGroupRemovedEvent:
    friendship_id: str
    user_id: str
    friend_id: str
    group_id: str


@dataclass
class FriendshipInteractionRecordedEvent:
    friendship_id: str
    user_id: str
    friend_id: str
    interaction_type: str
    interaction_count: int
