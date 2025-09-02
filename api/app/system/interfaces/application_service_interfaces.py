from abc import ABC, abstractmethod
from app.system.schemas.system import SystemSettingsResponse, SystemSettingsUpdate


class ISystemApplicationService(ABC):
    """系统设置应用服务接口"""
    
    @abstractmethod
    async def get_system_settings(self) -> SystemSettingsResponse:
        """获取系统设置用例"""
        pass
    
    @abstractmethod
    async def update_system_settings(self, settings_update: SystemSettingsUpdate) -> SystemSettingsResponse:
        """更新系统设置用例"""
        pass
    
    @abstractmethod
    async def get_system_health(self) -> dict:
        """获取系统健康状态用例"""
        pass
