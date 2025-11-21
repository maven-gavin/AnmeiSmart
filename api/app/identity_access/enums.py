import enum

class AdminLevel(str, enum.Enum):
    """管理员级别枚举"""
    BASIC = "basic"           # 基础管理员
    ADVANCED = "advanced"     # 高级管理员
    SUPER = "super"           # 超级管理员

