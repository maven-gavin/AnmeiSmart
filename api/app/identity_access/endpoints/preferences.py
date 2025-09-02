from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.identity_access.deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.identity_access.deps.identity_access import get_identity_access_application_service
from app.identity_access.application import IdentityAccessApplicationService
from app.identity_access.schemas.profile import (
    UserPreferencesInfo, UserPreferencesCreate, UserPreferencesUpdate,
    UserDefaultRoleInfo, UserDefaultRoleUpdate,
    LoginHistoryInfo, LoginHistoryCreate,
    UserProfileInfo, ChangePasswordRequest
)

router = APIRouter()


@router.get("/me", response_model=UserProfileInfo)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserProfileInfo:
    """
    获取当前用户的个人中心完整信息
    """
    try:
        return await identity_access_service.get_user_profile_use_case(str(current_user.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取个人中心信息失败"
        )


@router.get("/preferences", response_model=UserPreferencesInfo)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserPreferencesInfo:
    """
    获取当前用户的偏好设置
    """
    try:
        preferences = await identity_access_service.get_user_preferences_use_case(str(current_user.id))
        if not preferences:
            # 如果不存在偏好设置，创建默认值
            default_preferences = UserPreferencesCreate()
            return await identity_access_service.create_user_preferences_use_case(
                str(current_user.id), 
                default_preferences
            )
        return preferences
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户偏好设置失败"
        )


@router.put("/preferences", response_model=UserPreferencesInfo)
async def update_my_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserPreferencesInfo:
    """
    更新当前用户的偏好设置
    """
    try:
        return await identity_access_service.update_user_preferences_use_case(
            str(current_user.id),
            preferences_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户偏好设置失败"
        )

@router.get("/default-role", response_model=UserDefaultRoleInfo)
async def get_my_default_role(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserDefaultRoleInfo:
    """
    获取当前用户的默认角色设置
    """
    try:
        default_role = await identity_access_service.get_user_default_role_setting_use_case(str(current_user.id))
        if not default_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="默认角色设置不存在"
            )
        return default_role
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取默认角色设置失败"
        )


@router.put("/default-role", response_model=UserDefaultRoleInfo)
async def set_my_default_role(
    default_role_data: UserDefaultRoleUpdate,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserDefaultRoleInfo:
    """
    设置当前用户的默认角色
    """
    try:
        return await identity_access_service.set_user_default_role_use_case(
            str(current_user.id),
            default_role_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置默认角色失败"
        )


@router.get("/login-history", response_model=List[LoginHistoryInfo])
async def get_my_login_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> List[LoginHistoryInfo]:
    """
    获取当前用户的登录历史
    """
    try:
        if limit > 50:  # 限制最大查询数量
            limit = 50
        
        login_histories = await identity_access_service.get_user_login_history_use_case(
            str(current_user.id),
            limit=limit
        )
        
        # 转换为LoginHistoryInfo格式
        return [
            LoginHistoryInfo(
                id=history["id"],
                user_id=str(current_user.id),
                ip_address=history["ip_address"],
                user_agent=history["user_agent"],
                login_role=history["login_role"],
                location=history["location"],
                login_time=datetime.fromisoformat(history["login_time"].replace('Z', '+00:00'))
            )
            for history in login_histories
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取登录历史失败"
        )


@router.post("/login-history", response_model=LoginHistoryInfo, status_code=status.HTTP_201_CREATED)
async def create_login_record(
    request: Request,
    login_role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> LoginHistoryInfo:
    """
    创建登录历史记录（通常在用户登录时自动调用）
    """
    try:
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
        
        success = await identity_access_service.create_login_history_use_case(login_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建登录历史记录失败"
            )
        
        # 返回创建的登录历史记录
        return LoginHistoryInfo(
            id=str(current_user.id),
            user_id=str(current_user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            login_role=login_role or "",
            location="",
            login_time=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建登录历史记录失败"
        )


@router.get("/should-apply-default-role")
async def check_should_apply_default_role(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> dict:
    """
    检查是否应该应用默认角色（首次登录逻辑）
    """
    try:
        default_role = await identity_access_service.should_apply_default_role_use_case(str(current_user.id))
        
        return {
            "should_apply": default_role is not None,
            "default_role": default_role
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查默认角色应用失败"
        )


@router.post("/change-password")
async def change_my_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> dict:
    """
    修改当前用户的密码
    """
    try:
        success = await identity_access_service.change_password_use_case(
            str(current_user.id),
            password_data
        )
        
        return {
            "success": success,
            "message": "密码修改成功"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )


# 管理员接口（可选，用于管理其他用户的个人中心信息）
@router.get("/{user_id}", response_model=UserProfileInfo)
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> UserProfileInfo:
    """
    获取指定用户的个人中心信息（管理员功能）
    """
    try:
        # 检查权限：只有管理员可以查看其他用户的信息
        can_view = await identity_access_service.check_permission_use_case(
            str(current_user.id), "user:view"
        )
        if not can_view and str(current_user.id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return await identity_access_service.get_user_profile_use_case(user_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户个人中心信息失败"
        )


@router.get("/{user_id}/login-history", response_model=List[LoginHistoryInfo])
async def get_user_login_history(
    user_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> List[LoginHistoryInfo]:
    """
    获取指定用户的登录历史（管理员功能）
    """
    try:
        # 检查权限：只有管理员可以查看其他用户的登录历史
        can_view = await identity_access_service.check_permission_use_case(
            str(current_user.id), "user:view"
        )
        if not can_view and str(current_user.id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        if limit > 50:  # 限制最大查询数量
            limit = 50
        
        login_histories = await identity_access_service.get_user_login_history_use_case(
            user_id,
            limit=limit
        )
        
        # 转换为LoginHistoryInfo格式
        return [
            LoginHistoryInfo(
                id=history["id"],
                user_id=user_id,
                ip_address=history["ip_address"],
                user_agent=history["user_agent"],
                login_role=history["login_role"],
                location=history["location"],
                login_time=datetime.fromisoformat(history["login_time"].replace('Z', '+00:00'))
            )
            for history in login_histories
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户登录历史失败"
        ) 