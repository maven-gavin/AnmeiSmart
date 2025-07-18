from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from app.db.models.user import User
from app.db.models.profile import UserPreferences, UserDefaultRole, LoginHistory
from app.schemas.profile import (
    UserPreferencesInfo, UserPreferencesCreate, UserPreferencesUpdate,
    UserDefaultRoleInfo, UserDefaultRoleCreate, UserDefaultRoleUpdate,
    LoginHistoryInfo, LoginHistoryCreate,
    UserProfileInfo, ChangePasswordRequest
)
from app.core.password_utils import verify_password, get_password_hash


class ProfileService:
    """个人中心服务类，处理用户偏好、默认角色、登录历史相关业务逻辑"""

    @staticmethod
    async def get_user_preferences(db: Session, user_id: str) -> Optional[UserPreferencesInfo]:
        """获取用户偏好设置"""
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        return UserPreferencesInfo.from_model(preferences)

    @staticmethod
    async def create_user_preferences(
        db: Session, 
        user_id: str, 
        preferences_data: UserPreferencesCreate
    ) -> UserPreferencesInfo:
        """创建用户偏好设置"""
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查是否已存在偏好设置
        existing_preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        if existing_preferences:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户偏好设置已存在"
            )
        
        # 创建新的偏好设置
        db_preferences = UserPreferences(
            user_id=user_id,
            **preferences_data.model_dump()
        )
        
        db.add(db_preferences)
        db.commit()
        db.refresh(db_preferences)
        
        result = UserPreferencesInfo.from_model(db_preferences)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建用户偏好设置失败"
            )
        return result

    @staticmethod
    async def update_user_preferences(
        db: Session,
        user_id: str, 
        preferences_data: UserPreferencesUpdate
    ) -> UserPreferencesInfo:
        """更新用户偏好设置"""
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            # 如果不存在，创建默认偏好设置
            default_preferences = UserPreferencesCreate()
            return await ProfileService.create_user_preferences(
                db, user_id, default_preferences
            )
        
        # 更新偏好设置
        update_data = preferences_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(preferences, field):
                setattr(preferences, field, value)
        
        preferences.updated_at = datetime.now()
        db.commit()
        db.refresh(preferences)
        
        result = UserPreferencesInfo.from_model(preferences)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户偏好设置失败"
            )
        return result

    @staticmethod
    async def get_user_default_role(db: Session, user_id: str) -> Optional[UserDefaultRoleInfo]:
        """获取用户默认角色设置"""
        default_role_setting = db.query(UserDefaultRole).filter(
            UserDefaultRole.user_id == user_id
        ).first()
        
        return UserDefaultRoleInfo.from_model(default_role_setting)

    @staticmethod
    async def set_user_default_role(
        db: Session, 
        user_id: str, 
        default_role_data: UserDefaultRoleUpdate
    ) -> UserDefaultRoleInfo:
        """设置用户默认角色"""
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证用户是否拥有该角色
        user_roles = [role.name for role in user.roles]
        if default_role_data.default_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"用户没有'{default_role_data.default_role}'角色权限"
            )
        
        # 查找或创建默认角色设置
        default_role_setting = db.query(UserDefaultRole).filter(
            UserDefaultRole.user_id == user_id
        ).first()
        
        if default_role_setting:
            # 更新现有设置
            setattr(default_role_setting, 'default_role', default_role_data.default_role)
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
        
        result = UserDefaultRoleInfo.from_model(default_role_setting)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="无法创建默认角色设置"
            )
        return result

    @staticmethod
    async def create_login_history(
        db: Session,
        login_data: LoginHistoryCreate
    ) -> LoginHistoryInfo:
        """创建登录历史记录"""
        # 检查用户是否存在
        user = db.query(User).filter(User.id == login_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 创建登录历史记录
        db_login_history = LoginHistory(
            **login_data.model_dump()
        )
        
        db.add(db_login_history)
        db.commit()
        db.refresh(db_login_history)
        
        result = LoginHistoryInfo.from_model(db_login_history)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="无法创建登录历史记录"
            )
        return result

    @staticmethod
    async def get_user_login_history(
        db: Session, 
        user_id: str, 
        limit: int = 10
    ) -> List[LoginHistoryInfo]:
        """获取用户登录历史"""
        login_histories = db.query(LoginHistory).filter(
            LoginHistory.user_id == user_id
        ).order_by(desc(LoginHistory.login_time)).limit(limit).all()
        
        return [
            result 
            for history in login_histories
            if (result := LoginHistoryInfo.from_model(history)) is not None
        ]
    @staticmethod
    async def get_user_profile(db: Session, user_id: str) -> UserProfileInfo:
        """获取用户完整的个人中心信息"""
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
            
        # 获取各项信息
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        default_role_setting = db.query(UserDefaultRole).filter(
            UserDefaultRole.user_id == user_id
        ).first()
        
        recent_login_history = db.query(LoginHistory).filter(
            LoginHistory.user_id == user_id
        ).order_by(desc(LoginHistory.login_time)).limit(5).all()
        
        result = UserProfileInfo.from_model(
            user=user,
            preferences=preferences,
            default_role_setting=default_role_setting,
            recent_login_history=recent_login_history
        )
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="无法获取用户信息"
            )
        return result
        # 获取各项信息
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        default_role_setting = db.query(UserDefaultRole).filter(
            UserDefaultRole.user_id == user_id
        ).first()
        
        recent_login_history = db.query(LoginHistory).filter(
            LoginHistory.user_id == user_id
        ).order_by(desc(LoginHistory.login_time)).limit(5).all()
        
        result = UserProfileInfo.from_model(
            user=user,
            preferences=preferences,
            default_role_setting=default_role_setting,
            recent_login_history=recent_login_history
        )
            
    @staticmethod
    async def should_apply_default_role(db: Session, user_id: str) -> Optional[str]:
        """检查是否应该应用默认角色（首次登录逻辑）"""
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
                return str(default_role_setting.default_role)
        
        return None

    @staticmethod
    async def change_password(
        db: Session, 
        user_id: str, 
        password_data: ChangePasswordRequest
    ) -> bool:
        """修改用户密码"""
        # 验证密码格式
        try:
            password_data.validate_passwords_match()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # 获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        # 验证当前密码
        if not verify_password(password_data.current_password, str(user.hashed_password)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        # 更新密码
        setattr(user, 'hashed_password', get_password_hash(password_data.new_password))
        setattr(user, 'updated_at', datetime.now())
        
        db.commit()
        return True


# 创建服务实例
profile_service = ProfileService() 