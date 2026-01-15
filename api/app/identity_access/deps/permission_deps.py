"""
权限检查相关依赖注入配置
"""
from typing import List, Optional
from fastapi import Depends, HTTPException, status

from app.identity_access.models.user import User


def get_user_primary_role(user: User) -> str:
    """获取用户主要角色"""
    if not user.roles:
        return "customer"  # 默认角色
    
    # 优先返回管理员角色
    for role in user.roles:
        if role.is_admin or role.name in ["administrator", "super_admin"]:
            return "admin"
    
    # 按优先级返回第一个角色
    # 处理 priority 为 None 的情况，将其视为 0
    sorted_roles = sorted(user.roles, key=lambda r: r.priority if r.priority is not None else 0, reverse=True)
    if sorted_roles:
        return sorted_roles[0].name
    
    # 如果没有角色，返回默认角色
    return "customer"


def get_user_roles(user: User) -> List[str]:
    """获取用户所有角色名称列表"""
    return [role.name for role in user.roles] if user.roles else []


def check_user_has_role(user: User, role_name: str) -> bool:
    """检查用户是否拥有特定角色"""
    if not user.roles:
        return False
    
    # 管理员拥有所有角色权限
    for role in user.roles:
        if role.is_admin or role.name in ["administrator", "super_admin"]:
            return True
    
    # 检查是否有指定角色
    return any(role.name == role_name for role in user.roles)


async def check_user_any_role(user: User, required_roles: List[str]) -> bool:
    """检查用户是否拥有任意一个指定角色"""
    if not user.roles:
        return False
    
    # 管理员拥有所有角色权限
    for role in user.roles:
        if role.is_admin or role.name in ["administrator", "super_admin"]:
            return True
    
    # 检查是否有任意一个指定角色
    user_role_names = {role.name for role in user.roles}
    return any(role_name in user_role_names for role_name in required_roles)


def require_any_role(required_roles: List[str]):
    """检查用户是否拥有任意一个指定角色（FastAPI依赖）"""
    from app.identity_access.deps.auth_deps import get_current_user
    
    async def check_role(current_user: User = Depends(get_current_user)):
        if not await check_user_any_role(current_user, required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下任一角色权限: {', '.join(required_roles)}"
            )
        return current_user
    return check_role


def check_role_permission(user: User, permission: str) -> bool:
    """检查用户是否有特定权限"""
    if not user.roles:
        return False
    
    # 管理员拥有所有权限
    for role in user.roles:
        if role.is_admin or role.name in ["administrator", "super_admin"]:
            return True
    
    # 检查角色权限
    for role in user.roles:
        if role.permissions:
            for perm in role.permissions:
                if perm.name == permission:
                    return True
    
    return False

