"""移除资源和权限的租户关联改为全局

Revision ID: 655edaab4479
Revises: d94d3d3dc500
Create Date: 2025-11-25 11:12:35.073778

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '655edaab4479'
down_revision: Union[str, None] = 'd94d3d3dc500'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    将资源和权限改为全局，移除租户关联
    架构调整：
    - 资源（Resource）：全局唯一，不区分租户
    - 权限（Permission）：全局唯一，不区分租户
    - 角色（Role）：保留租户关联
    - 用户（User）：保留租户关联
    """
    conn = op.get_bind()
    
    # 如果事务处于失败状态，先回滚
    try:
        conn.execute(sa.text('ROLLBACK'))
    except Exception:
        pass
    
    # ========== 1. 修改 resources 表 ==========
    # 1.1 删除租户相关的唯一约束（如果存在）
    try:
        op.drop_constraint('uq_resource_name_tenant', 'resources', type_='unique')
    except Exception:
        # 约束不存在，忽略错误
        pass
    
    # 1.2 添加全局唯一约束（name 全局唯一）
    # 先检查是否有重复的 name（如果有，需要先处理数据）
    try:
        result = conn.execute(sa.text("""
            SELECT COUNT(*) 
            FROM (
                SELECT name, COUNT(*) as cnt
                FROM resources
                GROUP BY name
                HAVING COUNT(*) > 1
            ) duplicates
        """))
        duplicate_count = result.scalar()
        if duplicate_count > 0:
            raise Exception('存在重复的资源名称，请先清理数据后再执行迁移')
    except Exception as e:
        # 如果查询失败，可能是事务问题，回滚后重试
        conn.execute(sa.text('ROLLBACK'))
        result = conn.execute(sa.text("""
            SELECT COUNT(*) 
            FROM (
                SELECT name, COUNT(*) as cnt
                FROM resources
                GROUP BY name
                HAVING COUNT(*) > 1
            ) duplicates
        """))
        duplicate_count = result.scalar()
        if duplicate_count > 0:
            raise Exception('存在重复的资源名称，请先清理数据后再执行迁移')
    
    # 创建全局唯一约束
    try:
        op.create_unique_constraint('uq_resource_name', 'resources', ['name'])
    except Exception:
        # 约束已存在，忽略错误
        pass
    
    # 1.3 添加 (resource_path, http_method) 唯一约束（用于 API 资源）
    # 注意：PostgreSQL 的唯一约束允许 NULL，多个 NULL 值不会违反约束
    try:
        op.create_unique_constraint('uq_resource_path_method', 'resources', ['resource_path', 'http_method'])
    except Exception:
        # 约束已存在，忽略错误
        pass
    
    # 1.4 删除外键约束（如果存在）
    try:
        op.drop_constraint('resources_tenant_id_fkey', 'resources', type_='foreignkey')
    except Exception:
        # 约束不存在，忽略错误
        pass
    
    # 1.5 删除 tenant_id 列
    try:
        op.drop_column('resources', 'tenant_id')
    except Exception:
        # 列不存在，忽略错误
        pass
    
    # ========== 2. 修改 permissions 表 ==========
    # 2.1 删除租户相关的唯一约束（如果存在）
    try:
        op.drop_constraint('uq_permission_code_tenant', 'permissions', type_='unique')
    except Exception:
        pass
    try:
        op.drop_constraint('uq_permission_name_tenant', 'permissions', type_='unique')
    except Exception:
        pass
    
    # 2.2 检查是否有重复的 code 和 name（如果有，需要先处理数据）
    try:
        result = conn.execute(sa.text("""
            SELECT COUNT(*) 
            FROM (
                SELECT code, COUNT(*) as cnt
                FROM permissions
                GROUP BY code
                HAVING COUNT(*) > 1
            ) duplicates
        """))
        duplicate_code_count = result.scalar()
        if duplicate_code_count > 0:
            raise Exception('存在重复的权限标识码，请先清理数据后再执行迁移')
    except Exception as e:
        if '存在重复的权限标识码' in str(e):
            raise
        # 如果查询失败，可能是事务问题，回滚后重试
        conn.execute(sa.text('ROLLBACK'))
        result = conn.execute(sa.text("""
            SELECT COUNT(*) 
            FROM (
                SELECT code, COUNT(*) as cnt
                FROM permissions
                GROUP BY code
                HAVING COUNT(*) > 1
            ) duplicates
        """))
        duplicate_code_count = result.scalar()
        if duplicate_code_count > 0:
            raise Exception('存在重复的权限标识码，请先清理数据后再执行迁移')
    
    try:
        result = conn.execute(sa.text("""
            SELECT COUNT(*) 
            FROM (
                SELECT name, COUNT(*) as cnt
                FROM permissions
                GROUP BY name
                HAVING COUNT(*) > 1
            ) duplicates
        """))
        duplicate_name_count = result.scalar()
        if duplicate_name_count > 0:
            raise Exception('存在重复的权限名称，请先清理数据后再执行迁移')
    except Exception as e:
        if '存在重复的权限名称' in str(e):
            raise
        # 如果查询失败，可能是事务问题，回滚后重试
        conn.execute(sa.text('ROLLBACK'))
        result = conn.execute(sa.text("""
            SELECT COUNT(*) 
            FROM (
                SELECT name, COUNT(*) as cnt
                FROM permissions
                GROUP BY name
                HAVING COUNT(*) > 1
            ) duplicates
        """))
        duplicate_name_count = result.scalar()
        if duplicate_name_count > 0:
            raise Exception('存在重复的权限名称，请先清理数据后再执行迁移')
    
    # 2.3 添加全局唯一约束
    try:
        op.create_unique_constraint('uq_permission_code', 'permissions', ['code'])
    except Exception:
        # 约束已存在，忽略错误
        pass
    try:
        op.create_unique_constraint('uq_permission_name', 'permissions', ['name'])
    except Exception:
        # 约束已存在，忽略错误
        pass
    
    # 2.4 删除外键约束（如果存在）
    try:
        op.drop_constraint('permissions_tenant_id_fkey', 'permissions', type_='foreignkey')
    except Exception:
        # 约束不存在，忽略错误
        pass
    
    # 2.5 删除 tenant_id 列
    try:
        op.drop_column('permissions', 'tenant_id')
    except Exception:
        # 列不存在，忽略错误
        pass


def downgrade() -> None:
    """
    回滚：恢复资源和权限的租户关联
    """
    
    # ========== 1. 恢复 permissions 表 ==========
    # 1.1 添加 tenant_id 列（默认值为 'system'）
    op.add_column('permissions', sa.Column('tenant_id', sa.String(36), nullable=True))
    op.execute("UPDATE permissions SET tenant_id = 'system' WHERE tenant_id IS NULL")
    op.alter_column('permissions', 'tenant_id', nullable=False, server_default="'system'")
    
    # 1.2 添加外键约束
    op.create_foreign_key(
        'permissions_tenant_id_fkey',
        'permissions', 'tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 1.3 删除全局唯一约束
    op.drop_constraint('uq_permission_name', 'permissions', type_='unique')
    op.drop_constraint('uq_permission_code', 'permissions', type_='unique')
    
    # 1.4 恢复租户相关的唯一约束
    op.create_unique_constraint('uq_permission_name_tenant', 'permissions', ['name', 'tenant_id'])
    op.create_unique_constraint('uq_permission_code_tenant', 'permissions', ['code', 'tenant_id'])
    
    # ========== 2. 恢复 resources 表 ==========
    # 2.1 添加 tenant_id 列（默认值为 'system'）
    op.add_column('resources', sa.Column('tenant_id', sa.String(36), nullable=True))
    op.execute("UPDATE resources SET tenant_id = 'system' WHERE tenant_id IS NULL")
    op.alter_column('resources', 'tenant_id', nullable=False, server_default="'system'")
    
    # 2.2 添加外键约束
    op.create_foreign_key(
        'resources_tenant_id_fkey',
        'resources', 'tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 2.3 删除全局唯一约束（如果存在）
    try:
        op.drop_constraint('uq_resource_path_method', 'resources', type_='unique')
    except Exception:
        pass
    try:
        op.drop_constraint('uq_resource_name', 'resources', type_='unique')
    except Exception:
        pass
    
    # 2.4 恢复租户相关的唯一约束
    op.create_unique_constraint('uq_resource_name_tenant', 'resources', ['name', 'tenant_id'])
