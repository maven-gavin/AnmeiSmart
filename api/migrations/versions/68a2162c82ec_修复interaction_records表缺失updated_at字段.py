"""修复interaction_records表缺失updated_at字段

Revision ID: 68a2162c82ec
Revises: 9ab05227adf8
Create Date: 2025-08-21 22:04:37.634320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68a2162c82ec'
down_revision: Union[str, None] = '9ab05227adf8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 为interaction_records表添加缺失的updated_at字段
    op.add_column('interaction_records', 
                  sa.Column('updated_at', sa.DateTime(timezone=True), 
                           server_default=sa.func.now(), nullable=False, 
                           comment='更新时间'))


def downgrade() -> None:
    # 删除updated_at字段
    op.drop_column('interaction_records', 'updated_at')
