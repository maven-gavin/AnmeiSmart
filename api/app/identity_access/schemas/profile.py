from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class UserPreferencesBase(BaseModel):
    """用户偏好设置基础模型"""
    notification_enabled: bool = Field(default=True, description="是否启用通知")
    email_notification: bool = Field(default=True, description="是否启用邮件通知")
    push_notification: bool = Field(default=True, description="是否启用推送通知")


class UserPreferencesCreate(UserPreferencesBase):
    """创建用户偏好设置请求模型"""
    pass


class UserPreferencesUpdate(BaseModel):
    """更新用户偏好设置请求模型"""
    notification_enabled: Optional[bool] = None
    email_notification: Optional[bool] = None
    push_notification: Optional[bool] = None


class UserPreferencesInfo(UserPreferencesBase):
    """用户偏好设置完整信息模型"""
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_model(preferences) -> Optional["UserPreferencesInfo"]:
        """从数据库模型转换为Schema"""
        if not preferences:
            return None
        
        return UserPreferencesInfo(
            user_id=preferences.user_id,
            notification_enabled=preferences.notification_enabled,
            email_notification=preferences.email_notification,
            push_notification=preferences.push_notification,
            created_at=preferences.created_at,
            updated_at=preferences.updated_at
        )

    model_config = ConfigDict(from_attributes=True)


class UserDefaultRoleBase(BaseModel):
    """用户默认角色设置基础模型"""
    default_role: str = Field(..., description="默认角色名称")


class UserDefaultRoleCreate(UserDefaultRoleBase):
    """创建用户默认角色设置请求模型"""
    pass


class UserDefaultRoleUpdate(BaseModel):
    """更新用户默认角色设置请求模型"""
    default_role: str = Field(..., description="默认角色名称")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str = Field(..., min_length=8, description="当前密码")
    new_password: str = Field(..., min_length=8, description="新密码")
    confirm_password: str = Field(..., min_length=8, description="确认新密码")

    def validate_passwords_match(self) -> "ChangePasswordRequest":
        """验证新密码和确认密码是否一致"""
        if self.new_password != self.confirm_password:
            raise ValueError("新密码和确认密码不一致")
        if self.current_password == self.new_password:
            raise ValueError("新密码不能与当前密码相同")
        return self


class UserDefaultRoleInfo(UserDefaultRoleBase):
    """用户默认角色设置完整信息模型"""
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_model(default_role_setting) -> Optional["UserDefaultRoleInfo"]:
        """从数据库模型转换为Schema"""
        if not default_role_setting:
            return None
        
        return UserDefaultRoleInfo(
            user_id=default_role_setting.user_id,
            default_role=default_role_setting.default_role,
            created_at=default_role_setting.created_at,
            updated_at=default_role_setting.updated_at
        )

    model_config = ConfigDict(from_attributes=True)


class LoginHistoryBase(BaseModel):
    """登录历史基础模型"""
    ip_address: Optional[str] = Field(None, description="登录IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理信息")
    login_role: Optional[str] = Field(None, description="登录时使用的角色")
    location: Optional[str] = Field(None, description="登录地点")


class LoginHistoryCreate(LoginHistoryBase):
    """创建登录历史请求模型"""
    user_id: str = Field(..., description="用户ID")


class LoginHistoryInfo(LoginHistoryBase):
    """登录历史完整信息模型"""
    id: str
    user_id: str
    login_time: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_model(login_history) -> Optional["LoginHistoryInfo"]:
        """从数据库模型转换为Schema"""
        if not login_history:
            return None
        
        return LoginHistoryInfo(
            id=login_history.id,
            user_id=login_history.user_id,
            ip_address=login_history.ip_address,
            user_agent=login_history.user_agent,
            login_time=login_history.login_time,
            login_role=login_history.login_role,
            location=login_history.location,
            created_at=login_history.created_at,
            updated_at=login_history.updated_at
        )

    model_config = ConfigDict(from_attributes=True)


class UserProfileInfo(BaseModel):
    """用户个人中心完整信息模型"""
    user_id: str
    preferences: Optional[UserPreferencesInfo] = None
    default_role_setting: Optional[UserDefaultRoleInfo] = None
    recent_login_history: List[LoginHistoryInfo] = Field(default_factory=list, description="最近登录历史")

    @staticmethod
    def from_model(user, preferences=None, default_role_setting=None, recent_login_history=None) -> "UserProfileInfo":
        """从数据库模型转换为Schema"""
        return UserProfileInfo(
            user_id=user.id,
            preferences=UserPreferencesInfo.from_model(preferences) if preferences else None,
            default_role_setting=UserDefaultRoleInfo.from_model(default_role_setting) if default_role_setting else None,
            recent_login_history=[
                history_info
                for history in (recent_login_history or [])
                for history_info in [LoginHistoryInfo.from_model(history)]
                if history_info is not None
            ]
        )

    model_config = ConfigDict(from_attributes=True) 