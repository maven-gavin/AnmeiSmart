"""
资源服务 - 资源管理逻辑
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.identity_access.models.user import Resource
from app.identity_access.schemas.resource_schemas import ResourceCreate, ResourceUpdate
from app.identity_access.enums import ResourceType
from app.core.api import BusinessException, ErrorCode


class ResourceService:
    """资源服务 - 直接操作数据库，遵循新架构规范"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name(self, name: str) -> Optional[Resource]:
        """根据资源名称获取资源"""
        return self.db.query(Resource).filter(Resource.name == name).first()
    
    def get_by_id(self, resource_id: str) -> Optional[Resource]:
        """根据ID获取资源"""
        return self.db.query(Resource).filter(Resource.id == resource_id).first()
    
    def get_all_resources(
        self, 
        resource_type: Optional[ResourceType] = None,
        is_active: Optional[bool] = None
    ) -> List[Resource]:
        """获取所有资源"""
        query = self.db.query(Resource)
        
        if resource_type:
            query = query.filter(Resource.resource_type == resource_type.value)
        
        if is_active is not None:
            query = query.filter(Resource.is_active == is_active)
        
        return query.order_by(Resource.priority.desc()).all()
    
    def create_resource(self, resource_in: ResourceCreate) -> Resource:
        """创建资源"""
        if self.get_by_name(resource_in.name):
            raise BusinessException("资源名称已存在", code=ErrorCode.RESOURCE_ALREADY_EXISTS)
        
        resource_data = resource_in.model_dump()
        resource = Resource(**resource_data)
        
        self.db.add(resource)
        self.db.commit()
        self.db.refresh(resource)
        return resource
    
    def update_resource(self, resource_id: str, resource_data: ResourceUpdate) -> Resource:
        """更新资源"""
        resource = self.get_by_id(resource_id)
        if not resource:
            raise BusinessException("资源不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 更新字段（ResourceUpdate 不包含 name 字段，资源名称通常不允许修改）
        update_data = resource_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(resource, key, value)
        
        self.db.commit()
        self.db.refresh(resource)
        return resource
    
    def create_or_update_resource(
        self,
        name: str,
        resource_path: str,
        resource_type: ResourceType,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        http_method: Optional[str] = None,
        **kwargs
    ) -> Resource:
        """创建或更新资源（用于同步）"""
        existing = self.get_by_name(name)
        
        if existing:
            # 更新现有资源
            update_data = {
                "resource_path": resource_path,
                "display_name": display_name or existing.display_name,
                "description": description or existing.description,
                "http_method": http_method,
                **kwargs
            }
            # 移除 None 值
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            for key, value in update_data.items():
                setattr(existing, key, value)
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # 创建新资源
            resource = Resource(
                name=name,
                resource_path=resource_path,
                resource_type=resource_type.value,
                display_name=display_name,
                description=description,
                http_method=http_method,
                **kwargs
            )
            
            self.db.add(resource)
            self.db.commit()
            self.db.refresh(resource)
            return resource

