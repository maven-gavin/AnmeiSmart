from enum import Enum
from typing import Optional
from dataclasses import dataclass


class SystemStatus(str, Enum):
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
        
        if len(self.site_name.strip()) > 100:
            raise ValueError("站点名称过长，不能超过100字符")
        
        if self.logo_url is not None and not self.logo_url.strip():
            raise ValueError("Logo URL不能为空字符串")
        
        if self.logo_url and len(self.logo_url.strip()) > 500:
            raise ValueError("Logo URL过长，不能超过500字符")
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        return self.site_name.strip()
    
    @property
    def has_logo(self) -> bool:
        """检查是否有Logo"""
        return bool(self.logo_url and self.logo_url.strip())


@dataclass(frozen=True)
class UserRegistrationConfig:
    """用户注册配置值对象"""
    enabled: bool
    
    def __post_init__(self):
        if not isinstance(self.enabled, bool):
            raise ValueError("用户注册配置必须是布尔值")
    
    @property
    def is_enabled(self) -> bool:
        """检查用户注册是否启用"""
        return self.enabled
    
    @property
    def status_text(self) -> str:
        """获取状态文本"""
        return "启用" if self.enabled else "禁用"


@dataclass(frozen=True)
class AIModelConfig:
    """AI模型配置值对象"""
    default_model_id: Optional[str]
    
    def __post_init__(self):
        if self.default_model_id is not None and not self.default_model_id.strip():
            raise ValueError("默认AI模型ID不能为空字符串")
        
        if self.default_model_id and len(self.default_model_id.strip()) > 100:
            raise ValueError("AI模型ID过长，不能超过100字符")
    
    @property
    def has_default_model(self) -> bool:
        """检查是否有默认模型"""
        return bool(self.default_model_id and self.default_model_id.strip())
    
    @property
    def model_id_display(self) -> str:
        """获取模型ID显示文本"""
        if not self.default_model_id:
            return "未设置"
        return self.default_model_id.strip()

