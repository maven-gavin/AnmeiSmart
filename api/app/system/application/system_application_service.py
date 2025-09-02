from typing import Optional
from app.system.interfaces.application_service_interfaces import ISystemApplicationService
from app.system.interfaces.repository_interfaces import ISystemSettingsRepository
from app.system.interfaces.domain_service_interfaces import ISystemDomainService
from app.system.domain.entities.system_settings import SystemSettings
from app.system.schemas.system import SystemSettingsResponse, SystemSettingsUpdate
from app.common.infrastructure.db.uuid_utils import system_id
import logging

logger = logging.getLogger(__name__)


class SystemApplicationService(ISystemApplicationService):
    """系统设置应用服务 - 用例编排和事务管理"""
    
    def __init__(
        self,
        system_settings_repository: ISystemSettingsRepository,
        system_domain_service: ISystemDomainService
    ):
        self.system_settings_repository = system_settings_repository
        self.system_domain_service = system_domain_service
    
    async def get_system_settings(self) -> SystemSettingsResponse:
        """获取系统设置用例"""
        try:
            # 获取系统设置
            settings = await self.system_settings_repository.get_system_settings()
            
            if not settings:
                # 如果不存在，创建默认设置
                settings = await self.system_settings_repository.create_default_system_settings(
                    system_id()
                )
                logger.info("创建了默认系统设置")
            
            # 验证设置有效性
            if not self.system_domain_service.validate_system_settings(settings):
                raise ValueError("系统设置验证失败")
            
            # 转换为响应格式
            from app.system.converters.system_settings_converter import SystemSettingsConverter
            settings_schema = SystemSettingsConverter.to_response(settings)
            
            return SystemSettingsResponse(
                success=True,
                data=settings_schema,
                message="获取系统设置成功"
            )
            
        except Exception as e:
            logger.error(f"获取系统设置失败: {e}")
            raise
    
    async def update_system_settings(self, settings_update: SystemSettingsUpdate) -> SystemSettingsResponse:
        """更新系统设置用例"""
        try:
            # 获取当前设置
            current_settings = await self.system_settings_repository.get_system_settings()
            if not current_settings:
                raise RuntimeError("系统设置未找到，请先初始化系统")
            
            # 应用更新
            from app.system.converters.system_settings_converter import SystemSettingsConverter
            update_data = SystemSettingsConverter.from_update_request(settings_update)
            
            # 更新站点配置
            if 'site_name' in update_data or 'logo_url' in update_data:
                current_settings.update_site_config(
                    site_name=update_data.get('site_name'),
                    logo_url=update_data.get('logo_url')
                )
            
            # 更新AI模型配置
            if 'default_model_id' in update_data:
                if not self.system_domain_service.validate_ai_model_config(update_data['default_model_id']):
                    raise ValueError("AI模型配置无效")
                current_settings.update_ai_model_config(update_data['default_model_id'])
            
            # 更新维护模式
            if 'maintenance_mode' in update_data:
                if update_data['maintenance_mode']:
                    if not self.system_domain_service.can_enable_maintenance_mode(current_settings):
                        raise ValueError("当前无法启用维护模式")
                else:
                    if not self.system_domain_service.can_disable_maintenance_mode(current_settings):
                        raise ValueError("当前无法禁用维护模式")
                current_settings.set_maintenance_mode(update_data['maintenance_mode'])
            
            # 更新用户注册设置
            if 'user_registration_enabled' in update_data:
                current_settings.set_user_registration(update_data['user_registration_enabled'])
            
            # 验证更新后的设置
            if not self.system_domain_service.validate_system_settings(current_settings):
                raise ValueError("更新后的系统设置验证失败")
            
            # 保存到数据库
            updated_settings = await self.system_settings_repository.save_system_settings(current_settings)
            
            # 转换为响应格式
            settings_schema = SystemSettingsConverter.to_response(updated_settings)
            
            # 通知相关服务配置变更
            await self._notify_config_change()
            
            return SystemSettingsResponse(
                success=True,
                data=settings_schema,
                message="系统设置更新成功"
            )
            
        except Exception as e:
            logger.error(f"更新系统设置失败: {e}")
            raise
    
    async def get_system_health(self) -> dict:
        """获取系统健康状态用例"""
        try:
            settings = await self.system_settings_repository.get_system_settings()
            if not settings:
                return {"status": "error", "message": "系统设置未初始化"}
            
            health_status = self.system_domain_service.get_system_health_status(settings)
            
            return {
                "status": health_status,
                "maintenance_mode": settings.is_maintenance_mode(),
                "user_registration_enabled": settings.is_user_registration_enabled(),
                "last_updated": settings.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取系统健康状态失败: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _notify_config_change(self):
        """通知相关服务配置已更改"""
        try:
            # 清除AI服务的全局实例，强制重新加载配置
            from app.ai.application import _ai_service_instance
            if _ai_service_instance:
                _ai_service_instance.reload_configurations()
            
            logger.info("AI服务配置变更通知已发送")
            
        except Exception as e:
            logger.error(f"通知AI服务配置变更失败: {e}")
            # 不抛出异常，避免影响主要业务流程
