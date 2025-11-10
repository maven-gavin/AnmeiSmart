"""
联系人标签实体
Contact领域的标签管理实体
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid


class TagCategory(Enum):
    """标签分类值对象"""
    WORK = "work"
    PERSONAL = "personal"
    BUSINESS = "business"
    MEDICAL = "medical"
    CUSTOM = "custom"


@dataclass
class ContactTagEntity:
    """联系人标签实体"""
    
    id: str
    userId: str
    name: str
    color: str = "#3B82F6"
    icon: Optional[str] = None
    description: Optional[str] = None
    category: TagCategory = TagCategory.CUSTOM
    displayOrder: int = 0
    isVisible: bool = True
    isSystemTag: bool = False
    usageCount: int = 0
    createdAt: datetime = field(default_factory=datetime.utcnow)
    updatedAt: datetime = field(default_factory=datetime.utcnow)
    _domainEvents: List[object] = field(default_factory=list, repr=False)
    
    def __post_init__(self) -> None:
        if not self.userId:
            raise ValueError("用户ID不能为空")
        
        if not self.name or not self.name.strip():
            raise ValueError("标签名称不能为空")
        if len(self.name.strip()) > 50:
            raise ValueError("标签名称不能超过50个字符")
        self.name = self.name.strip()
        
        if not self._isValidColor(self.color):
            raise ValueError("无效的颜色格式")
        
        if self.icon and len(self.icon) > 50:
            raise ValueError("图标名称不能超过50个字符")
        
        if self.description and len(self.description) > 200:
            raise ValueError("标签描述不能超过200个字符")
        
        if self.displayOrder < 0:
            raise ValueError("显示顺序不能为负数")
        
        if self.usageCount < 0:
            raise ValueError("使用次数不能为负数")
        
        self.createdAt = self.createdAt or datetime.utcnow()
        self.updatedAt = self.updatedAt or datetime.utcnow()
        self._domainEvents = list(self._domainEvents or [])
    
    @property
    def domainEvents(self) -> List[object]:
        return list(self._domainEvents)
    
    def updateName(self, name: str) -> None:
        """更新标签名称"""
        if not name or not name.strip():
            raise ValueError("标签名称不能为空")
        
        if len(name.strip()) > 50:
            raise ValueError("标签名称不能超过50个字符")
        
        old_name = self.name
        self.name = name.strip()
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent(ContactTagNameUpdatedEvent(
            tagId=self.id,
            userId=self.userId,
            oldName=old_name,
            newName=self.name
        ))
    
    def updateColor(self, color: str) -> None:
        """更新标签颜色"""
        if not self._isValidColor(color):
            raise ValueError("无效的颜色格式")
        
        self.color = color
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent(ContactTagColorUpdatedEvent(
            tagId=self.id,
            userId=self.userId,
            color=color
        ))
    
    def updateIcon(self, icon: Optional[str]) -> None:
        """更新标签图标"""
        if icon and len(icon) > 50:
            raise ValueError("图标名称不能超过50个字符")
        
        self.icon = icon
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent(ContactTagIconUpdatedEvent(
            tagId=self.id,
            userId=self.userId,
            icon=icon
        ))
    
    def updateDescription(self, description: Optional[str]) -> None:
        """更新标签描述"""
        if description and len(description) > 200:
            raise ValueError("标签描述不能超过200个字符")
        
        self.description = description
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent(ContactTagDescriptionUpdatedEvent(
            tagId=self.id,
            userId=self.userId,
            description=description
        ))
    
    def updateCategory(self, category: TagCategory) -> None:
        """更新标签分类"""
        self.category = category
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent(ContactTagCategoryUpdatedEvent(
            tagId=self.id,
            userId=self.userId,
            category=category.value
        ))
    
    def updateDisplayOrder(self, displayOrder: int) -> None:
        """更新显示顺序"""
        if displayOrder < 0:
            raise ValueError("显示顺序不能为负数")
        
        self.displayOrder = displayOrder
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent(ContactTagDisplayOrderUpdatedEvent(
            tagId=self.id,
            userId=self.userId,
            displayOrder=displayOrder
        ))
    
    def toggleVisibility(self) -> None:
        """切换可见性"""
        self.isVisible = not self.isVisible
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent(ContactTagVisibilityToggledEvent(
            tagId=self.id,
            userId=self.userId,
            isVisible=self.isVisible
        ))
    
    def incrementUsageCount(self) -> None:
        """增加使用次数"""
        self.usageCount += 1
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent(ContactTagUsageIncrementedEvent(
            tagId=self.id,
            userId=self.userId,
            usageCount=self.usageCount
        ))
    
    def decrementUsageCount(self) -> None:
        """减少使用次数"""
        if self.usageCount > 0:
            self.usageCount -= 1
            self.updatedAt = datetime.utcnow()
            
            self._addDomainEvent(ContactTagUsageDecrementedEvent(
                tagId=self.id,
                userId=self.userId,
                usageCount=self.usageCount
            ))
    
    def canBeDeleted(self) -> bool:
        """检查是否可以删除"""
        return not self.isSystemTag and self.usageCount == 0
    
    def isAvailable(self) -> bool:
        """检查是否可用"""
        return self.isVisible
    
    @classmethod
    def create(
        cls,
        userId: str,
        name: str,
        color: str = "#3B82F6",
        icon: Optional[str] = None,
        description: Optional[str] = None,
        category: TagCategory = TagCategory.CUSTOM,
        displayOrder: int = 0
    ) -> "ContactTagEntity":
        """创建联系人标签"""
        tag_id = str(uuid.uuid4())
        
        return cls(
            id=tag_id,
            userId=userId,
            name=name,
            color=color,
            icon=icon,
            description=description,
            category=category,
            displayOrder=displayOrder
        )
    
    @classmethod
    def createSystemTag(
        cls,
        userId: str,
        name: str,
        color: str = "#3B82F6",
        category: TagCategory = TagCategory.CUSTOM
    ) -> "ContactTagEntity":
        """创建系统标签"""
        tag = cls.create(userId, name, color, category=category)
        tag.isSystemTag = True
        return tag
    
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
            f"ContactTagEntity(id={self.id}, userId={self.userId}, name={self.name}, "
            f"category={self.category}, isVisible={self.isVisible}, isSystemTag={self.isSystemTag}, "
            f"usageCount={self.usageCount}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
    
    def __repr__(self) -> str:
        return (
            f"ContactTagEntity(id={self.id}, userId={self.userId}, name={self.name}, color={self.color}, "
            f"icon={self.icon}, description={self.description}, category={self.category}, "
            f"displayOrder={self.displayOrder}, isVisible={self.isVisible}, isSystemTag={self.isSystemTag}, "
            f"usageCount={self.usageCount}, domainEvents={self.domainEvents}, "
            f"createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )


@dataclass
class ContactTagNameUpdatedEvent:
    tagId: str
    userId: str
    oldName: str
    newName: str


@dataclass
class ContactTagColorUpdatedEvent:
    tagId: str
    userId: str
    color: str


@dataclass
class ContactTagIconUpdatedEvent:
    tagId: str
    userId: str
    icon: Optional[str]


@dataclass
class ContactTagDescriptionUpdatedEvent:
    tagId: str
    userId: str
    description: Optional[str]


@dataclass
class ContactTagCategoryUpdatedEvent:
    tagId: str
    userId: str
    category: str


@dataclass
class ContactTagDisplayOrderUpdatedEvent:
    tagId: str
    userId: str
    displayOrder: int


@dataclass
class ContactTagVisibilityToggledEvent:
    tagId: str
    userId: str
    isVisible: bool


@dataclass
class ContactTagUsageIncrementedEvent:
    tagId: str
    userId: str
    usageCount: int


@dataclass
class ContactTagUsageDecrementedEvent:
    tagId: str
    userId: str
    usageCount: int
