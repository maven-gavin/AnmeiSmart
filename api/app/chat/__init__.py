"""
聊天服务模块 - 新架构
"""

# 导出控制器
from .controllers import chat_router

# 导出模型
from .models import Conversation, Message, ConversationParticipant, MessageAttachment

# 导出服务
from .services import ChatService

__all__ = [
    "chat_router",
    "Conversation",
    "Message", 
    "ConversationParticipant",
    "MessageAttachment",
    "ChatService",
]
