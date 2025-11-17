"""
资源类型值对象

定义资源的类型枚举。
"""

from enum import Enum


class ResourceType(Enum):
    """资源类型枚举"""
    
    API = "api"           # API资源（后端API端点）
    MENU = "menu"         # 菜单资源（前端菜单项）
    
    @classmethod
    def get_api_types(cls) -> list["ResourceType"]:
        """获取API类型列表"""
        return [cls.API]
    
    @classmethod
    def get_menu_types(cls) -> list["ResourceType"]:
        """获取菜单类型列表"""
        return [cls.MENU]
    
    def is_api_type(self) -> bool:
        """检查是否为API类型"""
        return self == self.API
    
    def is_menu_type(self) -> bool:
        """检查是否为菜单类型"""
        return self == self.MENU

