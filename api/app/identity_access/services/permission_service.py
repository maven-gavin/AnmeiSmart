"""
权限服务 - 权限管理逻辑
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

from app.identity_access.models.user import Permission
from app.identity_access.schemas.permission_schemas import PermissionCreate, PermissionUpdate
from app.identity_access.enums import PermissionType, PermissionScope
from app.core.api import BusinessException, ErrorCode


class PermissionService:
    """权限服务 - 直接操作数据库，遵循新架构规范"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_code(self, code: str) -> Optional[Permission]:
        """根据权限标识码获取权限（全局，不区分租户）"""
        from sqlalchemy import text
        
        # 先尝试使用 ORM 查询（如果枚举值有效）
        try:
            perm = self.db.query(Permission).filter(Permission.code == code).first()
            if perm:
                return perm
        except (LookupError, ValueError):
            # 如果枚举值无效，使用原始 SQL 查询
            pass
        
        # 使用原始 SQL 查询避免枚举转换错误
        sql = text("""
            SELECT id, code, name, display_name, description, 
                   permission_type, scope,
                   is_active, is_system, is_admin, priority,
                   created_at, updated_at
            FROM permissions
            WHERE code = :code
            LIMIT 1
        """)
        
        result = self.db.execute(sql, {"code": code})
        row = result.first()
        
        if not row:
            return None
        
        perm = Permission()
        perm.id = row.id
        perm.code = row.code
        perm.name = row.name
        perm.display_name = row.display_name
        perm.description = row.description
        perm.permission_type = row.permission_type
        perm.scope = row.scope
        perm.is_active = row.is_active
        perm.is_system = row.is_system
        perm.is_admin = row.is_admin
        perm.priority = row.priority
        perm.created_at = row.created_at
        perm.updated_at = row.updated_at
        
        # 使用 merge 将对象合并到会话中，使其成为持久化对象
        return self.db.merge(perm)
    
    def get_by_id(self, permission_id: str) -> Optional[Permission]:
        """根据ID获取权限"""
        from sqlalchemy import text
        
        # 先尝试使用 ORM 查询（如果枚举值有效）
        try:
            perm = self.db.query(Permission).filter(Permission.id == permission_id).first()
            if perm:
                return perm
        except (LookupError, ValueError):
            # 如果枚举值无效，使用原始 SQL 查询
            pass
        
        # 使用原始 SQL 查询避免枚举转换错误
        sql = text("""
            SELECT id, code, name, display_name, description, 
                   permission_type, scope,
                   is_active, is_system, is_admin, priority,
                   created_at, updated_at
            FROM permissions
            WHERE id = :permission_id
            LIMIT 1
        """)
        
        result = self.db.execute(sql, {"permission_id": permission_id})
        row = result.first()
        
        if not row:
            return None
        
        # 使用 merge 将对象添加到会话中
        perm = Permission()
        perm.id = row.id
        perm.code = row.code
        perm.name = row.name
        perm.display_name = row.display_name
        perm.description = row.description
        perm.permission_type = row.permission_type
        perm.scope = row.scope
        perm.is_active = row.is_active
        perm.is_system = row.is_system
        perm.is_admin = row.is_admin
        perm.priority = row.priority
        perm.created_at = row.created_at
        perm.updated_at = row.updated_at
        
        # 使用 merge 将对象合并到会话中，使其成为持久化对象
        return self.db.merge(perm)
    
    def get_all_permissions(
        self,
        is_active: Optional[bool] = None
    ) -> List[Permission]:
        """获取所有权限（全局，不区分租户）"""
        # 使用原始 SQL 查询避免枚举转换错误
        from sqlalchemy import text
        
        # 构建 SQL 查询
        conditions = []
        params = {}
        
        if is_active is not None:
            conditions.append("is_active = :is_active")
            params["is_active"] = is_active
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = text(f"""
            SELECT id, code, name, display_name, description, 
                   permission_type, scope,
                   is_active, is_system, is_admin, priority,
                   created_at, updated_at
            FROM permissions
            WHERE {where_clause}
            ORDER BY priority DESC, created_at DESC
        """)
        
        result = self.db.execute(sql, params)
        
        # 手动构建 Permission 对象
        permissions = []
        for row in result:
            perm = Permission()
            perm.id = row.id
            perm.code = row.code
            perm.name = row.name
            perm.display_name = row.display_name
            perm.description = row.description
            # 直接存储原始值，不进行枚举转换
            perm.permission_type = row.permission_type
            perm.scope = row.scope
            perm.is_active = row.is_active
            perm.is_system = row.is_system
            perm.is_admin = row.is_admin
            perm.priority = row.priority
            perm.created_at = row.created_at
            perm.updated_at = row.updated_at
            permissions.append(perm)
        
        return permissions
    
    def create_permission(self, permission_in: PermissionCreate) -> Permission:
        """创建权限（全局，不区分租户）"""
        # 检查权限标识码是否已存在（全局唯一）
        if self.get_by_code(permission_in.code):
            raise BusinessException(
                f"权限标识码 '{permission_in.code}' 已存在",
                code=ErrorCode.BUSINESS_ERROR
            )
        
        # 检查权限名称是否已存在（全局唯一）
        from sqlalchemy import text
        check_name_sql = text("""
            SELECT id FROM permissions
            WHERE name = :name
            LIMIT 1
        """)
        result = self.db.execute(check_name_sql, {"name": permission_in.name})
        if result.first():
            raise BusinessException(
                f"权限名称 '{permission_in.name}' 已存在",
                code=ErrorCode.BUSINESS_ERROR
            )
        
        permission_data = permission_in.model_dump()
        # 移除 tenant_id（如果存在）
        permission_data.pop('tenant_id', None)
        
        permission = Permission(**permission_data)
        
        try:
            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)
            return permission
        except IntegrityError as e:
            self.db.rollback()
            # 检查是否是唯一约束错误
            if isinstance(e.orig, UniqueViolation):
                error_msg = str(e.orig)
                if 'code' in error_msg.lower() or 'uq_permission_code' in error_msg:
                    raise BusinessException(
                        f"权限标识码 '{permission_in.code}' 已存在",
                        code=ErrorCode.BUSINESS_ERROR
                    )
                elif 'name' in error_msg.lower() or 'uq_permission_name' in error_msg:
                    raise BusinessException(
                        f"权限名称 '{permission_in.name}' 已存在",
                        code=ErrorCode.BUSINESS_ERROR
                    )
            # 其他数据库错误
            raise BusinessException(
                f"创建权限失败: {str(e)}",
                code=ErrorCode.SYSTEM_ERROR
            )
    
    def update_permission(self, permission_id: str, permission_data: PermissionUpdate) -> Permission:
        """更新权限"""
        permission = self.get_by_id(permission_id)
        if not permission:
            raise BusinessException("权限不存在", code=ErrorCode.NOT_FOUND)
        
        # 系统权限不允许修改
        if permission.is_system:
            raise BusinessException("系统权限无法修改", code=ErrorCode.PERMISSION_DENIED)
        
        # 更新字段
        update_data = permission_data.model_dump(exclude_unset=True)
        
        # 如果更新了 code，需要检查新 code 是否已存在（全局唯一）
        if 'code' in update_data and update_data['code'] != permission.code:
            existing = self.get_by_code(update_data['code'])
            if existing and existing.id != permission_id:
                raise BusinessException(
                    f"权限标识码 '{update_data['code']}' 已存在",
                    code=ErrorCode.BUSINESS_ERROR
                )
        
        # 如果更新了 name，需要检查新 name 是否已存在（全局唯一）
        if 'name' in update_data and update_data['name'] != permission.name:
            existing = self.db.query(Permission).filter(
                Permission.name == update_data['name'],
                Permission.id != permission_id
            ).first()
            if existing:
                raise BusinessException(
                    f"权限名称 '{update_data['name']}' 已存在",
                    code=ErrorCode.BUSINESS_ERROR
                )
        
        # 移除 tenant_id（如果存在）
        update_data.pop('tenant_id', None)
        
        for key, value in update_data.items():
            setattr(permission, key, value)
        
        self.db.commit()
        # 重新查询以确保对象在会话中
        updated_permission = self.get_by_id(permission_id)
        if not updated_permission:
            raise BusinessException("更新权限后无法重新获取", code=ErrorCode.SYSTEM_ERROR)
        return updated_permission
    
    def delete_permission(self, permission_id: str) -> bool:
        """删除权限（物理删除）"""
        permission = self.get_by_id(permission_id)
        if not permission:
            raise BusinessException("权限不存在", code=ErrorCode.NOT_FOUND)
        
        # 系统权限不允许删除
        if permission.is_system:
            raise BusinessException("系统权限无法删除", code=ErrorCode.PERMISSION_DENIED)
        
        self.db.delete(permission)
        self.db.commit()
        return True
    
    def get_permission_resources(self, permission_id: str):
        """获取权限已分配的资源"""
        permission = self.get_by_id(permission_id)
        if not permission:
            raise BusinessException("权限不存在", code=ErrorCode.NOT_FOUND)
        
        # 通过关系获取资源
        return permission.resources
    
    def assign_resources_to_permission(self, permission_id: str, resource_ids: list[str]):
        """为权限分配资源"""
        permission = self.get_by_id(permission_id)
        if not permission:
            raise BusinessException("权限不存在", code=ErrorCode.NOT_FOUND)
        
        # 获取资源对象
        from app.identity_access.models.user import Resource
        resources = self.db.query(Resource).filter(Resource.id.in_(resource_ids)).all()
        
        if len(resources) != len(resource_ids):
            raise BusinessException("部分资源不存在", code=ErrorCode.NOT_FOUND)
        
        # 添加资源到权限（避免重复）
        for resource in resources:
            if resource not in permission.resources:
                permission.resources.append(resource)
        
        self.db.commit()
        return permission
    
    def unassign_resources_from_permission(self, permission_id: str, resource_ids: list[str]):
        """从权限移除资源"""
        permission = self.get_by_id(permission_id)
        if not permission:
            raise BusinessException("权限不存在", code=ErrorCode.NOT_FOUND)
        
        # 获取资源对象
        from app.identity_access.models.user import Resource
        resources = self.db.query(Resource).filter(Resource.id.in_(resource_ids)).all()
        
        # 从权限移除资源
        for resource in resources:
            if resource in permission.resources:
                permission.resources.remove(resource)
        
        self.db.commit()
        return permission

