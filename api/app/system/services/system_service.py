"""
系统服务 - 核心业务逻辑
处理系统设置CRUD、系统健康检查等功能
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.system.models.system import SystemSettings
from app.system.schemas.system import SystemSettingsUpdate, SystemSettingsResponse, SystemSettings
from app.common.deps.uuid_utils import system_id
from app.core.api import BusinessException, ErrorCode

logger = logging.getLogger(__name__)


class SystemService:
    """系统服务 - 直接操作数据库模型"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_system_settings(self) -> SystemSettingsResponse:
        """获取系统设置"""
        settings = self.db.query(SystemSettings).first()
        
        if not settings:
            # 创建默认设置
            settings = SystemSettings(
                id=system_id(),
                site_name="安美智能咨询系统",
                logo_url="/logo.png",
                default_model_id=None,
                maintenance_mode=False,
                user_registration_enabled=True
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
            logger.info("创建了默认系统设置")
        
        # 手动构建响应Schema（因为字段名不同：snake_case vs camelCase）
        settings_schema = SystemSettings(
            siteName=settings.site_name,
            logoUrl=settings.logo_url,
            defaultModelId=settings.default_model_id,
            maintenanceMode=settings.maintenance_mode,
            userRegistrationEnabled=settings.user_registration_enabled
        )
        
        return SystemSettingsResponse(
            success=True,
            data=settings_schema,
            message="获取系统设置成功"
        )
    
    def update_system_settings(self, settings_update: SystemSettingsUpdate) -> SystemSettingsResponse:
        """更新系统设置"""
        settings = self.db.query(SystemSettings).first()
        
        if not settings:
            raise BusinessException("系统设置未找到，请先初始化系统", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 更新字段
        update_dict = settings_update.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            # 转换camelCase到snake_case
            if key == "siteName":
                setattr(settings, "site_name", value)
            elif key == "logoUrl":
                setattr(settings, "logo_url", value)
            elif key == "defaultModelId":
                setattr(settings, "default_model_id", value)
            elif key == "maintenanceMode":
                setattr(settings, "maintenance_mode", value)
            elif key == "userRegistrationEnabled":
                setattr(settings, "user_registration_enabled", value)
            else:
                setattr(settings, key, value)
        
        self.db.commit()
        self.db.refresh(settings)
        
        # 手动构建响应Schema（因为字段名不同：snake_case vs camelCase）
        settings_schema = SystemSettings(
            siteName=settings.site_name,
            logoUrl=settings.logo_url,
            defaultModelId=settings.default_model_id,
            maintenanceMode=settings.maintenance_mode,
            userRegistrationEnabled=settings.user_registration_enabled
        )
        
        return SystemSettingsResponse(
            success=True,
            data=settings_schema,
            message="更新系统设置成功"
        )
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        from datetime import datetime
        
        try:
            # 检查数据库连接
            self.db.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            db_status = "unhealthy"
        
        health_status = {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "components": {
                "database": db_status,
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return health_status

