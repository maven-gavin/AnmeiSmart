"""add hashed_api_key to mcp_tool_groups

Revision ID: 9c0f1a2dcb10
Revises: 46a889469f7b
Create Date: 2025-08-08 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c0f1a2dcb10'
down_revision: Union[str, None] = '46a889469f7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加列（若已存在则忽略由数据库处理）
    op.add_column('mcp_tool_groups', sa.Column('hashed_api_key', sa.String(length=64), nullable=True, comment='API密钥SHA-256哈希（查询用）'))
    # 创建索引
    op.create_index(op.f('ix_mcp_tool_groups_hashed_api_key'), 'mcp_tool_groups', ['hashed_api_key'], unique=False)


def downgrade() -> None:
    # 删除索引与列
    op.drop_index(op.f('ix_mcp_tool_groups_hashed_api_key'), table_name='mcp_tool_groups')
    op.drop_column('mcp_tool_groups', 'hashed_api_key')


