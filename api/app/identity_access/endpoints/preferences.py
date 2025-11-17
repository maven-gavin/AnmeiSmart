from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.identity_access.deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.identity_access.deps import get_identity_access_application_service
from app.identity_access.application import IdentityAccessApplicationService
from app.identity_access.schemas.profile import (
    UserPreferencesInfo, UserPreferencesCreate, UserPreferencesUpdate,
    UserDefaultRoleInfo, UserDefaultRoleUpdate,
    LoginHistoryInfo, LoginHistoryCreate,
    UserProfileInfo, ChangePasswordRequest
)
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

router = APIRouter()

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)


@router.get("/me", response_model=ApiResponse[UserProfileInfo])
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    identity_access_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserProfileInfo]:
    """
    获取当前用户的个人中心完整信息
    """
    try:
        profile = await identity_access_service.get_user_profile(str(current_user.id))
        return ApiResponse.success(profile)
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        raise _handle_unexpected_error("获取个人中心信息失败", e)


@router.get("/preferences", response_model=ApiResponse[UserPreferencesInfo])
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    identity_access_app_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserPreferencesInfo]:
    """
    获取当前用户的偏好设置
    """
    try:
        preferences = await identity_access_app_service.get_user_preferences(str(current_user.id))
        if not preferences:
            default_preferences = UserPreferencesCreate()
            created = await identity_access_app_service.create_user_preferences(
                str(current_user.id), 
                default_preferences
            )
            return ApiResponse.success(created)
        return ApiResponse.success(preferences)
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        raise _handle_unexpected_error("获取用户偏好设置失败", e)


@router.put("/preferences", response_model=ApiResponse[UserPreferencesInfo])
async def update_my_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    identity_access_app_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserPreferencesInfo]:
    """
    更新当前用户的偏好设置
    """
    try:
        updated = await identity_access_app_service.update_user_preferences(
            str(current_user.id),
            preferences_data
        )
        return ApiResponse.success(updated)
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise _handle_unexpected_error("更新用户偏好设置失败", e)

@router.get("/default-role", response_model=ApiResponse[UserDefaultRoleInfo])
async def get_my_default_role(
    current_user: User = Depends(get_current_user),
    identity_access_app_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserDefaultRoleInfo]:
    """
    获取当前用户的默认角色设置
    """
    try:
        default_role = await identity_access_app_service.get_user_default_role_setting(str(current_user.id))
        if not default_role:
            raise BusinessException("默认角色设置不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        return ApiResponse.success(default_role)
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取默认角色设置失败", e)


@router.put("/default-role", response_model=ApiResponse[UserDefaultRoleInfo])
async def set_my_default_role(
    default_role_data: UserDefaultRoleUpdate,
    current_user: User = Depends(get_current_user),
    identity_access_app_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserDefaultRoleInfo]:
    """
    设置当前用户的默认角色
    """
    try:
        info = await identity_access_app_service.set_user_default_role(
            str(current_user.id),
            default_role_data
        )
        return ApiResponse.success(info)
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise _handle_unexpected_error("设置默认角色失败", e)


@router.get("/login-history", response_model=ApiResponse[List[LoginHistoryInfo]])
async def get_my_login_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    identity_access_app_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[List[LoginHistoryInfo]]:
    """
    获取当前用户的登录历史
    """
    try:
        if limit > 50:
            limit = 50
        
        login_histories = await identity_access_app_service.get_user_login_history(
            str(current_user.id),
            limit=limit
        )
        
        result = [
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
        return ApiResponse.success(result)
    except Exception as e:
        raise _handle_unexpected_error("获取登录历史失败", e)


@router.post("/login-history", response_model=ApiResponse[LoginHistoryInfo], status_code=status.HTTP_201_CREATED)
async def create_login_record(
    request: Request,
    login_role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    identity_access_app_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[LoginHistoryInfo]:
    """
    创建登录历史记录（通常在用户登录时自动调用）
    """
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        login_data = LoginHistoryCreate(
            user_id=str(current_user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            login_role=login_role or "",
            location=""
        )
        
        success = await identity_access_app_service.create_login_history(login_data)
        if not success:
            raise BusinessException("创建登录历史记录失败")
        
        return ApiResponse.success(
            LoginHistoryInfo(
                id=str(current_user.id),
                user_id=str(current_user.id),
                ip_address=ip_address,
                user_agent=user_agent,
                login_role=login_role or "",
                location="",
                login_time=datetime.now()
            ),
            message="创建登录历史记录成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("创建登录历史记录失败", e)


@router.get("/should-apply-default-role", response_model=ApiResponse[dict])
async def check_should_apply_default_role(
    current_user: User = Depends(get_current_user),
    identity_access_app_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> dict:
    """
    检查是否应该应用默认角色（首次登录逻辑）
    """
    try:
        default_role = await identity_access_app_service.should_apply_default_role(str(current_user.id))
        return ApiResponse.success({
            "should_apply": default_role is not None,
            "default_role": default_role
        })
    except Exception as e:
        raise _handle_unexpected_error("检查默认角色应用失败", e)


@router.post("/change-password", response_model=ApiResponse[dict])
async def change_my_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    identity_access_app_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> dict:
    """
    修改当前用户的密码
    """
    try:
        success = await identity_access_app_service.change_password(
            str(current_user.id),
            password_data
        )
        
        return ApiResponse.success({"success": success, "message": "密码修改成功"})
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise _handle_unexpected_error("修改密码失败", e)


# 管理员接口（可选，用于管理其他用户的个人中心信息）
@router.get("/{user_id}", response_model=ApiResponse[UserProfileInfo])
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    identity_access_app_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[UserProfileInfo]:
    """
    获取指定用户的个人中心信息（管理员功能）
    """
    try:
        can_view = await identity_access_app_service.check_permission(
            str(current_user.id), "user:view"
        )
        if not can_view and str(current_user.id) != str(user_id):
            raise BusinessException("权限不足", code=ErrorCode.PERMISSION_DENIED, status_code=status.HTTP_403_FORBIDDEN)
        
        profile = await identity_access_app_service.get_user_profile(user_id)
        return ApiResponse.success(profile)
    except BusinessException:
        raise
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        raise _handle_unexpected_error("获取用户个人中心信息失败", e)


@router.get("/{user_id}/login-history", response_model=ApiResponse[List[LoginHistoryInfo]])
async def get_user_login_history(
    user_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    identity_access_app_service: IdentityAccessApplicationService = Depends(get_identity_access_application_service)
) -> ApiResponse[List[LoginHistoryInfo]]:
    """
    获取指定用户的登录历史（管理员功能）
    """
    try:
        can_view = await identity_access_app_service.check_permission(
            str(current_user.id), "user:view"
        )
        if not can_view and str(current_user.id) != str(user_id):
            raise BusinessException("权限不足", code=ErrorCode.PERMISSION_DENIED, status_code=status.HTTP_403_FORBIDDEN)
        
        if limit > 50:
            limit = 50
        
        login_histories = await identity_access_app_service.get_user_login_history(
            user_id,
            limit=limit
        )
        
        result = [
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
        return ApiResponse.success(result)
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取用户登录历史失败", e)