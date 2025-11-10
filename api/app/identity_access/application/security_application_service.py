"""
安全应用服务

编排安全相关的用例，处理表现层的请求。
"""

from typing import Optional, List
from fastapi import HTTPException, status
import logging

from ..domain.security_domain_service import SecurityDomainService
from ..domain.entities.user import UserEntity

logger = logging.getLogger(__name__)

class SecurityApplicationService:
    """安全应用服务 - 编排安全相关的用例"""
    
    def __init__(self, security_domain_service: SecurityDomainService):
        self.security_domain_service = security_domain_service
    
    async def get_current_user(self, token: str) -> UserEntity:
        """
        获取当前用户用例
        
        Args:
            token: JWT令牌
            
        Returns:
            User: 认证成功的用户对象
            
        Raises:
            HTTPException: 如果认证失败或用户不存在
        """
        try:
            userEntity = await self.security_domain_service.authenticate_user_by_token(token)
            if not userEntity:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无法验证凭据",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return userEntity
        except ValueError as e:
            # 业务逻辑错误 - 403 Forbidden
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        except Exception as e:
            # 系统错误 - 500 Internal Server Error
            logger.error(f"获取当前用户失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="内部服务器错误"
            )
    
    async def check_role_permission(
        self, 
        user: UserEntity, 
        required_roles: Optional[List[str]] = None
    ) -> UserEntity:
        """
        检查用户角色权限用例
        
        Args:
            user: 用户对象
            required_roles: 所需的角色列表
            
        Returns:
            User: 通过权限检查的用户对象
            
        Raises:
            HTTPException: 如果用户权限不足
        """
        try:
            has_permission = self.security_domain_service.check_user_permissions(user, required_roles or [])
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="用户权限不足",
                )
            return user
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            # 系统错误 - 500 Internal Server Error
            logger.error(f"检查用户权限失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="内部服务器错误"
            )
    
    async def get_current_admin(self, user: UserEntity) -> UserEntity:
        """
        获取当前管理员用户用例
        
        Args:
            user: 当前认证用户
            
        Returns:
            User: 管理员用户对象
            
        Raises:
            HTTPException: 如果用户不是管理员
        """
        try:
            logger.info(f"SecurityApplicationService.get_current_admin开始检查管理员权限 - user_id: {user.id}")
            logger.debug(f"用户对象信息 - user_id: {user.id}, user.roles类型: {type(user.roles)}, user.roles内容: {user.roles}")
            
            is_admin = self.security_domain_service.check_admin_permission(user)
            logger.info(f"SecurityApplicationService.get_current_admin检查结果 - user_id: {user.id}, is_admin: {is_admin}")
            
            if not is_admin:
                logger.warning(f"用户 {user.id} 不是管理员，拒绝访问")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="需要管理员权限",
                )
            
            logger.info(f"用户 {user.id} 管理员权限检查通过")
            return user
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            # 系统错误 - 500 Internal Server Error
            logger.error(f"检查管理员权限失败: {e}")
            logger.error(f"用户对象详细信息 - user_id: {getattr(user, 'id', 'N/A')}, user.roles: {getattr(user, 'roles', 'N/A')}")
            import traceback
            logger.error(f"管理员权限检查错误堆栈: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="内部服务器错误"
            )
