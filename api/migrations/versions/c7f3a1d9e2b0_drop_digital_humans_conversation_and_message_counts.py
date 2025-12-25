"""drop_digital_humans_conversation_and_message_counts

Revision ID: c7f3a1d9e2b0
Revises: b2d1c0a4f7e3
Create Date: 2025-12-25 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7f3a1d9e2b0"
down_revision: Union[str, None] = "b2d1c0a4f7e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("digital_humans", "conversation_count")
    op.drop_column("digital_humans", "message_count")


def downgrade() -> None:
    op.add_column(
        "digital_humans",
        sa.Column("conversation_count", sa.Integer(), nullable=False, server_default="0", comment="会话总数"),
    )
    op.add_column(
        "digital_humans",
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0", comment="消息总数"),
    )


