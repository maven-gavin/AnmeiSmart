"""
AI模块依赖注入配置

管理AI服务的依赖关系，提供统一的依赖注入接口。
"""

from .ai_deps import *

__all__ = [
    "get_ai_service",
    "get_ai_gateway_service",
    "get_agent_config_service",
    "get_agent_chat_service"
]
