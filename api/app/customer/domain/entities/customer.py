"""
客户聚合根实体
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.common.domain.entities.base_entity import BaseEntity
from app.customer.domain.value_objects.customer_status import CustomerPriority


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


@dataclass(kw_only=True)
class CustomerEntity(BaseEntity):
    """客户聚合根 - 管理客户的核心业务逻辑"""

    id: str
    userId: str
    medicalHistory: Optional[str] = None
    allergies: Optional[str] = None
    preferences: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    priority: CustomerPriority = CustomerPriority.MEDIUM
    tags: List[str] = field(default_factory=list)
    createdAt: datetime = field(default_factory=datetime.now)
    updatedAt: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        super().__init__(self.id)
        self._normalize()
        self.validate()

    def _normalize(self) -> None:
        self.medicalHistory = _normalize_text(self.medicalHistory)
        self.allergies = _normalize_text(self.allergies)
        self.preferences = _normalize_text(self.preferences)
        self.gender = _normalize_text(self.gender)
        self.tags = [tag.strip() for tag in self.tags if tag and tag.strip()]

    def updateMedicalHistory(self, medicalHistory: Optional[str]) -> None:
        if medicalHistory and len(medicalHistory.strip()) > 1000:
            raise ValueError("病史信息过长，不能超过1000字符")
        self.medicalHistory = _normalize_text(medicalHistory)
        self.updatedAt = datetime.now()

    def updateAllergies(self, allergies: Optional[str]) -> None:
        if allergies and len(allergies.strip()) > 500:
            raise ValueError("过敏史信息过长，不能超过500字符")
        self.allergies = _normalize_text(allergies)
        self.updatedAt = datetime.now()

    def updatePreferences(self, preferences: Optional[str]) -> None:
        if preferences and len(preferences.strip()) > 500:
            raise ValueError("偏好信息过长，不能超过500字符")
        self.preferences = _normalize_text(preferences)
        self.updatedAt = datetime.now()

    def updateDemographics(self, age: Optional[int] = None, gender: Optional[str] = None) -> None:
        if age is not None:
            if age < 0 or age > 150:
                raise ValueError("年龄必须在0-150之间")
            self.age = age

        if gender is not None:
            normalized_gender = _normalize_text(gender)
            if normalized_gender and normalized_gender not in ["male", "female", "other"]:
                raise ValueError("性别值无效")
            self.gender = normalized_gender

        self.updatedAt = datetime.now()

    def setPriority(self, priority: CustomerPriority) -> None:
        self.priority = priority
        self.updatedAt = datetime.now()

    def addTag(self, tag: str) -> None:
        if not tag or not tag.strip():
            raise ValueError("标签不能为空")
        normalized = tag.strip()
        if normalized not in self.tags:
            self.tags.append(normalized)
            self.updatedAt = datetime.now()

    def removeTag(self, tag: str) -> None:
        if tag in self.tags:
            self.tags.remove(tag)
            self.updatedAt = datetime.now()

    def hasMedicalCondition(self) -> bool:
        return bool(self.medicalHistory)

    def hasAllergies(self) -> bool:
        return bool(self.allergies)

    def validate(self) -> None:
        if not self.userId:
            raise ValueError("用户ID不能为空")
        if self.age is not None and (self.age < 0 or self.age > 150):
            raise ValueError("年龄必须在0-150之间")
        if self.gender and self.gender not in ["male", "female", "other"]:
            raise ValueError("性别值无效")

    @classmethod
    def create(
        cls,
        userId: str,
        medicalHistory: Optional[str] = None,
        allergies: Optional[str] = None,
        preferences: Optional[str] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        priority: CustomerPriority = CustomerPriority.MEDIUM,
        tags: Optional[List[str]] = None,
    ) -> "CustomerEntity":
        from app.common.infrastructure.db.uuid_utils import customer_id

        return cls(
            id=customer_id(),
            userId=userId,
            medicalHistory=medicalHistory,
            allergies=allergies,
            preferences=preferences,
            age=age,
            gender=gender,
            priority=priority,
            tags=tags or [],
        )

    def __str__(self) -> str:
        return (
            f"CustomerEntity(id={self.id}, userId={self.userId}, priority={self.priority}, "
            f"age={self.age}, gender={self.gender}, tags={self.tags})"
        )

    def __repr__(self) -> str:
        return (
            f"CustomerEntity(id={self.id}, userId={self.userId}, medicalHistory={self.medicalHistory}, "
            f"allergies={self.allergies}, preferences={self.preferences}, age={self.age}, gender={self.gender}, "
            f"priority={self.priority}, tags={self.tags}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )


@dataclass(kw_only=True)
class CustomerProfileEntity(BaseEntity):
    """客户档案实体 - 扩展客户信息"""

    id: str
    customerId: str
    medicalHistory: Optional[str] = None
    allergies: Optional[str] = None
    preferences: Optional[str] = None
    tags: Optional[str] = None
    riskNotes: List[Dict[str, Any]] = field(default_factory=list)
    createdAt: datetime = field(default_factory=datetime.now)
    updatedAt: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        super().__init__(self.id)
        self._normalize()
        self.validate()

    def _normalize(self) -> None:
        self.medicalHistory = _normalize_text(self.medicalHistory)
        self.allergies = _normalize_text(self.allergies)
        self.preferences = _normalize_text(self.preferences)
        self.tags = _normalize_text(self.tags)

    def updateMedicalHistory(self, medicalHistory: Optional[str]) -> None:
        if medicalHistory and len(medicalHistory.strip()) > 1000:
            raise ValueError("病史信息过长，不能超过1000字符")
        self.medicalHistory = _normalize_text(medicalHistory)
        self.updatedAt = datetime.now()

    def updateAllergies(self, allergies: Optional[str]) -> None:
        if allergies and len(allergies.strip()) > 500:
            raise ValueError("过敏史信息过长，不能超过500字符")
        self.allergies = _normalize_text(allergies)
        self.updatedAt = datetime.now()

    def updatePreferences(self, preferences: Optional[str]) -> None:
        if preferences and len(preferences.strip()) > 500:
            raise ValueError("偏好信息过长，不能超过500字符")
        self.preferences = _normalize_text(preferences)
        self.updatedAt = datetime.now()

    def updateTags(self, tags: Optional[str]) -> None:
        if tags and len(tags.strip()) > 200:
            raise ValueError("标签信息过长，不能超过200字符")
        self.tags = _normalize_text(tags)
        self.updatedAt = datetime.now()

    def addRiskNote(self, riskNote: Dict[str, Any]) -> None:
        required_fields = ["type", "description", "level"]
        for field in required_fields:
            if field not in riskNote:
                raise ValueError(f"风险提示缺少必要字段: {field}")
        if riskNote["level"] not in ["high", "medium", "low"]:
            raise ValueError("风险级别必须是 high、medium 或 low")
        self.riskNotes.append(riskNote)
        self.updatedAt = datetime.now()

    def removeRiskNote(self, noteIndex: int) -> None:
        if 0 <= noteIndex < len(self.riskNotes):
            self.riskNotes.pop(noteIndex)
            self.updatedAt = datetime.now()

    def getTagsList(self) -> List[str]:
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    def validate(self) -> None:
        if not self.customerId:
            raise ValueError("客户ID不能为空")

    @classmethod
    def create(
        cls,
        customerId: str,
        medicalHistory: Optional[str] = None,
        allergies: Optional[str] = None,
        preferences: Optional[str] = None,
        tags: Optional[str] = None,
        riskNotes: Optional[List[Dict[str, Any]]] = None,
    ) -> "CustomerProfileEntity":
        from app.common.infrastructure.db.uuid_utils import profile_id

        return cls(
            id=profile_id(),
            customerId=customerId,
            medicalHistory=medicalHistory,
            allergies=allergies,
            preferences=preferences,
            tags=tags,
            riskNotes=riskNotes or [],
        )

    def __str__(self) -> str:
        return (
            f"CustomerProfileEntity(id={self.id}, customerId={self.customerId}, "
            f"medicalHistory={self.medicalHistory}, allergies={self.allergies})"
        )

    def __repr__(self) -> str:
        return (
            f"CustomerProfileEntity(id={self.id}, customerId={self.customerId}, medicalHistory={self.medicalHistory}, "
            f"allergies={self.allergies}, preferences={self.preferences}, tags={self.tags}, "
            f"riskNotes={self.riskNotes}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )

