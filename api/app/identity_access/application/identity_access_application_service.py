"""
用户身份与权限应用服务

统一的应用服务，编排领域服务完成业务用例。
遵循DDD统一应用服务模式，简化开发者体验。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.identity_access.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse
from app.identity_access.schemas.token import Token, RefreshTokenRequest
from app.identity_access.schemas.profile import (
    LoginHistoryCreate, UserPreferencesInfo, UserPreferencesCreate, UserPreferencesUpdate,
    UserDefaultRoleInfo, UserDefaultRoleUpdate, LoginHistoryInfo, UserProfileInfo, ChangePasswordRequest
)

from ..interfaces.application_service_interfaces import IIdentityAccessApplicationService
from ..interfaces.repository_interfaces import IUserRepository, IRoleRepository, ILoginHistoryRepository
from ..interfaces.domain_service_interfaces import IUserDomainService, IAuthenticationDomainService, IPermissionDomainService
from ..converters.user_converter import UserConverter
from ..converters.role_converter import RoleConverter

logger = logging.getLogger(__name__)


class IdentityAccessApplicationService(IIdentityAccessApplicationService):
    """用户身份与权限应用服务 - 统一应用服务模式"""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        role_repository: IRoleRepository,
        login_history_repository: ILoginHistoryRepository,
        user_domain_service: IUserDomainService,
        authentication_domain_service: IAuthenticationDomainService,
        permission_domain_service: IPermissionDomainService
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.login_history_repository = login_history_repository
        self.user_domain_service = user_domain_service
        self.authentication_domain_service = authentication_domain_service
        self.permission_domain_service = permission_domain_service
    
    # 用户管理用例
    async def create_user_use_case(
        self,
        user_data: UserCreate
    ) -> UserResponse:
        """创建用户用例"""
        try:
            # 调用领域服务创建用户
            user = await self.user_domain_service.create_user(
                username=user_data.username,
                email=user_data.email,
                password=user_data.password,
                phone=user_data.phone,
                avatar=user_data.avatar,
                roles=user_data.roles
            )
            
            # 转换为响应格式
            return UserConverter.to_response(user)
            
        except ValueError as e:
            logger.warning(f"创建用户失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"创建用户异常: {str(e)}", exc_info=True)
            raise
    
    async def get_user_by_id_use_case(self, user_id: str) -> Optional[UserResponse]:
        """根据ID获取用户用例"""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return None
            
            # 获取用户默认角色
            active_role = await self._get_user_default_role(user_id)
            
            return UserConverter.to_response(user, active_role)
            
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}", exc_info=True)
            raise
    
    async def get_user_by_email_use_case(self, email: str) -> Optional[UserResponse]:
        """根据邮箱获取用户用例"""
        try:
            user = await self.user_repository.get_by_email(email)
            if not user:
                return None
            
            return UserConverter.to_response(user)
            
        except Exception as e:
            logger.error(f"根据邮箱获取用户失败: {str(e)}", exc_info=True)
            raise
    
    async def update_user_use_case(
        self,
        user_id: str,
        user_data: UserUpdate
    ) -> UserResponse:
        """更新用户用例"""
        try:
            # 准备更新数据
            updates = {}
            if user_data.username is not None:
                updates["username"] = user_data.username
            if user_data.phone is not None:
                updates["phone"] = user_data.phone
            if user_data.avatar is not None:
                updates["avatar"] = user_data.avatar
            
            # 调用领域服务更新用户
            user = await self.user_domain_service.update_user_profile(user_id, updates)
            
            return UserConverter.to_response(user)
            
        except ValueError as e:
            logger.warning(f"更新用户失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"更新用户异常: {str(e)}", exc_info=True)
            raise
    
    async def delete_user_use_case(self, user_id: str) -> bool:
        """删除用户用例"""
        try:
            return await self.user_repository.delete(user_id)
            
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}", exc_info=True)
            raise
    
    async def get_users_list_use_case(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UserResponse]:
        """获取用户列表用例"""
        try:
            users = await self.user_repository.get_multi(skip=skip, limit=limit, filters=filters)
            return UserConverter.to_list_response(users)
            
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}", exc_info=True)
            raise
    
    # 认证用例
    async def login_use_case(
        self,
        username_or_email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Token:
        """用户登录用例"""
        try:
            # 认证用户
            user = await self.authentication_domain_service.authenticate_user(
                username_or_email, password
            )
            
            if not user:
                raise ValueError("用户名或密码错误")
            
            # 记录登录历史
            primary_role = user.get_primary_role()
            await self.authentication_domain_service.record_login(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                login_role=primary_role
            )
            
            # 生成令牌
            token_data = await self._generate_tokens(user.id, primary_role)
            
            return Token(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type="bearer"
            )
            
        except ValueError as e:
            logger.warning(f"用户登录失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"用户登录异常: {str(e)}", exc_info=True)
            raise
    
    async def refresh_token_use_case(
        self,
        refresh_token_request: RefreshTokenRequest
    ) -> Token:
        """刷新令牌用例"""
        try:
            # 调用领域服务刷新令牌
            token_data = await self.authentication_domain_service.refresh_token(
                refresh_token_request.token
            )
            
            if not token_data:
                raise ValueError("无效的刷新令牌")
            
            return Token(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type="bearer"
            )
            
        except ValueError as e:
            logger.warning(f"刷新令牌失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"刷新令牌异常: {str(e)}", exc_info=True)
            raise
    
    async def logout_use_case(self, token: str) -> bool:
        """用户登出用例"""
        try:
            return await self.authentication_domain_service.revoke_token(token)
            
        except Exception as e:
            logger.error(f"用户登出失败: {str(e)}", exc_info=True)
            raise
    
    # 权限管理用例
    async def get_user_roles_use_case(self, user_id: str) -> List[str]:
        """获取用户角色用例"""
        try:
            return await self.permission_domain_service.get_user_roles(user_id)
            
        except Exception as e:
            logger.error(f"获取用户角色失败: {str(e)}", exc_info=True)
            raise
    
    async def switch_role_use_case(
        self,
        user_id: str,
        target_role: str
    ) -> Token:
        """切换用户角色用例"""
        try:
            # 验证用户是否有目标角色
            if not await self.permission_domain_service.check_user_role(user_id, target_role):
                raise ValueError(f"用户没有 '{target_role}' 角色权限")
            
            # 切换角色
            success = await self.permission_domain_service.switch_user_role(user_id, target_role)
            if not success:
                raise ValueError("角色切换失败")
            
            # 生成新令牌
            token_data = await self._generate_tokens(user_id, target_role)
            
            return Token(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type="bearer"
            )
            
        except ValueError as e:
            logger.warning(f"切换角色失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"切换角色异常: {str(e)}", exc_info=True)
            raise
    
    async def check_permission_use_case(
        self,
        user_id: str,
        permission: str
    ) -> bool:
        """检查用户权限用例"""
        try:
            return await self.permission_domain_service.check_user_permission(user_id, permission)
            
        except Exception as e:
            logger.error(f"检查权限失败: {str(e)}", exc_info=True)
            raise
    
    # 角色管理用例
    async def get_all_roles_use_case(self) -> List[RoleResponse]:
        """获取所有角色用例"""
        try:
            roles = await self.role_repository.get_all()
            return RoleConverter.to_list_response(roles)
            
        except Exception as e:
            logger.error(f"获取角色列表失败: {str(e)}", exc_info=True)
            raise
    
    async def create_role_use_case(
        self,
        name: str,
        description: Optional[str] = None
    ) -> RoleResponse:
        """创建角色用例"""
        try:
            from ..domain.entities.role import Role
            
            role = Role.create(name=name, description=description)
            saved_role = await self.role_repository.save(role)
            
            return RoleConverter.to_response(saved_role)
            
        except ValueError as e:
            logger.warning(f"创建角色失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"创建角色异常: {str(e)}", exc_info=True)
            raise
    
    async def assign_role_to_user_use_case(
        self,
        user_id: str,
        role_name: str
    ) -> bool:
        """分配角色给用户用例"""
        try:
            return await self.user_domain_service.assign_roles(user_id, [role_name])
            
        except ValueError as e:
            logger.warning(f"分配角色失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"分配角色异常: {str(e)}", exc_info=True)
            raise
    
    async def remove_role_from_user_use_case(
        self,
        user_id: str,
        role_name: str
    ) -> bool:
        """移除用户角色用例"""
        try:
            return await self.user_domain_service.remove_roles(user_id, [role_name])
            
        except ValueError as e:
            logger.warning(f"移除角色失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"移除角色异常: {str(e)}", exc_info=True)
            raise
    
    # 登录历史用例
    async def create_login_history_use_case(
        self,
        login_data: LoginHistoryCreate
    ) -> bool:
        """创建登录历史用例"""
        try:
            from ..domain.value_objects.login_history import LoginHistory
            
            login_history = LoginHistory.create(
                user_id=login_data.user_id,
                ip_address=login_data.ip_address,
                user_agent=login_data.user_agent,
                login_role=login_data.login_role,
                location=login_data.location
            )
            
            await self.login_history_repository.create(login_history)
            return True
            
        except Exception as e:
            logger.error(f"创建登录历史失败: {str(e)}", exc_info=True)
            raise
    
    async def get_user_login_history_use_case(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取用户登录历史用例"""
        try:
            login_histories = await self.login_history_repository.get_user_login_history(
                user_id=user_id, limit=limit
            )
            
            return [
                {
                    "id": history.user_id,
                    "ip_address": history.ip_address,
                    "user_agent": history.user_agent,
                    "login_role": history.login_role,
                    "location": history.location,
                    "login_time": history.login_time.isoformat()
                }
                for history in login_histories
            ]
            
        except Exception as e:
            logger.error(f"获取登录历史失败: {str(e)}", exc_info=True)
            raise
    
    # 私有辅助方法
    async def _generate_tokens(self, user_id: str, active_role: Optional[str]) -> Dict[str, str]:
        """生成访问令牌和刷新令牌"""
        try:
            # 延迟导入避免循环依赖
            from app.core.security import create_access_token, create_refresh_token
            from app.core.config import get_settings
            
            settings = get_settings()
            
            # 创建访问令牌
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                subject=user_id,
                expires_delta=access_token_expires,
                active_role=active_role
            )
            
            # 创建刷新令牌
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            refresh_token = create_refresh_token(
                subject=user_id,
                expires_delta=refresh_token_expires,
                active_role=active_role
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token
            }
            
        except Exception as e:
            logger.error(f"生成令牌失败: {str(e)}", exc_info=True)
            raise
    
    async def _get_user_default_role(self, user_id: str) -> Optional[str]:
        """获取用户默认角色"""
        try:
            # 通过用户仓储获取用户默认角色设置
            default_role_setting = await self.user_repository.get_user_default_role(user_id)
            
            if default_role_setting and default_role_setting.get("default_role"):
                return default_role_setting["default_role"]
            
            return None
            
        except Exception as e:
            logger.warning(f"获取用户默认角色失败: {str(e)}")
            return None
    
    # 个人中心用例
    async def get_user_profile_use_case(self, user_id: str) -> UserProfileInfo:
        """获取用户完整个人中心信息用例"""
        try:
            # 获取用户基本信息
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise ValueError("用户不存在")
            
            # 获取用户偏好设置
            preferences = await self._get_user_preferences(user_id)
            
            # 获取用户默认角色设置
            default_role_setting = await self._get_user_default_role_setting(user_id)
            
            # 获取最近登录历史
            recent_login_history = await self.get_user_login_history_use_case(user_id, limit=5)
            
            # 构建用户个人中心信息
            return UserProfileInfo(
                user_id=user_id,
                username=user.username,
                email=user.get_email_value(),
                phone=user.phone,
                avatar=user.avatar,
                is_active=user.status.to_bool(),
                created_at=user.created_at,
                updated_at=user.updated_at,
                roles=list(user.roles),
                preferences=preferences,
                default_role_setting=default_role_setting,
                recent_login_history=[
                    LoginHistoryInfo(
                        id=history["id"],
                        user_id=user_id,
                        ip_address=history["ip_address"],
                        user_agent=history["user_agent"],
                        login_role=history["login_role"],
                        location=history["location"],
                        login_time=datetime.fromisoformat(history["login_time"].replace('Z', '+00:00'))
                    )
                    for history in recent_login_history
                ]
            )
            
        except ValueError as e:
            logger.warning(f"获取用户个人中心信息失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"获取用户个人中心信息异常: {str(e)}", exc_info=True)
            raise
    
    async def get_user_preferences_use_case(self, user_id: str) -> Optional[UserPreferencesInfo]:
        """获取用户偏好设置用例"""
        try:
            return await self._get_user_preferences(user_id)
        except Exception as e:
            logger.error(f"获取用户偏好设置失败: {str(e)}", exc_info=True)
            raise
    
    async def create_user_preferences_use_case(
        self,
        user_id: str,
        preferences_data: UserPreferencesCreate
    ) -> UserPreferencesInfo:
        """创建用户偏好设置用例"""
        try:
            # 延迟导入避免循环依赖
            from app.identity_access.infrastructure.db.profile import UserPreferences
            from app.common.infrastructure.db.base import get_db
            
            db = next(get_db())
            
            # 检查用户是否存在
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise ValueError("用户不存在")
            
            # 创建偏好设置
            preferences = UserPreferences(
                user_id=user_id,
                notification_enabled=preferences_data.notification_enabled,
                email_notification=preferences_data.email_notification,
                push_notification=preferences_data.push_notification,
                language=preferences_data.language,
                timezone=preferences_data.timezone
            )
            
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
            
            return UserPreferencesInfo.from_model(preferences)
            
        except ValueError as e:
            logger.warning(f"创建用户偏好设置失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"创建用户偏好设置异常: {str(e)}", exc_info=True)
            raise
    
    async def update_user_preferences_use_case(
        self,
        user_id: str,
        preferences_data: UserPreferencesUpdate
    ) -> UserPreferencesInfo:
        """更新用户偏好设置用例"""
        try:
            # 延迟导入避免循环依赖
            from app.identity_access.infrastructure.db.profile import UserPreferences
            from app.common.infrastructure.db.base import get_db
            
            db = next(get_db())
            
            # 获取现有偏好设置
            preferences = db.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()
            
            if not preferences:
                raise ValueError("用户偏好设置不存在")
            
            # 更新偏好设置
            update_data = preferences_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(preferences, key, value)
            
            preferences.updated_at = datetime.now()
            
            db.commit()
            db.refresh(preferences)
            
            return UserPreferencesInfo.from_model(preferences)
            
        except ValueError as e:
            logger.warning(f"更新用户偏好设置失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"更新用户偏好设置异常: {str(e)}", exc_info=True)
            raise
    
    async def get_user_default_role_setting_use_case(self, user_id: str) -> Optional[UserDefaultRoleInfo]:
        """获取用户默认角色设置用例"""
        try:
            return await self._get_user_default_role_setting(user_id)
        except Exception as e:
            logger.error(f"获取用户默认角色设置失败: {str(e)}", exc_info=True)
            raise
    
    async def set_user_default_role_use_case(
        self,
        user_id: str,
        default_role_data: UserDefaultRoleUpdate
    ) -> UserDefaultRoleInfo:
        """设置用户默认角色用例"""
        try:
            # 延迟导入避免循环依赖
            from app.identity_access.infrastructure.db.profile import UserDefaultRole
            from app.common.infrastructure.db.base import get_db
            
            db = next(get_db())
            
            # 检查用户是否存在
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise ValueError("用户不存在")
            
            # 验证用户是否拥有该角色
            if default_role_data.default_role not in user.roles:
                raise ValueError(f"用户没有'{default_role_data.default_role}'角色权限")
            
            # 查找或创建默认角色设置
            default_role_setting = db.query(UserDefaultRole).filter(
                UserDefaultRole.user_id == user_id
            ).first()
            
            if default_role_setting:
                # 更新现有设置
                default_role_setting.default_role = default_role_data.default_role
                default_role_setting.updated_at = datetime.now()
            else:
                # 创建新设置
                default_role_setting = UserDefaultRole(
                    user_id=user_id,
                    default_role=default_role_data.default_role
                )
                db.add(default_role_setting)
            
            db.commit()
            db.refresh(default_role_setting)
            
            return UserDefaultRoleInfo.from_model(default_role_setting)
            
        except ValueError as e:
            logger.warning(f"设置用户默认角色失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"设置用户默认角色异常: {str(e)}", exc_info=True)
            raise
    
    async def change_password_use_case(
        self,
        user_id: str,
        password_data: ChangePasswordRequest
    ) -> bool:
        """修改用户密码用例"""
        try:
            # 延迟导入避免循环依赖
            from app.core.password_utils import verify_password, get_password_hash
            from app.common.infrastructure.db.base import get_db
            
            db = next(get_db())
            
            # 获取用户
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise ValueError("用户不存在")
            
            # 验证当前密码
            if not verify_password(password_data.current_password, user.get_password_hash()):
                raise ValueError("当前密码错误")
            
            # 更新密码
            new_password_hash = get_password_hash(password_data.new_password)
            await self.user_repository.update_password(user_id, new_password_hash)
            
            return True
            
        except ValueError as e:
            logger.warning(f"修改用户密码失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"修改用户密码异常: {str(e)}", exc_info=True)
            raise
    
    async def should_apply_default_role_use_case(self, user_id: str) -> Optional[str]:
        """检查是否应该应用默认角色用例"""
        try:
            # 延迟导入避免循环依赖
            from app.identity_access.infrastructure.db.profile import LoginHistory, UserDefaultRole
            from app.common.infrastructure.db.base import get_db
            
            db = next(get_db())
            
            # 获取用户的登录历史数量
            login_count = db.query(LoginHistory).filter(
                LoginHistory.user_id == user_id
            ).count()
            
            # 如果是首次登录（没有历史记录），检查是否设置了默认角色
            if login_count == 0:
                default_role_setting = db.query(UserDefaultRole).filter(
                    UserDefaultRole.user_id == user_id
                ).first()
                if default_role_setting:
                    return default_role_setting.default_role
            
            return None
            
        except Exception as e:
            logger.error(f"检查默认角色应用失败: {str(e)}", exc_info=True)
            raise
    
    # 私有辅助方法
    async def _get_user_preferences(self, user_id: str) -> Optional[UserPreferencesInfo]:
        """获取用户偏好设置"""
        try:
            # 通过用户仓储获取用户偏好设置
            preferences_data = await self.user_repository.get_user_preferences(user_id)
            
            if not preferences_data:
                return None
            
            return UserPreferencesInfo(
                id=preferences_data["id"],
                user_id=preferences_data["user_id"],
                notification_enabled=preferences_data["notification_enabled"],
                email_notification=preferences_data["email_notification"],
                push_notification=preferences_data["push_notification"],
                language=preferences_data["language"],
                timezone=preferences_data["timezone"],
                created_at=preferences_data["created_at"],
                updated_at=preferences_data["updated_at"]
            )
            
        except Exception as e:
            logger.warning(f"获取用户偏好设置失败: {str(e)}")
            return None
    
    async def _get_user_default_role_setting(self, user_id: str) -> Optional[UserDefaultRoleInfo]:
        """获取用户默认角色设置"""
        try:
            # 通过用户仓储获取用户默认角色设置
            default_role_data = await self.user_repository.get_user_default_role(user_id)
            
            if not default_role_data:
                return None
            
            return UserDefaultRoleInfo(
                id=default_role_data["id"],
                user_id=default_role_data["user_id"],
                default_role=default_role_data["default_role"],
                created_at=default_role_data["created_at"],
                updated_at=default_role_data["updated_at"]
            )
            
        except Exception as e:
            logger.warning(f"获取用户默认角色设置失败: {str(e)}")
            return None
