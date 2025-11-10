"""
好友关系聚合根
Contact领域的核心聚合，管理好友关系的生命周期和业务规则
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid


class FriendshipStatus(Enum):
    """好友关系状态值对象"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    DELETED = "deleted"


@dataclass
class InteractionRecordEntity:
    """交互记录值对象"""
    interactionType: str
    interactionTime: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FriendshipEntity:
    """好友关系聚合根"""

    id: str
    userId: str
    friendId: str
    status: FriendshipStatus = FriendshipStatus.PENDING
    nickname: Optional[str] = None
    remark: Optional[str] = None
    isStarred: bool = False
    isMuted: bool = False
    isPinned: bool = False
    isBlocked: bool = False
    verificationMessage: Optional[str] = None
    source: str = "manual"
    createdAt: datetime = field(default_factory=datetime.utcnow)
    updatedAt: datetime = field(default_factory=datetime.utcnow)
    interactionCount: int = 0
    lastInteractionAt: Optional[datetime] = None
    _tags: Set[str] = field(default_factory=set, repr=False)
    _groups: Set[str] = field(default_factory=set, repr=False)
    _interactionRecords: List[InteractionRecordEntity] = field(default_factory=list, repr=False)
    _domainEvents: List[object] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self._normalize()
        self._validate()

    def _normalize(self) -> None:
        if self.nickname:
            self.nickname = self.nickname.strip()
        if self.verificationMessage:
            self.verificationMessage = self.verificationMessage.strip() or None
        if self.remark:
            self.remark = self.remark.strip()

    def _validate(self) -> None:
        if not self.userId or not self.friendId:
            raise ValueError("用户ID和好友ID不能为空")
        if self.userId == self.friendId:
            raise ValueError("不能与自己建立好友关系")
        if self.nickname and len(self.nickname) > 100:
            raise ValueError("昵称不能超过100个字符")
        if self.remark and len(self.remark) > 500:
            raise ValueError("备注不能超过500个字符")
        if self.interactionCount < 0:
            raise ValueError("交互次数不能为负数")

    @property
    def tags(self) -> Set[str]:
        return set(self._tags)

    @property
    def groups(self) -> Set[str]:
        return set(self._groups)

    @property
    def interactionRecords(self) -> List[InteractionRecordEntity]:
        return [record for record in self._interactionRecords]

    @property
    def domainEvents(self) -> List[object]:
        return list(self._domainEvents)

    def acceptFriendship(self) -> None:
        if self.status != FriendshipStatus.PENDING:
            raise ValueError("只能接受待处理的好友请求")
        self.status = FriendshipStatus.ACCEPTED
        self.updatedAt = datetime.utcnow()
        self.lastInteractionAt = datetime.utcnow()
        self.interactionCount = 0
        self._addDomainEvent(FriendshipAcceptedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId
        ))

    def rejectFriendship(self) -> None:
        if self.status != FriendshipStatus.PENDING:
            raise ValueError("只能拒绝待处理的好友请求")
        self.status = FriendshipStatus.REJECTED
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipRejectedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId
        ))

    def blockFriend(self) -> None:
        if self.status == FriendshipStatus.BLOCKED:
            raise ValueError("好友已经被拉黑")
        self.status = FriendshipStatus.BLOCKED
        self.isBlocked = True
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipBlockedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId
        ))

    def unblockFriend(self) -> None:
        if self.status != FriendshipStatus.BLOCKED:
            raise ValueError("好友未被拉黑")
        self.status = FriendshipStatus.ACCEPTED
        self.isBlocked = False
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipUnblockedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId
        ))

    def deleteFriendship(self) -> None:
        self.status = FriendshipStatus.DELETED
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipDeletedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId
        ))

    def updateNickname(self, nickname: Optional[str]) -> None:
        if nickname and len(nickname.strip()) > 100:
            raise ValueError("昵称不能超过100个字符")
        self.nickname = nickname.strip() if nickname else None
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipNicknameUpdatedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId,
            nickname=self.nickname
        ))

    def updateRemark(self, remark: Optional[str]) -> None:
        self.remark = remark.strip() if remark else None
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipRemarkUpdatedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId,
            remark=self.remark
        ))

    def toggleStar(self) -> None:
        self.isStarred = not self.isStarred
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipStarToggledEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId,
            isStarred=self.isStarred
        ))

    def toggleMute(self) -> None:
        self.isMuted = not self.isMuted
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipMuteToggledEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId,
            isMuted=self.isMuted
        ))

    def togglePin(self) -> None:
        self.isPinned = not self.isPinned
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipPinToggledEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId,
            isPinned=self.isPinned
        ))

    def addTag(self, tagId: str) -> None:
        if tagId in self._tags:
            raise ValueError("标签已存在")
        self._tags.add(tagId)
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipTagAddedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId,
            tagId=tagId
        ))

    def removeTag(self, tagId: str) -> None:
        if tagId not in self._tags:
            raise ValueError("标签不存在")
        self._tags.remove(tagId)
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipTagRemovedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId,
            tagId=tagId
        ))

    def addToGroup(self, groupId: str) -> None:
        if groupId in self._groups:
            raise ValueError("已在分组中")
        self._groups.add(groupId)
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipGroupAddedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId,
            groupId=groupId
        ))

    def removeFromGroup(self, groupId: str) -> None:
        if groupId not in self._groups:
            raise ValueError("不在分组中")
        self._groups.remove(groupId)
        self.updatedAt = datetime.utcnow()
        self._addDomainEvent(FriendshipGroupRemovedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId,
            groupId=groupId
        ))

    def recordInteraction(self, interactionType: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self.status != FriendshipStatus.ACCEPTED:
            raise ValueError("只能与已接受的好友记录交互")
        self.interactionCount += 1
        self.lastInteractionAt = datetime.utcnow()
        self.updatedAt = datetime.utcnow()
        interaction_record = InteractionRecordEntity(
            interactionType=interactionType,
            interactionTime=datetime.utcnow(),
            metadata=dict(metadata or {})
        )
        self._interactionRecords.append(interaction_record)
        self._addDomainEvent(FriendshipInteractionRecordedEvent(
            friendshipId=self.id,
            userId=self.userId,
            friendId=self.friendId,
            interactionType=interactionType,
            interactionCount=self.interactionCount
        ))

    def canInteract(self) -> bool:
        return self.status == FriendshipStatus.ACCEPTED and not self.isBlocked

    def isActive(self) -> bool:
        return self.status == FriendshipStatus.ACCEPTED

    def isPending(self) -> bool:
        return self.status == FriendshipStatus.PENDING

    def isBlockedState(self) -> bool:
        return self.status == FriendshipStatus.BLOCKED or self.isBlocked

    @classmethod
    def create(
        cls,
        userId: str,
        friendId: str,
        verificationMessage: Optional[str] = None,
        source: str = "manual"
    ) -> "FriendshipEntity":
        friendship_id = str(uuid.uuid4())
        return cls(
            id=friendship_id,
            userId=userId,
            friendId=friendId,
            status=FriendshipStatus.PENDING,
            verificationMessage=verificationMessage,
            source=source
        )

    def _addDomainEvent(self, event: object) -> None:
        self._domainEvents.append(event)

    def clearDomainEvents(self) -> None:
        self._domainEvents.clear()

    def __str__(self) -> str:
        return (
            f"FriendshipEntity(id={self.id}, userId={self.userId}, friendId={self.friendId}, "
            f"status={self.status}, isStarred={self.isStarred}, isMuted={self.isMuted}, "
            f"isPinned={self.isPinned}, isBlocked={self.isBlocked}, interactionCount={self.interactionCount})"
        )

    def __repr__(self) -> str:
        return (
            f"FriendshipEntity(id={self.id}, userId={self.userId}, friendId={self.friendId}, "
            f"status={self.status}, nickname={self.nickname}, remark={self.remark}, "
            f"isStarred={self.isStarred}, isMuted={self.isMuted}, isPinned={self.isPinned}, "
            f"isBlocked={self.isBlocked}, tags={list(self.tags)}, groups={list(self.groups)}, "
            f"interactionCount={self.interactionCount}, lastInteractionAt={self.lastInteractionAt}, "
            f"domainEvents={self.domainEvents}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )


@dataclass
class FriendshipAcceptedEvent:
    friendshipId: str
    userId: str
    friendId: str


@dataclass
class FriendshipRejectedEvent:
    friendshipId: str
    userId: str
    friendId: str


@dataclass
class FriendshipBlockedEvent:
    friendshipId: str
    userId: str
    friendId: str


@dataclass
class FriendshipUnblockedEvent:
    friendshipId: str
    userId: str
    friendId: str


@dataclass
class FriendshipDeletedEvent:
    friendshipId: str
    userId: str
    friendId: str


@dataclass
class FriendshipNicknameUpdatedEvent:
    friendshipId: str
    userId: str
    friendId: str
    nickname: Optional[str]


@dataclass
class FriendshipRemarkUpdatedEvent:
    friendshipId: str
    userId: str
    friendId: str
    remark: Optional[str]


@dataclass
class FriendshipStarToggledEvent:
    friendshipId: str
    userId: str
    friendId: str
    isStarred: bool


@dataclass
class FriendshipMuteToggledEvent:
    friendshipId: str
    userId: str
    friendId: str
    isMuted: bool


@dataclass
class FriendshipPinToggledEvent:
    friendshipId: str
    userId: str
    friendId: str
    isPinned: bool


@dataclass
class FriendshipTagAddedEvent:
    friendshipId: str
    userId: str
    friendId: str
    tagId: str


@dataclass
class FriendshipTagRemovedEvent:
    friendshipId: str
    userId: str
    friendId: str
    tagId: str


@dataclass
class FriendshipGroupAddedEvent:
    friendshipId: str
    userId: str
    friendId: str
    groupId: str


@dataclass
class FriendshipGroupRemovedEvent:
    friendshipId: str
    userId: str
    friendId: str
    groupId: str


@dataclass
class FriendshipInteractionRecordedEvent:
    friendshipId: str
    userId: str
    friendId: str
    interactionType: str
    interactionCount: int

