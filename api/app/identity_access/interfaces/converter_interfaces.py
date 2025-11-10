"""
转换器接口定义

定义数据转换器的抽象接口，用于依赖注入。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..domain.entities.user import UserEntity
from ..domain.entities.role import RoleEntity
from ..infrastructure.db.user import User as UserModel, Role as RoleModel
from ..schemas.user import UserCreate, UserUpdate, UserResponse


class IUserConverter(ABC):
    """用户转换器接口"""
    
    @abstractmethod
    def to_response(self, user: UserEntity, active_role: Optional[str] = None) -> UserResponse:
        """转换用户实体为响应格式"""
        pass
    
    @abstractmethod
    def to_list_response(self, users: list[UserEntity]) -> list[UserResponse]:
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
    def from_model(self, model: UserModel) -> UserEntity:
        """从ORM模型转换为领域实体"""
        pass
    
    @abstractmethod
    def to_model_dict(self, user: UserEntity) -> Dict[str, Any]:
        """转换用户实体为ORM模型字典"""
        pass


class IRoleConverter(ABC):
    """角色转换器接口"""
    
    @abstractmethod
    def from_model(self, model: RoleModel) -> RoleEntity:
        """从ORM模型转换为领域实体"""
        pass
    
    @abstractmethod
    def to_model_dict(self, role: RoleEntity) -> Dict[str, Any]:
        """转换角色实体为ORM模型字典"""
        pass
