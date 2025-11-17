"""移除咨询/术前模拟/方案推荐相关表

Revision ID: cleanup_remove_consultation_modules
Revises: 2a40476ccc24
Create Date: 2025-11-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cln_consult_mods'
down_revision: Union[str, None] = '2a40476ccc24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 使用原生SQL安全删除（若存在）
    conn = op.get_bind()
    # 先删除依赖表
    op.execute("DROP TABLE IF EXISTS plan_versions CASCADE;")
    op.execute("DROP TABLE IF EXISTS simulation_images CASCADE;")
    op.execute("DROP TABLE IF EXISTS personalized_plans CASCADE;")
    op.execute("DROP TABLE IF EXISTS customer_preferences CASCADE;")
    op.execute("DROP TABLE IF EXISTS project_types CASCADE;")
    op.execute("DROP TABLE IF EXISTS project_templates CASCADE;")
    # 删除可能遗留的枚举类型
    # PostgreSQL 下 type 名称需要带引号避免冲突
    try:
        op.execute("DROP TYPE IF EXISTS planstatusenum;")
    except Exception:
        # 忽略类型删除错误（例如非PostgreSQL或类型不存在）
        pass


def downgrade() -> None:
    # 不自动恢复这些表，避免误创建历史结构
    pass


