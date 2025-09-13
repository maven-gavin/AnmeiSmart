from typing import Optional
from datetime import datetime, timezone
from app.system.domain.value_objects.system_config import (
    SystemStatus, 
    MaintenanceMode, 
    SiteConfiguration, 
    UserRegistrationConfig, 
    AIModelConfig
)
from app.common.domain.entities.base_entity import BaseEntity, DomainEvent

class SystemSettings(BaseEntity):
    """系统设置聚合根"""
    
    def __init__(
        self,
        id: str,
        site_config: SiteConfiguration,
        ai_model_config: AIModelConfig,
        maintenance_mode: MaintenanceMode,
        user_registration_config: UserRegistrationConfig,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        # 调用父类构造函数
        super().__init__(id)
        
        # 设置属性
        self.site_config = site_config
        self.ai_model_config = ai_model_config
        self.maintenance_mode = maintenance_mode
        self.user_registration_config = user_registration_config
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        
        # 验证实体状态
        self.validate()
    
    def validate(self) -> None:
        """验证实体状态 - 必须实现"""
        if not self.id:
            raise ValueError("系统设置ID不能为空")
        
        if not self.site_config:
            raise ValueError("站点配置不能为空")
        
        if not self.ai_model_config:
            raise ValueError("AI模型配置不能为空")
        
        if not self.maintenance_mode:
            raise ValueError("维护模式配置不能为空")
        
        if not self.user_registration_config:
            raise ValueError("用户注册配置不能为空")
    
    @property
    def system_status(self) -> SystemStatus:
        """获取当前系统状态"""
        if self.maintenance_mode == MaintenanceMode.ENABLED:
            return SystemStatus.MAINTENANCE
        return SystemStatus.NORMAL
    
    def update_site_config(self, site_name: Optional[str] = None, logo_url: Optional[str] = None) -> None:
        """更新站点配置"""
        old_site_name = self.site_config.site_name
        old_logo_url = self.site_config.logo_url
        
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
        
        self.updated_at = datetime.now(timezone.utc)
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="system_site_config_updated",
            aggregate_id=self.id,
            data={
                "old_site_name": old_site_name,
                "new_site_name": self.site_config.site_name,
                "old_logo_url": old_logo_url,
                "new_logo_url": self.site_config.logo_url
            }
        ))
    
    def update_ai_model_config(self, default_model_id: Optional[str] = None) -> None:
        """更新AI模型配置"""
        old_model_id = self.ai_model_config.default_model_id
        
        if default_model_id is not None:
            if default_model_id and not default_model_id.strip():
                raise ValueError("默认AI模型ID不能为空字符串")
            self.ai_model_config = AIModelConfig(
                default_model_id=default_model_id.strip() if default_model_id else None
            )
            self.updated_at = datetime.now(timezone.utc)
            
            # 添加领域事件
            self._add_domain_event(DomainEvent(
                event_type="system_ai_model_config_updated",
                aggregate_id=self.id,
                data={
                    "old_model_id": old_model_id,
                    "new_model_id": self.ai_model_config.default_model_id
                }
            ))
    
    def set_maintenance_mode(self, enabled: bool) -> None:
        """设置维护模式"""
        old_mode = self.maintenance_mode
        self.maintenance_mode = MaintenanceMode.ENABLED if enabled else MaintenanceMode.DISABLED
        self.updated_at = datetime.now(timezone.utc)
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="system_maintenance_mode_changed",
            aggregate_id=self.id,
            data={
                "old_mode": old_mode.value,
                "new_mode": self.maintenance_mode.value,
                "enabled": enabled
            }
        ))
    
    def set_user_registration(self, enabled: bool) -> None:
        """设置用户注册开关"""
        old_enabled = self.user_registration_config.enabled
        self.user_registration_config = UserRegistrationConfig(enabled=enabled)
        self.updated_at = datetime.now(timezone.utc)
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="system_user_registration_changed",
            aggregate_id=self.id,
            data={
                "old_enabled": old_enabled,
                "new_enabled": enabled
            }
        ))
    
    def is_maintenance_mode(self) -> bool:
        """检查是否处于维护模式"""
        return self.maintenance_mode == MaintenanceMode.ENABLED
    
    def is_user_registration_enabled(self) -> bool:
        """检查用户注册是否启用"""
        return self.user_registration_config.enabled
    
    @classmethod
    def create_default(cls, id: str) -> "SystemSettings":
        """创建默认系统设置"""
        settings = cls(
            id=id,
            site_config=SiteConfiguration(
                site_name="安美智能咨询系统",
                logo_url="/logo.png"
            ),
            ai_model_config=AIModelConfig(default_model_id=None),
            maintenance_mode=MaintenanceMode.DISABLED,
            user_registration_config=UserRegistrationConfig(enabled=True)
        )
        
        # 创建后必须验证
        settings.validate()
        return settings
    
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
