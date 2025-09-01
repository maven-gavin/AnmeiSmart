"""
领域服务接口定义 - 用户身份与权限上下文

定义跨聚合的业务逻辑接口，处理复杂的领域规则。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..domain.entities.user import User
from ..domain.entities.role import Role
from ..domain.value_objects.login_history import LoginHistory


class IUserDomainService(ABC):
    """用户领域服务接口"""
    
    @abstractmethod
    async def create_user(
        self, 
        username: str, 
        email: str, 
        password: str,
        phone: Optional[str] = None,
        avatar: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> User:
        """创建用户 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def update_user_profile(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> User:
        """更新用户资料 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def change_password(
        self, 
        user_id: str, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """修改密码 - 领域逻辑"""
        pass
    
    @abstractmethod
    async def activate_user(self, user_id: str) -> bool:
        """激活用户"""
        pass
    
    @abstractmethod
    async def deactivate_user(self, user_id: str) -> bool:
        """停用用户"""
        pass
    
    @abstractmethod
    async def assign_roles(self, user_id: str, role_names: List[str]) -> bool:
        """分配角色给用户"""
        pass
    
    @abstractmethod
    async def remove_roles(self, user_id: str, role_names: List[str]) -> bool:
        """移除用户角色"""
        pass


class IAuthenticationDomainService(ABC):
    """认证领域服务接口"""
    
    @abstractmethod
    async def authenticate_user(
        self, 
        username_or_email: str, 
        password: str
    ) -> Optional[User]:
        """用户身份认证"""
        pass
    
    @abstractmethod
    async def record_login(
        self, 
        user_id: str, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        login_role: Optional[str] = None,
        location: Optional[str] = None
    ) -> LoginHistory:
        """记录登录历史"""
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """刷新令牌"""
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """撤销令牌"""
        pass


class IPermissionDomainService(ABC):
    """权限领域服务接口"""
    
    @abstractmethod
    async def check_user_permission(
        self, 
        user_id: str, 
        permission: str
    ) -> bool:
        """检查用户权限"""
        pass
    
    @abstractmethod
    async def check_user_role(self, user_id: str, role_name: str) -> bool:
        """检查用户角色"""
        pass
    
    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限列表"""
        pass
    
    @abstractmethod
    async def get_user_roles(self, user_id: str) -> List[str]:
        """获取用户角色列表"""
        pass
    
    @abstractmethod
    async def switch_user_role(
        self, 
        user_id: str, 
        target_role: str
    ) -> bool:
        """切换用户角色"""
        pass
    
    @abstractmethod
    async def validate_admin_permission(self, user_id: str) -> bool:
        """验证管理员权限"""
        pass
