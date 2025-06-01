from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """令牌模型"""
    access_token: str
    refresh_token: str
    token_type: str

class TokenPayload(BaseModel):
    """令牌载荷模型"""
    sub: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    token: str 