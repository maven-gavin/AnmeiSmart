"""make_digital_humans_user_id_nullable

Revision ID: b2d1c0a4f7e3
Revises: 0cf50faf4ed7
Create Date: 2025-12-25 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2d1c0a4f7e3"
down_revision: Union[str, None] = "0cf50faf4ed7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "digital_humans",
        "user_id",
        existing_type=sa.String(length=36),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "digital_humans",
        "user_id",
        existing_type=sa.String(length=36),
        nullable=False,
    )


