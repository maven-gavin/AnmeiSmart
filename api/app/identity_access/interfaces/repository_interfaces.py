"""
仓储接口定义

定义所有仓储的接口，支持依赖注入和测试。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.entities.user import User
from ..domain.entities.role import Role
from ..domain.entities.tenant import Tenant
from ..domain.entities.permission import Permission
from ..domain.value_objects.login_history import LoginHistory
from ..domain.value_objects.tenant_status import TenantStatus


class IUserRepository(ABC):
    """用户仓储接口"""
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        pass
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """保存用户"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """删除用户"""
        pass
    
    @abstractmethod
    async def list_active(self, limit: int = 100, offset: int = 0) -> List[User]:
        """获取活跃用户列表"""
        pass
    
    @abstractmethod
    async def count_by_tenant_id(self, tenant_id: str) -> int:
        """统计租户下的用户数量"""
        pass
    
    @abstractmethod
    async def get_user_roles(self, user_id: str) -> List[Role]:
        """获取用户的角色列表"""
        pass
    
    @abstractmethod
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好设置"""
        pass


class IRoleRepository(ABC):
    """角色仓储接口"""
    
    @abstractmethod
    async def get_by_id(self, role_id: str) -> Optional[Role]:
        """根据ID获取角色"""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        pass
    
    @abstractmethod
    async def save(self, role: Role) -> Role:
        """保存角色"""
        pass
    
    @abstractmethod
    async def delete(self, role_id: str) -> bool:
        """删除角色"""
        pass
    
    @abstractmethod
    async def list_active(self, tenant_id: Optional[str] = None) -> List[Role]:
        """获取活跃角色列表"""
        pass
    
    @abstractmethod
    async def list_system_roles(self) -> List[Role]:
        """获取系统角色列表"""
        pass
    
    @abstractmethod
    async def list_admin_roles(self) -> List[Role]:
        """获取管理员角色列表"""
        pass
    
    @abstractmethod
    async def assign_permission(self, role_id: str, permission_id: str) -> bool:
        """为角色分配权限"""
        pass
    
    @abstractmethod
    async def remove_permission(self, role_id: str, permission_id: str) -> bool:
        """从角色移除权限"""
        pass
    
    @abstractmethod
    async def get_permissions(self, role_id: str) -> List[Permission]:
        """获取角色的权限列表"""
        pass


class ITenantRepository(ABC):
    """租户仓储接口"""
    
    @abstractmethod
    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """根据ID获取租户"""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Tenant]:
        """根据名称获取租户"""
        pass
    
    @abstractmethod
    async def get_system_tenant(self) -> Optional[Tenant]:
        """获取系统租户"""
        pass
    
    @abstractmethod
    async def save(self, tenant: Tenant) -> Tenant:
        """保存租户"""
        pass
    
    @abstractmethod
    async def delete(self, tenant_id: str) -> bool:
        """删除租户"""
        pass
    
    @abstractmethod
    async def list_by_status(self, status: TenantStatus) -> List[Tenant]:
        """根据状态获取租户列表"""
        pass
    
    @abstractmethod
    async def list_active(self) -> List[Tenant]:
        """获取活跃租户列表"""
        pass


class IPermissionRepository(ABC):
    """权限仓储接口"""
    
    @abstractmethod
    async def get_by_id(self, permission_id: str) -> Optional[Permission]:
        """根据ID获取权限"""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Permission]:
        """根据名称获取权限"""
        pass
    
    @abstractmethod
    async def save(self, permission: Permission) -> Permission:
        """保存权限"""
        pass
    
    @abstractmethod
    async def delete(self, permission_id: str) -> bool:
        """删除权限"""
        pass
    
    @abstractmethod
    async def list_active(self, tenant_id: Optional[str] = None) -> List[Permission]:
        """获取活跃权限列表"""
        pass
    
    @abstractmethod
    async def list_system_permissions(self) -> List[Permission]:
        """获取系统权限列表"""
        pass
    
    @abstractmethod
    async def get_roles(self, permission_id: str) -> List[Role]:
        """获取拥有指定权限的角色列表"""
        pass


class ILoginHistoryRepository(ABC):
    """登录历史仓储接口"""
    
    @abstractmethod
    async def get_by_id(self, history_id: str) -> Optional[LoginHistory]:
        """根据ID获取登录历史"""
        pass
    
    @abstractmethod
    async def save(self, login_history: LoginHistory) -> LoginHistory:
        """保存登录历史"""
        pass
    
    @abstractmethod
    async def list_by_user_id(self, user_id: str, limit: int = 100, offset: int = 0) -> List[LoginHistory]:
        """获取用户的登录历史列表"""
        pass
    
    @abstractmethod
    async def get_latest_by_user_id(self, user_id: str) -> Optional[LoginHistory]:
        """获取用户最新的登录历史"""
        pass