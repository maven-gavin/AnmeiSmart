"""
转换器接口定义

定义数据转换器的抽象接口，用于依赖注入。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..domain.entities.user import User
from ..domain.entities.role import Role
from ..infrastructure.db.user import User as UserModel, Role as RoleModel
from ..schemas.user import UserCreate, UserUpdate, UserResponse


class IUserConverter(ABC):
    """用户转换器接口"""
    
    @abstractmethod
    def to_response(self, user: User, active_role: Optional[str] = None) -> UserResponse:
        """转换用户实体为响应格式"""
        pass
    
    @abstractmethod
    def to_list_response(self, users: list[User]) -> list[UserResponse]:
        """转换用户列表为响应格式"""
        pass
    
    @abstractmethod
    def from_create_request(self, request: UserCreate) -> Dict[str, Any]:
        """从创建请求转换为领域对象参数"""
        pass
    
    @abstractmethod
    def from_update_request(self, request: UserUpdate) -> Dict[str, Any]:
        """从更新请求转换为领域对象参数"""
        pass
    
    @abstractmethod
    def from_model(self, model: UserModel) -> User:
        """从ORM模型转换为领域实体"""
        pass
    
    @abstractmethod
    def to_model_dict(self, user: User) -> Dict[str, Any]:
        """转换用户实体为ORM模型字典"""
        pass


class IRoleConverter(ABC):
    """角色转换器接口"""
    
    @abstractmethod
    def from_model(self, model: RoleModel) -> Role:
        """从ORM模型转换为领域实体"""
        pass
    
    @abstractmethod
    def to_model_dict(self, role: Role) -> Dict[str, Any]:
        """转换角色实体为ORM模型字典"""
        pass
