"""
用户数据转换器

负责用户领域对象与API Schema之间的转换。
"""

from typing import List, Optional, Dict, Any

from app.identity_access.schemas.user import UserCreate, UserUpdate, UserResponse
from ..domain.entities.user import UserEntity
from ..domain.value_objects.user_status import UserStatus
from app.identity_access.infrastructure.db.user import User as UserModel


from ..interfaces.converter_interfaces import IUserConverter

class UserConverter(IUserConverter):
    """用户数据转换器"""
    
    @staticmethod
    def to_response(user: UserEntity, active_role: Optional[str] = None) -> UserResponse:
        """转换用户实体为响应格式"""
        # 如果没有提供active_role，使用用户的第一个角色作为默认角色
        if active_role is None and user.roles:
            # 确保与UserResponse.from_model的逻辑一致
            first_role = list(user.roles)[0]
            if hasattr(first_role, 'name'):
                active_role = first_role.name
            else:
                active_role = str(first_role)
        
        # 处理角色，确保与UserResponse.from_model的逻辑一致
        roles_list = []
        if user.roles:
            for role in user.roles:
                if hasattr(role, 'name'):
                    roles_list.append(role.name)
                else:
                    roles_list.append(str(role))
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.get_email_value(),
            phone=user.phone,
            avatar=user.avatar,
            is_active=user.status.to_bool(),
            roles=roles_list,
            active_role=active_role,
            created_at=user.createdAt,
            updated_at=user.updatedAt,
            last_login_at=user.lastLoginAt,
            extended_info=None  # 暂时设为None，避免前向引用问题
        )
    
    @staticmethod
    def to_list_response(users: List[UserEntity]) -> List[UserResponse]:
        """转换用户列表为响应格式"""
        return [UserConverter.to_response(user) for user in users]
    
    @staticmethod
    def from_create_request(request: UserCreate) -> Dict[str, Any]:
        """从创建请求转换为领域对象参数"""
        return {
            "username": request.username,
            "email": request.email,
            "password": request.password,
            "phone": request.phone,
            "avatar": request.avatar,
            "roles": request.roles
        }
    
    @staticmethod
    def from_update_request(request: UserUpdate) -> Dict[str, Any]:
        """从更新请求转换为领域对象参数"""
        updates = {}
        if request.username is not None:
            updates["username"] = request.username
        if request.phone is not None:
            updates["phone"] = request.phone
        if request.avatar is not None:
            updates["avatar"] = request.avatar
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        return updates
    
    @staticmethod
    def from_model(model: UserModel) -> UserEntity:
        """从ORM模型转换为领域实体"""
        from ..domain.value_objects.email import Email
        from ..domain.value_objects.password import Password
        
        # 创建值对象
        email = Email(model.email)
        password = Password.from_hash(model.hashed_password)
        
        # 处理角色
        roles = set()
        if hasattr(model, 'roles') and model.roles:
            for role in model.roles:
                if hasattr(role, 'name'):
                    roles.add(role.name)
                else:
                    roles.add(role)
        
        # 创建用户实体
        user = UserEntity(
            id=model.id,
            username=model.username,
            email=email,
            password=password,
            phone=model.phone,
            avatar=model.avatar,
            status=UserStatus.from_bool(model.is_active),
            createdAt=model.created_at,
            updatedAt=model.updated_at,
            lastLoginAt=getattr(model, 'last_login_at', None),
            roles=roles,
            tenantId=model.tenant_id
        )
        
        return user
    
    @staticmethod
    def to_model_dict(user: UserEntity) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.get_email_value(),
            "hashed_password": user.get_password_hash(),
            "phone": user.phone,
            "avatar": user.avatar,
            "is_active": user.status.to_bool(),
            "created_at": user.createdAt,
            "updated_at": user.updatedAt,
            "last_login_at": user.lastLoginAt,
            "tenant_id": user.tenantId
        }
    
    @staticmethod
    def to_public_response(user: UserEntity) -> Dict[str, Any]:
        """转换为公开响应格式（不包含敏感信息）"""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.get_email_value(),
            "avatar": user.avatar,
            "is_active": user.status.to_bool(),
            "roles": list(user.roles),
            "created_at": user.createdAt.isoformat(),
            "last_login_at": user.lastLoginAt.isoformat() if user.lastLoginAt else None
        }
    
    @staticmethod
    def to_summary_response(user: UserEntity) -> Dict[str, Any]:
        """转换为摘要响应格式"""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.get_email_value(),
            "avatar": user.avatar,
            "primary_role": user.get_primary_role(),
            "is_active": user.status.to_bool()
        }
