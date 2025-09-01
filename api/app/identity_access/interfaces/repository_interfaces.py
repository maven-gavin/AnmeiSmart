"""
仓储接口定义 - 用户身份与权限上下文

定义数据访问层的抽象接口，实现依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.entities.user import User
from ..domain.entities.role import Role
from ..domain.value_objects.login_history import LoginHistory


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
    async def get_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否存在"""
        pass
    
    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """检查用户名是否存在"""
        pass
    
    @abstractmethod
    async def exists_by_phone(self, phone: str) -> bool:
        """检查手机号是否存在"""
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
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[User]:
        """获取用户列表"""
        pass
    
    @abstractmethod
    async def get_user_roles(self, user_id: str) -> List[str]:
        """获取用户角色列表"""
        pass
    
    @abstractmethod
    async def assign_role(self, user_id: str, role_name: str) -> bool:
        """分配角色给用户"""
        pass
    
    @abstractmethod
    async def remove_role(self, user_id: str, role_name: str) -> bool:
        """移除用户角色"""
        pass
    
    @abstractmethod
    async def get_user_default_role(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户默认角色设置"""
        pass
    
    @abstractmethod
    async def save_user_default_role(self, user_id: str, default_role: str) -> Dict[str, Any]:
        """保存用户默认角色设置"""
        pass
    
    @abstractmethod
    async def update_user_default_role(self, user_id: str, default_role: str) -> Dict[str, Any]:
        """更新用户默认角色设置"""
        pass
    
    @abstractmethod
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好设置"""
        pass
    
    @abstractmethod
    async def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """保存用户偏好设置"""
        pass
    
    @abstractmethod
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户偏好设置"""
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
    async def get_all(self) -> List[Role]:
        """获取所有角色"""
        pass
    
    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """检查角色名称是否存在"""
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
    async def get_or_create(self, name: str, description: Optional[str] = None) -> Role:
        """获取或创建角色"""
        pass


class ILoginHistoryRepository(ABC):
    """登录历史仓储接口"""
    
    @abstractmethod
    async def create(self, login_history: LoginHistory) -> LoginHistory:
        """创建登录历史记录"""
        pass
    
    @abstractmethod
    async def get_user_login_history(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[LoginHistory]:
        """获取用户登录历史"""
        pass
    
    @abstractmethod
    async def get_recent_logins(
        self, 
        user_id: str, 
        since: datetime,
        limit: int = 10
    ) -> List[LoginHistory]:
        """获取用户最近登录记录"""
        pass



