"""
客户档案数据转换器
"""
from typing import List, Optional, Dict, Any

from app.customer.domain.entities.customer import CustomerProfileEntity
from app.customer.schemas.customer import CustomerProfileInfo, CustomerProfileCreate, CustomerProfileUpdate
from app.identity_access.infrastructure.db.user import User


class CustomerProfileConverter:
    """客户档案数据转换器"""
    
    @staticmethod
    def to_response(profile: CustomerProfileEntity, user: User) -> CustomerProfileInfo:
        """转换客户档案实体为API响应格式"""
        from app.customer.schemas.customer import CustomerBasicInfo
        
        return CustomerProfileInfo(
            id=profile.id,
            basicInfo=CustomerBasicInfo(
                name=user.username,
                phone=user.phone
            ),
            medical_history=profile.medicalHistory,
            allergies=profile.allergies,
            preferences=profile.preferences,
            tags=profile.getTagsList(),
            riskNotes=profile.riskNotes,
            created_at=profile.createdAt,
            updated_at=profile.updatedAt
        )
    
    @staticmethod
    def to_list_response(profiles: List[CustomerProfileEntity], users: List[User]) -> List[CustomerProfileInfo]:
        """转换客户档案列表为API响应格式"""
        # 创建用户ID到用户对象的映射
        user_map = {user.id: user for user in users}
        
        result = []
        for profile in profiles:
            user = user_map.get(profile.customerId)
            if user:
                result.append(CustomerProfileConverter.to_response(profile, user))
        
        return result
    
    @staticmethod
    def from_create_request(request: CustomerProfileCreate, customer_id: str) -> Dict[str, Any]:
        """从创建请求转换为领域对象参数"""
        return {
            "customer_id": customer_id,
            "medical_history": request.medical_history,
            "allergies": request.allergies,
            "preferences": request.preferences,
            "tags": request.tags
        }
    
    @staticmethod
    def from_update_request(request: CustomerProfileUpdate) -> Dict[str, Any]:
        """从更新请求转换为领域对象参数"""
        update_data = {}
        
        if request.medical_history is not None:
            update_data["medical_history"] = request.medical_history
        
        if request.allergies is not None:
            update_data["allergies"] = request.allergies
        
        if request.preferences is not None:
            update_data["preferences"] = request.preferences
        
        if request.tags is not None:
            update_data["tags"] = request.tags
        
        if request.risk_notes is not None:
            update_data["risk_notes"] = [note.model_dump() for note in request.risk_notes]
        
        return update_data
    
    @staticmethod
    def from_model(model) -> CustomerProfileEntity:
        """从ORM模型转换为领域实体"""
        from app.customer.domain.entities.customer import CustomerProfileEntity
        
        return CustomerProfileEntity(
            id=model.id,
            customerId=model.customer_id,
            medicalHistory=model.medical_history,
            allergies=model.allergies,
            preferences=model.preferences,
            tags=model.tags,
            riskNotes=model.risk_notes or [],
            createdAt=model.created_at,
            updatedAt=model.updated_at
        )
    
    @staticmethod
    def to_model_dict(profile: CustomerProfileEntity) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": profile.id,
            "customer_id": profile.customerId,
            "medical_history": profile.medicalHistory,
            "allergies": profile.allergies,
            "preferences": profile.preferences,
            "tags": profile.tags,
            "risk_notes": profile.riskNotes,
            "created_at": profile.createdAt,
            "updated_at": profile.updatedAt
        }
    
    @staticmethod
    def format_tags_for_storage(tags: List[str]) -> Optional[str]:
        """将标签列表格式化为存储字符串"""
        if not tags:
            return None
        
        # 过滤空标签并去重
        valid_tags = list(set(tag.strip() for tag in tags if tag and tag.strip()))
        valid_tags.sort()
        
        return ','.join(valid_tags)
    
    @staticmethod
    def parse_tags_from_storage(tags_string: Optional[str]) -> List[str]:
        """从存储字符串解析标签列表"""
        if not tags_string:
            return []
        
        tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
        return list(set(tags))  # 去重
