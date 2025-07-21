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

# 可以在这里添加导出特定模型类的快捷方式
from .user import User, Role, Doctor, Consultant, Operator, Administrator
from .chat import Conversation, Message
from .customer import Customer, CustomerProfile
from .system import SystemSettings, AIModelConfig, DifyConfig
from .upload import UploadSession, UploadChunk  # 添加upload模型导出
from .consultant import PersonalizedPlan, ProjectType, SimulationImage, ProjectTemplate, CustomerPreference, PlanVersion  # 添加consultant模型导出 
from .plan_generation import PlanGenerationSession, PlanDraft, InfoCompleteness  # 添加plan_generation模型导出
from .profile import UserPreferences, UserDefaultRole, LoginHistory  # 添加profile模型导出 