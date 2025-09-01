"""
联系人标签实体
Contact领域的标签管理实体
"""
from typing import Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class TagCategory(Enum):
    """标签分类值对象"""
    WORK = "work"
    PERSONAL = "personal"
    BUSINESS = "business"
    MEDICAL = "medical"
    CUSTOM = "custom"


class ContactTag:
    """联系人标签实体"""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        name: str,
        color: str = "#3B82F6",
        icon: Optional[str] = None,
        description: Optional[str] = None,
        category: TagCategory = TagCategory.CUSTOM,
        display_order: int = 0,
        is_visible: bool = True,
        is_system_tag: bool = False,
        usage_count: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self._id = id
        self._user_id = user_id
        self._name = name
        self._color = color
        self._icon = icon
        self._description = description
        self._category = category
        self._display_order = display_order
        self._is_visible = is_visible
        self._is_system_tag = is_system_tag
        self._usage_count = usage_count
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()
        
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
    def color(self) -> str:
        return self._color
    
    @property
    def icon(self) -> Optional[str]:
        return self._icon
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @property
    def category(self) -> TagCategory:
        return self._category
    
    @property
    def display_order(self) -> int:
        return self._display_order
    
    @property
    def is_visible(self) -> bool:
        return self._is_visible
    
    @property
    def is_system_tag(self) -> bool:
        return self._is_system_tag
    
    @property
    def usage_count(self) -> int:
        return self._usage_count
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def domain_events(self) -> list:
        return self._domain_events.copy()
    
    # ============ 领域方法 ============
    
    def update_name(self, name: str) -> None:
        """更新标签名称"""
        if not name or not name.strip():
            raise ValueError("标签名称不能为空")
        
        if len(name.strip()) > 50:
            raise ValueError("标签名称不能超过50个字符")
        
        self._name = name.strip()
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactTagNameUpdatedEvent(
            tag_id=self._id,
            user_id=self._user_id,
            old_name=self._name,
            new_name=name
        ))
    
    def update_color(self, color: str) -> None:
        """更新标签颜色"""
        if not self._is_valid_color(color):
            raise ValueError("无效的颜色格式")
        
        self._color = color
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactTagColorUpdatedEvent(
            tag_id=self._id,
            user_id=self._user_id,
            color=color
        ))
    
    def update_icon(self, icon: Optional[str]) -> None:
        """更新标签图标"""
        if icon and len(icon) > 50:
            raise ValueError("图标名称不能超过50个字符")
        
        self._icon = icon
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactTagIconUpdatedEvent(
            tag_id=self._id,
            user_id=self._user_id,
            icon=icon
        ))
    
    def update_description(self, description: Optional[str]) -> None:
        """更新标签描述"""
        if description and len(description) > 200:
            raise ValueError("标签描述不能超过200个字符")
        
        self._description = description
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactTagDescriptionUpdatedEvent(
            tag_id=self._id,
            user_id=self._user_id,
            description=description
        ))
    
    def update_category(self, category: TagCategory) -> None:
        """更新标签分类"""
        self._category = category
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactTagCategoryUpdatedEvent(
            tag_id=self._id,
            user_id=self._user_id,
            category=category.value
        ))
    
    def update_display_order(self, display_order: int) -> None:
        """更新显示顺序"""
        if display_order < 0:
            raise ValueError("显示顺序不能为负数")
        
        self._display_order = display_order
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactTagDisplayOrderUpdatedEvent(
            tag_id=self._id,
            user_id=self._user_id,
            display_order=display_order
        ))
    
    def toggle_visibility(self) -> None:
        """切换可见性"""
        self._is_visible = not self._is_visible
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactTagVisibilityToggledEvent(
            tag_id=self._id,
            user_id=self._user_id,
            is_visible=self._is_visible
        ))
    
    def increment_usage_count(self) -> None:
        """增加使用次数"""
        self._usage_count += 1
        self._updated_at = datetime.utcnow()
        
        # 发布领域事件
        self._add_domain_event(ContactTagUsageIncrementedEvent(
            tag_id=self._id,
            user_id=self._user_id,
            usage_count=self._usage_count
        ))
    
    def decrement_usage_count(self) -> None:
        """减少使用次数"""
        if self._usage_count > 0:
            self._usage_count -= 1
            self._updated_at = datetime.utcnow()
            
            # 发布领域事件
            self._add_domain_event(ContactTagUsageDecrementedEvent(
                tag_id=self._id,
                user_id=self._user_id,
                usage_count=self._usage_count
            ))
    
    # ============ 业务规则验证 ============
    
    def can_be_deleted(self) -> bool:
        """检查是否可以删除"""
        return not self._is_system_tag and self._usage_count == 0
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self._is_visible
    
    # ============ 工厂方法 ============
    
    @classmethod
    def create(
        cls,
        user_id: str,
        name: str,
        color: str = "#3B82F6",
        icon: Optional[str] = None,
        description: Optional[str] = None,
        category: TagCategory = TagCategory.CUSTOM,
        display_order: int = 0
    ) -> "ContactTag":
        """创建联系人标签"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        if not name or not name.strip():
            raise ValueError("标签名称不能为空")
        
        if len(name.strip()) > 50:
            raise ValueError("标签名称不能超过50个字符")
        
        if not cls._is_valid_color(color):
            raise ValueError("无效的颜色格式")
        
        # 生成ID（实际实现中应该使用UUID生成器）
        import uuid
        tag_id = str(uuid.uuid4())
        
        return cls(
            id=tag_id,
            user_id=user_id,
            name=name.strip(),
            color=color,
            icon=icon,
            description=description,
            category=category,
            display_order=display_order
        )
    
    @classmethod
    def create_system_tag(
        cls,
        user_id: str,
        name: str,
        color: str = "#3B82F6",
        category: TagCategory = TagCategory.CUSTOM
    ) -> "ContactTag":
        """创建系统标签"""
        tag = cls.create(user_id, name, color, category=category)
        tag._is_system_tag = True
        return tag
    
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
class ContactTagNameUpdatedEvent:
    tag_id: str
    user_id: str
    old_name: str
    new_name: str


@dataclass
class ContactTagColorUpdatedEvent:
    tag_id: str
    user_id: str
    color: str


@dataclass
class ContactTagIconUpdatedEvent:
    tag_id: str
    user_id: str
    icon: Optional[str]


@dataclass
class ContactTagDescriptionUpdatedEvent:
    tag_id: str
    user_id: str
    description: Optional[str]


@dataclass
class ContactTagCategoryUpdatedEvent:
    tag_id: str
    user_id: str
    category: str


@dataclass
class ContactTagDisplayOrderUpdatedEvent:
    tag_id: str
    user_id: str
    display_order: int


@dataclass
class ContactTagVisibilityToggledEvent:
    tag_id: str
    user_id: str
    is_visible: bool


@dataclass
class ContactTagUsageIncrementedEvent:
    tag_id: str
    user_id: str
    usage_count: int


@dataclass
class ContactTagUsageDecrementedEvent:
    tag_id: str
    user_id: str
    usage_count: int
