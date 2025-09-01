"""
顾问实体
"""
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class Consultant:
    """顾问实体 - 管理顾问信息和能力"""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        name: str,
        specialization: str,
        experience_years: int,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._id = id
        self._user_id = user_id
        self._name = name
        self._specialization = specialization
        self._experience_years = experience_years
        self._is_active = is_active
        self._created_at = created_at
        self._updated_at = updated_at
        self._metadata = metadata or {}
    
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
    def specialization(self) -> str:
        return self._specialization
    
    @property
    def experience_years(self) -> int:
        return self._experience_years
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata.copy()
    
    def update_profile(
        self,
        name: Optional[str] = None,
        specialization: Optional[str] = None,
        experience_years: Optional[int] = None
    ) -> None:
        """更新顾问资料"""
        if name is not None:
            if not name.strip():
                raise ValueError("顾问姓名不能为空")
            self._name = name.strip()
        
        if specialization is not None:
            if not specialization.strip():
                raise ValueError("专业领域不能为空")
            self._specialization = specialization.strip()
        
        if experience_years is not None:
            if experience_years < 0:
                raise ValueError("工作经验年数不能为负数")
            self._experience_years = experience_years
        
        self._updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """激活顾问"""
        if self._is_active:
            raise ValueError("顾问已经是激活状态")
        
        self._is_active = True
        self._updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用顾问"""
        if not self._is_active:
            raise ValueError("顾问已经是停用状态")
        
        self._is_active = False
        self._updated_at = datetime.utcnow()
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新元数据"""
        self._metadata.update(metadata)
        self._updated_at = datetime.utcnow()
    
    def can_handle_consultation(self, consultation_type: str) -> bool:
        """检查是否可以处理特定类型的咨询"""
        if not self._is_active:
            return False
        
        # 检查专业领域是否匹配
        supported_types = self._metadata.get("supported_consultation_types", [])
        return consultation_type in supported_types
    
    @classmethod
    def create(
        cls,
        user_id: str,
        name: str,
        specialization: str,
        experience_years: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Consultant":
        """创建新的顾问"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        if not name or not name.strip():
            raise ValueError("顾问姓名不能为空")
        
        if not specialization or not specialization.strip():
            raise ValueError("专业领域不能为空")
        
        if experience_years < 0:
            raise ValueError("工作经验年数不能为负数")
        
        consultant_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        return cls(
            id=consultant_id,
            user_id=user_id,
            name=name.strip(),
            specialization=specialization.strip(),
            experience_years=experience_years,
            is_active=True,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Consultant):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)
