"""
Schema包初始化
按领域组织各种数据模型的导入
"""

# 聊天领域
from .chat import (
    MessageSender,
    MessageBase,
    MessageCreate,
    MessageCreateRequest,
    AIChatRequest,
    MessageInfo,
    ConversationBase,
    ConversationCreate,
    ConversationInfo,
    # 新增的消息内容结构
    TextMessageContent,
    MediaInfo,
    MediaMessageContent,
    SystemEventContent,
    # 便利函数
    create_text_message_content,
    create_media_message_content,
    create_system_event_content,
)

# 文件领域
from .file import (
    FileInfo,
    FileUploadResponse,
    FileUploadRequest,
    ChunkUploadRequest,
    UploadStatusResponse,
    CompleteUploadRequest,
    ResumableUploadInfo,
    StartResumableUploadRequest,
    StartResumableUploadResponse,
    CancelUploadResponse,
)

# WebSocket领域（目前未使用，保留供将来扩展）
from .websocket import (
    WebSocketMessage,
    WebSocketConnectionInfo,
    WebSocketError,
    WebSocketStats,
)

# 为了向后兼容，提供一些常用的导入别名
__all__ = [
    # 聊天领域
    "MessageSender",
    "MessageBase", 
    "MessageCreate",
    "MessageCreateRequest",
    "AIChatRequest",
    "MessageInfo",
    "ConversationBase",
    "ConversationCreate", 
    "ConversationInfo",
    # 新增的消息内容结构
    "TextMessageContent",
    "MediaInfo",
    "MediaMessageContent",
    "SystemEventContent",
    # 便利函数
    "create_text_message_content",
    "create_media_message_content",
    "create_system_event_content",
    
    # 文件领域
    "FileInfo",
    "FileUploadResponse",
    "FileUploadRequest",
    "ChunkUploadRequest",
    "UploadStatusResponse", 
    "CompleteUploadRequest",
    "ResumableUploadInfo",
    "StartResumableUploadRequest",
    "StartResumableUploadResponse",
    "CancelUploadResponse",
    
    # WebSocket领域
    "WebSocketMessage",
    "WebSocketConnectionInfo",
    "WebSocketError", 
    "WebSocketStats",
] 