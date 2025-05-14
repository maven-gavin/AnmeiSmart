from pydantic import BaseModel

class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """令牌载荷模型"""
    sub: str | None = None 