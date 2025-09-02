"""
安全相关依赖注入配置

提供安全服务的依赖注入函数。
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.common.infrastructure.db.base import get_db
from app.identity_access.infrastructure.db.user import User
from app.identity_access.infrastructure.jwt_service import JWTService
from app.identity_access.domain.security_domain_service import SecurityDomainService
from app.identity_access.application.security_application_service import SecurityApplicationService

# 获取配置
settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_jwt_service() -> JWTService:
    """获取JWT服务实例"""
    return JWTService()

from app.identity_access.infrastructure.repositories.user_repository import UserRepository
from app.identity_access.converters.user_converter import UserConverter

def get_user_repository(db: Session = Depends(get_db)):
    """获取用户仓储实例"""
    return UserRepository(db, UserConverter())

def get_security_domain_service(
    jwt_service: JWTService = Depends(get_jwt_service),
    user_repository = Depends(get_user_repository)
) -> SecurityDomainService:
    """获取安全领域服务实例"""
    return SecurityDomainService(user_repository, jwt_service)

def get_security_application_service(
    security_domain_service: SecurityDomainService = Depends(get_security_domain_service)
) -> SecurityApplicationService:
    """获取安全应用服务实例"""
    return SecurityApplicationService(security_domain_service)

# 重构后的依赖函数
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    security_app_service: SecurityApplicationService = Depends(get_security_application_service)
) -> User:
    """
    获取当前用户 - 重构后的依赖函数
    
    Args:
        token: JWT令牌
        security_app_service: 安全应用服务
        
    Returns:
        User: 认证成功的用户对象
        
    Raises:
        HTTPException: 如果认证失败或用户不存在
    """
    return await security_app_service.get_current_user_use_case(token)

def check_role_permission(required_roles: Optional[List[str]] = None):
    """
    检查用户是否有所需角色的装饰器工厂函数
    
    Args:
        required_roles: 所需的角色列表
        
    Returns:
        函数: 检查用户角色的依赖函数
    """
    async def check_permission(
        current_user: User = Depends(get_current_user),
        security_app_service: SecurityApplicationService = Depends(get_security_application_service)
    ):
        """检查用户权限的依赖函数"""
        return await security_app_service.check_role_permission_use_case(current_user, required_roles)
    
    return check_permission

async def get_current_admin(
    current_user: User = Depends(get_current_user),
    security_app_service: SecurityApplicationService = Depends(get_security_application_service)
) -> User:
    """
    获取当前管理员用户 - 重构后的依赖函数
    
    Args:
        current_user: 当前认证用户
        security_app_service: 安全应用服务
        
    Returns:
        User: 管理员用户对象
        
    Raises:
        HTTPException: 如果用户不是管理员
    """
    return await security_app_service.get_current_admin_use_case(current_user)

# 向后兼容的函数 - 从原security.py迁移
def verify_token(token: str) -> Optional[str]:
    """
    验证JWT令牌并提取用户ID - 向后兼容函数
    
    Args:
        token: JWT令牌
    
    Returns:
        str: 用户ID，如果令牌无效则返回None
    """
    jwt_service = JWTService()
    payload = jwt_service.verify_token(token)
    if payload:
        return payload.get("sub")
    return None

def create_access_token(
    subject, 
    expires_delta=None,
    active_role=None
) -> str:
    """
    创建访问令牌 - 向后兼容函数
    
    Args:
        subject: 令牌主体 (通常是用户ID)
        expires_delta: 过期时间增量
        active_role: 用户当前活跃角色
        
    Returns:
        str: JWT令牌
    """
    jwt_service = JWTService()
    return jwt_service.create_access_token(subject, expires_delta, active_role)

def create_refresh_token(
    subject,
    expires_delta=None,
    active_role=None
) -> str:
    """
    创建刷新令牌 - 向后兼容函数
    
    Args:
        subject: 令牌主体 (通常是用户ID)
        expires_delta: 过期时间增量
        active_role: 用户当前活跃角色
        
    Returns:
        str: JWT刷新令牌
    """
    jwt_service = JWTService()
    return jwt_service.create_refresh_token(subject, expires_delta, active_role)
