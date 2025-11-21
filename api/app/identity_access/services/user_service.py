"""
用户服务 - 核心业务逻辑
处理用户CRUD、角色分配、个人资料管理等功能
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.identity_access.models.user import User, Role
from app.identity_access.models.profile import UserPreferences, UserDefaultRole, LoginHistory
from app.identity_access.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse
from app.identity_access.schemas.profile import UserPreferencesCreate, UserPreferencesUpdate, ChangePasswordRequest
from app.core.password_utils import get_password_hash, verify_password
from app.core.api import BusinessException, ErrorCode

class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def create_user(self, user_in: UserCreate) -> User:
        """创建用户"""
        # 1. 检查唯一性
        if self.get_by_username(user_in.username):
            raise BusinessException("用户名已存在", code=ErrorCode.RESOURCE_ALREADY_EXISTS)
        
        if self.get_by_email(user_in.email):
            raise BusinessException("邮箱已存在", code=ErrorCode.RESOURCE_ALREADY_EXISTS)
            
        if user_in.phone and self.get_by_phone(user_in.phone):
            raise BusinessException("手机号已存在", code=ErrorCode.RESOURCE_ALREADY_EXISTS)

        # 2. 准备用户数据
        user_data = user_in.model_dump(exclude={"roles", "password"})
        user_data["hashed_password"] = get_password_hash(user_in.password)
        
        # 3. 创建用户实例
        user = User(**user_data)
        
        # 4. 处理角色
        if user_in.roles:
            for role_name in user_in.roles:
                role = self.db.query(Role).filter(Role.name == role_name).first()
                if role:
                    user.roles.append(role)
                else:
                    # 如果角色不存在，是否报错？通常应该报错
                    raise BusinessException(f"角色 '{role_name}' 不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        return self.db.query(User).filter(User.phone == phone).first()

    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """更新用户"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)

        # 检查唯一性冲突
        if user_data.username and user_data.username != user.username:
            if self.get_by_username(user_data.username):
                raise BusinessException("用户名已存在", code=ErrorCode.RESOURCE_ALREADY_EXISTS)
                
        if user_data.email and user_data.email != user.email:
            if self.get_by_email(user_data.email):
                raise BusinessException("邮箱已存在", code=ErrorCode.RESOURCE_ALREADY_EXISTS)

        if user_data.phone and user_data.phone != user.phone:
            if self.get_by_phone(user_data.phone):
                raise BusinessException("手机号已存在", code=ErrorCode.RESOURCE_ALREADY_EXISTS)

        # 更新字段
        update_dict = user_data.model_dump(exclude_unset=True, exclude={"roles", "password"})
        for field, value in update_dict.items():
            setattr(user, field, value)
            
        # 如果有密码更新
        if user_data.password:
            user.hashed_password = get_password_hash(user_data.password)

        # 如果有角色更新
        if user_data.roles is not None:
            # 清空现有角色并重新分配
            user.roles = []
            for role_name in user_data.roles:
                role = self.db.query(Role).filter(Role.name == role_name).first()
                if role:
                    user.roles.append(role)
                else:
                    raise BusinessException(f"角色 '{role_name}' 不存在", code=ErrorCode.RESOURCE_NOT_FOUND)

        self.db.commit()
        self.db.refresh(user)
        return user

    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
            
        self.db.delete(user)
        self.db.commit()
        return True

    async def get_users_list(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """获取用户列表"""
        query = self.db.query(User)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
            
        if role:
            query = query.join(User.roles).filter(Role.name == role)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.phone.ilike(search_term)
                )
            )
            
        return query.order_by(User.updated_at.desc()).offset(skip).limit(limit).all()

    async def change_password(self, user_id: str, password_data: ChangePasswordRequest) -> bool:
        """修改密码"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
            
        if not verify_password(password_data.current_password, user.hashed_password):
            raise BusinessException("当前密码错误", code=ErrorCode.INVALID_CREDENTIALS)
            
        user.hashed_password = get_password_hash(password_data.new_password)
        self.db.commit()
        return True

    # 偏好设置相关
    async def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        return self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()

    async def update_user_preferences(self, user_id: str, preferences_data: UserPreferencesUpdate) -> UserPreferences:
        preferences = await self.get_user_preferences(user_id)
        if not preferences:
            # 如果不存在则创建
            preferences = UserPreferences(user_id=user_id)
            self.db.add(preferences)
            
        update_dict = preferences_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(preferences, field, value)
            
        preferences.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(preferences)
        return preferences
        
    # 默认角色相关
    async def get_user_default_role(self, user_id: str) -> Optional[str]:
        setting = self.db.query(UserDefaultRole).filter(UserDefaultRole.user_id == user_id).first()
        return setting.default_role if setting else None
        
    async def set_user_default_role(self, user_id: str, role_name: str) -> UserDefaultRole:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
            
        # 验证用户是否拥有该角色
        user_role_names = [r.name for r in user.roles]
        if role_name not in user_role_names:
             raise BusinessException(f"用户未拥有角色 '{role_name}'", code=ErrorCode.PERMISSION_DENIED)
             
        setting = self.db.query(UserDefaultRole).filter(UserDefaultRole.user_id == user_id).first()
        if setting:
            setting.default_role = role_name
            setting.updated_at = datetime.now()
        else:
            setting = UserDefaultRole(user_id=user_id, default_role=role_name)
            self.db.add(setting)
            
        self.db.commit()
        self.db.refresh(setting)
        return setting


