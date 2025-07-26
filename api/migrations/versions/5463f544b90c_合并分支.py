"""合并分支

Revision ID: 5463f544b90c
Revises: 23747bb7569c, e1234567890a
Create Date: 2025-07-26 23:42:03.975203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5463f544b90c'
down_revision: Union[str, None] = ('23747bb7569c', 'e1234567890a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
