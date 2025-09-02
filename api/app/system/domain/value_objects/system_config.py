from enum import Enum
from typing import Optional
from dataclasses import dataclass


class SystemStatus(Enum):
    """系统状态枚举"""
    NORMAL = "normal"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class MaintenanceMode(Enum):
    """维护模式枚举"""
    DISABLED = False
    ENABLED = True


@dataclass(frozen=True)
class SiteConfiguration:
    """站点配置值对象"""
    site_name: str
    logo_url: Optional[str]
    
    def __post_init__(self):
        if not self.site_name or not self.site_name.strip():
            raise ValueError("站点名称不能为空")
        
        if self.logo_url is not None and not self.logo_url.strip():
            raise ValueError("Logo URL不能为空字符串")


@dataclass(frozen=True)
class UserRegistrationConfig:
    """用户注册配置值对象"""
    enabled: bool
    
    def __post_init__(self):
        if not isinstance(self.enabled, bool):
            raise ValueError("用户注册配置必须是布尔值")


@dataclass(frozen=True)
class AIModelConfig:
    """AI模型配置值对象"""
    default_model_id: Optional[str]
    
    def __post_init__(self):
        if self.default_model_id is not None and not self.default_model_id.strip():
            raise ValueError("默认AI模型ID不能为空字符串")

