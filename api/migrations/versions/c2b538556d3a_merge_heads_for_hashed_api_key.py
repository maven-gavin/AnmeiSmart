"""merge heads for hashed_api_key

Revision ID: c2b538556d3a
Revises: 8e9e55642430, 9c0f1a2dcb10
Create Date: 2025-08-10 10:51:32.875492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2b538556d3a'
down_revision: Union[str, None] = ('8e9e55642430', '9c0f1a2dcb10')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
