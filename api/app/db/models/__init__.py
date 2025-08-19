"""
数据库模型包
"""
# 导入所有模型模块，确保它们被包含在 Base.metadata 中
from . import user
from . import chat
from . import system
from . import customer
from . import upload  # 添加upload模块导入
from . import consultant  # 添加consultant模块导入
from . import plan_generation  # 添加plan_generation模块导入
from . import profile  # 添加profile模块导入
from . import mcp  # 添加mcp模块导入
from . import digital_human  # 添加digital_human模块导入
from . import message_attachment  # 添加message_attachment模块导入


# 可以在这里添加导出特定模型类的快捷方式
from .user import User, Role, Doctor, Consultant, Operator, Administrator
from .chat import Conversation, Message, ConversationParticipant
from .customer import Customer, CustomerProfile
from .system import SystemSettings, AIModelConfig, AgentConfig
from .upload import UploadSession, UploadChunk  # 添加upload模型导出
from .consultant import PersonalizedPlan, ProjectType, SimulationImage, ProjectTemplate, CustomerPreference, PlanVersion  # 添加consultant模型导出 
from .plan_generation import PlanGenerationSession, PlanDraft, InfoCompleteness  # 添加plan_generation模型导出
from .profile import UserPreferences, UserDefaultRole, LoginHistory  # 添加profile模型导出
from .mcp import MCPToolGroup, MCPTool, MCPCallLog  # 添加mcp模型导出
from .digital_human import DigitalHuman, DigitalHumanAgentConfig, ConsultationRecord, PendingTask  # 添加digital_human模型导出
from .message_attachment import MessageAttachment  # 添加message_attachment模型导出
 