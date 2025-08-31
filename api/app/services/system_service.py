from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.system import SystemSettings as ORMSystemSettings
from app.schemas.system import (
    SystemSettingsUpdate, SystemSettings, SystemSettingsResponse
)


def get_system_settings(db: Session) -> SystemSettingsResponse:
    """
    获取系统设置及所有AI模型配置
    :param db: 数据库会话
    :return: SystemSettingsResponse
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    
    settings_schema = SystemSettings(
        siteName=orm_settings.site_name,
        logoUrl=orm_settings.logo_url,
        defaultModelId=orm_settings.default_model_id,
        maintenanceMode=orm_settings.maintenance_mode,
        userRegistrationEnabled=orm_settings.user_registration_enabled
    )
    return SystemSettingsResponse(success=True, data=settings_schema, message="获取系统设置成功")


def update_system_settings(db: Session, settings_update: SystemSettingsUpdate) -> SystemSettingsResponse:
    """
    更新系统设置
    :param db: 数据库会话
    :param settings_update: 系统设置更新数据
    :return: SystemSettingsResponse
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    
    update_data = settings_update.model_dump(exclude_unset=True)
    # 映射camelCase到snake_case字段名
    field_mapping = {
        'siteName': 'site_name',
        'logoUrl': 'logo_url',
        'defaultModelId': 'default_model_id',
        'maintenanceMode': 'maintenance_mode',
        'userRegistrationEnabled': 'user_registration_enabled'
    }
    
    for key, value in update_data.items():
        if value is not None:
            # 使用映射的字段名
            db_field = field_mapping.get(key, key)
            if isinstance(db_field, str) and hasattr(orm_settings, db_field):
                setattr(orm_settings, db_field, value)
    
    db.commit()
    db.refresh(orm_settings)
    return get_system_settings(db)


 