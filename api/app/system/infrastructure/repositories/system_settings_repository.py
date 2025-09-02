from typing import Optional
from sqlalchemy.orm import Session
from app.system.interfaces.repository_interfaces import ISystemSettingsRepository
from app.system.domain.entities.system_settings import SystemSettings
from app.common.infrastructure.db.uuid_utils import system_id


class SystemSettingsRepository(ISystemSettingsRepository):
    """系统设置仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_system_settings(self) -> Optional[SystemSettings]:
        """获取系统设置"""
        # 延迟导入避免循环依赖
        from app.system.infrastructure.db.system import SystemSettings as ORMSystemSettings
        from app.system.converters.system_settings_converter import SystemSettingsConverter
        
        orm_settings = self.db.query(ORMSystemSettings).first()
        if not orm_settings:
            return None
        
        return SystemSettingsConverter.from_model(orm_settings)
    
    async def save_system_settings(self, settings: SystemSettings) -> SystemSettings:
        """保存系统设置"""
        # 延迟导入避免循环依赖
        from app.system.infrastructure.db.system import SystemSettings as ORMSystemSettings
        from app.system.converters.system_settings_converter import SystemSettingsConverter
        
        # 检查是否已存在
        existing_settings = self.db.query(ORMSystemSettings).first()
        
        if existing_settings:
            # 更新现有记录
            update_data = SystemSettingsConverter.to_model_dict(settings)
            for key, value in update_data.items():
                if key != 'id':  # 不更新ID
                    setattr(existing_settings, key, value)
            self.db.commit()
            self.db.refresh(existing_settings)
            return SystemSettingsConverter.from_model(existing_settings)
        else:
            # 创建新记录
            new_settings = ORMSystemSettings(**SystemSettingsConverter.to_model_dict(settings))
            self.db.add(new_settings)
            self.db.commit()
            self.db.refresh(new_settings)
            return SystemSettingsConverter.from_model(new_settings)
    
    async def create_default_system_settings(self, settings_id: str) -> SystemSettings:
        """创建默认系统设置"""
        default_settings = SystemSettings.create_default(settings_id)
        return await self.save_system_settings(default_settings)
    
    async def exists(self) -> bool:
        """检查系统设置是否存在"""
        # 延迟导入避免循环依赖
        from app.system.infrastructure.db.system import SystemSettings as ORMSystemSettings
        
        return self.db.query(ORMSystemSettings).first() is not None
