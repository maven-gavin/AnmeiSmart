"""
用户服务 - 核心业务逻辑
处理用户CRUD、角色分配、个人资料管理等功能
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.identity_access.models.user import User, Role, Doctor, Consultant, Operator, Administrator
from app.identity_access.models.profile import UserPreferences, UserDefaultRole, LoginHistory
from app.identity_access.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse
from app.identity_access.schemas.profile import UserPreferencesCreate, UserPreferencesUpdate, ChangePasswordRequest
from app.core.password_utils import get_password_hash, verify_password
from app.core.api import BusinessException, ErrorCode

import logging
logger = logging.getLogger(__name__)
class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def create_user(self, user_in: UserCreate) -> User:
        """创建用户"""
        
        try:
            logger.info(f"[UserService] 开始创建用户: username={user_in.username}, email={user_in.email}")
            logger.debug(f"[UserService] 用户输入完整数据: {user_in.model_dump(exclude={'password'})}")
            
            # 1. 检查唯一性
            logger.debug(f"[UserService] 检查用户名唯一性: {user_in.username}")
            existing_user = self.get_by_username(user_in.username)
            if existing_user:
                logger.warning(f"[UserService] 用户名已存在: {user_in.username}")
                raise BusinessException("用户名已存在", code=ErrorCode.BUSINESS_ERROR)
            logger.debug(f"[UserService] 用户名唯一性检查通过")
            
            logger.debug(f"[UserService] 检查邮箱唯一性: {user_in.email}")
            existing_email = self.get_by_email(user_in.email)
            if existing_email:
                logger.warning(f"[UserService] 邮箱已存在: {user_in.email}")
                raise BusinessException("邮箱已存在", code=ErrorCode.BUSINESS_ERROR)
            logger.debug(f"[UserService] 邮箱唯一性检查通过")
            
            if user_in.phone:
                logger.debug(f"[UserService] 检查手机号唯一性: {user_in.phone}")
                existing_phone = self.get_by_phone(user_in.phone)
                if existing_phone:
                    logger.warning(f"[UserService] 手机号已存在: {user_in.phone}")
                    raise BusinessException("手机号已存在", code=ErrorCode.BUSINESS_ERROR)
                logger.debug(f"[UserService] 手机号唯一性检查通过")

            # 2. 准备用户数据（排除扩展信息字段）
            logger.debug(f"[UserService] 准备用户数据")
            # 排除 roles, password 和所有扩展信息字段
            # 扩展信息由对应的业务模块（如客户管理）后续补充，不在创建用户时处理
            exclude_fields = {
                "roles", "password", 
                "customer_info", "doctor_info", "consultant_info", 
                "operator_info", "administrator_info"
            }
            user_data = user_in.model_dump(exclude=exclude_fields)
            logger.debug(f"[UserService] 用户数据（排除密码、角色和扩展信息）: {user_data}")
            
            logger.debug(f"[UserService] 生成密码哈希")
            user_data["hashed_password"] = get_password_hash(user_in.password)
            logger.debug(f"[UserService] 密码哈希生成完成")
            
            # 3. 创建用户实例
            logger.debug(f"[UserService] 创建User实例")
            user = User(**user_data)
            logger.debug(f"[UserService] User实例创建成功: user_id={user.id if hasattr(user, 'id') else 'N/A'}")
            
            # 4. 处理角色
            if user_in.roles:
                logger.info(f"[UserService] 处理用户角色: {user_in.roles}")
                for role_name in user_in.roles:
                    logger.debug(f"[UserService] 查找角色: {role_name}")
                    role = self.db.query(Role).filter(Role.name == role_name).first()
                    if role:
                        logger.debug(f"[UserService] 找到角色: {role_name} (id={role.id})")
                        user.roles.append(role)
                        logger.debug(f"[UserService] 角色已添加到用户: {role_name}")
                    else:
                        logger.error(f"[UserService] 角色不存在: {role_name}")
                        raise BusinessException(f"角色 '{role_name}' 不存在", code=ErrorCode.NOT_FOUND)
            else:
                logger.debug(f"[UserService] 用户没有指定角色")
            
            # 5. 保存用户
            logger.debug(f"[UserService] 添加用户到数据库会话")
            self.db.add(user)
            logger.debug(f"[UserService] 提交数据库事务")
            self.db.commit()
            logger.debug(f"[UserService] 刷新用户对象")
            self.db.refresh(user)
            logger.info(f"[UserService] 用户创建成功: user_id={user.id}, username={user.username}")
            # 注意：扩展信息（如客户信息、医生信息等）由对应的业务模块后续补充
            return user
        except BusinessException:
            logger.warning(f"[UserService] 业务异常: 创建用户失败")
            raise
        except Exception as e:
            logger.error(f"[UserService] 创建用户时发生未预期错误: {str(e)}", exc_info=True)
            raise

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
            raise BusinessException("用户不存在", code=ErrorCode.NOT_FOUND)

        # 检查唯一性冲突
        if user_data.username and user_data.username != user.username:
            if self.get_by_username(user_data.username):
                raise BusinessException("用户名已存在", code=ErrorCode.BUSINESS_ERROR)
                
        if user_data.email and user_data.email != user.email:
            if self.get_by_email(user_data.email):
                raise BusinessException("邮箱已存在", code=ErrorCode.BUSINESS_ERROR)

        if user_data.phone and user_data.phone != user.phone:
            if self.get_by_phone(user_data.phone):
                    raise BusinessException("手机号已存在", code=ErrorCode.BUSINESS_ERROR)

        # 更新字段
        update_dict = user_data.model_dump(exclude_unset=True, exclude={"roles", "password"})
        logger.info(f"[UserService] 更新字段: {update_dict}")
        for field, value in update_dict.items():
            logger.info(f"[UserService] 设置字段 {field} = {value} (类型: {type(value)})")
            setattr(user, field, value)
            logger.info(f"[UserService] 设置后 user.{field} = {getattr(user, field)}")
            
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
                    raise BusinessException(f"角色 '{role_name}' 不存在", code=ErrorCode.NOT_FOUND)

        self.db.commit()
        logger.info(f"[UserService] 数据库提交成功，刷新前 user.is_active = {user.is_active}")
        self.db.refresh(user)
        logger.info(f"[UserService] 刷新后 user.is_active = {user.is_active}")
        return user

    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.NOT_FOUND)
            
        self.db.delete(user)
        self.db.commit()
        return True

    def _build_users_query(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ):
        """构建用户查询，用于复用查询逻辑"""
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
        
        return query

    async def count_users(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """统计用户总数（应用筛选条件后）"""
        query = self._build_users_query(search=search, role=role, is_active=is_active)
        # 如果有关联查询（如role），需要去重
        if role:
            return query.distinct().count()
        return query.count()

    async def get_users_list(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """获取用户列表"""
        query = self._build_users_query(search=search, role=role, is_active=is_active)
        # 如果有关联查询（如role），需要去重
        if role:
            query = query.distinct()
        users = query.order_by(User.updated_at.desc()).offset(skip).limit(limit).all()
        # 记录查询返回的用户状态
        for user in users:
            logger.info(f"[UserService] 查询返回用户: {user.id[:20]}... | username={user.username} | is_active={user.is_active} (类型: {type(user.is_active)})")
        return users

    async def change_password(self, user_id: str, password_data: ChangePasswordRequest) -> bool:
        """修改密码"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.NOT_FOUND)
            
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
            raise BusinessException("用户不存在", code=ErrorCode.NOT_FOUND)
            
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


