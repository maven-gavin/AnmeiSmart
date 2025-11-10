"""
聊天服务模块 - DDD架构重构完成
"""
# 导出应用服务层
from .application.chat_application_service import ChatApplicationService

# 导出领域层
from .domain.entities.conversation import ConversationEntity
from .domain.entities.message import MessageEntity
from .domain.conversation_domain_service import ConversationDomainService
from .domain.message_domain_service import MessageDomainService

# 导出基础设施层
from .infrastructure.conversation_repository import ConversationRepository
from .infrastructure.message_repository import MessageRepository

# 导出转换器
from .converters.conversation_converter import ConversationConverter
from .converters.message_converter import MessageConverter


__all__ = [
    # 应用服务层
    "ChatApplicationService",
    
    # 领域层
    "ConversationEntity",
    "MessageEntity",
    "ConversationDomainService",
    "MessageDomainService",
    
    # 基础设施层
    "ConversationRepository",
    "MessageRepository",
    
    # 转换器
    "ConversationConverter",
    "MessageConverter",
] 