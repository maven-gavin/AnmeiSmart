"""
统一数据库模型导入文件

确保所有数据库模型都被正确导入，避免SQLAlchemy映射错误。
按照DDD分层架构组织导入顺序。
"""

# 基础模型
from app.common.infrastructure.db.base_model import BaseModel

# 身份与权限模块
from app.identity_access.infrastructure.db.user import User, Role, Doctor, Consultant, Operator, Administrator
from app.identity_access.infrastructure.db.profile import UserPreferences, UserDefaultRole, LoginHistory

# 客户模块
from app.customer.infrastructure.db.customer import Customer, CustomerProfile

# 系统模块
from app.system.infrastructure.db.system import SystemSettings

# 聊天模块
from app.chat.infrastructure.db.chat import Conversation, Message
from app.chat.infrastructure.db.message_attachment import MessageAttachment

# 咨询模块
from app.consultation.infrastructure.db.plan_generation import PlanGenerationSession, PlanDraft, InfoCompleteness

# 数字人模块
from app.digital_humans.infrastructure.db.digital_human import DigitalHuman

# 通讯录模块
from app.contacts.infrastructure.db.contacts import ContactTag, ContactGroup, ContactPrivacySetting, Friendship

# 任务模块
from app.tasks.infrastructure.db.task import PendingTask

# MCP模块
from app.mcp.infrastructure.db.mcp import MCPToolGroup, MCPTool, MCPCallLog

# AI模块
from app.ai.infrastructure.db.agent_config import AgentConfig

# 通用模块
from app.common.infrastructure.db.upload import UploadSession, UploadChunk

# 确保所有模型都被导入，这样SQLAlchemy可以正确建立关系映射
__all__ = [
    # 基础模型
    "BaseModel",
    
    # 身份与权限模块
    "User", "Role", "Doctor", "Consultant", "Operator", "Administrator",
    "UserPreferences", "UserDefaultRole", "LoginHistory",
    
    # 客户模块
    "Customer", "CustomerProfile",
    
    # 系统模块
    "SystemSettings",
    
    # 聊天模块
    "Conversation", "Message", "MessageAttachment",
    
    # 咨询模块
    "PlanGenerationSession", "PlanDraft", "InfoCompleteness",
    
    # 数字人模块
    "DigitalHuman",
    
    # 通讯录模块
    "ContactTag", "ContactGroup", "ContactPrivacySetting", "Friendship",
    
    # 任务模块
    "PendingTask",
    
    # MCP模块
    "MCPToolGroup", "MCPTool", "MCPCallLog",
    
    # AI模块
    "AgentConfig",
    
    # 通用模块
    "UploadSession", "UploadChunk",
]
