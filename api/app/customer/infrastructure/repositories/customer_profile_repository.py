"""
客户档案仓储实现
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.customer.domain.entities.customer import CustomerProfile
from app.customer.infrastructure.db.customer import CustomerProfile as CustomerProfileModel


class CustomerProfileRepository:
    """客户档案仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def save(self, profile: CustomerProfile) -> CustomerProfile:
        """保存客户档案"""
        # 检查是否已存在
        existing_profile = self.db.query(CustomerProfileModel).filter(
            CustomerProfileModel.customer_id == profile.customer_id
        ).first()
        
        if existing_profile:
            # 更新现有记录
            existing_profile.medical_history = profile.medical_history
            existing_profile.allergies = profile.allergies
            existing_profile.preferences = profile.preferences
            existing_profile.tags = profile.tags
            existing_profile.risk_notes = profile.risk_notes
            existing_profile.updated_at = profile.updated_at
            profile_to_save = existing_profile
        else:
            # 创建新记录
            profile_to_save = CustomerProfileModel(
                id=profile.id,
                customer_id=profile.customer_id,
                medical_history=profile.medical_history,
                allergies=profile.allergies,
                preferences=profile.preferences,
                tags=profile.tags,
                risk_notes=profile.risk_notes,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
            self.db.add(profile_to_save)
        
        self.db.commit()
        self.db.refresh(profile_to_save)
        
        return self._to_entity(profile_to_save)
    
    async def get_by_id(self, profile_id: str) -> Optional[CustomerProfile]:
        """根据ID获取客户档案"""
        profile_model = self.db.query(CustomerProfileModel).filter(
            CustomerProfileModel.id == profile_id
        ).first()
        
        if not profile_model:
            return None
        
        return self._to_entity(profile_model)
    
    async def get_by_customer_id(self, customer_id: str) -> Optional[CustomerProfile]:
        """根据客户ID获取档案"""
        profile_model = self.db.query(CustomerProfileModel).filter(
            CustomerProfileModel.customer_id == customer_id
        ).first()
        
        if not profile_model:
            return None
        
        return self._to_entity(profile_model)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[CustomerProfile]:
        """获取所有客户档案"""
        profiles = self.db.query(CustomerProfileModel).offset(skip).limit(limit).all()
        return [self._to_entity(profile) for profile in profiles]
    
    async def exists_by_customer_id(self, customer_id: str) -> bool:
        """检查客户ID是否存在档案记录"""
        return self.db.query(CustomerProfileModel).filter(
            CustomerProfileModel.customer_id == customer_id
        ).first() is not None
    
    async def delete_by_customer_id(self, customer_id: str) -> bool:
        """根据客户ID删除档案记录"""
        profile = self.db.query(CustomerProfileModel).filter(
            CustomerProfileModel.customer_id == customer_id
        ).first()
        
        if profile:
            self.db.delete(profile)
            self.db.commit()
            return True
        
        return False
    
    def _to_entity(self, model: CustomerProfileModel) -> CustomerProfile:
        """ORM模型转换为领域实体"""
        from app.customer.domain.entities.customer import CustomerProfile
        
        return CustomerProfile(
            id=model.id,
            customer_id=model.customer_id,
            medical_history=model.medical_history,
            allergies=model.allergies,
            preferences=model.preferences,
            tags=model.tags,
            risk_notes=model.risk_notes or [],
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, entity: CustomerProfile) -> CustomerProfileModel:
        """领域实体转换为ORM模型"""
        return CustomerProfileModel(
            id=entity.id,
            customer_id=entity.customer_id,
            medical_history=entity.medical_history,
            allergies=entity.allergies,
            preferences=entity.preferences,
            tags=entity.tags,
            risk_notes=entity.risk_notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
