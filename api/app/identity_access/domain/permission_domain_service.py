"""
权限领域服务

处理用户权限验证和角色管理相关的业务逻辑。
支持新的数据库配置权限系统，同时保持向后兼容。
"""

from typing import List, Set, Optional
from datetime import datetime
import logging

from .entities.user import User
from .value_objects.role_type import RoleType

logger = logging.getLogger(__name__)


class PermissionDomainService:
    """权限领域服务"""
    
    def __init__(self, user_repository, role_permission_service=None):
        self.user_repository = user_repository
        self.role_permission_service = role_permission_service
    
    async def check_user_permission(
        self,
        user_id: str,
        permission: str
    ) -> bool:
        """检查用户权限"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # 检查用户状态
        if not user.can_access_system():
            return False
        
        # 优先使用新的权限服务
        if self.role_permission_service:
            return await self.role_permission_service.check_user_permission(user_id, permission)
        
        # 回退到传统权限检查
        user_permissions = await self._get_user_permissions(user)
        return permission in user_permissions
    
    async def check_user_role(self, user_id: str, role_name: str) -> bool:
        """检查用户角色"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # 优先使用新的权限服务
        if self.role_permission_service:
            return await self.role_permission_service.check_user_role(user_id, role_name)
        
        # 回退到传统角色检查
        return user.has_role(role_name)
    
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限列表"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return []
        
        # 优先使用新的权限服务
        if self.role_permission_service:
            permissions = await self.role_permission_service.get_user_permissions(user_id)
            return list(permissions)
        
        # 回退到传统权限获取
        user_permissions = await self._get_user_permissions(user)
        return list(user_permissions)
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """获取用户角色列表"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return []
        
        # 优先使用新的权限服务
        if self.role_permission_service:
            return await self.role_permission_service.get_user_roles(user_id)
        
        # 回退到传统角色获取
        return list(user.roles)
    
    async def switch_user_role(
        self,
        user_id: str,
        target_role: str
    ) -> bool:
        """切换用户角色"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # 检查用户是否有目标角色
        if not user.has_role(target_role):
            return False
        
        # 这里可以实现角色切换逻辑
        # 比如更新用户的当前活跃角色
        return True
    
    async def validate_admin_permission(self, user_id: str) -> bool:
        """验证管理员权限"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        return user.is_admin()
    
    async def can_manage_users(self, user_id: str) -> bool:
        """检查是否可以管理用户"""
        return await self.check_user_permission(user_id, "user:create") or \
               await self.check_user_permission(user_id, "user:delete")
    
    async def can_access_admin_panel(self, user_id: str) -> bool:
        """检查是否可以访问管理面板"""
        return await self.check_user_permission(user_id, "system:admin")
    
    async def can_manage_roles(self, user_id: str) -> bool:
        """检查是否可以管理角色"""
        return await self.check_user_permission(user_id, "role:manage")
    
    async def can_delete_data(self, user_id: str) -> bool:
        """检查是否可以删除数据"""
        return await self.check_user_permission(user_id, "user:delete") or \
               await self.check_user_permission(user_id, "conversation:delete") or \
               await self.check_user_permission(user_id, "message:delete")
    
    async def _get_user_permissions(self, user: User) -> Set[str]:
        """获取用户所有权限"""
        permissions = set()
        
        for role_name in user.roles:
            try:
                role_type = RoleType(role_name)
                role_permissions = role_type.get_permissions()
                permissions.update(role_permissions)
            except ValueError:
                # 忽略无效角色
                continue
        
        return permissions
    
    async def get_user_primary_role(self, user_id: str) -> str:
        """获取用户主要角色"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return RoleType.CUSTOMER.value
        
        primary_role = user.get_primary_role()
        return primary_role or RoleType.CUSTOMER.value
    
    async def is_medical_staff(self, user_id: str) -> bool:
        """检查是否为医疗人员"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        return user.is_medical_staff()
    
    async def get_role_hierarchy_level(self, user_id: str) -> int:
        """获取用户角色层级（数字越大权限越高）"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return 0
        
        # 定义角色层级
        role_hierarchy = {
            RoleType.CUSTOMER.value: 1,
            RoleType.CONSULTANT.value: 2,
            RoleType.DOCTOR.value: 3,
            RoleType.OPERATOR.value: 4,
            RoleType.ADMINISTRATOR.value: 5
        }
        
        max_level = 0
        for role_name in user.roles:
            level = role_hierarchy.get(role_name, 0)
            max_level = max(max_level, level)
        
        return max_level
