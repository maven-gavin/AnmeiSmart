"""
用户相关依赖注入配置

遵循 @ddd_service_schema.mdc 第3章依赖注入配置规范：
- 使用FastAPI的依赖注入避免循环依赖
- 接口抽象：使用抽象接口而不是具体实现
- 依赖方向：确保依赖方向指向领域层
- 生命周期管理：合理管理依赖的作用域
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.infrastructure.repositories.user_repository import UserRepository
from app.identity_access.infrastructure.repositories.role_repository import RoleRepository
from app.identity_access.application.identity_access_application_service import IdentityAccessApplicationService


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """获取用户仓储实例
    
    遵循DDD规范：
    - 使用FastAPI的依赖注入避免循环依赖
    - 依赖方向：确保依赖方向指向领域层
    """
    return UserRepository(db)


def get_role_repository(db: Session = Depends(get_db)) -> RoleRepository:
    """获取角色仓储实例
    
    遵循DDD规范：
    - 使用FastAPI的依赖注入避免循环依赖
    - 依赖方向：确保依赖方向指向领域层
    """
    return RoleRepository(db)


def get_identity_access_application_service(
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository)
) -> IdentityAccessApplicationService:
    """获取身份访问应用服务实例
    
    遵循DDD规范：
    - 编排领域服务，实现用例，事务管理
    - 无状态，协调领域对象完成业务用例
    """
    return IdentityAccessApplicationService(
        user_repository=user_repository,
        role_repository=role_repository
    )


# 导出所有依赖函数
__all__ = [
    "get_user_repository",
    "get_role_repository", 
    "get_identity_access_application_service"
]
