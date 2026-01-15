"""remove_doctor_consultant_tables

Revision ID: 4625c0c73da9
Revises: 9c3a1f2b4d10
Create Date: 2026-01-15 16:08:15.325230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4625c0c73da9'
down_revision: Union[str, None] = '9c3a1f2b4d10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 删除 doctors 和 consultants 表
    # 注意：这些表可能不存在（如果数据库是新建的），所以使用 IF EXISTS
    op.execute("DROP TABLE IF EXISTS doctors CASCADE")
    op.execute("DROP TABLE IF EXISTS consultants CASCADE")
    
    # 从 roles 表中删除 doctor 和 consultant 角色（如果存在）
    op.execute("DELETE FROM roles WHERE name IN ('doctor', 'consultant')")


def downgrade() -> None:
    # 重新创建 doctors 表
    op.create_table('doctors',
        sa.Column('id', sa.String(length=36), nullable=False, comment='记录ID'),
        sa.Column('user_id', sa.String(length=36), nullable=False, comment='用户ID'),
        sa.Column('specialization', sa.String(length=255), nullable=True, comment='专科方向'),
        sa.Column('certification', sa.String(length=255), nullable=True, comment='资格证书'),
        sa.Column('license_number', sa.String(length=100), nullable=True, comment='执业证号'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        comment='医生表，存储医生扩展信息'
    )
    
    # 重新创建 consultants 表
    op.create_table('consultants',
        sa.Column('id', sa.String(length=36), nullable=False, comment='记录ID'),
        sa.Column('user_id', sa.String(length=36), nullable=False, comment='用户ID'),
        sa.Column('expertise', sa.String(length=255), nullable=True, comment='专长领域'),
        sa.Column('performance_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='业绩指标'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        comment='顾问表，存储顾问扩展信息'
    )
