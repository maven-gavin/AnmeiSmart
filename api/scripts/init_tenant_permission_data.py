#!/usr/bin/env python3
"""
租户和权限数据初始化脚本

创建默认的系统租户、基础角色和权限配置。
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.common.infrastructure.db.base import get_db
from app.identity_access.infrastructure.db.user import Tenant, Role, Permission, User
from app.identity_access.domain.entities.role import RoleEntity
from app.identity_access.domain.entities.permission import PermissionEntity
from app.identity_access.domain.value_objects.tenant_status import TenantStatus
from app.identity_access.domain.value_objects.tenant_type import TenantType
from app.identity_access.domain.value_objects.permission_type import PermissionType
from app.identity_access.domain.value_objects.permission_scope import PermissionScope


class TenantPermissionDataInitializer:
    """租户和权限数据初始化器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def initialize_all(self):
        """初始化所有数据"""
        print("开始初始化租户和权限数据...")
        
        # 1. 创建系统租户
        system_tenant = await self.create_system_tenant()
        print(f"✓ 创建系统租户: {system_tenant.name}")
        
        # 2. 创建默认租户
        default_tenant = await self.create_default_tenant()
        print(f"✓ 创建默认租户: {default_tenant.name}")
        
        # 3. 创建系统权限
        system_permissions = await self.create_system_permissions(system_tenant.id)
        print(f"✓ 创建系统权限: {len(system_permissions)} 个")
        
        # 4. 创建业务权限
        business_permissions = await self.create_business_permissions(default_tenant.id)
        print(f"✓ 创建业务权限: {len(business_permissions)} 个")
        
        # 5. 创建系统角色
        system_roles = await self.create_system_roles(system_tenant.id, system_permissions)
        print(f"✓ 创建系统角色: {len(system_roles)} 个")
        
        # 6. 创建业务角色
        business_roles = await self.create_business_roles(default_tenant.id, business_permissions)
        print(f"✓ 创建业务角色: {len(business_roles)} 个")
        
        # 7. 提交所有更改
        self.db.commit()
        print("✓ 所有数据初始化完成！")
    
    async def create_system_tenant(self) -> Tenant:
        """创建系统租户"""
        # 检查是否已存在
        existing = self.db.query(Tenant).filter(Tenant.name == "system").first()
        if existing:
            return existing
        
        tenant = Tenant(
            id="system-tenant-001",
            name="system",
            display_name="系统租户",
            description="系统级租户，用于管理全局权限和配置",
            tenant_type="system",
            status="active",
            is_active=True,
            is_system=True,
            is_admin=True,
            priority=1000,
            contact_name="系统管理员",
            contact_email="admin@system.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(tenant)
        return tenant
    
    async def create_default_tenant(self) -> Tenant:
        """创建默认业务租户"""
        # 检查是否已存在
        existing = self.db.query(Tenant).filter(Tenant.name == "default").first()
        if existing:
            return existing
        
        tenant = Tenant(
            id="default-tenant-001",
            name="default",
            display_name="默认租户",
            description="默认业务租户，用于普通业务操作",
            tenant_type="standard",
            status="active",
            is_active=True,
            is_system=False,
            is_admin=False,
            priority=100,
            contact_name="租户管理员",
            contact_email="admin@default.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(tenant)
        return tenant
    
    async def create_system_permissions(self, tenant_id: str) -> List[Permission]:
        """创建系统权限"""
        system_permissions_data = [
            # 系统管理权限
            {
                "id": "perm-system-admin",
                "name": "system:admin",
                "display_name": "系统管理",
                "description": "系统级管理权限",
                "permission_type": "system",
                "scope": "system",
                "is_system": True,
                "is_admin": True,
                "priority": 1000
            },
            {
                "id": "perm-system-config",
                "name": "system:config",
                "display_name": "系统配置",
                "description": "系统配置管理权限",
                "permission_type": "system",
                "scope": "system",
                "is_system": True,
                "is_admin": True,
                "priority": 900
            },
            {
                "id": "perm-tenant-manage",
                "name": "tenant:manage",
                "display_name": "租户管理",
                "description": "租户管理权限",
                "permission_type": "system",
                "scope": "system",
                "is_system": True,
                "is_admin": True,
                "priority": 800
            },
            {
                "id": "perm-role-manage",
                "name": "role:manage",
                "display_name": "角色管理",
                "description": "角色管理权限",
                "permission_type": "system",
                "scope": "system",
                "is_system": True,
                "is_admin": True,
                "priority": 700
            },
            {
                "id": "perm-permission-manage",
                "name": "permission:manage",
                "display_name": "权限管理",
                "description": "权限管理权限",
                "permission_type": "system",
                "scope": "system",
                "is_system": True,
                "is_admin": True,
                "priority": 600
            }
        ]
        
        permissions = []
        for perm_data in system_permissions_data:
            # 检查是否已存在
            existing = self.db.query(Permission).filter(Permission.id == perm_data["id"]).first()
            if existing:
                permissions.append(existing)
                continue
            
            permission = Permission(
                **perm_data,
                tenant_id=tenant_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(permission)
            permissions.append(permission)
        
        return permissions
    
    async def create_business_permissions(self, tenant_id: str) -> List[Permission]:
        """创建业务权限"""
        business_permissions_data = [
            # 用户管理权限
            {
                "id": "perm-user-create",
                "name": "user:create",
                "display_name": "创建用户",
                "description": "创建新用户权限",
                "permission_type": "action",
                "scope": "tenant",
                "resource": "user",
                "action": "create",
                "is_system": False,
                "is_admin": False,
                "priority": 100
            },
            {
                "id": "perm-user-read",
                "name": "user:read",
                "display_name": "查看用户",
                "description": "查看用户信息权限",
                "permission_type": "action",
                "scope": "tenant",
                "resource": "user",
                "action": "read",
                "is_system": False,
                "is_admin": False,
                "priority": 90
            },
            {
                "id": "perm-user-update",
                "name": "user:update",
                "display_name": "更新用户",
                "description": "更新用户信息权限",
                "permission_type": "action",
                "scope": "tenant",
                "resource": "user",
                "action": "update",
                "is_system": False,
                "is_admin": False,
                "priority": 80
            },
            {
                "id": "perm-user-delete",
                "name": "user:delete",
                "display_name": "删除用户",
                "description": "删除用户权限",
                "permission_type": "action",
                "scope": "tenant",
                "resource": "user",
                "action": "delete",
                "is_system": False,
                "is_admin": False,
                "priority": 70
            },
            # 聊天管理权限
            {
                "id": "perm-chat-create",
                "name": "chat:create",
                "display_name": "创建聊天",
                "description": "创建聊天会话权限",
                "permission_type": "action",
                "scope": "tenant",
                "resource": "chat",
                "action": "create",
                "is_system": False,
                "is_admin": False,
                "priority": 60
            },
            {
                "id": "perm-chat-read",
                "name": "chat:read",
                "display_name": "查看聊天",
                "description": "查看聊天内容权限",
                "permission_type": "action",
                "scope": "tenant",
                "resource": "chat",
                "action": "read",
                "is_system": False,
                "is_admin": False,
                "priority": 50
            },
            {
                "id": "perm-chat-manage",
                "name": "chat:manage",
                "display_name": "管理聊天",
                "description": "管理聊天会话权限",
                "permission_type": "action",
                "scope": "tenant",
                "resource": "chat",
                "action": "manage",
                "is_system": False,
                "is_admin": True,
                "priority": 40
            },
            # 任务管理权限
            {
                "id": "perm-task-create",
                "name": "task:create",
                "display_name": "创建任务",
                "description": "创建任务权限",
                "permission_type": "action",
                "scope": "tenant",
                "resource": "task",
                "action": "create",
                "is_system": False,
                "is_admin": False,
                "priority": 30
            },
            {
                "id": "perm-task-assign",
                "name": "task:assign",
                "display_name": "分配任务",
                "description": "分配任务权限",
                "permission_type": "action",
                "scope": "tenant",
                "resource": "task",
                "action": "assign",
                "is_system": False,
                "is_admin": True,
                "priority": 20
            },
            {
                "id": "perm-task-manage",
                "name": "task:manage",
                "display_name": "管理任务",
                "description": "管理任务权限",
                "permission_type": "action",
                "scope": "tenant",
                "resource": "task",
                "action": "manage",
                "is_system": False,
                "is_admin": True,
                "priority": 10
            }
        ]
        
        permissions = []
        for perm_data in business_permissions_data:
            # 检查是否已存在
            existing = self.db.query(Permission).filter(Permission.id == perm_data["id"]).first()
            if existing:
                permissions.append(existing)
                continue
            
            permission = Permission(
                **perm_data,
                tenant_id=tenant_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(permission)
            permissions.append(permission)
        
        return permissions
    
    async def create_system_roles(self, tenant_id: str, permissions: List[Permission]) -> List[Role]:
        """创建系统角色"""
        system_roles_data = [
            {
                "id": "role-super-admin",
                "name": "super_admin",
                "display_name": "超级管理员",
                "description": "系统超级管理员，拥有所有权限",
                "is_system": True,
                "is_admin": True,
                "priority": 1000,
                "permissions": ["system:admin", "system:config", "tenant:manage", "role:manage", "permission:manage"]
            },
            {
                "id": "role-system-admin",
                "name": "system_admin",
                "display_name": "系统管理员",
                "description": "系统管理员，拥有系统管理权限",
                "is_system": True,
                "is_admin": True,
                "priority": 900,
                "permissions": ["system:config", "tenant:manage", "role:manage", "permission:manage"]
            }
        ]
        
        roles = []
        for role_data in system_roles_data:
            # 检查是否已存在
            existing = self.db.query(Role).filter(Role.id == role_data["id"]).first()
            if existing:
                roles.append(existing)
                continue
            
            role = Role(
                id=role_data["id"],
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_active=True,
                is_system=role_data["is_system"],
                is_admin=role_data["is_admin"],
                priority=role_data["priority"],
                tenant_id=tenant_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(role)
            
            # 分配权限
            for perm_name in role_data["permissions"]:
                permission = next((p for p in permissions if p.name == perm_name), None)
                if permission:
                    role.permissions.append(permission)
            
            roles.append(role)
        
        return roles
    
    async def create_business_roles(self, tenant_id: str, permissions: List[Permission]) -> List[Role]:
        """创建业务角色"""
        business_roles_data = [
            {
                "id": "role-tenant-admin",
                "name": "tenant_admin",
                "display_name": "租户管理员",
                "description": "租户管理员，拥有租户内所有权限",
                "is_system": False,
                "is_admin": True,
                "priority": 800,
                "permissions": [
                    "user:create", "user:read", "user:update", "user:delete",
                    "chat:create", "chat:read", "chat:manage",
                    "task:create", "task:assign", "task:manage"
                ]
            },
            {
                "id": "role-operator",
                "name": "operator",
                "display_name": "运营人员",
                "description": "运营人员，负责日常运营工作",
                "is_system": False,
                "is_admin": False,
                "priority": 300,
                "permissions": [
                    "user:read", "user:update",
                    "chat:create", "chat:read", "chat:manage",
                    "task:create", "task:assign", "task:manage"
                ]
            },
            {
                "id": "role-consultant",
                "name": "consultant",
                "display_name": "顾问",
                "description": "医美顾问，负责客户咨询",
                "is_system": False,
                "is_admin": False,
                "priority": 200,
                "permissions": [
                    "user:read",
                    "chat:create", "chat:read",
                    "task:create"
                ]
            },
            {
                "id": "role-customer",
                "name": "customer",
                "display_name": "客户",
                "description": "普通客户用户",
                "is_system": False,
                "is_admin": False,
                "priority": 100,
                "permissions": [
                    "user:read",
                    "chat:create", "chat:read"
                ]
            }
        ]
        
        roles = []
        for role_data in business_roles_data:
            # 检查是否已存在
            existing = self.db.query(Role).filter(Role.id == role_data["id"]).first()
            if existing:
                roles.append(existing)
                continue
            
            role = Role(
                id=role_data["id"],
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_active=True,
                is_system=role_data["is_system"],
                is_admin=role_data["is_admin"],
                priority=role_data["priority"],
                tenant_id=tenant_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(role)
            
            # 分配权限
            for perm_name in role_data["permissions"]:
                permission = next((p for p in permissions if p.name == perm_name), None)
                if permission:
                    role.permissions.append(permission)
            
            roles.append(role)
        
        return roles


async def main():
    """主函数"""
    print("=" * 60)
    print("租户和权限数据初始化脚本")
    print("=" * 60)
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 创建初始化器并执行初始化
        initializer = TenantPermissionDataInitializer(db)
        await initializer.initialize_all()
        
        print("\n" + "=" * 60)
        print("数据初始化完成！")
        print("=" * 60)
        
        # 显示统计信息
        tenant_count = db.query(Tenant).count()
        role_count = db.query(Role).count()
        permission_count = db.query(Permission).count()
        
        print(f"租户数量: {tenant_count}")
        print(f"角色数量: {role_count}")
        print(f"权限数量: {permission_count}")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
