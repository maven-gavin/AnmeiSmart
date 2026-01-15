#!/usr/bin/env python3
"""
租户和权限数据初始化脚本（简化版）

创建默认的系统租户、基础角色和权限配置。
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings
settings = Settings()

# 创建数据库连接
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_tenant_permission_data():
    """初始化租户和权限数据"""
    print("=" * 60)
    print("租户和权限数据初始化脚本")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 1. 创建系统租户
        print("创建系统租户...")
        db.execute(text("""
            INSERT INTO tenants (id, name, display_name, description, tenant_type, status, 
                               is_active, is_system, is_admin, priority, contact_name, contact_email, 
                               created_at, updated_at)
            VALUES ('system-tenant-001', 'system', '系统租户', '系统级租户，用于管理全局权限和配置', 
                   'system', 'active', true, true, true, 1000, '系统管理员', 'admin@system.com', 
                   NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """))
        
        # 2. 创建默认租户
        print("创建默认租户...")
        db.execute(text("""
            INSERT INTO tenants (id, name, display_name, description, tenant_type, status, 
                               is_active, is_system, is_admin, priority, contact_name, contact_email, 
                               created_at, updated_at)
            VALUES ('default-tenant-001', 'default', '默认租户', '默认业务租户，用于普通业务操作', 
                   'standard', 'active', true, false, false, 100, '租户管理员', 'admin@default.com', 
                   NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """))
        
        # 3. 创建系统权限
        print("创建系统权限...")
        system_permissions = [
            ('perm-system-admin', 'system:admin', '系统管理', '系统级管理权限', 'system', 'system', True, True, 1000, 'system-tenant-001'),
            ('perm-system-config', 'system:config', '系统配置', '系统配置管理权限', 'system', 'system', True, True, 900, 'system-tenant-001'),
            ('perm-tenant-manage', 'tenant:manage', '租户管理', '租户管理权限', 'system', 'system', True, True, 800, 'system-tenant-001'),
            ('perm-role-manage', 'role:manage', '角色管理', '角色管理权限', 'system', 'system', True, True, 700, 'system-tenant-001'),
            ('perm-permission-manage', 'permission:manage', '权限管理', '权限管理权限', 'system', 'system', True, True, 600, 'system-tenant-001')
        ]
        
        for perm_id, name, display_name, description, perm_type, scope, is_system, is_admin, priority, tenant_id in system_permissions:
            db.execute(text("""
                INSERT INTO permissions (id, name, display_name, description, permission_type, scope, 
                                      is_active, is_system, is_admin, priority, tenant_id, created_at, updated_at)
                VALUES (:id, :name, :display_name, :description, :permission_type, :scope, 
                       true, :is_system, :is_admin, :priority, :tenant_id, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                'id': perm_id, 'name': name, 'display_name': display_name, 'description': description,
                'permission_type': perm_type, 'scope': scope, 'is_system': is_system, 
                'is_admin': is_admin, 'priority': priority, 'tenant_id': tenant_id
            })
        
        # 4. 创建业务权限
        print("创建业务权限...")
        business_permissions = [
            ('perm-user-create', 'user:create', '创建用户', '创建新用户权限', 'action', 'tenant', 'user', 'create', False, False, 100, 'default-tenant-001'),
            ('perm-user-read', 'user:read', '查看用户', '查看用户信息权限', 'action', 'tenant', 'user', 'read', False, False, 90, 'default-tenant-001'),
            ('perm-user-update', 'user:update', '更新用户', '更新用户信息权限', 'action', 'tenant', 'user', 'update', False, False, 80, 'default-tenant-001'),
            ('perm-user-delete', 'user:delete', '删除用户', '删除用户权限', 'action', 'tenant', 'user', 'delete', False, False, 70, 'default-tenant-001'),
            ('perm-chat-create', 'chat:create', '创建聊天', '创建聊天会话权限', 'action', 'tenant', 'chat', 'create', False, False, 60, 'default-tenant-001'),
            ('perm-chat-read', 'chat:read', '查看聊天', '查看聊天内容权限', 'action', 'tenant', 'chat', 'read', False, False, 50, 'default-tenant-001'),
            ('perm-chat-manage', 'chat:manage', '管理聊天', '管理聊天会话权限', 'action', 'tenant', 'chat', 'manage', False, True, 40, 'default-tenant-001'),
            ('perm-task-create', 'task:create', '创建任务', '创建任务权限', 'action', 'tenant', 'task', 'create', False, False, 30, 'default-tenant-001'),
            ('perm-task-assign', 'task:assign', '分配任务', '分配任务权限', 'action', 'tenant', 'task', 'assign', False, True, 20, 'default-tenant-001'),
            ('perm-task-manage', 'task:manage', '管理任务', '管理任务权限', 'action', 'tenant', 'task', 'manage', False, True, 10, 'default-tenant-001')
        ]
        
        for perm_id, name, display_name, description, perm_type, scope, resource, action, is_system, is_admin, priority, tenant_id in business_permissions:
            db.execute(text("""
                INSERT INTO permissions (id, name, display_name, description, permission_type, scope, resource, action,
                                      is_active, is_system, is_admin, priority, tenant_id, created_at, updated_at)
                VALUES (:id, :name, :display_name, :description, :permission_type, :scope, :resource, :action,
                       true, :is_system, :is_admin, :priority, :tenant_id, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                'id': perm_id, 'name': name, 'display_name': display_name, 'description': description,
                'permission_type': perm_type, 'scope': scope, 'resource': resource, 'action': action,
                'is_system': is_system, 'is_admin': is_admin, 'priority': priority, 'tenant_id': tenant_id
            })
        
        # 5. 创建系统角色
        print("创建系统角色...")
        system_roles = [
            ('role-super-admin', 'super_admin', '超级管理员', '系统超级管理员，拥有所有权限', True, True, 1000, 'system-tenant-001'),
            ('role-system-admin', 'system_admin', '系统管理员', '系统管理员，拥有系统管理权限', True, True, 900, 'system-tenant-001')
        ]
        
        for role_id, name, display_name, description, is_system, is_admin, priority, tenant_id in system_roles:
            db.execute(text("""
                INSERT INTO roles (id, name, display_name, description, is_active, is_system, is_admin, priority, tenant_id, created_at, updated_at)
                VALUES (:id, :name, :display_name, :description, true, :is_system, :is_admin, :priority, :tenant_id, NOW(), NOW())
                ON CONFLICT (name) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    description = EXCLUDED.description,
                    is_active = EXCLUDED.is_active,
                    is_system = EXCLUDED.is_system,
                    is_admin = EXCLUDED.is_admin,
                    priority = EXCLUDED.priority,
                    tenant_id = EXCLUDED.tenant_id,
                    updated_at = NOW()
            """), {
                'id': role_id, 'name': name, 'display_name': display_name, 'description': description,
                'is_system': is_system, 'is_admin': is_admin, 'priority': priority, 'tenant_id': tenant_id
            })
        
        # 6. 创建业务角色
        print("创建业务角色...")
        business_roles = [
            ('role-tenant-admin', 'tenant_admin', '租户管理员', '租户管理员，拥有租户内所有权限', False, True, 800, 'default-tenant-001'),
            ('role-operator', 'operator', '运营人员', '运营人员，负责日常运营工作', False, False, 300, 'default-tenant-001'),
            ('role-customer', 'customer', '客户', '普通客户用户', False, False, 100, 'default-tenant-001')
        ]
        
        for role_id, name, display_name, description, is_system, is_admin, priority, tenant_id in business_roles:
            db.execute(text("""
                INSERT INTO roles (id, name, display_name, description, is_active, is_system, is_admin, priority, tenant_id, created_at, updated_at)
                VALUES (:id, :name, :display_name, :description, true, :is_system, :is_admin, :priority, :tenant_id, NOW(), NOW())
                ON CONFLICT (name) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    description = EXCLUDED.description,
                    is_active = EXCLUDED.is_active,
                    is_system = EXCLUDED.is_system,
                    is_admin = EXCLUDED.is_admin,
                    priority = EXCLUDED.priority,
                    tenant_id = EXCLUDED.tenant_id,
                    updated_at = NOW()
            """), {
                'id': role_id, 'name': name, 'display_name': display_name, 'description': description,
                'is_system': is_system, 'is_admin': is_admin, 'priority': priority, 'tenant_id': tenant_id
            })
        
        # 7. 分配权限给角色
        print("分配权限给角色...")
        
        # 超级管理员 - 所有系统权限
        db.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r, permissions p 
            WHERE r.name = 'super_admin' AND p.tenant_id = 'system-tenant-001'
            ON CONFLICT DO NOTHING
        """))
        
        # 系统管理员 - 除超级管理员外的系统权限
        db.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r, permissions p 
            WHERE r.name = 'system_admin' AND p.tenant_id = 'system-tenant-001' AND p.name != 'system:admin'
            ON CONFLICT DO NOTHING
        """))
        
        # 租户管理员 - 所有业务权限
        db.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r, permissions p 
            WHERE r.name = 'tenant_admin' AND p.tenant_id = 'default-tenant-001'
            ON CONFLICT DO NOTHING
        """))
        
        # 运营人员 - 部分业务权限
        db.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r, permissions p 
            WHERE r.name = 'operator' AND p.tenant_id = 'default-tenant-001' 
            AND p.name IN ('user:read', 'user:update', 'chat:create', 'chat:read', 'chat:manage', 'task:create', 'task:assign', 'task:manage')
            ON CONFLICT DO NOTHING
        """))
        
        # 客户 - 最基础权限
        db.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r, permissions p 
            WHERE r.name = 'customer' AND p.tenant_id = 'default-tenant-001' 
            AND p.name IN ('user:read', 'chat:create', 'chat:read')
            ON CONFLICT DO NOTHING
        """))
        
        # 提交所有更改
        db.commit()
        print("✓ 所有数据初始化完成！")
        
        # 显示统计信息
        result = db.execute(text("SELECT COUNT(*) FROM tenants")).scalar()
        print(f"租户数量: {result}")
        
        result = db.execute(text("SELECT COUNT(*) FROM roles")).scalar()
        print(f"角色数量: {result}")
        
        result = db.execute(text("SELECT COUNT(*) FROM permissions")).scalar()
        print(f"权限数量: {result}")
        
        result = db.execute(text("SELECT COUNT(*) FROM role_permissions")).scalar()
        print(f"角色权限关联数量: {result}")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_tenant_permission_data()
