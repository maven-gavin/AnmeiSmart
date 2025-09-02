"""
系统设置基础设施层

包含：
- 仓储实现：SystemSettingsRepository
- 数据库模型：SystemSettings
"""

from app.system.infrastructure.repositories.system_settings_repository import SystemSettingsRepository

__all__ = [
    "SystemSettingsRepository",
]
