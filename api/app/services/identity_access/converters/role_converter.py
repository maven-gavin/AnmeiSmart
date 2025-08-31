"""
角色数据转换器

负责角色领域对象与API Schema之间的转换。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from app.schemas.user import RoleResponse
from ..domain.entities.role import Role


class RoleConverter:
    """角色数据转换器"""
    
    @staticmethod
    def to_response(role: Role) -> RoleResponse:
        """转换角色实体为响应格式"""
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
    
    @staticmethod
    def to_list_response(roles: List[Role]) -> List[RoleResponse]:
        """转换角色列表为响应格式"""
        return [RoleConverter.to_response(role) for role in roles]
    
    @staticmethod
    def from_model(model) -> Role:
        """从ORM模型转换为领域实体"""
        role = Role(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
        
        return role
    
    @staticmethod
    def to_model_dict(role: Role) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        }
    
    @staticmethod
    def to_public_response(role: Role) -> Dict[str, Any]:
        """转换为公开响应格式"""
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": list(role.get_permissions()),
            "is_admin": role.is_admin_role(),
            "is_medical": role.is_medical_role()
        }
    
    @staticmethod
    def to_summary_response(role: Role) -> Dict[str, Any]:
        """转换为摘要响应格式"""
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description
        }
