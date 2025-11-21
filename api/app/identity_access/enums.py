import enum

class AdminLevel(str, enum.Enum):
    """管理员级别枚举"""
    BASIC = "basic"           # 基础管理员
    ADVANCED = "advanced"     # 高级管理员
    SUPER = "super"           # 超级管理员

class TenantStatus(str, enum.Enum):
    """租户状态枚举"""
    ACTIVE = "active"       # 正常
    INACTIVE = "inactive"   # 停用
    SUSPENDED = "suspended" # 挂起
    PENDING = "pending"     # 待审核

class TenantType(str, enum.Enum):
    """租户类型枚举"""
    STANDARD = "standard"       # 标准租户
    ENTERPRISE = "enterprise"   # 企业租户
    TRIAL = "trial"             # 试用租户

class ResourceType(str, enum.Enum):
    """资源类型枚举"""
    API = "api"       # API接口
    MENU = "menu"     # 菜单
    BUTTON = "button" # 按钮

class PermissionType(str, enum.Enum):
    """权限类型枚举"""
    ACTION = "action"   # 操作权限
    DATA = "data"       # 数据权限
    MENU = "menu"       # 菜单权限

class PermissionScope(str, enum.Enum):
    """权限范围枚举"""
    TENANT = "tenant"     # 租户级别
    GLOBAL = "global"     # 全局级别 (系统级)
    DEPARTMENT = "department" # 部门级别
    PERSONAL = "personal" # 个人级别
