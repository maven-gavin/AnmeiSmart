"""
客户聚合根实体
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from app.common.domain.entities.base_entity import BaseEntity
from app.customer.domain.value_objects.customer_status import CustomerStatus, CustomerPriority


@dataclass
class Customer(BaseEntity):
    """客户聚合根 - 管理客户的核心业务逻辑"""
    
    user_id: str
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    preferences: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    priority: CustomerPriority = CustomerPriority.MEDIUM
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.user_id:
            raise ValueError("用户ID不能为空")
        
        if self.age is not None and (self.age < 0 or self.age > 150):
            raise ValueError("年龄必须在0-150之间")
        
        if self.gender and self.gender not in ['male', 'female', 'other']:
            raise ValueError("性别值无效")
    
    def update_medical_history(self, medical_history: str) -> None:
        """更新病史信息"""
        if medical_history and len(medical_history.strip()) > 1000:
            raise ValueError("病史信息过长，不能超过1000字符")
        
        self.medical_history = medical_history.strip() if medical_history else None
        self.updated_at = datetime.now()
    
    def update_allergies(self, allergies: str) -> None:
        """更新过敏史信息"""
        if allergies and len(allergies.strip()) > 500:
            raise ValueError("过敏史信息过长，不能超过500字符")
        
        self.allergies = allergies.strip() if allergies else None
        self.updated_at = datetime.now()
    
    def update_preferences(self, preferences: str) -> None:
        """更新偏好信息"""
        if preferences and len(preferences.strip()) > 500:
            raise ValueError("偏好信息过长，不能超过500字符")
        
        self.preferences = preferences.strip() if preferences else None
        self.updated_at = datetime.now()
    
    def update_demographics(self, age: Optional[int] = None, gender: Optional[str] = None) -> None:
        """更新人口统计学信息"""
        if age is not None:
            if age < 0 or age > 150:
                raise ValueError("年龄必须在0-150之间")
            self.age = age
        
        if gender is not None:
            if gender not in ['male', 'female', 'other']:
                raise ValueError("性别值无效")
            self.gender = gender
        
        self.updated_at = datetime.now()
    
    def set_priority(self, priority: CustomerPriority) -> None:
        """设置客户优先级"""
        self.priority = priority
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """添加客户标签"""
        if not tag or not tag.strip():
            raise ValueError("标签不能为空")
        
        if tag.strip() not in self.tags:
            self.tags.append(tag.strip())
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """移除客户标签"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def has_medical_condition(self) -> bool:
        """检查是否有病史"""
        return bool(self.medical_history and self.medical_history.strip())
    
    def has_allergies(self) -> bool:
        """检查是否有过敏史"""
        return bool(self.allergies and self.allergies.strip())
    
    def validate(self) -> None:
        """验证实体状态"""
        if not self.user_id:
            raise ValueError("用户ID不能为空")
        
        if self.age is not None and (self.age < 0 or self.age > 150):
            raise ValueError("年龄必须在0-150之间")
        
        if self.gender and self.gender not in ['male', 'female', 'other']:
            raise ValueError("性别值无效")
    
    @classmethod
    def create(
        cls,
        user_id: str,
        medical_history: Optional[str] = None,
        allergies: Optional[str] = None,
        preferences: Optional[str] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None
    ) -> "Customer":
        """创建客户聚合根"""
        from app.common.infrastructure.db.uuid_utils import customer_id
        
        customer = cls(
            id=customer_id(),
            user_id=user_id,
            medical_history=medical_history,
            allergies=allergies,
            preferences=preferences,
            age=age,
            gender=gender
        )
        
        customer.validate()
        return customer


@dataclass
class CustomerProfile(BaseEntity):
    """客户档案实体 - 扩展客户信息"""
    
    customer_id: str
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    preferences: Optional[str] = None
    tags: Optional[str] = None
    risk_notes: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.customer_id:
            raise ValueError("客户ID不能为空")
    
    def update_medical_history(self, medical_history: str) -> None:
        """更新病史信息"""
        if medical_history and len(medical_history.strip()) > 1000:
            raise ValueError("病史信息过长，不能超过1000字符")
        
        self.medical_history = medical_history.strip() if medical_history else None
        self.updated_at = datetime.now()
    
    def update_allergies(self, allergies: str) -> None:
        """更新过敏史信息"""
        if allergies and len(allergies.strip()) > 500:
            raise ValueError("过敏史信息过长，不能超过500字符")
        
        self.allergies = allergies.strip() if allergies else None
        self.updated_at = datetime.now()
    
    def update_preferences(self, preferences: str) -> None:
        """更新偏好信息"""
        if preferences and len(preferences.strip()) > 500:
            raise ValueError("偏好信息过长，不能超过500字符")
        
        self.preferences = preferences.strip() if preferences else None
        self.updated_at = datetime.now()
    
    def update_tags(self, tags: str) -> None:
        """更新标签信息"""
        if tags and len(tags.strip()) > 200:
            raise ValueError("标签信息过长，不能超过200字符")
        
        self.tags = tags.strip() if tags else None
        self.updated_at = datetime.now()
    
    def add_risk_note(self, risk_note: Dict[str, Any]) -> None:
        """添加风险提示"""
        required_fields = ['type', 'description', 'level']
        for field in required_fields:
            if field not in risk_note:
                raise ValueError(f"风险提示缺少必要字段: {field}")
        
        if risk_note['level'] not in ['high', 'medium', 'low']:
            raise ValueError("风险级别必须是 high、medium 或 low")
        
        self.risk_notes.append(risk_note)
        self.updated_at = datetime.now()
    
    def remove_risk_note(self, note_index: int) -> None:
        """移除风险提示"""
        if 0 <= note_index < len(self.risk_notes):
            self.risk_notes.pop(note_index)
            self.updated_at = datetime.now()
    
    def get_tags_list(self) -> List[str]:
        """获取标签列表"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def validate(self) -> None:
        """验证实体状态"""
        if not self.customer_id:
            raise ValueError("客户ID不能为空")
    
    @classmethod
    def create(
        cls,
        customer_id: str,
        medical_history: Optional[str] = None,
        allergies: Optional[str] = None,
        preferences: Optional[str] = None,
        tags: Optional[str] = None
    ) -> "CustomerProfile":
        """创建客户档案"""
        from app.common.infrastructure.db.uuid_utils import profile_id
        
        profile = cls(
            id=profile_id(),
            customer_id=customer_id,
            medical_history=medical_history,
            allergies=allergies,
            preferences=preferences,
            tags=tags
        )
        
        profile.validate()
        return profile

