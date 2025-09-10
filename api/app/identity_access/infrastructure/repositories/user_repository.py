"""
用户仓储实现

实现用户数据访问的具体逻辑。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.identity_access.domain.entities.user import User
from app.identity_access.domain.entities.role import Role
from app.identity_access.infrastructure.db.profile import UserDefaultRole, UserPreferences
from app.identity_access.infrastructure.db.user import User as UserModel, Role as RoleModel
from ...interfaces.repository_interfaces import IUserRepository
from ...interfaces.converter_interfaces import IUserConverter


class UserRepository(IUserRepository):
    """用户仓储实现"""
    
    def __init__(self, db: Session, user_converter: IUserConverter):
        self.db = db
        self.user_converter = user_converter
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user_model:
            return None
        
        return self.user_converter.from_model(user_model)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        user_model = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not user_model:
            return None
        
        return self.user_converter.from_model(user_model)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        user_model = self.db.query(UserModel).filter(UserModel.username == username).first()
        if not user_model:
            return None
        
        return self.user_converter.from_model(user_model)
    
    async def get_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        user_model = self.db.query(UserModel).filter(UserModel.phone == phone).first()
        if not user_model:
            return None
        
        return self.user_converter.from_model(user_model)
    
    async def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否存在"""
        return self.db.query(UserModel).filter(UserModel.email == email).first() is not None
    
    async def exists_by_username(self, username: str) -> bool:
        """检查用户名是否存在"""
        return self.db.query(UserModel).filter(UserModel.username == username).first() is not None
    
    async def exists_by_phone(self, phone: str) -> bool:
        """检查手机号是否存在"""
        return self.db.query(UserModel).filter(UserModel.phone == phone).first() is not None
    
    async def save(self, user: User) -> User:
        """保存用户"""
        # 检查用户是否存在
        existing_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        
        if existing_user:
            # 更新现有用户
            user_dict = self.user_converter.to_model_dict(user)
            for key, value in user_dict.items():
                if key != "id":  # 不更新ID
                    setattr(existing_user, key, value)
            
            # 更新角色关联
            await self._update_user_roles(existing_user, user.roles)
            
            self.db.commit()
            self.db.refresh(existing_user)
            return self.user_converter.from_model(existing_user)
        else:
            # 创建新用户
            user_dict = self.user_converter.to_model_dict(user)
            new_user = UserModel(**user_dict)
            
            # 设置角色关联
            await self._set_user_roles(new_user, user.roles)
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            return self.user_converter.from_model(new_user)
    
    async def delete(self, user_id: str) -> bool:
        """删除用户"""
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    async def list_active(self, limit: int = 100, offset: int = 0) -> List[User]:
        """获取活跃用户列表"""
        users = self.db.query(UserModel).filter(
            UserModel.is_active == True
        ).offset(offset).limit(limit).all()
        
        return [self.user_converter.from_model(user) for user in users]

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UserModel]:
        """获取用户列表"""
        query = self.db.query(UserModel)
        
        # 应用过滤器
        if filters:
            if "is_active" in filters:
                query = query.filter(UserModel.is_active == filters["is_active"])
            if "role" in filters:
                query = query.join(UserModel.roles).filter(RoleModel.name == filters["role"])
            if "search" in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        UserModel.username.ilike(search_term),
                        UserModel.email.ilike(search_term)
                    )
                )
        
        # 分页
        users = query.offset(skip).limit(limit).all()
        
        return [self.user_converter.from_model(user) for user in users]
    
    
    async def assign_role(self, user_id: str, role_name: str) -> bool:
        """分配角色给用户"""
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        role = self.db.query(RoleModel).filter(RoleModel.name == role_name).first()
        
        if not user or not role:
            return False
        
        if role not in user.roles:
            user.roles.append(role)
            self.db.commit()
        
        return True
    
    async def remove_role(self, user_id: str, role_name: str) -> bool:
        """移除用户角色"""
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        role = self.db.query(RoleModel).filter(RoleModel.name == role_name).first()
        
        if not user or not role:
            return False
        
        if role in user.roles:
            user.roles.remove(role)
            self.db.commit()
        
        return True
    
    async def _update_user_roles(self, user_model: UserModel, role_names: set) -> None:
        """更新用户角色关联"""
        # 获取当前角色
        current_roles = {role.name for role in user_model.roles}
        
        # 需要添加的角色
        roles_to_add = role_names - current_roles
        # 需要移除的角色
        roles_to_remove = current_roles - role_names
        
        # 添加新角色
        for role_name in roles_to_add:
            role = self.db.query(RoleModel).filter(RoleModel.name == role_name).first()
            if role:
                user_model.roles.append(role)
        
        # 移除旧角色
        for role_name in roles_to_remove:
            role = self.db.query(RoleModel).filter(RoleModel.name == role_name).first()
            if role and role in user_model.roles:
                user_model.roles.remove(role)
    
    async def _set_user_roles(self, user_model: UserModel, role_names: set) -> None:
        """设置用户角色关联"""
        roles = []
        for role_name in role_names:
            role = self.db.query(RoleModel).filter(RoleModel.name == role_name).first()
            if role:
                roles.append(role)
        
        user_model.roles = roles
    
    # 用户默认角色相关方法
    async def get_user_default_role(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户默认角色设置"""
        try:
            default_role_setting = self.db.query(UserDefaultRole).filter(
                UserDefaultRole.user_id == user_id
            ).first()
            
            if not default_role_setting:
                return None
            
            return {
                "id": default_role_setting.id,
                "user_id": default_role_setting.user_id,
                "default_role": default_role_setting.default_role,
                "created_at": default_role_setting.created_at,
                "updated_at": default_role_setting.updated_at
            }
        except Exception as e:
            raise Exception(f"获取用户默认角色设置失败: {str(e)}")
    
    async def save_user_default_role(self, user_id: str, default_role: str) -> Dict[str, Any]:
        """保存用户默认角色设置"""
        try:
            default_role_setting = UserDefaultRole(
                user_id=user_id,
                default_role=default_role
            )
            
            self.db.add(default_role_setting)
            self.db.commit()
            self.db.refresh(default_role_setting)
            
            return {
                "id": default_role_setting.id,
                "user_id": default_role_setting.user_id,
                "default_role": default_role_setting.default_role,
                "created_at": default_role_setting.created_at,
                "updated_at": default_role_setting.updated_at
            }
        except Exception as e:
            self.db.rollback()
            raise Exception(f"保存用户默认角色设置失败: {str(e)}")
    
    async def update_user_default_role(self, user_id: str, default_role: str) -> Dict[str, Any]:
        """更新用户默认角色设置"""
        try:
            default_role_setting = self.db.query(UserDefaultRole).filter(
                UserDefaultRole.user_id == user_id
            ).first()
            
            if not default_role_setting:
                raise ValueError("用户默认角色设置不存在")
            
            default_role_setting.default_role = default_role
            default_role_setting.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(default_role_setting)
            
            return {
                "id": default_role_setting.id,
                "user_id": default_role_setting.user_id,
                "default_role": default_role_setting.default_role,
                "created_at": default_role_setting.created_at,
                "updated_at": default_role_setting.updated_at
            }
        except Exception as e:
            self.db.rollback()
            raise Exception(f"更新用户默认角色设置失败: {str(e)}")
    
    # 用户偏好设置相关方法
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好设置"""
        try:
            preferences = self.db.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()
            
            if not preferences:
                return None
            
            return {
                "id": preferences.id,
                "user_id": preferences.user_id,
                "notification_enabled": preferences.notification_enabled,
                "email_notification": preferences.email_notification,
                "push_notification": preferences.push_notification,
                "created_at": preferences.created_at,
                "updated_at": preferences.updated_at
            }
        except Exception as e:
            raise Exception(f"获取用户偏好设置失败: {str(e)}")
    
    async def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """保存用户偏好设置"""
        try:
            user_preferences = UserPreferences(
                user_id=user_id,
                notification_enabled=preferences.get("notification_enabled", True),
                email_notification=preferences.get("email_notification", True),
                push_notification=preferences.get("push_notification", True),
            )
            
            self.db.add(user_preferences)
            self.db.commit()
            self.db.refresh(user_preferences)
            
            return {
                "id": user_preferences.id,
                "user_id": user_preferences.user_id,
                "notification_enabled": user_preferences.notification_enabled,
                "email_notification": user_preferences.email_notification,
                "push_notification": user_preferences.push_notification,
                "created_at": user_preferences.created_at,
                "updated_at": user_preferences.updated_at
            }
        except Exception as e:
            self.db.rollback()
            raise Exception(f"保存用户偏好设置失败: {str(e)}")
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户偏好设置"""
        try:
            user_preferences = self.db.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()
            
            if not user_preferences:
                raise ValueError("用户偏好设置不存在")
            
            # 更新字段
            for key, value in preferences.items():
                if hasattr(user_preferences, key):
                    setattr(user_preferences, key, value)
            
            user_preferences.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(user_preferences)
            
            return {
                "id": user_preferences.id,
                "user_id": user_preferences.user_id,
                "notification_enabled": user_preferences.notification_enabled,
                "email_notification": user_preferences.email_notification,
                "push_notification": user_preferences.push_notification,
                "created_at": user_preferences.created_at,
                "updated_at": user_preferences.updated_at
            }
        except Exception as e:
            self.db.rollback()
            raise Exception(f"更新用户偏好设置失败: {str(e)}")
    
    async def count_by_tenant_id(self, tenant_id: str) -> int:
        """统计租户下的用户数量"""
        return self.db.query(UserModel).filter(UserModel.tenant_id == tenant_id).count()
    
    async def get_user_roles(self, user_id: str) -> List[Role]:
        """获取用户的角色列表"""
        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user_model:
            return []
        
        # 通过关联表获取角色
        db_roles = user_model.roles
        return [self._role_to_entity(role) for role in db_roles]
    
    def _role_to_entity(self, db_role: RoleModel) -> Role:
        """将角色数据库模型转换为领域实体"""
        return Role(
            id=db_role.id,
            name=db_role.name,
            display_name=db_role.display_name,
            description=db_role.description,
            is_active=db_role.is_active,
            is_system=db_role.is_system,
            is_admin=db_role.is_admin,
            priority=db_role.priority,
            tenant_id=db_role.tenant_id,
            created_at=db_role.created_at,
            updated_at=db_role.updated_at
        )