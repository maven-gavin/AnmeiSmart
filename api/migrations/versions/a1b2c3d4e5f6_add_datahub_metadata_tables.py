"""add_datahub_metadata_tables

Revision ID: a1b2c3d4e5f6
Revises: 4625c0c73da9
Create Date: 2026-05-12 17:58:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "4625c0c73da9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "datahub_dataset_catalog",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建人ID"),
        sa.Column("updated_by", sa.String(length=36), nullable=True, comment="修改人ID"),
        sa.Column("dataset_key", sa.String(length=100), nullable=False, comment="数据集唯一键"),
        sa.Column("layer", sa.String(length=20), nullable=False, comment="数据层：raw/normalized/features"),
        sa.Column("schema_version", sa.String(length=20), nullable=False, server_default="1.0", comment="Schema 版本"),
        sa.Column("primary_keys", sa.JSON(), nullable=True, comment="主键定义"),
        sa.Column("partition_by", sa.JSON(), nullable=True, comment="分区字段"),
        sa.Column("description", sa.Text(), nullable=True, comment="说明"),
        sa.Column("is_active", sa.String(length=10), nullable=False, server_default="true", comment="是否启用"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_key", name="uq_datahub_dataset_catalog_dataset_key"),
        comment="DataHub 数据集目录与口径元信息",
    )

    op.create_table(
        "datahub_dataset_watermarks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建人ID"),
        sa.Column("updated_by", sa.String(length=36), nullable=True, comment="修改人ID"),
        sa.Column("dataset", sa.String(length=100), nullable=False, comment="数据集"),
        sa.Column("symbol", sa.String(length=32), nullable=True, comment="证券代码"),
        sa.Column("last_success_date", sa.Date(), nullable=True, comment="最近成功日期"),
        sa.Column("last_quality_score", sa.Float(), nullable=True, comment="最近质量分"),
        sa.Column("last_object_key", sa.String(length=500), nullable=True, comment="最近对象路径"),
        sa.Column("last_batch_id", sa.String(length=64), nullable=True, comment="最近批次ID"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset", "symbol", name="uq_datahub_dataset_watermarks_dataset_symbol"),
        comment="DataHub 数据集增量水位",
    )
    op.create_index("idx_datahub_dataset_watermarks_dataset", "datahub_dataset_watermarks", ["dataset"], unique=False)

    op.create_table(
        "datahub_job_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建人ID"),
        sa.Column("updated_by", sa.String(length=36), nullable=True, comment="修改人ID"),
        sa.Column("job_type", sa.String(length=50), nullable=False, comment="作业类型：backfill/daily_incremental"),
        sa.Column("dataset", sa.String(length=100), nullable=True, comment="数据集"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending", comment="状态"),
        sa.Column("trigger_source", sa.String(length=50), nullable=True, comment="触发来源：api/cli/cron"),
        sa.Column("job_params", sa.JSON(), nullable=True, comment="作业参数快照"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True, comment="开始时间"),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True, comment="结束时间"),
        sa.Column("task_total", sa.Integer(), nullable=False, server_default="0", comment="任务总数"),
        sa.Column("task_success", sa.Integer(), nullable=False, server_default="0", comment="成功任务数"),
        sa.Column("task_failed", sa.Integer(), nullable=False, server_default="0", comment="失败任务数"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="错误信息"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        comment="DataHub 作业运行记录",
    )
    op.create_index("idx_datahub_job_runs_job_type", "datahub_job_runs", ["job_type"], unique=False)
    op.create_index("idx_datahub_job_runs_status", "datahub_job_runs", ["status"], unique=False)
    op.create_index("idx_datahub_job_runs_dataset", "datahub_job_runs", ["dataset"], unique=False)

    op.create_table(
        "datahub_job_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建人ID"),
        sa.Column("updated_by", sa.String(length=36), nullable=True, comment="修改人ID"),
        sa.Column("job_run_id", sa.String(length=36), nullable=False, comment="作业ID"),
        sa.Column("dataset", sa.String(length=100), nullable=False, comment="数据集"),
        sa.Column("symbol", sa.String(length=32), nullable=True, comment="证券代码"),
        sa.Column("start_date", sa.Date(), nullable=True, comment="任务起始日期"),
        sa.Column("end_date", sa.Date(), nullable=True, comment="任务结束日期"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending", comment="状态"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0", comment="重试次数"),
        sa.Column("last_error", sa.Text(), nullable=True, comment="最后错误"),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True, comment="锁定时间"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_run_id"], ["datahub_job_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="DataHub 作业子任务记录",
    )
    op.create_index("idx_datahub_job_tasks_run_id", "datahub_job_tasks", ["job_run_id"], unique=False)
    op.create_index("idx_datahub_job_tasks_dataset_symbol", "datahub_job_tasks", ["dataset", "symbol"], unique=False)
    op.create_index("idx_datahub_job_tasks_status", "datahub_job_tasks", ["status"], unique=False)

    op.create_table(
        "datahub_provider_health",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建人ID"),
        sa.Column("updated_by", sa.String(length=36), nullable=True, comment="修改人ID"),
        sa.Column("provider", sa.String(length=50), nullable=False, comment="数据源标识"),
        sa.Column("dataset", sa.String(length=100), nullable=False, comment="数据集"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="healthy", comment="健康状态"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0", comment="成功次数"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0", comment="失败次数"),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True, comment="最近成功时间"),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True, comment="最近失败时间"),
        sa.Column("last_error", sa.Text(), nullable=True, comment="最近错误"),
        sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=True, comment="冷却到期时间"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "dataset", name="uq_datahub_provider_health_provider_dataset"),
        comment="DataHub Provider 健康状态",
    )
    op.create_index("idx_datahub_provider_health_status", "datahub_provider_health", ["status"], unique=False)

    op.create_table(
        "datahub_quality_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建人ID"),
        sa.Column("updated_by", sa.String(length=36), nullable=True, comment="修改人ID"),
        sa.Column("dataset", sa.String(length=100), nullable=False, comment="数据集"),
        sa.Column("symbol", sa.String(length=32), nullable=True, comment="证券代码"),
        sa.Column("biz_date", sa.Date(), nullable=True, comment="业务日期"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0", comment="质量分"),
        sa.Column("severity", sa.String(length=10), nullable=False, server_default="p2", comment="问题等级"),
        sa.Column("issues", sa.JSON(), nullable=True, comment="问题详情"),
        sa.Column("object_key", sa.String(length=500), nullable=True, comment="关联对象路径"),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, comment="检查时间"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        comment="DataHub 数据质量报告",
    )
    op.create_index("idx_datahub_quality_reports_dataset_symbol", "datahub_quality_reports", ["dataset", "symbol"], unique=False)
    op.create_index("idx_datahub_quality_reports_checked_at", "datahub_quality_reports", ["checked_at"], unique=False)

    op.create_table(
        "datahub_object_index",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建人ID"),
        sa.Column("updated_by", sa.String(length=36), nullable=True, comment="修改人ID"),
        sa.Column("bucket", sa.String(length=128), nullable=False, comment="MinIO bucket"),
        sa.Column("object_key", sa.String(length=500), nullable=False, comment="对象路径"),
        sa.Column("dataset", sa.String(length=100), nullable=False, comment="数据集"),
        sa.Column("layer", sa.String(length=20), nullable=False, comment="层级"),
        sa.Column("provider", sa.String(length=50), nullable=True, comment="来源数据源"),
        sa.Column("symbol", sa.String(length=32), nullable=True, comment="证券代码"),
        sa.Column("start_date", sa.Date(), nullable=True, comment="覆盖起始日期"),
        sa.Column("end_date", sa.Date(), nullable=True, comment="覆盖结束日期"),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0", comment="行数"),
        sa.Column("schema_version", sa.String(length=20), nullable=False, server_default="1.0", comment="Schema 版本"),
        sa.Column("content_hash", sa.String(length=128), nullable=True, comment="内容哈希"),
        sa.Column("quality_score", sa.Float(), nullable=True, comment="质量分"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bucket", "object_key", name="uq_datahub_object_index_bucket_object_key"),
        comment="DataHub MinIO 对象索引",
    )
    op.create_index("idx_datahub_object_index_dataset_layer", "datahub_object_index", ["dataset", "layer"], unique=False)
    op.create_index("idx_datahub_object_index_symbol_date", "datahub_object_index", ["symbol", "start_date", "end_date"], unique=False)



def downgrade() -> None:
    op.drop_index("idx_datahub_object_index_symbol_date", table_name="datahub_object_index")
    op.drop_index("idx_datahub_object_index_dataset_layer", table_name="datahub_object_index")
    op.drop_table("datahub_object_index")

    op.drop_index("idx_datahub_quality_reports_checked_at", table_name="datahub_quality_reports")
    op.drop_index("idx_datahub_quality_reports_dataset_symbol", table_name="datahub_quality_reports")
    op.drop_table("datahub_quality_reports")

    op.drop_index("idx_datahub_provider_health_status", table_name="datahub_provider_health")
    op.drop_table("datahub_provider_health")

    op.drop_index("idx_datahub_job_tasks_status", table_name="datahub_job_tasks")
    op.drop_index("idx_datahub_job_tasks_dataset_symbol", table_name="datahub_job_tasks")
    op.drop_index("idx_datahub_job_tasks_run_id", table_name="datahub_job_tasks")
    op.drop_table("datahub_job_tasks")

    op.drop_index("idx_datahub_job_runs_dataset", table_name="datahub_job_runs")
    op.drop_index("idx_datahub_job_runs_status", table_name="datahub_job_runs")
    op.drop_index("idx_datahub_job_runs_job_type", table_name="datahub_job_runs")
    op.drop_table("datahub_job_runs")

    op.drop_index("idx_datahub_dataset_watermarks_dataset", table_name="datahub_dataset_watermarks")
    op.drop_table("datahub_dataset_watermarks")

    op.drop_table("datahub_dataset_catalog")
