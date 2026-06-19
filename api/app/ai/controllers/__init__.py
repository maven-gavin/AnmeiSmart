"""
AI模块控制器导出
"""

from .agent_knowledge import router as agent_knowledge_router
from .agent_config import router as agent_config_router
from .agent_chat import router as agent_chat_router
from .ai_gateway import router as ai_gateway_router

__all__ = [
    "agent_config_router",
    "agent_chat_router",
    "agent_knowledge_router",
    "ai_gateway_router",
]

