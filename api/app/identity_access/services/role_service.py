"""
角色服务 - 角色管理逻辑
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.identity_access.models.user import Role, User
from app.identity_access.schemas.user import RoleCreate, RoleUpdate
from app.core.api import BusinessException, ErrorCode

class RoleService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_roles(self, search: Optional[str] = None, include_system: bool = True) -> List[Role]:
        """获取所有角色"""
        query = self.db.query(Role)
        # 加载租户关系
        query = query.options(joinedload(Role.tenant))
        
        if not include_system:
            query = query.filter(Role.is_system == False)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Role.name.ilike(search_term)) | 
                (Role.display_name.ilike(search_term))
            )
            
        return query.order_by(Role.priority.desc()).all()

    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """根据ID获取角色"""
        return self.db.query(Role).options(joinedload(Role.tenant)).filter(Role.id == role_id).first()
        
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        return self.db.query(Role).filter(Role.name == name).first()

    def create_role(self, role_in: RoleCreate) -> Role:
        """创建角色"""
        if self.get_role_by_name(role_in.name):
            raise BusinessException("角色名称已存在", code=ErrorCode.BUSINESS_ERROR)
            
        role_data = role_in.model_dump()
        role = Role(**role_data)
        
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def update_role(self, role_id: str, role_data: RoleUpdate) -> Role:
        """更新角色"""
        role = self.get_role_by_id(role_id)
        if not role:
            raise BusinessException("角色不存在", code=ErrorCode.NOT_FOUND)
            
        if role_data.name and role_data.name != role.name:
            if self.get_role_by_name(role_data.name):
                raise BusinessException("角色名称已存在", code=ErrorCode.BUSINESS_ERROR)
        
        update_dict = role_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(role, field, value)
            
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        role = self.get_role_by_id(role_id)
        if not role:
            raise BusinessException("角色不存在", code=ErrorCode.NOT_FOUND)
            
        if role.is_system:
             raise BusinessException("系统角色无法删除", code=ErrorCode.PERMISSION_DENIED)
             
        self.db.delete(role)
        self.db.commit()
        return True
        
    async def check_permission(self, user_id: str, permission_code: str) -> bool:
        """
        检查用户权限
        基于 Permission.code 进行判断
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
            
        for role in user.roles:
            if role.is_admin or role.name in ["administrator", "super_admin"]:
                return True
                
            # 检查具体权限关联
            for perm in role.permissions:
                if perm.code == permission_code:
                    return True
        
        return False

