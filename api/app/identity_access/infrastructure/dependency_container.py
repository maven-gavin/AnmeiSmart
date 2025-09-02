"""
依赖注入容器

管理身份访问模块的依赖关系，解决循环导入问题。
"""

# 延迟导入避免循环依赖
# from .repositories.user_repository import UserRepository
# from .repositories.role_repository import RoleRepository
# from .repositories.login_history_repository import LoginHistoryRepository
# from ..converters.user_converter import UserConverter
# from ..converters.role_converter import RoleConverter


class IdentityAccessDependencyContainer:
    """身份访问模块依赖容器"""
    
    def __init__(self):
        self._user_converter = None
        self._role_converter = None
    
    @property
    def user_converter(self):
        """获取用户转换器实例"""
        if self._user_converter is None:
            from ..converters.user_converter import UserConverter
            self._user_converter = UserConverter()
        return self._user_converter
    
    @property
    def role_converter(self):
        """获取角色转换器实例"""
        if self._role_converter is None:
            from ..converters.role_converter import RoleConverter
            self._role_converter = RoleConverter()
        return self._role_converter
    
    def create_user_repository(self, db):
        """创建用户仓储实例"""
        from .repositories.user_repository import UserRepository
        return UserRepository(db, self.user_converter)
    
    def create_role_repository(self, db):
        """创建角色仓储实例"""
        from .repositories.role_repository import RoleRepository
        return RoleRepository(db, self.role_converter)
    
    def create_login_history_repository(self, db):
        """创建登录历史仓储实例"""
        from .repositories.login_history_repository import LoginHistoryRepository
        return LoginHistoryRepository(db)


# 全局依赖容器实例
dependency_container = IdentityAccessDependencyContainer()
