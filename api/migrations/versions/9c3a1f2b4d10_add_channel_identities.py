"""add_channel_identities

Revision ID: 9c3a1f2b4d10
Revises: 884721983323
Create Date: 2026-01-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9c3a1f2b4d10"
down_revision: Union[str, None] = "884721983323"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "channel_identities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建人ID"),
        sa.Column("updated_by", sa.String(length=36), nullable=True, comment="修改人ID"),
        sa.Column("channel_type", sa.String(length=50), nullable=False, comment="渠道类型：wechat_work, lark, dingtalk 等"),
        sa.Column("peer_id", sa.String(length=255), nullable=False, comment="渠道侧用户唯一标识（peer_id/open_id）"),
        sa.Column("user_id", sa.String(length=36), nullable=False, comment="系统内客户用户ID"),
        sa.Column("peer_name", sa.String(length=255), nullable=True, comment="渠道侧昵称/展示名"),
        sa.Column("extra_data", sa.JSON(), nullable=True, comment="渠道侧原始信息（头像、union_id、扩展字段等）"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="首次出现时间"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="最后出现时间"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel_type", "peer_id", name="uq_channel_identity_type_peer"),
        comment="渠道身份映射表：外部 peer_id 映射到系统内 customer(User)",
    )
    op.create_index("idx_channel_identity_user_id", "channel_identities", ["user_id"], unique=False)
    op.create_index("idx_channel_identity_type_peer", "channel_identities", ["channel_type", "peer_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_channel_identity_type_peer", table_name="channel_identities")
    op.drop_index("idx_channel_identity_user_id", table_name="channel_identities")
    op.drop_table("channel_identities")

