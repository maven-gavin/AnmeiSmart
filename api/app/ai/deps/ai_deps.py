"""
AI模块依赖注入配置

提供AI服务的依赖注入函数，统一管理AI相关服务的创建和配置。
"""

from app.ai.ai_gateway_service import get_ai_gateway_service
from app.ai.application.agent_config_service import (
    get_agent_configs,
    get_agent_config,
    get_agent_configs_by_environment,
    get_active_agent_configs,
    create_agent_config,
    update_agent_config,
    delete_agent_config,
    reload_ai_gateway_service
)


def get_agent_config_service():
    """获取Agent配置服务函数集合"""
    return {
        "get_agent_configs": get_agent_configs,
        "get_agent_config": get_agent_config,
        "get_agent_configs_by_environment": get_agent_configs_by_environment,
        "get_active_agent_configs": get_active_agent_configs,
        "create_agent_config": create_agent_config,
        "update_agent_config": update_agent_config,
        "delete_agent_config": delete_agent_config,
        "reload_ai_gateway_service": reload_ai_gateway_service
    }
