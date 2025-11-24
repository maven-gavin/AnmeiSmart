"""优化身份访问模型：多租户唯一约束和枚举类型

Revision ID: 5e40eb248348
Revises: 
Create Date: 2025-11-23 15:29:38.828214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5e40eb248348'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 创建枚举类型
    # 租户状态枚举
    tenant_status_enum = postgresql.ENUM(
        'active', 'frozen', 'inactive', 'suspended', 'pending',
        name='tenantstatus'
    )
    tenant_status_enum.create(op.get_bind(), checkfirst=True)
    
    # 用户状态枚举
    user_status_enum = postgresql.ENUM(
        'pending', 'active', 'suspended', 'deleted',
        name='userstatus'
    )
    user_status_enum.create(op.get_bind(), checkfirst=True)
    
    # 权限类型枚举
    permission_type_enum = postgresql.ENUM(
        'action', 'data', 'menu',
        name='permissiontype'
    )
    permission_type_enum.create(op.get_bind(), checkfirst=True)
    
    # 权限范围枚举
    permission_scope_enum = postgresql.ENUM(
        'tenant', 'global', 'department', 'personal',
        name='permissionscope'
    )
    permission_scope_enum.create(op.get_bind(), checkfirst=True)
    
    # 2. 修改tenants表
    # 删除is_active字段
    op.drop_column('tenants', 'is_active')
    
    # 修改status字段为枚举类型
    # 先添加新列
    op.add_column('tenants', sa.Column('status_new', tenant_status_enum, nullable=True))
    # 迁移数据：将旧status值映射到新枚举值
    op.execute("""
        UPDATE tenants 
        SET status_new = CASE 
            WHEN status = 'active' THEN 'active'::tenantstatus
            WHEN status = 'frozen' THEN 'frozen'::tenantstatus
            WHEN status = 'inactive' THEN 'inactive'::tenantstatus
            WHEN status = 'suspended' THEN 'suspended'::tenantstatus
            WHEN status = 'pending' THEN 'pending'::tenantstatus
            ELSE 'active'::tenantstatus
        END
    """)
    # 删除旧列
    op.drop_column('tenants', 'status')
    # 重命名新列
    op.alter_column('tenants', 'status_new', new_column_name='status', nullable=False)
    op.alter_column('tenants', 'status', server_default="'active'::tenantstatus")
    
    # 3. 修改roles表
    # 删除name的唯一约束（如果存在）
    op.drop_constraint('roles_name_key', 'roles', type_='unique', if_exists=True)
    # 添加(name, tenant_id)唯一约束
    op.create_unique_constraint('uq_role_name_tenant', 'roles', ['name', 'tenant_id'])
    
    # 4. 修改permissions表
    # 删除code和name的唯一约束（如果存在）
    op.drop_constraint('permissions_code_key', 'permissions', type_='unique', if_exists=True)
    op.drop_constraint('permissions_name_key', 'permissions', type_='unique', if_exists=True)
    # 添加(code, tenant_id)和(name, tenant_id)唯一约束
    op.create_unique_constraint('uq_permission_code_tenant', 'permissions', ['code', 'tenant_id'])
    op.create_unique_constraint('uq_permission_name_tenant', 'permissions', ['name', 'tenant_id'])
    
    # 修改permission_type为枚举类型
    op.add_column('permissions', sa.Column('permission_type_new', permission_type_enum, nullable=True))
    op.execute("""
        UPDATE permissions 
        SET permission_type_new = CASE 
            WHEN permission_type = 'action' THEN 'action'::permissiontype
            WHEN permission_type = 'data' THEN 'data'::permissiontype
            WHEN permission_type = 'menu' THEN 'menu'::permissiontype
            ELSE 'action'::permissiontype
        END
    """)
    op.drop_column('permissions', 'permission_type')
    op.alter_column('permissions', 'permission_type_new', new_column_name='permission_type', nullable=False)
    op.alter_column('permissions', 'permission_type', server_default="'action'::permissiontype")
    
    # 修改scope为枚举类型
    op.add_column('permissions', sa.Column('scope_new', permission_scope_enum, nullable=True))
    op.execute("""
        UPDATE permissions 
        SET scope_new = CASE 
            WHEN scope = 'tenant' THEN 'tenant'::permissionscope
            WHEN scope = 'global' THEN 'global'::permissionscope
            WHEN scope = 'department' THEN 'department'::permissionscope
            WHEN scope = 'personal' THEN 'personal'::permissionscope
            ELSE 'tenant'::permissionscope
        END
    """)
    op.drop_column('permissions', 'scope')
    op.alter_column('permissions', 'scope_new', new_column_name='scope', nullable=False)
    op.alter_column('permissions', 'scope', server_default="'tenant'::permissionscope")
    
    # 5. 修改users表
    # 先添加status枚举字段
    op.add_column('users', sa.Column('status', user_status_enum, nullable=True))
    # 迁移数据：将is_active值映射到status
    op.execute("""
        UPDATE users 
        SET status = CASE 
            WHEN is_active = true THEN 'active'::userstatus
            ELSE 'pending'::userstatus
        END
    """)
    # 设置默认值
    op.execute("UPDATE users SET status = 'active'::userstatus WHERE status IS NULL")
    op.alter_column('users', 'status', nullable=False)
    op.alter_column('users', 'status', server_default="'pending'::userstatus")
    # 删除is_active字段
    op.drop_column('users', 'is_active')
    
    # 6. 修改resources表
    # 删除name的唯一约束（如果存在）
    op.drop_constraint('resources_name_key', 'resources', type_='unique', if_exists=True)
    # 添加(name, tenant_id)唯一约束
    op.create_unique_constraint('uq_resource_name_tenant', 'resources', ['name', 'tenant_id'])


def downgrade() -> None:
    # 1. 修改resources表
    op.drop_constraint('uq_resource_name_tenant', 'resources', type_='unique')
    op.create_unique_constraint('resources_name_key', 'resources', ['name'])
    
    # 2. 修改users表
    op.drop_column('users', 'status')
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    op.alter_column('users', 'is_active', nullable=False)
    
    # 3. 修改permissions表
    # 恢复scope为字符串
    op.add_column('permissions', sa.Column('scope_old', sa.String(20), nullable=True))
    op.execute("UPDATE permissions SET scope_old = scope::text")
    op.drop_column('permissions', 'scope')
    op.alter_column('permissions', 'scope_old', new_column_name='scope', nullable=False)
    op.alter_column('permissions', 'scope', server_default="'tenant'")
    
    # 恢复permission_type为字符串
    op.add_column('permissions', sa.Column('permission_type_old', sa.String(20), nullable=True))
    op.execute("UPDATE permissions SET permission_type_old = permission_type::text")
    op.drop_column('permissions', 'permission_type')
    op.alter_column('permissions', 'permission_type_old', new_column_name='permission_type', nullable=False)
    op.alter_column('permissions', 'permission_type', server_default="'action'")
    
    # 恢复唯一约束
    op.drop_constraint('uq_permission_name_tenant', 'permissions', type_='unique')
    op.drop_constraint('uq_permission_code_tenant', 'permissions', type_='unique')
    op.create_unique_constraint('permissions_name_key', 'permissions', ['name'])
    op.create_unique_constraint('permissions_code_key', 'permissions', ['code'])
    
    # 4. 修改roles表
    op.drop_constraint('uq_role_name_tenant', 'roles', type_='unique')
    op.create_unique_constraint('roles_name_key', 'roles', ['name'])
    
    # 5. 修改tenants表
    op.add_column('tenants', sa.Column('status_old', sa.String(20), nullable=True))
    op.execute("UPDATE tenants SET status_old = status::text")
    op.drop_column('tenants', 'status')
    op.alter_column('tenants', 'status_old', new_column_name='status', nullable=False)
    op.alter_column('tenants', 'status', server_default="'active'")
    op.add_column('tenants', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    op.alter_column('tenants', 'is_active', nullable=False)
    
    # 6. 删除枚举类型（可选，如果不再使用）
    # op.execute("DROP TYPE IF EXISTS userstatus")
    # op.execute("DROP TYPE IF EXISTS tenantstatus")
    # op.execute("DROP TYPE IF EXISTS permissiontype")
    # op.execute("DROP TYPE IF EXISTS permissionscope")
