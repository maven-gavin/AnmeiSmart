"""
依赖注入模块 - 统一入口，保持向后兼容

模块结构：
- common: 通用依赖（数据库、基础服务）
- auth: 认证相关依赖
- chat: 聊天相关依赖
- websocket: WebSocket相关依赖（未来扩展）
"""

# 重新导出所有依赖，保持向后兼容
from .common import get_db
from .auth import (
    get_current_user, 
    get_current_admin, 
    require_admin_role, 
    get_user_roles, 
    check_user_has_role,
    oauth2_scheme
)
from .chat import (
    get_message_repository,
    get_conversation_repository, 
    get_conversation_domain_service,
    get_message_domain_service,
    get_chat_application_service
)

__all__ = [
    # 通用依赖
    "get_db",
    
    # 认证依赖
    "get_current_user", 
    "get_current_admin", 
    "require_admin_role", 
    "get_user_roles", 
    "check_user_has_role",
    "oauth2_scheme",
    
    # 聊天依赖
    "get_message_repository",
    "get_conversation_repository", 
    "get_conversation_domain_service",
    "get_message_domain_service",
    "get_chat_application_service"
]
