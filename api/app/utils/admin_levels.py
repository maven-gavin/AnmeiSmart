"""
管理员级别工具模块

提供管理员级别相关的辅助函数和权限检查工具
"""

from typing import Optional
from app.identity_access.enums import AdminLevel
from app.identity_access.models.user import User


class AdminLevelHelper:
    """管理员级别辅助类"""
    
    @staticmethod
    def get_level_description(level: str) -> str:
        """获取管理员级别的中文描述"""
        descriptions = {
            AdminLevel.BASIC: "基础管理员 - 具有基本的系统管理权限",
            AdminLevel.ADVANCED: "高级管理员 - 具有进阶的系统管理权限", 
            AdminLevel.SUPER: "超级管理员 - 具有完整的系统管理权限"
        }
        return descriptions.get(level, "未知级别")
    
    @staticmethod
    def get_level_priority(level: str) -> int:
        """获取管理员级别的优先级（数字越大权限越高）"""
        priorities = {
            AdminLevel.BASIC: 1,
            AdminLevel.ADVANCED: 2,
            AdminLevel.SUPER: 3
        }
        return priorities.get(level, 0)
    
    @staticmethod
    def can_manage_level(manager_level: str, target_level: str) -> bool:
        """检查管理员是否可以管理指定级别的用户
        
        Args:
            manager_level: 管理员自己的级别
            target_level: 目标用户的级别
            
        Returns:
            bool: 是否可以管理
        """
        manager_priority = AdminLevelHelper.get_level_priority(manager_level)
        target_priority = AdminLevelHelper.get_level_priority(target_level)
        
        # 只能管理同级或低级别的用户
        return manager_priority >= target_priority
    
    @staticmethod
    def is_super_admin(user: User) -> bool:
        """检查用户是否为超级管理员
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 是否为超级管理员
        """
        if not user.administrator:
            return False
        return user.administrator.admin_level == AdminLevel.SUPER
    
    @staticmethod
    def get_user_admin_level(user: User) -> Optional[str]:
        """获取用户的管理员级别
        
        Args:
            user: 用户对象
            
        Returns:
            Optional[str]: 管理员级别，如果不是管理员则返回None
        """
        if not user.administrator:
            return None
        return user.administrator.admin_level


# 便捷的常量导出
ADMIN_LEVELS = {
    'BASIC': AdminLevel.BASIC,
    'ADVANCED': AdminLevel.ADVANCED, 
    'SUPER': AdminLevel.SUPER
}


def create_admin_info(level: str = AdminLevel.BASIC, permissions: str = None) -> dict:
    """创建管理员信息的便捷函数
    
    Args:
        level: 管理员级别
        permissions: 权限描述
        
    Returns:
        dict: 管理员信息字典
    """
    return {
        "admin_level": level,
        "access_permissions": permissions or AdminLevelHelper.get_level_description(level)
    }


# 使用示例和说明
"""
使用示例：

1. 创建不同级别的管理员：
   basic_admin = create_admin_info(AdminLevel.BASIC, "用户管理权限")
   super_admin = create_admin_info(AdminLevel.SUPER, "全局系统管理权限")

2. 检查权限：
   if AdminLevelHelper.is_super_admin(user):
       # 执行需要超级管理员权限的操作
       pass
   
   if AdminLevelHelper.can_manage_level(current_user_level, target_user_level):
       # 可以管理该用户
       pass

3. 获取级别信息：
   description = AdminLevelHelper.get_level_description(user.administrator.admin_level)
   priority = AdminLevelHelper.get_level_priority(user.administrator.admin_level)
""" 