"""
联系人分组实体
Contact领域的分组管理实体
"""
from typing import List, Optional, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


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
class GroupMember:
    """分组成员值对象"""
    friendship_id: str
    role: GroupMemberRole
    joined_at: datetime


class ContactGroup:
    """联系人分组实体"""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        color: str = "#3B82F6",
        icon: Optional[str] = None,
        group_type: GroupType = GroupType.PERSONAL,
        member_count: int = 0,
        is_visible: bool = True,
        display_order: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self._id = id
        self._user_id = user_id
        self._name = name
        self._description = description
        self._color = color
        self._icon = icon
        self._group_type = group_type
        self._member_count = member_count
        self._is_visible = is_visible
        self._display_order = display_order
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()
        
        # 聚合内部状态
        self._members: Set[str] = set()  # 好友关系ID集合
        self._member_details: List[GroupMember] = []  # 成员详细信息
        
        # 领域事件
        self._domain_events = []
    
    # ============ 属性访问器 ============
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def user_id(self) -> str:
        return self._user_id
    
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
    def group_type(self) -> GroupType:
        return self._group_type
    
    @property
    def member_count(self) -> int:
        return self._member_count
    
    @property
    def is_visible(self) -> bool:
        return self._is_visible
    
    @property
    def display_order(self) -> int:
        return self._display_order
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def members(self) -> Set[str]:
        return self._members.copy()
    
    @property
    def member_details(self) -> List[GroupMember]:
        return self._member_details.copy()
    
    @property
    def domain_events(self) -> list:
        return self._domain_events.copy()
    
    # ============ 领域方法 ============
    
    def update_name(self, name: str) -> None:
        """更新分组名称"""
        if not name or not name.strip():
            raise ValueError("分组名称不能为空")
        
        if len(name.strip()) > 100:
            raise ValueError("分组名称不能超过100个字符")
        
        self._name = name.strip()
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactGroupNameUpdatedEvent(
            group_id=self._id,
            user_id=self._user_id,
            old_name=self._name,
            new_name=name
        ))
    
    def update_description(self, description: Optional[str]) -> None:
        """更新分组描述"""
        if description and len(description) > 500:
            raise ValueError("分组描述不能超过500个字符")
        
        self._description = description
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactGroupDescriptionUpdatedEvent(
            group_id=self._id,
            user_id=self._user_id,
            description=description
        ))
    
    def update_color(self, color: str) -> None:
        """更新分组颜色"""
        if not self._is_valid_color(color):
            raise ValueError("无效的颜色格式")
        
        self._color = color
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactGroupColorUpdatedEvent(
            group_id=self._id,
            user_id=self._user_id,
            color=color
        ))
    
    def update_icon(self, icon: Optional[str]) -> None:
        """更新分组图标"""
        if icon and len(icon) > 50:
            raise ValueError("图标名称不能超过50个字符")
        
        self._icon = icon
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactGroupIconUpdatedEvent(
            group_id=self._id,
            user_id=self._user_id,
            icon=icon
        ))
    
    def update_group_type(self, group_type: GroupType) -> None:
        """更新分组类型"""
        self._group_type = group_type
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactGroupTypeUpdatedEvent(
            group_id=self._id,
            user_id=self._user_id,
            group_type=group_type.value
        ))
    
    def update_display_order(self, display_order: int) -> None:
        """更新显示顺序"""
        if display_order < 0:
            raise ValueError("显示顺序不能为负数")
        
        self._display_order = display_order
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactGroupDisplayOrderUpdatedEvent(
            group_id=self._id,
            user_id=self._user_id,
            display_order=display_order
        ))
    
    def toggle_visibility(self) -> None:
        """切换可见性"""
        self._is_visible = not self._is_visible
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactGroupVisibilityToggledEvent(
            group_id=self._id,
            user_id=self._user_id,
            is_visible=self._is_visible
        ))
    
    def add_member(self, friendship_id: str, role: GroupMemberRole = GroupMemberRole.MEMBER) -> None:
        """添加成员"""
        if friendship_id in self._members:
            raise ValueError("成员已存在")
        
        self._members.add(friendship_id)
        self._member_count += 1
        
        # 添加成员详细信息
        member_detail = GroupMember(
            friendship_id=friendship_id,
            role=role,
            joined_at=datetime.utcnow()
        )
        self._member_details.append(member_detail)
        
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactGroupMemberAddedEvent(
            group_id=self._id,
            user_id=self._user_id,
            friendship_id=friendship_id,
            role=role.value
        ))
    
    def remove_member(self, friendship_id: str) -> None:
        """移除成员"""
        if friendship_id not in self._members:
            raise ValueError("成员不存在")
        
        self._members.remove(friendship_id)
        self._member_count -= 1
        
        # 移除成员详细信息
        self._member_details = [
            member for member in self._member_details 
            if member.friendship_id != friendship_id
        ]
        
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactGroupMemberRemovedEvent(
            group_id=self._id,
            user_id=self._user_id,
            friendship_id=friendship_id
        ))
    
    def update_member_role(self, friendship_id: str, role: GroupMemberRole) -> None:
        """更新成员角色"""
        if friendship_id not in self._members:
            raise ValueError("成员不存在")
        
        # 更新成员详细信息中的角色
        for member in self._member_details:
            if member.friendship_id == friendship_id:
                member.role = role
                break
        
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactGroupMemberRoleUpdatedEvent(
            group_id=self._id,
            user_id=self._user_id,
            friendship_id=friendship_id,
            role=role.value
        ))
    
    def get_member_role(self, friendship_id: str) -> Optional[GroupMemberRole]:
        """获取成员角色"""
        for member in self._member_details:
            if member.friendship_id == friendship_id:
                return member.role
        return None
    
    def is_member(self, friendship_id: str) -> bool:
        """检查是否为成员"""
        return friendship_id in self._members
    
    def can_be_deleted(self) -> bool:
        """检查是否可以删除"""
        return self._member_count == 0
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self._is_visible
    
    # ============ 工厂方法 ============
    
    @classmethod
    def create(
        cls,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        color: str = "#3B82F6",
        icon: Optional[str] = None,
        group_type: GroupType = GroupType.PERSONAL,
        display_order: int = 0
    ) -> "ContactGroup":
        """创建联系人分组"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        if not name or not name.strip():
            raise ValueError("分组名称不能为空")
        
        if len(name.strip()) > 100:
            raise ValueError("分组名称不能超过100个字符")
        
        if not cls._is_valid_color(color):
            raise ValueError("无效的颜色格式")
        
        # 生成ID（实际实现中应该使用UUID生成器）
        import uuid
        group_id = str(uuid.uuid4())
        
        return cls(
            id=group_id,
            user_id=user_id,
            name=name.strip(),
            description=description,
            color=color,
            icon=icon,
            group_type=group_type,
            display_order=display_order
        )
    
    # ============ 私有方法 ============
    
    @staticmethod
    def _is_valid_color(color: str) -> bool:
        """验证颜色格式"""
        import re
        return bool(re.match(r"^#[0-9A-Fa-f]{6}$", color))
    
    def _add_domain_event(self, event: object) -> None:
        """添加领域事件"""
        self._domain_events.append(event)
    
    def clear_domain_events(self) -> None:
        """清除领域事件"""
        self._domain_events.clear()


# ============ 领域事件定义 ============

@dataclass
class ContactGroupNameUpdatedEvent:
    group_id: str
    user_id: str
    old_name: str
    new_name: str


@dataclass
class ContactGroupDescriptionUpdatedEvent:
    group_id: str
    user_id: str
    description: Optional[str]


@dataclass
class ContactGroupColorUpdatedEvent:
    group_id: str
    user_id: str
    color: str


@dataclass
class ContactGroupIconUpdatedEvent:
    group_id: str
    user_id: str
    icon: Optional[str]


@dataclass
class ContactGroupTypeUpdatedEvent:
    group_id: str
    user_id: str
    group_type: str


@dataclass
class ContactGroupDisplayOrderUpdatedEvent:
    group_id: str
    user_id: str
    display_order: int


@dataclass
class ContactGroupVisibilityToggledEvent:
    group_id: str
    user_id: str
    is_visible: bool


@dataclass
class ContactGroupMemberAddedEvent:
    group_id: str
    user_id: str
    friendship_id: str
    role: str


@dataclass
class ContactGroupMemberRemovedEvent:
    group_id: str
    user_id: str
    friendship_id: str


@dataclass
class ContactGroupMemberRoleUpdatedEvent:
    group_id: str
    user_id: str
    friendship_id: str
    role: str
