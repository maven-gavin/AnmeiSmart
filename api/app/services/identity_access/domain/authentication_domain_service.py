"""
认证领域服务

处理用户认证和令牌管理相关的业务逻辑。
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .entities.user import User
from .value_objects.login_history import LoginHistory


class AuthenticationDomainService:
    """认证领域服务"""
    
    def __init__(
        self,
        user_repository,
        login_history_repository
    ):
        self.user_repository = user_repository
        self.login_history_repository = login_history_repository
    
    async def authenticate_user(
        self,
        username_or_email: str,
        password: str
    ) -> Optional[User]:
        """用户身份认证"""
        # 判断是邮箱还是用户名
        is_email = "@" in username_or_email
        
        # 获取用户
        if is_email:
            user = await self.user_repository.get_by_email(username_or_email)
        else:
            user = await self.user_repository.get_by_username(username_or_email)
        
        if not user:
            return None
        
        # 验证密码
        if not user.verify_password(password):
            return None
        
        # 检查用户状态
        if not user.can_login():
            return None
        
        # 记录登录时间
        user.record_login()
        await self.user_repository.save(user)
        
        return user
    
    async def record_login(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        login_role: Optional[str] = None,
        location: Optional[str] = None
    ) -> LoginHistory:
        """记录登录历史"""
        login_history = LoginHistory.create(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            login_role=login_role,
            location=location
        )
        
        saved_history = await self.login_history_repository.create(login_history)
        return saved_history
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            # 延迟导入避免循环依赖
            from app.core.security import get_current_user_from_token
            
            # 这里需要实现令牌验证逻辑
            # 暂时返回None，实际实现需要调用security模块
            return None
            
        except Exception:
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """刷新令牌"""
        try:
            # 延迟导入避免循环依赖
            from app.core.security import create_access_token, create_refresh_token
            from app.core.config import get_settings
            
            settings = get_settings()
            
            # 这里需要实现刷新令牌逻辑
            # 暂时返回None，实际实现需要调用security模块
            return None
            
        except Exception:
            return None
    
    async def revoke_token(self, token: str) -> bool:
        """撤销令牌"""
        try:
            # 这里需要实现令牌撤销逻辑
            # 可能需要将令牌加入黑名单或更新数据库状态
            return True
            
        except Exception:
            return False
    
    async def get_user_active_sessions(self, user_id: str) -> int:
        """获取用户活跃会话数"""
        # 这里可以实现获取用户当前活跃会话数的逻辑
        # 暂时返回0
        return 0
    
    async def is_recent_login(self, user_id: str, minutes: int = 30) -> bool:
        """检查是否为最近登录"""
        try:
            recent_logins = await self.login_history_repository.get_recent_logins(
                user_id=user_id,
                since=datetime.utcnow() - timedelta(minutes=minutes),
                limit=1
            )
            return len(recent_logins) > 0
        except Exception:
            return False
