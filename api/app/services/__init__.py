# 导入所有服务模块
from . import user_service
from . import profile_service
from . import system_service
from . import consultant_service
from . import file_service
from . import notification_service
from . import agent_config_service

# 定义公共API（可选）
__all__ = [
    'user_service',
    'profile_service',
    'system_service',
    'consultant_service',
    'file_service',
    'notification_service',
    'agent_config_service'
]