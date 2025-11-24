"""修复users表status字段缺失问题

Revision ID: d94d3d3dc500
Revises: 9c59fee21a1d
Create Date: 2025-11-24 15:44:50.404862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd94d3d3dc500'
down_revision: Union[str, None] = '9c59fee21a1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """修复users表status字段缺失问题"""
    conn = op.get_bind()
    
    # 1. 检查并创建 userstatus 枚举类型（如果不存在）
    inspector = sa.inspect(conn)
    enum_types = []
    try:
        enum_types = [t['name'] for t in inspector.get_enums()]
    except Exception:
        # 如果 get_enums() 不可用，使用 SQL 查询
        result = conn.execute(sa.text("SELECT typname FROM pg_type WHERE typtype = 'e' AND typname = 'userstatus'"))
        enum_types = [row[0] for row in result] if result else []
    
    # 枚举类型已存在，值为 PENDING, ACTIVE, SUSPENDED, DELETED (大写)
    # 不需要重新创建
    
    # 2. 检查 users 表的列
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    
    # 3. 如果 status 字段不存在，添加它
    if 'status' not in existing_columns:
        # 直接添加枚举类型字段
        op.add_column('users', sa.Column('status', postgresql.ENUM('PENDING', 'ACTIVE', 'SUSPENDED', 'DELETED', name='userstatus', create_type=False), nullable=True))
        
        # 4. 从 is_active 迁移数据到 status
        if 'is_active' in existing_columns:
            op.execute(sa.text("""
                UPDATE users 
                SET status = CASE 
                    WHEN is_active = true THEN 'ACTIVE'::userstatus
                    ELSE 'PENDING'::userstatus
                END
            """))
            # 设置默认值
            op.execute(sa.text("UPDATE users SET status = 'ACTIVE'::userstatus WHERE status IS NULL"))
        else:
            # 如果没有 is_active 字段，设置默认值
            op.execute(sa.text("UPDATE users SET status = 'ACTIVE'::userstatus WHERE status IS NULL"))
        
        # 5. 设置 status 字段为 NOT NULL
        op.alter_column('users', 'status', nullable=False)
        op.alter_column('users', 'status', server_default=sa.text("'PENDING'::userstatus"))
    
    # 6. 如果 is_active 字段存在，删除它
    if 'is_active' in existing_columns:
        op.drop_column('users', 'is_active')


def downgrade() -> None:
    """回滚：恢复 is_active 字段，删除 status 字段"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    
    # 1. 如果 status 字段存在，恢复 is_active 字段
    if 'status' in existing_columns:
        # 添加 is_active 字段
        if 'is_active' not in existing_columns:
            op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
        
        # 从 status 迁移数据到 is_active
        op.execute("""
            UPDATE users 
            SET is_active = CASE 
                WHEN status = 'active'::userstatus THEN true
                ELSE false
            END
        """)
        op.alter_column('users', 'is_active', nullable=False)
        
        # 删除 status 字段
        op.drop_column('users', 'status')
