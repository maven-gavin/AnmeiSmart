"""添加租户和权限表

Revision ID: 07ce9993a478
Revises: 3f33a810ffc1
Create Date: 2025-09-10 11:11:10.337011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07ce9993a478'
down_revision: Union[str, None] = '3f33a810ffc1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建租户表
    op.create_table('tenants',
        sa.Column('id', sa.String(length=36), nullable=False, comment='租户ID'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='租户名称'),
        sa.Column('display_name', sa.String(length=50), nullable=True, comment='租户显示名称'),
        sa.Column('description', sa.String(length=255), nullable=True, comment='租户描述'),
        sa.Column('tenant_type', sa.String(length=20), nullable=True, comment='租户类型'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='租户状态'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否系统租户'),
        sa.Column('is_admin', sa.Boolean(), nullable=True, comment='是否管理员租户'),
        sa.Column('priority', sa.Integer(), nullable=True, comment='租户优先级'),
        sa.Column('encrypted_pub_key', sa.String(length=255), nullable=True, comment='加密公钥'),
        sa.Column('contact_phone', sa.String(length=20), nullable=True, comment='负责人联系电话'),
        sa.Column('contact_email', sa.String(length=50), nullable=True, comment='负责人邮箱'),
        sa.Column('contact_name', sa.String(length=50), nullable=True, comment='负责人姓名'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        comment='租户表，存储系统所有租户信息'
    )
    op.create_index(op.f('ix_tenants_name'), 'tenants', ['name'], unique=True)
    
    # 创建权限表
    op.create_table('permissions',
        sa.Column('id', sa.String(length=36), nullable=False, comment='权限ID'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='权限名称'),
        sa.Column('display_name', sa.String(length=50), nullable=True, comment='权限显示名称'),
        sa.Column('description', sa.String(length=255), nullable=True, comment='权限描述'),
        sa.Column('permission_type', sa.String(length=20), nullable=True, comment='权限类型'),
        sa.Column('scope', sa.String(length=20), nullable=True, comment='权限范围'),
        sa.Column('resource', sa.String(length=50), nullable=True, comment='权限资源'),
        sa.Column('action', sa.String(length=50), nullable=True, comment='权限动作'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否系统权限'),
        sa.Column('is_admin', sa.Boolean(), nullable=True, comment='是否管理员权限'),
        sa.Column('priority', sa.Integer(), nullable=True, comment='权限优先级'),
        sa.Column('tenant_id', sa.String(length=36), nullable=True, comment='租户ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='权限配置表，存储系统所有权限配置信息'
    )
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)
    
    # 创建角色权限关联表
    op.create_table('role_permissions',
        sa.Column('role_id', sa.String(length=36), nullable=False, comment='角色ID'),
        sa.Column('permission_id', sa.String(length=36), nullable=False, comment='权限ID'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # 为角色表添加新字段
    op.add_column('roles', sa.Column('display_name', sa.String(length=50), nullable=True, comment='角色显示名称'))
    op.add_column('roles', sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'))
    op.add_column('roles', sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否系统角色'))
    op.add_column('roles', sa.Column('is_admin', sa.Boolean(), nullable=True, comment='是否管理员角色'))
    op.add_column('roles', sa.Column('priority', sa.Integer(), nullable=True, comment='角色优先级'))
    op.add_column('roles', sa.Column('tenant_id', sa.String(length=36), nullable=True, comment='租户ID'))
    op.create_foreign_key('fk_roles_tenant_id', 'roles', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    
    # 为用户表添加租户字段
    op.add_column('users', sa.Column('tenant_id', sa.String(length=36), nullable=True, comment='租户ID'))
    op.create_foreign_key('fk_users_tenant_id', 'users', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # 删除用户表的租户字段
    op.drop_constraint('fk_users_tenant_id', 'users', type_='foreignkey')
    op.drop_column('users', 'tenant_id')
    
    # 删除角色表的新字段
    op.drop_constraint('fk_roles_tenant_id', 'roles', type_='foreignkey')
    op.drop_column('roles', 'tenant_id')
    op.drop_column('roles', 'priority')
    op.drop_column('roles', 'is_admin')
    op.drop_column('roles', 'is_system')
    op.drop_column('roles', 'is_active')
    op.drop_column('roles', 'display_name')
    
    # 删除角色权限关联表
    op.drop_table('role_permissions')
    
    # 删除权限表
    op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
    op.drop_table('permissions')
    
    # 删除租户表
    op.drop_index(op.f('ix_tenants_name'), table_name='tenants')
    op.drop_table('tenants')
