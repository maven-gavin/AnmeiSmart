"""
AI模块依赖注入配置

提供AI服务的依赖注入函数，统一管理AI相关服务的创建和配置。
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.ai.ai_gateway_service import get_ai_gateway_service
from app.ai.services.agent_config_service import AgentConfigService
from app.ai.adapters.dify_agent_client import DifyAgentClientFactory
from app.chat.services.chat_service import ChatService
from app.chat.deps.chat import get_chat_service
from app.websocket.broadcasting_service import BroadcastingService
from app.websocket.broadcasting_factory import get_broadcasting_service_dependency


def get_agent_config_service(db: Session = Depends(get_db)) -> AgentConfigService:
    """获取Agent配置服务"""
    return AgentConfigService(db)


def get_agent_chat_service(
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
    broadcasting_service: BroadcastingService = Depends(get_broadcasting_service_dependency)
):
    """
    获取 Agent 对话服务实例
    
    依赖注入配置：
    - 数据库会话
    - Chat服务（用于会话和消息管理）
    - WebSocket 广播服务（用于实时消息推送）
    """
    from app.ai.services.agent_chat_service import AgentChatService
    
    # 创建 Dify Agent 客户端工厂
    dify_client_factory = DifyAgentClientFactory()
    
    # 创建并返回服务
    return AgentChatService(
        dify_client_factory=dify_client_factory,
        chat_service=chat_service,
        broadcasting_service=broadcasting_service,
        db=db
    )
