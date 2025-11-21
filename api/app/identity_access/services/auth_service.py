"""
认证服务 - 处理登录、令牌管理等
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.identity_access.models.user import User
from app.identity_access.models.profile import LoginHistory
from app.identity_access.schemas.token import Token
from app.identity_access.services.user_service import UserService
from app.identity_access.services.jwt_service import JWTService
from app.core.password_utils import verify_password
from app.core.api import BusinessException, ErrorCode

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.jwt_service = JWTService()

    async def login(
        self,
        username_or_email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Token:
        """用户登录"""
        # 1. 查找用户
        user = self.user_service.get_by_username(username_or_email)
        if not user:
            user = self.user_service.get_by_email(username_or_email)
            
        if not user:
            raise BusinessException("用户名或密码错误", code=ErrorCode.INVALID_CREDENTIALS)

        # 2. 验证密码
        if not verify_password(password, user.hashed_password):
            raise BusinessException("用户名或密码错误", code=ErrorCode.INVALID_CREDENTIALS)
            
        if not user.is_active:
            raise BusinessException("账号已被禁用", code=ErrorCode.USER_DISABLED)

        # 3. 获取当前角色
        # 优先使用默认角色，否则使用第一个角色
        active_role = await self.user_service.get_user_default_role(user.id)
        if not active_role and user.roles:
            active_role = user.roles[0].name
            
        # 4. 记录登录历史
        login_history = LoginHistory(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            login_role=active_role,
            login_time=datetime.now()
        )
        self.db.add(login_history)
        
        # 更新最后登录时间 (如果User模型有这个字段)
        # user.last_login_at = datetime.now() 
        
        self.db.commit()

        # 5. 生成令牌
        return self._generate_tokens(user.id, active_role)

    async def refresh_token(self, token: str) -> Token:
        """刷新令牌"""
        payload = self.jwt_service.verify_token(token)
        if not payload or payload.get("type") != "refresh":
            raise BusinessException("无效的刷新令牌", code=ErrorCode.INVALID_TOKEN)
            
        user_id = payload.get("sub")
        active_role = payload.get("role")
        
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
             raise BusinessException("用户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
             
        return self._generate_tokens(user_id, active_role)

    def _generate_tokens(self, user_id: str, active_role: Optional[str]) -> Token:
        """生成访问令牌和刷新令牌"""
        access_token_expires = timedelta(minutes=self.jwt_service.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.jwt_service.create_access_token(
            subject=user_id,
            expires_delta=access_token_expires,
            active_role=active_role
        )
        
        refresh_token_expires = timedelta(days=self.jwt_service.settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = self.jwt_service.create_refresh_token(
            subject=user_id,
            expires_delta=refresh_token_expires,
            active_role=active_role
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def switch_role(self, user_id: str, target_role: str) -> Token:
        """切换角色"""
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
            
        # 验证用户是否有该角色
        has_role = False
        for role in user.roles:
            if role.name == target_role:
                has_role = True
                break
        
        if not has_role:
            raise BusinessException(f"用户没有 '{target_role}' 角色权限", code=ErrorCode.PERMISSION_DENIED)
            
        return self._generate_tokens(user_id, target_role)

