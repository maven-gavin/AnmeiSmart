"""
认证授权相关依赖注入配置
"""
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.common.deps import get_db
from app.identity_access.models.user import User, Role
from app.identity_access.services.user_service import UserService
from app.identity_access.services.jwt_service import JWTService
from app.identity_access.deps.user_deps import get_user_service

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    jwt_service = JWTService()
    payload = jwt_service.verify_token(token)
    
    if not payload:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id: str = payload.get("sub")
    if user_id is None:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 直接查询数据库或使用Service
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    # 从 JWT token 中获取活跃角色（如果存在）
    active_role = payload.get("role")
    if active_role:
        # 将活跃角色存储为用户对象的临时属性
        user._active_role = active_role
        
    return user

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前管理员用户"""
    # 简单检查是否为管理员
    is_admin = False
    for role in current_user.roles:
        if role.is_admin or role.name in ["administrator", "super_admin"]:
            is_admin = True
            break
            
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：需要管理员权限"
        )
    return current_user

def require_role(role_name: str):
    """检查用户是否拥有特定角色"""
    async def check_role(current_user: User = Depends(get_current_user)):
        has_role = False
        for role in current_user.roles:
            if role.name == role_name or role.is_admin: # 管理员拥有所有角色权限
                has_role = True
                break
        
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色权限: {role_name}"
            )
        return current_user
    return check_role

def require_permission(permission_code: str):
    """检查用户是否拥有特定权限"""
    async def check_permission(current_user: User = Depends(get_current_user)):
        # 1. 如果是超级管理员，直接通过
        for role in current_user.roles:
            if role.is_admin:
                return current_user
                
        # 2. 检查用户的所有角色的所有权限
        has_permission = False
        # 如果有活跃角色上下文，优先检查活跃角色（这里简化为检查所有角色）
        for role in current_user.roles:
            for permission in role.permissions:
                if permission.code == permission_code:
                    has_permission = True
                    break
            if has_permission:
                break
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要操作权限: {permission_code}"
            )
        return current_user
    return check_permission
