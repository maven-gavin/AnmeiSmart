"""
系统设置领域异常

定义系统设置相关的业务异常
"""


class SystemSettingsError(Exception):
    """系统设置基础异常"""
    pass


class SystemSettingsNotFoundError(SystemSettingsError):
    """系统设置未找到异常"""
    pass


class SystemSettingsValidationError(SystemSettingsError):
    """系统设置验证失败异常"""
    pass


class MaintenanceModeError(SystemSettingsError):
    """维护模式操作异常"""
    pass


class AIModelConfigError(SystemSettingsError):
    """AI模型配置异常"""
    pass


class SiteConfigurationError(SystemSettingsError):
    """站点配置异常"""
    pass


class UserRegistrationConfigError(SystemSettingsError):
    """用户注册配置异常"""
    pass

