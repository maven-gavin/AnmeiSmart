"""
登录历史值对象

封装用户登录历史信息。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class LoginHistory:
    """登录历史值对象"""
    
    user_id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    login_role: Optional[str]
    location: Optional[str]
    login_time: datetime
    
    @classmethod
    def create(
        cls,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        login_role: Optional[str] = None,
        location: Optional[str] = None,
        login_time: Optional[datetime] = None
    ) -> "LoginHistory":
        """创建登录历史记录"""
        if not user_id or not user_id.strip():
            raise ValueError("用户ID不能为空")
        
        return cls(
            user_id=user_id.strip(),
            ip_address=ip_address,
            user_agent=user_agent,
            login_role=login_role,
            location=location or "",
            login_time=login_time or datetime.utcnow()
        )
    
    def is_recent(self, minutes: int = 30) -> bool:
        """是否为最近登录"""
        from datetime import timedelta
        return datetime.utcnow() - self.login_time < timedelta(minutes=minutes)
    
    def get_location_info(self) -> str:
        """获取位置信息"""
        if self.location:
            return self.location
        if self.ip_address:
            return f"IP: {self.ip_address}"
        return "未知位置"
    
    def get_device_info(self) -> str:
        """获取设备信息"""
        if not self.user_agent:
            return "未知设备"
        
        # 简单的设备信息提取
        user_agent = self.user_agent.lower()
        if "mobile" in user_agent or "android" in user_agent or "iphone" in user_agent:
            return "移动设备"
        elif "windows" in user_agent:
            return "Windows设备"
        elif "mac" in user_agent:
            return "Mac设备"
        elif "linux" in user_agent:
            return "Linux设备"
        else:
            return "其他设备"
    
    def __str__(self) -> str:
        return f"LoginHistory(user_id={self.user_id}, time={self.login_time})"
