"""add_datahub_worker_heartbeat

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-05-12 22:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("datahub_worker_heartbeat"):
        op.create_table(
            "datahub_worker_heartbeat",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
            sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建人ID"),
            sa.Column("updated_by", sa.String(length=36), nullable=True, comment="修改人ID"),
            sa.Column("worker_name", sa.String(length=100), nullable=False, comment="Worker 名称"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="idle", comment="状态：idle/running/error"),
            sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False, comment="最近心跳时间"),
            sa.Column("last_run_id", sa.String(length=36), nullable=True, comment="最近处理的作业ID"),
            sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0", comment="累计处理作业数"),
            sa.Column("last_error", sa.Text(), nullable=True, comment="最近错误"),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("worker_name", name="uq_datahub_worker_heartbeat_worker_name"),
            comment="DataHub Worker 心跳状态",
        )

    indexes = {idx["name"] for idx in inspector.get_indexes("datahub_worker_heartbeat")}
    if "idx_datahub_worker_heartbeat_last_heartbeat_at" not in indexes:
        op.create_index(
            "idx_datahub_worker_heartbeat_last_heartbeat_at",
            "datahub_worker_heartbeat",
            ["last_heartbeat_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("datahub_worker_heartbeat"):
        indexes = {idx["name"] for idx in inspector.get_indexes("datahub_worker_heartbeat")}
        if "idx_datahub_worker_heartbeat_last_heartbeat_at" in indexes:
            op.drop_index("idx_datahub_worker_heartbeat_last_heartbeat_at", table_name="datahub_worker_heartbeat")
        op.drop_table("datahub_worker_heartbeat")
