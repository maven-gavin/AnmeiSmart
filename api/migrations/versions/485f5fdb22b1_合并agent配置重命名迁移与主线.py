"""合并Agent配置重命名迁移与主线

Revision ID: 485f5fdb22b1
Revises: 0c496d1b37a1, 6e9a9cccd06b
Create Date: 2025-08-19 15:47:02.755004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '485f5fdb22b1'
down_revision: Union[str, None] = ('0c496d1b37a1', '6e9a9cccd06b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
