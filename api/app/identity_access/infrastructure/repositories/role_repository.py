"""
角色仓储实现

实现角色数据访问的具体逻辑。
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.identity_access.infrastructure.db.user import Role as RoleModel
from ...interfaces.repository_interfaces import IRoleRepository
from ...converters.role_converter import RoleConverter


class RoleRepository(IRoleRepository):
    """角色仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, role_id: str) -> Optional[RoleModel]:
        """根据ID获取角色"""
        role_model = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role_model:
            return None
        
        return RoleConverter.from_model(role_model)
    
    async def get_by_name(self, name: str) -> Optional[RoleModel]:
        """根据名称获取角色"""
        role_model = self.db.query(RoleModel).filter(RoleModel.name == name).first()
        if not role_model:
            return None
        
        return RoleConverter.from_model(role_model)
    
    async def get_all(self) -> List[RoleModel]:
        """获取所有角色"""
        roles = self.db.query(RoleModel).all()
        return [RoleConverter.from_model(role) for role in roles]
    
    async def exists_by_name(self, name: str) -> bool:
        """检查角色名称是否存在"""
        return self.db.query(RoleModel).filter(RoleModel.name == name).first() is not None
    
    async def save(self, role: RoleModel) -> RoleModel:
        """保存角色"""
        # 检查角色是否存在
        existing_role = self.db.query(RoleModel).filter(RoleModel.id == role.id).first()
        
        if existing_role:
            # 更新现有角色
            role_dict = RoleConverter.to_model_dict(role)
            for key, value in role_dict.items():
                if key != "id":  # 不更新ID
                    setattr(existing_role, key, value)
            
            self.db.commit()
            self.db.refresh(existing_role)
            return RoleConverter.from_model(existing_role)
        else:
            # 创建新角色
            role_dict = RoleConverter.to_model_dict(role)
            new_role = RoleModel(**role_dict)
            
            self.db.add(new_role)
            self.db.commit()
            self.db.refresh(new_role)
            return RoleConverter.from_model(new_role)
    
    async def delete(self, role_id: str) -> bool:
        """删除角色"""
        role = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role:
            return False
        
        self.db.delete(role)
        self.db.commit()
        return True
    
    async def get_or_create(self, name: str, description: Optional[str] = None) -> RoleModel:
        """获取或创建角色"""
        # 先尝试获取现有角色
        existing_role = await self.get_by_name(name)
        if existing_role:
            return existing_role
        
        # 创建新角色
        from ...domain.entities.role import Role
        
        role = Role.create(name=name, description=description)
        return await self.save(role)
