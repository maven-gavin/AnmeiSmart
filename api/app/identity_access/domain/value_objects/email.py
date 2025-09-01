"""
邮箱值对象

封装邮箱的验证逻辑和业务规则。
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """邮箱值对象"""
    
    value: str
    
    def __post_init__(self):
        """验证邮箱格式"""
        if not self._is_valid(self.value):
            raise ValueError(f"邮箱格式不正确: {self.value}")
    
    def _is_valid(self, email: str) -> bool:
        """验证邮箱格式"""
        if not email or not isinstance(email, str):
            return False
        
        # 基本格式验证
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # 长度验证
        if len(email) > 254:  # RFC 5321 标准
            return False
        
        return True
    
    def normalize(self) -> str:
        """标准化邮箱（转小写）"""
        return self.value.lower()
    
    def get_domain(self) -> str:
        """获取邮箱域名"""
        return self.value.split('@')[1].lower()
    
    def get_local_part(self) -> str:
        """获取邮箱本地部分"""
        return self.value.split('@')[0].lower()
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Email('{self.value}')"
