from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field
from app.system.domain.value_objects.system_config import (
    SystemStatus, 
    MaintenanceMode, 
    SiteConfiguration, 
    UserRegistrationConfig, 
    AIModelConfig
)


@dataclass
class SystemSettings:
    """系统设置聚合根"""
    id: str
    site_config: SiteConfiguration
    ai_model_config: AIModelConfig
    maintenance_mode: MaintenanceMode
    user_registration_config: UserRegistrationConfig
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("系统设置ID不能为空")
        
        # 更新修改时间
        self.updated_at = datetime.utcnow()
    
    @property
    def system_status(self) -> SystemStatus:
        """获取当前系统状态"""
        if self.maintenance_mode == MaintenanceMode.ENABLED:
            return SystemStatus.MAINTENANCE
        return SystemStatus.NORMAL
    
    def update_site_config(self, site_name: Optional[str] = None, logo_url: Optional[str] = None) -> None:
        """更新站点配置"""
        if site_name is not None:
            if not site_name.strip():
                raise ValueError("站点名称不能为空")
            self.site_config = SiteConfiguration(
                site_name=site_name.strip(),
                logo_url=logo_url or self.site_config.logo_url
            )
        elif logo_url is not None:
            if logo_url and not logo_url.strip():
                raise ValueError("Logo URL不能为空字符串")
            self.site_config = SiteConfiguration(
                site_name=self.site_config.site_name,
                logo_url=logo_url.strip() if logo_url else None
            )
        
        self.updated_at = datetime.utcnow()
    
    def update_ai_model_config(self, default_model_id: Optional[str] = None) -> None:
        """更新AI模型配置"""
        if default_model_id is not None:
            if default_model_id and not default_model_id.strip():
                raise ValueError("默认AI模型ID不能为空字符串")
            self.ai_model_config = AIModelConfig(
                default_model_id=default_model_id.strip() if default_model_id else None
            )
            self.updated_at = datetime.utcnow()
    
    def set_maintenance_mode(self, enabled: bool) -> None:
        """设置维护模式"""
        self.maintenance_mode = MaintenanceMode.ENABLED if enabled else MaintenanceMode.DISABLED
        self.updated_at = datetime.utcnow()
    
    def set_user_registration(self, enabled: bool) -> None:
        """设置用户注册开关"""
        self.user_registration_config = UserRegistrationConfig(enabled=enabled)
        self.updated_at = datetime.utcnow()
    
    def is_maintenance_mode(self) -> bool:
        """检查是否处于维护模式"""
        return self.maintenance_mode == MaintenanceMode.ENABLED
    
    def is_user_registration_enabled(self) -> bool:
        """检查用户注册是否启用"""
        return self.user_registration_config.enabled
    
    @classmethod
    def create_default(cls, id: str) -> "SystemSettings":
        """创建默认系统设置"""
        return cls(
            id=id,
            site_config=SiteConfiguration(
                site_name="安美智能咨询系统",
                logo_url="/logo.png"
            ),
            ai_model_config=AIModelConfig(default_model_id=None),
            maintenance_mode=MaintenanceMode.DISABLED,
            user_registration_config=UserRegistrationConfig(enabled=True)
        )
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "site_name": self.site_config.site_name,
            "logo_url": self.site_config.logo_url,
            "default_model_id": self.ai_model_config.default_model_id,
            "maintenance_mode": self.maintenance_mode.value,
            "user_registration_enabled": self.user_registration_config.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
