"""
客户数据转换器
"""
from typing import List, Optional, Dict, Any

from app.customer.domain.entities.customer import CustomerEntity
from app.customer.schemas.customer import CustomerInfo, CustomerBase
from app.identity_access.infrastructure.db.user import User


class CustomerConverter:
    """客户数据转换器"""
    
    @staticmethod
    def to_response(customer: CustomerEntity, user: User) -> CustomerInfo:
        """转换客户实体为API响应格式"""
        return CustomerInfo(
            id=customer.id,
            user_id=customer.userId,
            username=user.username,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            medical_history=customer.medicalHistory,
            allergies=customer.allergies,
            preferences=customer.preferences,
            created_at=customer.createdAt,
            updated_at=customer.updatedAt
        )
    
    @staticmethod
    def to_list_response(customers: List[CustomerEntity], users: List[User]) -> List[CustomerInfo]:
        """转换客户列表为API响应格式"""
        # 创建用户ID到用户对象的映射
        user_map = {user.id: user for user in users}
        
        result = []
        for customer in customers:
            user = user_map.get(customer.userId)
            if user:
                result.append(CustomerConverter.to_response(customer, user))
        
        return result
    
    @staticmethod
    def from_create_request(request: CustomerBase, user_id: str) -> Dict[str, Any]:
        """从创建请求转换为领域对象参数"""
        return {
            "user_id": user_id,
            "medical_history": request.medical_history,
            "allergies": request.allergies,
            "preferences": request.preferences
        }
    
    @staticmethod
    def from_update_request(request: CustomerBase) -> Dict[str, Any]:
        """从更新请求转换为领域对象参数"""
        update_data = {}
        
        if request.medical_history is not None:
            update_data["medical_history"] = request.medical_history
        
        if request.allergies is not None:
            update_data["allergies"] = request.allergies
        
        if request.preferences is not None:
            update_data["preferences"] = request.preferences
        
        return update_data
    
    @staticmethod
    def from_model(model) -> CustomerEntity:
        """从ORM模型转换为领域实体"""
        from app.customer.domain.entities.customer import CustomerEntity
        
        return CustomerEntity(
            id=model.id,
            userId=model.user_id,
            medicalHistory=model.medical_history,
            allergies=model.allergies,
            preferences=model.preferences,
            createdAt=model.created_at,
            updatedAt=model.updated_at
        )
    
    @staticmethod
    def to_model_dict(customer: CustomerEntity) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": customer.id,
            "user_id": customer.userId,
            "medical_history": customer.medicalHistory,
            "allergies": customer.allergies,
            "preferences": customer.preferences,
            "created_at": customer.createdAt,
            "updated_at": customer.updatedAt
        }
    
    @staticmethod
    def to_customer_summary(customer: CustomerEntity, user: User, last_message: Optional[Dict] = None, unread_count: int = 0) -> Dict[str, Any]:
        """转换为客户摘要信息"""
        return {
            "id": customer.id,
            "name": user.username,
            "avatar": user.avatar or '/avatars/user.png',
            "is_online": getattr(user, 'is_online', False),
            "last_message": last_message,
            "unread_count": unread_count,
            "tags": getattr(customer, 'tags', []),
            "priority": getattr(customer, 'priority', 'medium'),
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
