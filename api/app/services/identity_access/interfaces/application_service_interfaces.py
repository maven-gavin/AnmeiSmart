"""
应用服务接口定义 - 用户身份与权限上下文

定义应用层的用例编排接口，协调领域服务完成业务用例。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse
from app.schemas.token import Token, RefreshTokenRequest
from app.schemas.profile import LoginHistoryCreate


class IIdentityAccessApplicationService(ABC):
    """用户身份与权限应用服务接口"""
    
    # 用户管理用例
    @abstractmethod
    async def create_user_use_case(
        self, 
        user_data: UserCreate
    ) -> UserResponse:
        """创建用户用例"""
        pass
    
    @abstractmethod
    async def get_user_by_id_use_case(self, user_id: str) -> Optional[UserResponse]:
        """根据ID获取用户用例"""
        pass
    
    @abstractmethod
    async def get_user_by_email_use_case(self, email: str) -> Optional[UserResponse]:
        """根据邮箱获取用户用例"""
        pass
    
    @abstractmethod
    async def update_user_use_case(
        self, 
        user_id: str, 
        user_data: UserUpdate
    ) -> UserResponse:
        """更新用户用例"""
        pass
    
    @abstractmethod
    async def delete_user_use_case(self, user_id: str) -> bool:
        """删除用户用例"""
        pass
    
    @abstractmethod
    async def get_users_list_use_case(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UserResponse]:
        """获取用户列表用例"""
        pass
    
    # 认证用例
    @abstractmethod
    async def login_use_case(
        self, 
        username_or_email: str, 
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Token:
        """用户登录用例"""
        pass
    
    @abstractmethod
    async def refresh_token_use_case(
        self, 
        refresh_token_request: RefreshTokenRequest
    ) -> Token:
        """刷新令牌用例"""
        pass
    
    @abstractmethod
    async def logout_use_case(self, token: str) -> bool:
        """用户登出用例"""
        pass
    
    # 权限管理用例
    @abstractmethod
    async def get_user_roles_use_case(self, user_id: str) -> List[str]:
        """获取用户角色用例"""
        pass
    
    @abstractmethod
    async def switch_role_use_case(
        self, 
        user_id: str, 
        target_role: str
    ) -> Token:
        """切换用户角色用例"""
        pass
    
    @abstractmethod
    async def check_permission_use_case(
        self, 
        user_id: str, 
        permission: str
    ) -> bool:
        """检查用户权限用例"""
        pass
    
    # 角色管理用例
    @abstractmethod
    async def get_all_roles_use_case(self) -> List[RoleResponse]:
        """获取所有角色用例"""
        pass
    
    @abstractmethod
    async def create_role_use_case(
        self, 
        name: str, 
        description: Optional[str] = None
    ) -> RoleResponse:
        """创建角色用例"""
        pass
    
    @abstractmethod
    async def assign_role_to_user_use_case(
        self, 
        user_id: str, 
        role_name: str
    ) -> bool:
        """分配角色给用户用例"""
        pass
    
    @abstractmethod
    async def remove_role_from_user_use_case(
        self, 
        user_id: str, 
        role_name: str
    ) -> bool:
        """移除用户角色用例"""
        pass
    
    # 登录历史用例
    @abstractmethod
    async def create_login_history_use_case(
        self, 
        login_data: LoginHistoryCreate
    ) -> bool:
        """创建登录历史用例"""
        pass
    
    @abstractmethod
    async def get_user_login_history_use_case(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取用户登录历史用例"""
        pass
