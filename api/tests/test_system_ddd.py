"""
系统设置DDD架构测试

测试领域实体、值对象、领域服务等各层的功能
"""

import pytest
from datetime import datetime
from app.system.domain.value_objects.system_config import (
    SystemStatus, 
    MaintenanceMode, 
    SiteConfiguration, 
    UserRegistrationConfig, 
    AIModelConfig
)
from app.system.domain.entities.system_settings import SystemSettingsEntity
from app.system.domain.system_domain_service import SystemDomainService
from app.system.domain.exceptions import (
    SystemSettingsValidationError,
    SiteConfigurationError
)


class TestSystemConfigValueObjects:
    """测试系统配置值对象"""
    
    def test_site_configuration_valid(self):
        """测试有效的站点配置"""
        config = SiteConfiguration(
            site_name="测试站点",
            logo_url="/test-logo.png"
        )
        assert config.site_name == "测试站点"
        assert config.logo_url == "/test-logo.png"
    
    def test_site_configuration_invalid_name(self):
        """测试无效的站点名称"""
        with pytest.raises(ValueError, match="站点名称不能为空"):
            SiteConfiguration(site_name="", logo_url="/logo.png")
    
    def test_site_configuration_invalid_logo_url(self):
        """测试无效的Logo URL"""
        with pytest.raises(ValueError, match="Logo URL不能为空字符串"):
            SiteConfiguration(site_name="测试站点", logo_url="")
    
    def test_user_registration_config(self):
        """测试用户注册配置"""
        config = UserRegistrationConfig(enabled=True)
        assert config.enabled is True
        
        config = UserRegistrationConfig(enabled=False)
        assert config.enabled is False
    
    def test_ai_model_config(self):
        """测试AI模型配置"""
        config = AIModelConfig(default_model_id="gpt-4")
        assert config.default_model_id == "gpt-4"
        
        config = AIModelConfig(default_model_id=None)
        assert config.default_model_id is None


class TestSystemSettingsEntity:
    """测试系统设置实体"""
    
    def test_create_default_system_settings(self):
        """测试创建默认系统设置"""
        settings = SystemSettingsEntity.createDefault("test-id")
        assert settings.id == "test-id"
        assert settings.siteConfig.site_name == "安美智能咨询系统"
        assert settings.maintenanceMode == MaintenanceMode.DISABLED
        assert settings.userRegistrationConfig.enabled is True
    
    def test_system_status_property(self):
        """测试系统状态属性"""
        settings = SystemSettingsEntity.createDefault("test-id")
        assert settings.systemStatus == SystemStatus.NORMAL
        
        settings.setMaintenanceMode(True)
        assert settings.systemStatus == SystemStatus.MAINTENANCE
    
    def test_update_site_config(self):
        """测试更新站点配置"""
        settings = SystemSettingsEntity.createDefault("test-id")
        original_updated_at = settings.updatedAt
        
        settings.updateSiteConfig(siteName="新站点名称")
        assert settings.siteConfig.site_name == "新站点名称"
        assert settings.updatedAt > original_updated_at
    
    def test_set_maintenance_mode(self):
        """测试设置维护模式"""
        settings = SystemSettingsEntity.createDefault("test-id")
        assert not settings.isMaintenanceMode()
        
        settings.setMaintenanceMode(True)
        assert settings.isMaintenanceMode()
        
        settings.setMaintenanceMode(False)
        assert not settings.isMaintenanceMode()
    
    def test_set_user_registration(self):
        """测试设置用户注册开关"""
        settings = SystemSettingsEntity.createDefault("test-id")
        assert settings.isUserRegistrationEnabled()
        
        settings.setUserRegistration(False)
        assert not settings.isUserRegistrationEnabled()
    
    def test_to_dict(self):
        """测试转换为字典"""
        settings = SystemSettingsEntity.createDefault("test-id")
        data = settings.toDict()
        
        assert data["id"] == "test-id"
        assert data["siteName"] == "安美智能咨询系统"
        assert data["maintenanceMode"] is False
        assert data["userRegistrationEnabled"] is True


class TestSystemDomainService:
    """测试系统领域服务"""
    
    def test_validate_system_settings(self):
        """测试验证系统设置"""
        service = SystemDomainService()
        settings = SystemSettingsEntity.createDefault("test-id")
        
        assert service.validate_system_settings(settings) is True
    
    def test_validate_ai_model_config(self):
        """测试验证AI模型配置"""
        service = SystemDomainService()
        
        assert service.validate_ai_model_config("gpt-4") is True
        assert service.validate_ai_model_config("") is False
        assert service.validate_ai_model_config(None) is True
    
    def test_get_system_health_status(self):
        """测试获取系统健康状态"""
        service = SystemDomainService()
        settings = SystemSettingsEntity.createDefault("test-id")
        
        assert service.get_system_health_status(settings) == "healthy"
        
        settings.setMaintenanceMode(True)
        assert service.get_system_health_status(settings) == "maintenance"


if __name__ == "__main__":
    pytest.main([__file__])
