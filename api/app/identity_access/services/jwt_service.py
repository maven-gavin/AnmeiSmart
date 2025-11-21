"""
JWT令牌服务 - 基础设施层

处理JWT令牌的创建、验证等基础设施功能。
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import JWTError, jwt
import logging

from app.core.config import get_settings

# 配置日志
logger = logging.getLogger(__name__)

class JWTService:
    """JWT令牌服务 - 基础设施层"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def create_access_token(
        self, 
        subject: Union[str, Any], 
        expires_delta: Optional[timedelta] = None,
        active_role: Optional[str] = None
    ) -> str:
        """
        创建访问令牌
        
        Args:
            subject: 令牌主体 (通常是用户ID)
            expires_delta: 过期时间增量
            active_role: 用户当前活跃角色
            
        Returns:
            str: JWT令牌
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {"exp": expire, "sub": str(subject)}
        
        # 如果提供了活跃角色，将其添加到令牌中
        if active_role:
            to_encode["role"] = active_role
        
        logger.debug(f"创建访问令牌: user_id={subject}, 过期时间={expire.isoformat()}, 活跃角色={active_role}")
        
        encoded_jwt = jwt.encode(
            to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM
        )
        return encoded_jwt
    
    def create_refresh_token(
        self,
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
        active_role: Optional[str] = None
    ) -> str:
        """
        创建刷新令牌
        
        Args:
            subject: 令牌主体 (通常是用户ID)
            expires_delta: 过期时间增量
            active_role: 用户当前活跃角色
            
        Returns:
            str: JWT刷新令牌
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
        
        # 如果提供了活跃角色，将其添加到令牌中
        if active_role:
            to_encode["role"] = active_role
        
        logger.debug(f"创建刷新令牌: user_id={subject}, 过期时间={expire.isoformat()}, 活跃角色={active_role}")
        
        encoded_jwt = jwt.encode(
            to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌并提取载荷
        
        Args:
            token: JWT令牌
        
        Returns:
            Dict[str, Any]: 令牌载荷，如果令牌无效则返回None
        """
        # 记录令牌前几个字符，避免完整记录敏感信息
        token_prefix = token[:10] if token and len(token) > 10 else "无token"
        logger.debug(f"开始验证令牌: {token_prefix}...")
        
        try:
            logger.debug(f"尝试解码令牌...")
            payload = jwt.decode(
                token, self.settings.SECRET_KEY, algorithms=[self.settings.ALGORITHM]
            )
            logger.debug(f"令牌解码成功")
            
            user_id = payload.get("sub")
            if user_id is None:
                logger.warning(f"令牌有效但未包含用户ID(sub)信息")
                return None
            
            # 检查令牌是否过期
            exp = payload.get("exp")
            if exp:
                current_time = datetime.utcnow().timestamp()
                if current_time > exp:
                    logger.warning(f"令牌已过期: 过期时间={datetime.fromtimestamp(exp).isoformat()}")
                    return None
                
            logger.debug(f"令牌验证成功: user_id={user_id}")
            return payload
        except JWTError as e:
            logger.warning(f"令牌验证失败: JWT错误 - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"令牌验证过程中发生未知错误: {str(e)}")
            return None
