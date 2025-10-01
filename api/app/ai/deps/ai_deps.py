"""
AI模块依赖注入配置

提供AI服务的依赖注入函数，统一管理AI相关服务的创建和配置。
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
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
from app.ai.application.agent_chat_service import AgentChatApplicationService
from app.ai.infrastructure.dify_agent_client import DifyAgentClientFactory
from app.chat.infrastructure.conversation_repository import ConversationRepository
from app.chat.infrastructure.message_repository import MessageRepository
from app.websocket import get_websocket_service_dependency


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


def get_agent_chat_service(
    db: Session = Depends(get_db),
    websocket_service = Depends(get_websocket_service_dependency)
) -> AgentChatApplicationService:
    """
    获取 Agent 对话应用服务实例
    
    依赖注入配置：
    - 数据库会话
    - WebSocket 服务（用于广播）
    """
    # 创建仓储实例
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    
    # 获取广播服务
    broadcasting_service = websocket_service.broadcasting_service if websocket_service else None
    
    # 创建 Dify Agent 客户端工厂
    dify_client_factory = DifyAgentClientFactory()
    
    # 创建并返回应用服务
    return AgentChatApplicationService(
        dify_client_factory=dify_client_factory,
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        broadcasting_service=broadcasting_service,
        db=db
    )
