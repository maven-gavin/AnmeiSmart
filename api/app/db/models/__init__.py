"""
数据库模型包
"""
# 导入所有模型模块，确保它们被包含在 Base.metadata 中
from . import user
from . import chat
from . import system
from . import customer

# 可以在这里添加导出特定模型类的快捷方式
from .user import User, Role, Doctor, Consultant, Operator, Administrator
from .chat import Conversation, Message
from .customer import Customer, CustomerProfile
from .system import SystemSettings, AIModelConfig 