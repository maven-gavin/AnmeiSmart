"""
密码值对象

封装密码的验证逻辑和安全规则。
"""

import re
from typing import Optional
from dataclasses import dataclass
from app.core.password_utils import get_password_hash, verify_password


@dataclass(frozen=True)
class Password:
    """密码值对象"""
    
    hashed_value: str
    
    @classmethod
    def create(cls, plain_password: str) -> "Password":
        """创建密码值对象"""
        if not cls._is_valid(plain_password):
            raise ValueError("密码不符合安全要求")
        
        hashed = get_password_hash(plain_password)
        return cls(hashed_value=hashed)
    
    @classmethod
    def from_hash(cls, hashed_password: str) -> "Password":
        """从哈希值创建密码对象"""
        return cls(hashed_value=hashed_password)
    
    def _is_valid(plain_password: str) -> bool:
        """验证密码强度"""
        if not plain_password or not isinstance(plain_password, str):
            return False
        
        # 长度要求：至少8位
        if len(plain_password) < 8:
            return False
        
        # 长度要求：最多128位
        if len(plain_password) > 128:
            return False
        
        # 复杂度要求：至少包含字母和数字
        has_letter = bool(re.search(r'[a-zA-Z]', plain_password))
        has_digit = bool(re.search(r'\d', plain_password))
        
        if not (has_letter and has_digit):
            return False
        
        return True
    
    def verify(self, plain_password: str) -> bool:
        """验证密码"""
        return verify_password(plain_password, self.hashed_value)
    
    def __str__(self) -> str:
        return "***"  # 安全考虑，不显示实际密码
    
    def __repr__(self) -> str:
        return "Password(***)"
