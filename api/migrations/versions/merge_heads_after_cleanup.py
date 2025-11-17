"""合并多头迁移（名称长度扩展与咨询表清理）

Revision ID: merge_heads_after_cleanup
Revises: 1564e7e60e73, cleanup_remove_consultation_modules
Create Date: 2025-11-16 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_heads_cln1'
down_revision: Union[str, None] = ('1564e7e60e73', 'cln_consult_mods')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 纯合并迁移，无需实际DDL
    pass


def downgrade() -> None:
    # 不支持自动拆分合并
    pass


