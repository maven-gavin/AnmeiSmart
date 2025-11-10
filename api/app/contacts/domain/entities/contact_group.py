"""
联系人分组实体
Contact领域的分组管理实体
"""
from typing import List, Optional, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import uuid


class GroupType(Enum):
    """分组类型值对象"""
    PERSONAL = "personal"
    WORK = "work"
    PROJECT = "project"
    TEMPORARY = "temporary"


class GroupMemberRole(Enum):
    """分组成员角色值对象"""
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


@dataclass
class GroupMemberEntity:
    """分组成员值对象"""
    friendshipId: str
    role: GroupMemberRole
    joinedAt: datetime


class ContactGroupEntity:
    """联系人分组实体"""
    
    def __init__(
        self,
        id: str,
        userId: str,
        name: str,
        description: Optional[str] = None,
        color: str = "#3B82F6",
        icon: Optional[str] = None,
        groupType: GroupType = GroupType.PERSONAL,
        memberCount: int = 0,
        isVisible: bool = True,
        displayOrder: int = 0,
        createdAt: Optional[datetime] = None,
        updatedAt: Optional[datetime] = None
    ):
        self._id = id
        self._userId = userId
        self._name = name
        self._description = description
        self._color = color
        self._icon = icon
        self._groupType = groupType
        self._memberCount = memberCount
        self._isVisible = isVisible
        self._displayOrder = displayOrder
        self._createdAt = createdAt or datetime.utcnow()
        self._updatedAt = updatedAt or datetime.utcnow()
        
        # 聚合内部状态
        self._members: Set[str] = set()  # 好友关系ID集合
        self._memberDetails: List[GroupMemberEntity] = []  # 成员详细信息
        
        # 领域事件
        self._domainEvents: List[object] = []
    
    # ============ 属性访问器 ============
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def userId(self) -> str:
        return self._userId
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @property
    def color(self) -> str:
        return self._color
    
    @property
    def icon(self) -> Optional[str]:
        return self._icon
    
    @property
    def groupType(self) -> GroupType:
        return self._groupType
    
    @property
    def memberCount(self) -> int:
        return self._memberCount
    
    @property
    def isVisible(self) -> bool:
        return self._isVisible
    
    @property
    def displayOrder(self) -> int:
        return self._displayOrder
    
    @property
    def createdAt(self) -> datetime:
        return self._createdAt
    
    @property
    def updatedAt(self) -> datetime:
        return self._updatedAt
    
    @property
    def members(self) -> Set[str]:
        return set(self._members)
    
    @property
    def memberDetails(self) -> List[GroupMemberEntity]:
        return [member for member in self._memberDetails]
    
    @property
    def domainEvents(self) -> List[object]:
        return list(self._domainEvents)
    
    # ============ 领域方法 ============
    
    def updateName(self, name: str) -> None:
        """更新分组名称"""
        if not name or not name.strip():
            raise ValueError("分组名称不能为空")
        
        if len(name.strip()) > 100:
            raise ValueError("分组名称不能超过100个字符")
        
        old_name = self._name
        self._name = name.strip()
        self._updatedAt = datetime.utcnow()
        
        # 发布领域事件
        self._addDomainEvent(ContactGroupNameUpdatedEvent(
            groupId=self._id,
            userId=self._userId,
            oldName=old_name,
            newName=self._name
        ))
    
    def updateDescription(self, description: Optional[str]) -> None:
        """更新分组描述"""
        if description and len(description) > 500:
            raise ValueError("分组描述不能超过500个字符")
        
        self._description = description
        self._updatedAt = datetime.utcnow()
        
        # 发布领域事件
        self._addDomainEvent(ContactGroupDescriptionUpdatedEvent(
            groupId=self._id,
            userId=self._userId,
            description=description
        ))
    
    def updateColor(self, color: str) -> None:
        """更新分组颜色"""
        if not self._isValidColor(color):
            raise ValueError("无效的颜色格式")
        
        self._color = color
        self._updatedAt = datetime.utcnow()
        
        # 发布领域事件
        self._addDomainEvent(ContactGroupColorUpdatedEvent(
            groupId=self._id,
            userId=self._userId,
            color=color
        ))
    
    def updateIcon(self, icon: Optional[str]) -> None:
        """更新分组图标"""
        if icon and len(icon) > 50:
            raise ValueError("图标名称不能超过50个字符")
        
        self._icon = icon
        self._updatedAt = datetime.utcnow()
        
        # 发布领域事件
        self._addDomainEvent(ContactGroupIconUpdatedEvent(
            groupId=self._id,
            userId=self._userId,
            icon=icon
        ))
    
    def updateGroupType(self, groupType: GroupType) -> None:
        """更新分组类型"""
        self._groupType = groupType
        self._updatedAt = datetime.utcnow()
        
        # 发布领域事件
        self._addDomainEvent(ContactGroupTypeUpdatedEvent(
            groupId=self._id,
            userId=self._userId,
            groupType=groupType.value
        ))
    
    def updateDisplayOrder(self, displayOrder: int) -> None:
        """更新显示顺序"""
        if displayOrder < 0:
            raise ValueError("显示顺序不能为负数")
        
        self._displayOrder = displayOrder
        self._updatedAt = datetime.utcnow()
        
        # 发布领域事件
        self._addDomainEvent(ContactGroupDisplayOrderUpdatedEvent(
            groupId=self._id,
            userId=self._userId,
            displayOrder=displayOrder
        ))
    
    def toggleVisibility(self) -> None:
        """切换可见性"""
        self._isVisible = not self._isVisible
        self._updatedAt = datetime.utcnow()
        
        # 发布领域事件
        self._addDomainEvent(ContactGroupVisibilityToggledEvent(
            groupId=self._id,
            userId=self._userId,
            isVisible=self._isVisible
        ))
    
    def addMember(self, friendshipId: str, role: GroupMemberRole = GroupMemberRole.MEMBER) -> None:
        """添加成员"""
        if friendshipId in self._members:
            raise ValueError("成员已存在")
        
        self._members.add(friendshipId)
        self._memberCount += 1
        
        # 添加成员详细信息
        member_detail = GroupMemberEntity(
            friendshipId=friendshipId,
            role=role,
            joinedAt=datetime.utcnow()
        )
        self._memberDetails.append(member_detail)
        
        self._updatedAt = datetime.utcnow()
        
        # 发布领域事件
        self._addDomainEvent(ContactGroupMemberAddedEvent(
            groupId=self._id,
            userId=self._userId,
            friendshipId=friendshipId,
            role=role.value
        ))
    
    def removeMember(self, friendshipId: str) -> None:
        """移除成员"""
        if friendshipId not in self._members:
            raise ValueError("成员不存在")
        
        self._members.remove(friendshipId)
        self._memberCount -= 1
        
        # 移除成员详细信息
        self._memberDetails = [
            member for member in self._memberDetails
            if member.friendshipId != friendshipId
        ]
        
        self._updatedAt = datetime.utcnow()
        
        # 发布领域事件
        self._addDomainEvent(ContactGroupMemberRemovedEvent(
            groupId=self._id,
            userId=self._userId,
            friendshipId=friendshipId
        ))
    
    def updateMemberRole(self, friendshipId: str, role: GroupMemberRole) -> None:
        """更新成员角色"""
        if friendshipId not in self._members:
            raise ValueError("成员不存在")
        
        # 更新成员详细信息中的角色
        for member in self._memberDetails:
            if member.friendshipId == friendshipId:
                member.role = role
                break
        
        self._updatedAt = datetime.utcnow()
        
        # 发布领域事件
        self._addDomainEvent(ContactGroupMemberRoleUpdatedEvent(
            groupId=self._id,
            userId=self._userId,
            friendshipId=friendshipId,
            role=role.value
        ))
    
    def getMemberRole(self, friendshipId: str) -> Optional[GroupMemberRole]:
        """获取成员角色"""
        for member in self._memberDetails:
            if member.friendshipId == friendshipId:
                return member.role
        return None
    
    def isMember(self, friendshipId: str) -> bool:
        """检查是否为成员"""
        return friendshipId in self._members
    
    def canBeDeleted(self) -> bool:
        """检查是否可以删除"""
        return self._memberCount == 0
    
    def isAvailable(self) -> bool:
        """检查是否可用"""
        return self._isVisible
    
    # ============ 工厂方法 ============
    
    @classmethod
    def create(
        cls,
        userId: str,
        name: str,
        description: Optional[str] = None,
        color: str = "#3B82F6",
        icon: Optional[str] = None,
        groupType: GroupType = GroupType.PERSONAL,
        displayOrder: int = 0
    ) -> "ContactGroupEntity":
        """创建联系人分组"""
        if not userId:
            raise ValueError("用户ID不能为空")
        
        if not name or not name.strip():
            raise ValueError("分组名称不能为空")
        
        if len(name.strip()) > 100:
            raise ValueError("分组名称不能超过100个字符")
        
        if not cls._isValidColor(color):
            raise ValueError("无效的颜色格式")
        
        group_id = str(uuid.uuid4())
        
        return cls(
            id=group_id,
            userId=userId,
            name=name.strip(),
            description=description,
            color=color,
            icon=icon,
            groupType=groupType,
            displayOrder=displayOrder
        )
    
    # ============ 私有方法 ============
    
    @staticmethod
    def _isValidColor(color: str) -> bool:
        """验证颜色格式"""
        import re
        return bool(re.match(r"^#[0-9A-Fa-f]{6}$", color))
    
    def _addDomainEvent(self, event: object) -> None:
        """添加领域事件"""
        self._domainEvents.append(event)
    
    def clearDomainEvents(self) -> None:
        """清除领域事件"""
        self._domainEvents.clear()
    
    def __str__(self) -> str:
        return (
            f"ContactGroupEntity(id={self.id}, userId={self.userId}, name={self.name}, "
            f"groupType={self.groupType}, memberCount={self.memberCount}, isVisible={self.isVisible}, "
            f"displayOrder={self.displayOrder}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
    
    def __repr__(self) -> str:
        return (
            f"ContactGroupEntity(id={self.id}, userId={self.userId}, name={self.name}, "
            f"description={self.description}, color={self.color}, icon={self.icon}, "
            f"groupType={self.groupType}, memberCount={self.memberCount}, members={list(self.members)}, "
            f"isVisible={self.isVisible}, displayOrder={self.displayOrder}, "
            f"domainEvents={self.domainEvents}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )


# ============ 领域事件定义 ============

@dataclass
class ContactGroupNameUpdatedEvent:
    groupId: str
    userId: str
    oldName: str
    newName: str


@dataclass
class ContactGroupDescriptionUpdatedEvent:
    groupId: str
    userId: str
    description: Optional[str]


@dataclass
class ContactGroupColorUpdatedEvent:
    groupId: str
    userId: str
    color: str


@dataclass
class ContactGroupIconUpdatedEvent:
    groupId: str
    userId: str
    icon: Optional[str]


@dataclass
class ContactGroupTypeUpdatedEvent:
    groupId: str
    userId: str
    groupType: str


@dataclass
class ContactGroupDisplayOrderUpdatedEvent:
    groupId: str
    userId: str
    displayOrder: int


@dataclass
class ContactGroupVisibilityToggledEvent:
    groupId: str
    userId: str
    isVisible: bool


@dataclass
class ContactGroupMemberAddedEvent:
    groupId: str
    userId: str
    friendshipId: str
    role: str


@dataclass
class ContactGroupMemberRemovedEvent:
    groupId: str
    userId: str
    friendshipId: str


@dataclass
class ContactGroupMemberRoleUpdatedEvent:
    groupId: str
    userId: str
    friendshipId: str
    role: str
