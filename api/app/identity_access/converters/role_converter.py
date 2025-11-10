"""
角色数据转换器

负责角色领域对象与API Schema之间的转换。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from app.identity_access.schemas.user import RoleResponse
from ..domain.entities.role import RoleEntity


from ..interfaces.converter_interfaces import IRoleConverter

class RoleConverter(IRoleConverter):
    """角色数据转换器"""
    
    @staticmethod
    def to_response(role: RoleEntity) -> RoleResponse:
        """转换角色实体为响应格式"""
        return RoleResponse(
            id=role.id,
            name=role.name,
            display_name=role.displayName,
            description=role.description,
            is_active=role.isActive,
            is_system=role.isSystem,
            is_admin=role.isAdmin,
            priority=role.priority,
            tenant_id=role.tenantId,
            created_at=role.createdAt,
            updated_at=role.updatedAt
        )
    
    @staticmethod
    def to_list_response(roles: List[RoleEntity]) -> List[RoleResponse]:
        """转换角色列表为响应格式"""
        return [RoleConverter.to_response(role) for role in roles]
    
    @staticmethod
    def from_model(model) -> RoleEntity:
        """从ORM模型转换为领域实体"""
        roleEntity = RoleEntity(
            id=model.id,
            name=model.name,
            displayName=model.display_name,
            description=model.description,
            isActive=model.is_active,
            isSystem=model.is_system,
            isAdmin=model.is_admin,
            priority=model.priority,
            tenantId=model.tenant_id,
            createdAt=model.created_at,
            updatedAt=model.updated_at
        )
        
        return roleEntity
    
    @staticmethod
    def to_model_dict(role: RoleEntity) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": role.id,
            "name": role.name,
            "display_name": role.displayName,
            "description": role.description,
            "is_active": role.isActive,
            "is_system": role.isSystem,
            "is_admin": role.isAdmin,
            "priority": role.priority,
            "tenant_id": role.tenantId,
            "created_at": role.createdAt,
            "updated_at": role.updatedAt
        }
    
    @staticmethod
    def to_public_response(role: RoleEntity) -> Dict[str, Any]:
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
    def to_summary_response(role: RoleEntity) -> Dict[str, Any]:
        """转换为摘要响应格式"""
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description
        }
