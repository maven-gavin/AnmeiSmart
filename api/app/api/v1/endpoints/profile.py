from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models.user import User
from app.services.profile_service import profile_service
from app.schemas.profile import (
    UserPreferencesInfo, UserPreferencesCreate, UserPreferencesUpdate,
    UserDefaultRoleInfo, UserDefaultRoleUpdate,
    LoginHistoryInfo, LoginHistoryCreate,
    UserProfileInfo, ChangePasswordRequest
)

router = APIRouter()


@router.get("/me", response_model=UserProfileInfo)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserProfileInfo:
    """
    获取当前用户的个人中心完整信息
    """
    return await profile_service.get_user_profile(db=db, user_id=str(current_user.id))


@router.get("/preferences", response_model=UserPreferencesInfo)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserPreferencesInfo:
    """
    获取当前用户的偏好设置
    """
    preferences = await profile_service.get_user_preferences(db=db, user_id=str(current_user.id))
    if not preferences:
        # 如果不存在偏好设置，返回默认值
        default_preferences = UserPreferencesCreate()
        return await profile_service.create_user_preferences(
            db=db, 
            user_id=str(current_user.id), 
            preferences_data=default_preferences
        )
    return preferences


@router.put("/preferences", response_model=UserPreferencesInfo)
async def update_my_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserPreferencesInfo:
    """
    更新当前用户的偏好设置
    """
    return await profile_service.update_user_preferences(
        db=db,
        user_id=current_user.id,
        preferences_data=preferences_data
    )


@router.get("/default-role", response_model=UserDefaultRoleInfo)
async def get_my_default_role(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserDefaultRoleInfo:
    """
    获取当前用户的默认角色设置
    """
    default_role = await profile_service.get_user_default_role(db=db, user_id=current_user.id)
    if not default_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="默认角色设置不存在"
        )
    return default_role


@router.put("/default-role", response_model=UserDefaultRoleInfo)
async def set_my_default_role(
    default_role_data: UserDefaultRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserDefaultRoleInfo:
    """
    设置当前用户的默认角色
    """
    return await profile_service.set_user_default_role(
        db=db,
        user_id=current_user.id,
        default_role_data=default_role_data
    )


@router.get("/login-history", response_model=List[LoginHistoryInfo])
async def get_my_login_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[LoginHistoryInfo]:
    """
    获取当前用户的登录历史
    """
    if limit > 50:  # 限制最大查询数量
        limit = 50
    
    return await profile_service.get_user_login_history(
        db=db,
        user_id=current_user.id,
        limit=limit
    )


@router.post("/login-history", response_model=LoginHistoryInfo, status_code=status.HTTP_201_CREATED)
async def create_login_record(
    request: Request,
    login_role: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> LoginHistoryInfo:
    """
    创建登录历史记录（通常在用户登录时自动调用）
    """
    # 获取客户端信息
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    
    login_data = LoginHistoryCreate(
        user_id=str(current_user.id),
        ip_address=ip_address,
        user_agent=user_agent,
        login_role=login_role or "",
        location=""  # 添加缺失的location参数
    )
    
    return await profile_service.create_login_history(db=db, login_data=login_data)


@router.get("/should-apply-default-role")
async def check_should_apply_default_role(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    检查是否应该应用默认角色（首次登录逻辑）
    """
    default_role = await profile_service.should_apply_default_role(
        db=db, 
        user_id=current_user.id
    )
    
    return {
        "should_apply": default_role is not None,
        "default_role": default_role
    }


@router.post("/change-password")
async def change_my_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    修改当前用户的密码
    """
    success = await profile_service.change_password(
        db=db,
        user_id=str(current_user.id),
        password_data=password_data
    )
    
    return {
        "success": success,
        "message": "密码修改成功"
    }


# 管理员接口（可选，用于管理其他用户的个人中心信息）
@router.get("/{user_id}", response_model=UserProfileInfo)
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserProfileInfo:
    """
    获取指定用户的个人中心信息（管理员功能）
    """
    # 检查权限：只有管理员可以查看其他用户的信息
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    return await profile_service.get_user_profile(db=db, user_id=user_id)


@router.get("/{user_id}/login-history", response_model=List[LoginHistoryInfo])
async def get_user_login_history(
    user_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[LoginHistoryInfo]:
    """
    获取指定用户的登录历史（管理员功能）
    """
    # 检查权限：只有管理员可以查看其他用户的登录历史
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    if limit > 50:  # 限制最大查询数量
        limit = 50
    
    return await profile_service.get_user_login_history(
        db=db,
        user_id=user_id,
        limit=limit
    ) 