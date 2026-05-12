"""add_job_params_to_datahub_job_runs

Revision ID: c3d4e5f6a7b8
Revises: b7c8d9e0f1a2
Create Date: 2026-05-12 22:18:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE datahub_job_runs
        ADD COLUMN IF NOT EXISTS job_params JSONB
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE datahub_job_runs
        DROP COLUMN IF EXISTS job_params
        """
    )
