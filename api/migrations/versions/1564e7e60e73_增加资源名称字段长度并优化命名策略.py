"""增加资源名称字段长度并优化命名策略

Revision ID: 1564e7e60e73
Revises: 2a40476ccc24
Create Date: 2025-11-16 18:33:50.871466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1564e7e60e73'
down_revision: Union[str, None] = '2a40476ccc24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 增加资源名称字段长度从50到100
    op.alter_column('resources', 'name',
                     existing_type=sa.String(length=50),
                     type_=sa.String(length=100),
                     existing_nullable=False,
                     comment='资源名称，如 menu:home, api:user:create')


def downgrade() -> None:
    # 恢复资源名称字段长度为50
    op.alter_column('resources', 'name',
                     existing_type=sa.String(length=100),
                     type_=sa.String(length=50),
                     existing_nullable=False,
                     comment='资源名称，如 menu:home, api:user:create')
