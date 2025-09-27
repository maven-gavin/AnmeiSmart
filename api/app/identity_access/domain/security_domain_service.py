"""
安全领域服务

处理用户认证、权限验证等安全相关的业务逻辑。
"""

from typing import Optional, List
import logging

from .entities.user import User

logger = logging.getLogger(__name__)

class SecurityDomainService:
    """安全领域服务 - 处理安全相关的业务逻辑"""
    
    def __init__(self, user_repository, jwt_service):
        self.user_repository = user_repository
        self.jwt_service = jwt_service
    
    async def authenticate_user_by_token(self, token: str) -> Optional[User]:
        """
        通过令牌认证用户 - 领域逻辑
        
        Args:
            token: JWT令牌
            
        Returns:
            User: 认证成功的用户对象，如果认证失败则返回None
        """
        # 验证令牌
        payload = self.jwt_service.verify_token(token)
        if not payload:
            return None
        
        # 获取用户ID
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # 从数据库获取用户
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None
        
        # 设置活跃角色
        active_role = payload.get("role")
        if active_role:
            self._set_user_active_role(user, active_role)
        
        return user
    
    def _set_user_active_role(self, user: User, role: str) -> None:
        """
        设置用户活跃角色 - 领域逻辑
        
        Args:
            user: 用户对象
            role: 要设置的活跃角色
            
        Raises:
            ValueError: 如果用户没有指定的角色权限
        """
        # 验证用户是否拥有此角色
        if not self._user_has_role(user, role):
            logger.warning(f"用户 {user.id} 没有令牌指定的角色权限: {role}")
            raise ValueError(f"用户没有角色权限: {role}")
        
        # 设置活跃角色（使用下划线前缀避免与数据库字段冲突）
        setattr(user, "_active_role", role)
        logger.debug(f"为用户 {user.id} 设置活跃角色: {role}")
    
    def _user_has_role(self, user: User, role: str) -> bool:
        """
        检查用户是否拥有指定角色
        
        Args:
            user: 用户对象
            role: 要检查的角色
            
        Returns:
            bool: 如果用户拥有指定角色则返回True
        """
        if not user.roles:
            return False
        
        user_roles = [role_obj.name if hasattr(role_obj, 'name') else role_obj for role_obj in user.roles]
        return role in user_roles
    
    def check_user_permissions(self, user: User, required_roles: List[str]) -> bool:
        """
        检查用户是否有所需的角色权限
        
        Args:
            user: 用户对象
            required_roles: 所需的角色列表
            
        Returns:
            bool: 如果用户有所需权限则返回True
        """
        logger.debug(f"SecurityDomainService.check_user_permissions开始检查用户权限 - user_id: {user.id}, required_roles: {required_roles}")
        
        # 如果未指定所需角色，允许任何已认证用户访问
        if not required_roles:
            logger.debug(f"未指定所需角色，允许用户 {user.id} 访问")
            return True
        
        # 获取当前用户的活跃角色
        active_role = getattr(user, "_active_role", None)
        logger.debug(f"检查用户 {user.id} 的权限, 活跃角色: {active_role}, 所需角色: {required_roles}")
        
        # 如果未设置活跃角色，使用用户的任何角色
        if not active_role:
            logger.debug(f"用户 {user.id} 没有活跃角色，检查所有角色")
            logger.debug(f"user.roles 类型: {type(user.roles)}, 内容: {user.roles}")
            
            # 安全地处理 user.roles，可能是字符串或对象
            user_roles = []
            for i, role in enumerate(user.roles):
                try:
                    logger.debug(f"处理第 {i+1} 个角色: {role}, 类型: {type(role)}")
                    if hasattr(role, 'name'):
                        role_name = role.name
                        logger.debug(f"角色对象，名称: {role_name}")
                    else:
                        role_name = str(role)
                        logger.debug(f"字符串角色: {role_name}")
                    user_roles.append(role_name)
                except Exception as e:
                    logger.error(f"处理第 {i+1} 个角色失败: {e}, 角色内容: {role}")
                    import traceback
                    logger.error(f"角色处理错误堆栈: {traceback.format_exc()}")
                    continue
            
            logger.debug(f"用户 {user.id} 的所有角色: {user_roles}")
            
            # 检查用户是否拥有任何所需角色
            if any(role in required_roles for role in user_roles):
                matching_roles = [role for role in user_roles if role in required_roles]
                logger.debug(f"用户 {user.id} 拥有所需角色: {matching_roles}")
                return True
            logger.warning(f"用户 {user.id} 没有所需角色: {required_roles}")
            return False
        
        # 否则只检查活跃角色
        if active_role in required_roles:
            logger.debug(f"用户 {user.id} 的活跃角色 {active_role} 符合要求")
            return True
        else:
            logger.warning(f"用户 {user.id} 的活跃角色 {active_role} 不符合要求: {required_roles}")
            return False
    
    def check_admin_permission(self, user: User) -> bool:
        """
        检查用户是否具有管理员权限
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 如果用户是管理员则返回True
        """
        logger.debug(f"SecurityDomainService.check_admin_permission开始检查管理员权限 - user_id: {user.id}")
        result = self.check_user_permissions(user, ["administrator"])
        logger.debug(f"SecurityDomainService.check_admin_permission结果 - user_id: {user.id}, is_admin: {result}")
        return result
