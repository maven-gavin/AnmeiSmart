from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.system.domain.value_objects.system_config import (
    SystemStatus,
    MaintenanceMode,
    SiteConfiguration,
    UserRegistrationConfig,
    AIModelConfig,
)
from app.common.domain.entities.base_entity import BaseEntity, DomainEvent


def _current_utc_time() -> datetime:
    return datetime.now(timezone.utc)


class SystemSettingsEntity(BaseEntity):
    """系统设置聚合根"""

    def __init__(
        self,
        id: str,
        siteConfig: SiteConfiguration,
        aiModelConfig: AIModelConfig,
        maintenanceMode: MaintenanceMode,
        userRegistrationConfig: UserRegistrationConfig,
        createdAt: Optional[datetime] = None,
        updatedAt: Optional[datetime] = None,
    ):
        super().__init__(id)
        self.siteConfig = siteConfig
        self.aiModelConfig = aiModelConfig
        self.maintenanceMode = maintenanceMode
        self.userRegistrationConfig = userRegistrationConfig
        self.createdAt = createdAt or _current_utc_time()
        self.updatedAt = updatedAt or _current_utc_time()
        self.validate()

    def validate(self) -> None:
        if not self.id:
            raise ValueError("系统设置ID不能为空")
        if not self.siteConfig:
            raise ValueError("站点配置不能为空")
        if not self.aiModelConfig:
            raise ValueError("AI模型配置不能为空")
        if self.maintenanceMode is None:
            raise ValueError("维护模式配置不能为空")
        if not self.userRegistrationConfig:
            raise ValueError("用户注册配置不能为空")

    @property
    def systemStatus(self) -> SystemStatus:
        if self.maintenanceMode == MaintenanceMode.ENABLED:
            return SystemStatus.MAINTENANCE
        return SystemStatus.NORMAL

    def updateSiteConfig(self, siteName: Optional[str] = None, logoUrl: Optional[str] = None) -> None:
        previous: Dict[str, Optional[str]] = {
            "oldSiteName": self.siteConfig.site_name,
            "oldLogoUrl": self.siteConfig.logo_url,
        }

        if siteName is not None:
            if not siteName.strip():
                raise ValueError("站点名称不能为空")
            self.siteConfig = SiteConfiguration(
                site_name=siteName.strip(),
                logo_url=logoUrl if logoUrl is not None else self.siteConfig.logo_url,
            )
        elif logoUrl is not None:
            if logoUrl and not logoUrl.strip():
                raise ValueError("Logo URL不能为空字符串")
            self.siteConfig = SiteConfiguration(
                site_name=self.siteConfig.site_name,
                logo_url=logoUrl.strip() if logoUrl else None,
            )
        else:
            return

        self.updatedAt = _current_utc_time()
        self._add_domain_event(
            DomainEvent(
                event_type="system_site_config_updated",
                aggregate_id=self.id,
                data={
                    **previous,
                    "newSiteName": self.siteConfig.site_name,
                    "newLogoUrl": self.siteConfig.logo_url,
                },
            )
        )

    def updateAiModelConfig(self, defaultModelId: Optional[str] = None) -> None:
        previous_model_id = self.aiModelConfig.default_model_id

        if defaultModelId is not None:
            if defaultModelId and not defaultModelId.strip():
                raise ValueError("默认AI模型ID不能为空字符串")
            self.aiModelConfig = AIModelConfig(
                default_model_id=defaultModelId.strip() if defaultModelId else None
            )
            self.updatedAt = _current_utc_time()
            self._add_domain_event(
                DomainEvent(
                    event_type="system_ai_model_config_updated",
                    aggregate_id=self.id,
                    data={
                        "oldModelId": previous_model_id,
                        "newModelId": self.aiModelConfig.default_model_id,
                    },
                )
            )

    def setMaintenanceMode(self, enabled: bool) -> None:
        previous_mode = self.maintenanceMode
        self.maintenanceMode = MaintenanceMode.ENABLED if enabled else MaintenanceMode.DISABLED
        self.updatedAt = _current_utc_time()
        self._add_domain_event(
            DomainEvent(
                event_type="system_maintenance_mode_changed",
                aggregate_id=self.id,
                data={
                    "oldMode": previous_mode.value,
                    "newMode": self.maintenanceMode.value,
                    "enabled": enabled,
                },
            )
        )

    def setUserRegistration(self, enabled: bool) -> None:
        previous_enabled = self.userRegistrationConfig.enabled
        self.userRegistrationConfig = UserRegistrationConfig(enabled=enabled)
        self.updatedAt = _current_utc_time()
        self._add_domain_event(
            DomainEvent(
                event_type="system_user_registration_changed",
                aggregate_id=self.id,
                data={
                    "oldEnabled": previous_enabled,
                    "newEnabled": enabled,
                },
            )
        )

    def isMaintenanceMode(self) -> bool:
        return self.maintenanceMode == MaintenanceMode.ENABLED

    def isUserRegistrationEnabled(self) -> bool:
        return self.userRegistrationConfig.enabled

    @classmethod
    def createDefault(cls, settingsId: str) -> "SystemSettingsEntity":
        settings = cls(
            id=settingsId,
            siteConfig=SiteConfiguration(site_name="安美智能咨询系统", logo_url="/logo.png"),
            aiModelConfig=AIModelConfig(default_model_id=None),
            maintenanceMode=MaintenanceMode.DISABLED,
            userRegistrationConfig=UserRegistrationConfig(enabled=True),
        )
        settings.validate()
        return settings

    def toDict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "siteName": self.siteConfig.site_name,
            "logoUrl": self.siteConfig.logo_url,
            "defaultModelId": self.aiModelConfig.default_model_id,
            "maintenanceMode": self.maintenanceMode.value,
            "userRegistrationEnabled": self.userRegistrationConfig.enabled,
            "createdAt": self.createdAt,
            "updatedAt": self.updatedAt,
        }

    def __str__(self) -> str:
        return (
            f"SystemSettingsEntity(id={self.id}, maintenanceMode={self.maintenanceMode}, "
            f"userRegistrationEnabled={self.userRegistrationConfig.enabled})"
        )

    def __repr__(self) -> str:
        return (
            "SystemSettingsEntity("
            f"id={self.id}, "
            f"siteConfig={self.siteConfig}, "
            f"aiModelConfig={self.aiModelConfig}, "
            f"maintenanceMode={self.maintenanceMode}, "
            f"userRegistrationConfig={self.userRegistrationConfig}, "
            f"createdAt={self.createdAt}, "
            f"updatedAt={self.updatedAt}"
            ")"
        )
