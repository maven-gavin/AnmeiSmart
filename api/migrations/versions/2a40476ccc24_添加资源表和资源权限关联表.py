"""添加资源表和资源权限关联表

Revision ID: 2a40476ccc24
Revises: aa1eb668317b
Create Date: 2025-11-16 17:51:08.820607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a40476ccc24'
down_revision: Union[str, None] = 'aa1eb668317b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建资源表
    op.create_table('resources',
        sa.Column('id', sa.String(length=36), nullable=False, comment='资源ID'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='资源名称，如 menu:home, api:user:create'),
        sa.Column('display_name', sa.String(length=50), nullable=True, comment='资源显示名称'),
        sa.Column('description', sa.String(length=255), nullable=True, comment='资源描述'),
        sa.Column('resource_type', sa.String(length=20), nullable=False, comment='资源类型：api 或 menu'),
        sa.Column('resource_path', sa.String(length=255), nullable=False, comment='API路径或菜单路径'),
        sa.Column('http_method', sa.String(length=10), nullable=True, comment='HTTP方法：GET, POST, PUT, DELETE（仅API资源）'),
        sa.Column('parent_id', sa.String(length=36), nullable=True, comment='父资源ID（菜单层级）'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否系统资源'),
        sa.Column('priority', sa.Integer(), nullable=True, comment='资源优先级'),
        sa.Column('tenant_id', sa.String(length=36), nullable=True, comment='租户ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['resources.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='资源表，存储API端点和菜单项'
    )
    op.create_index(op.f('ix_resources_name'), 'resources', ['name'], unique=True)
    
    # 创建资源-权限关联表
    op.create_table('resource_permissions',
        sa.Column('resource_id', sa.String(length=36), nullable=False, comment='资源ID'),
        sa.Column('permission_id', sa.String(length=36), nullable=False, comment='权限ID'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('resource_id', 'permission_id')
    )


def downgrade() -> None:
    # 删除资源-权限关联表
    op.drop_table('resource_permissions')
    
    # 删除资源表
    op.drop_index(op.f('ix_resources_name'), table_name='resources')
    op.drop_table('resources')
