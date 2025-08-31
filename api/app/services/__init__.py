# 导入所有服务模块
from . import system_service
from . import file_service
from . import notification_service
from . import agent_config_service

# 定义公共API（可选）
__all__ = [
    'system_service',
    'file_service',
    'notification_service',
    'agent_config_service'
]