"""
租户类型值对象

定义租户的类型枚举。
"""

from enum import Enum


class TenantType(Enum):
    """租户类型枚举"""
    
    SYSTEM = "system"           # 系统租户
    STANDARD = "standard"       # 标准租户
    PREMIUM = "premium"         # 高级租户
    ENTERPRISE = "enterprise"   # 企业租户
    
    @classmethod
    def get_system_types(cls) -> list["TenantType"]:
        """获取系统类型列表"""
        return [cls.SYSTEM]
    
    @classmethod
    def get_business_types(cls) -> list["TenantType"]:
        """获取业务类型列表"""
        return [cls.STANDARD, cls.PREMIUM, cls.ENTERPRISE]
    
    def is_system_type(self) -> bool:
        """检查是否为系统类型"""
        return self == self.SYSTEM
    
    def is_business_type(self) -> bool:
        """检查是否为业务类型"""
        return self in self.get_business_types()
    
    def get_priority(self) -> int:
        """获取类型优先级（数字越大优先级越高）"""
        priority_map = {
            self.SYSTEM: 1000,
            self.ENTERPRISE: 300,
            self.PREMIUM: 200,
            self.STANDARD: 100
        }
        return priority_map.get(self, 0)
