from abc import ABC, abstractmethod
from typing import Optional
from app.system.domain.entities.system_settings import SystemSettings


class ISystemSettingsRepository(ABC):
    """系统设置仓储接口"""
    
    @abstractmethod
    async def get_system_settings(self) -> Optional[SystemSettings]:
        """获取系统设置"""
        pass
    
    @abstractmethod
    async def save_system_settings(self, settings: SystemSettings) -> SystemSettings:
        """保存系统设置"""
        pass
    
    @abstractmethod
    async def create_default_system_settings(self, settings_id: str) -> SystemSettings:
        """创建默认系统设置"""
        pass
    
    @abstractmethod
    async def exists(self) -> bool:
        """检查系统设置是否存在"""
        pass
