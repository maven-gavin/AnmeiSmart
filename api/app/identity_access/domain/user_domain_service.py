"""
用户领域服务

处理用户相关的跨聚合业务逻辑。
"""

from typing import List, Optional, Dict, Any

from .entities.user import User


class UserDomainService:
    """用户领域服务"""
    
    def __init__(
        self,
        user_repository,
        role_repository
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        avatar: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> User:
        """创建用户 - 领域逻辑"""
        # 验证用户名唯一性
        if await self.user_repository.exists_by_username(username):
            raise ValueError(f"用户名 '{username}' 已存在")
        
        # 验证邮箱唯一性
        if await self.user_repository.exists_by_email(email):
            raise ValueError(f"邮箱 '{email}' 已存在")
        
        # 验证手机号唯一性（如果提供）
        if phone and await self.user_repository.exists_by_phone(phone):
            raise ValueError(f"手机号 '{phone}' 已存在")
        
        # 验证角色有效性
        if roles:
            for role_name in roles:
                if not await self.role_repository.exists_by_name(role_name):
                    raise ValueError(f"角色 '{role_name}' 不存在")
        
        # 创建用户
        user = User.create(
            username=username,
            email=email,
            password=password,
            phone=phone,
            avatar=avatar,
            roles=roles
        )
        
        # 保存用户
        saved_user = await self.user_repository.save(user)
        return saved_user
    
    async def update_user_profile(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> User:
        """更新用户资料 - 领域逻辑"""
        # 获取用户
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户不存在: {user_id}")
        
        # 验证用户名唯一性（如果要更新）
        if "username" in updates:
            new_username = updates["username"]
            if new_username != user.username:
                if await self.user_repository.exists_by_username(new_username):
                    raise ValueError(f"用户名 '{new_username}' 已存在")
        
        # 验证手机号唯一性（如果要更新）
        if "phone" in updates:
            new_phone = updates["phone"]
            if new_phone and new_phone != user.phone:
                if await self.user_repository.exists_by_phone(new_phone):
                    raise ValueError(f"手机号 '{new_phone}' 已存在")
        
        # 更新用户资料
        user.update_profile(
            username=updates.get("username"),
            phone=updates.get("phone"),
            avatar=updates.get("avatar")
        )
        
        # 保存更新
        updated_user = await self.user_repository.save(user)
        return updated_user
    
    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """修改密码 - 领域逻辑"""
        # 获取用户
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户不存在: {user_id}")
        
        # 修改密码
        user.change_password(old_password, new_password)
        
        # 保存更新
        await self.user_repository.save(user)
        return True
    
    async def activate_user(self, user_id: str) -> bool:
        """激活用户"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户不存在: {user_id}")
        
        user.activate()
        await self.user_repository.save(user)
        return True
    
    async def deactivate_user(self, user_id: str) -> bool:
        """停用用户"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户不存在: {user_id}")
        
        user.deactivate()
        await self.user_repository.save(user)
        return True
    
    async def assign_roles(self, user_id: str, role_names: List[str]) -> bool:
        """分配角色给用户"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户不存在: {user_id}")
        
        # 验证角色有效性
        for role_name in role_names:
            if not await self.role_repository.exists_by_name(role_name):
                raise ValueError(f"角色 '{role_name}' 不存在")
        
        # 分配角色
        for role_name in role_names:
            user.add_role(role_name)
            await self.user_repository.assign_role(user_id, role_name)
        
        # 保存用户
        await self.user_repository.save(user)
        return True
    
    async def remove_roles(self, user_id: str, role_names: List[str]) -> bool:
        """移除用户角色"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"用户不存在: {user_id}")
        
        # 移除角色
        for role_name in role_names:
            user.remove_role(role_name)
            await self.user_repository.remove_role(user_id, role_name)
        
        # 保存用户
        await self.user_repository.save(user)
        return True
