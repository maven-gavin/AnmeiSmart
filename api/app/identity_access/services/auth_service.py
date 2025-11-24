"""
认证服务 - 处理登录、令牌管理等
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.identity_access.models.user import User
from app.identity_access.models.profile import LoginHistory
from app.identity_access.schemas.token import Token
from app.identity_access.services.user_service import UserService
from app.identity_access.services.jwt_service import JWTService
from app.identity_access.enums import UserStatus
from app.core.password_utils import verify_password
from app.core.api import BusinessException, ErrorCode

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.jwt_service = JWTService()

    async def login(
        self,
        username_or_email: str,
        password: str,
        tenant_id: str = "system",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Token:
        """用户登录"""
        logger.debug(f"开始登录流程: username_or_email={username_or_email}, tenant_id={tenant_id}")
        
        try:
            # 1. 查找用户
            logger.debug(f"步骤1: 查找用户 - 尝试通过用户名查找")
            user = self.user_service.get_by_username(username_or_email, tenant_id)
            if not user:
                logger.debug(f"步骤1: 通过用户名未找到用户，尝试通过邮箱查找")
                user = self.user_service.get_by_email(username_or_email, tenant_id)
            else:
                logger.debug(f"步骤1: 通过用户名找到用户: user_id={user.id}, username={user.username}")
                
            if not user:
                logger.warning(f"步骤1失败: 未找到用户 - username_or_email={username_or_email}, tenant_id={tenant_id}")
                raise BusinessException("用户名或密码错误", code=ErrorCode.INVALID_CREDENTIALS)

            logger.debug(f"步骤2: 验证密码 - user_id={user.id}, has_password={bool(user.hashed_password)}")
            # 2. 验证密码
            if not verify_password(password, user.hashed_password):
                logger.warning(f"步骤2失败: 密码验证失败 - user_id={user.id}, username={user.username}")
                raise BusinessException("用户名或密码错误", code=ErrorCode.INVALID_CREDENTIALS)
            
            logger.debug(f"步骤2: 密码验证成功")
            
            logger.debug(f"步骤3: 检查用户状态 - user_id={user.id}, status={user.status}")
            if user.status != UserStatus.ACTIVE:
                logger.warning(f"步骤3失败: 用户状态非活跃 - user_id={user.id}, status={user.status}")
                raise BusinessException("账号已被禁用", code=ErrorCode.USER_DISABLED)
            
            logger.debug(f"步骤3: 用户状态检查通过")

            # 3. 获取当前角色
            logger.debug(f"步骤4: 获取用户角色 - user_id={user.id}")
            # 优先使用默认角色，否则使用第一个角色
            active_role = await self.user_service.get_user_default_role(user.id)
            logger.debug(f"步骤4: 默认角色查询结果 - active_role={active_role}")
            if not active_role and user.roles:
                active_role = user.roles[0].name
                logger.debug(f"步骤4: 使用第一个角色 - active_role={active_role}")
            logger.debug(f"步骤4: 最终活跃角色 - active_role={active_role}")
                
            # 4. 记录登录历史
            logger.debug(f"步骤5: 记录登录历史 - user_id={user.id}, active_role={active_role}")
            try:
                login_history = LoginHistory(
                    user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    login_role=active_role,
                    login_time=datetime.now()
                )
                self.db.add(login_history)
                logger.debug(f"步骤5: 登录历史对象已创建")
                
                # 更新最后登录时间 (如果User模型有这个字段)
                # user.last_login_at = datetime.now() 
                
                self.db.commit()
                logger.debug(f"步骤5: 登录历史已提交到数据库")
            except Exception as db_error:
                logger.error(f"步骤5失败: 记录登录历史时出错 - user_id={user.id}, error={str(db_error)}", exc_info=True)
                # 登录历史记录失败不应该阻止登录，只记录错误
                self.db.rollback()

            # 5. 生成令牌
            logger.debug(f"步骤6: 生成令牌 - user_id={user.id}, active_role={active_role}")
            try:
                token = self._generate_tokens(user.id, active_role)
                logger.info(f"登录流程完成: user_id={user.id}, username={user.username}, active_role={active_role}")
                return token
            except Exception as token_error:
                logger.error(f"步骤6失败: 生成令牌时出错 - user_id={user.id}, error={str(token_error)}", exc_info=True)
                raise
                
        except BusinessException:
            # 业务异常直接抛出，不记录额外日志（已在抛出点记录）
            raise
        except Exception as e:
            logger.error(
                f"登录流程异常: username_or_email={username_or_email}, tenant_id={tenant_id}, "
                f"exception_type={type(e).__name__}, error={str(e)}",
                exc_info=True
            )
            raise

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

