"""重命名 pending_tasks 表为 tasks

Revision ID: 9b10c1943252
Revises: 1a2b3c4d5e6f
Create Date: 2025-12-15 19:27:06.699537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9b10c1943252'
down_revision: Union[str, None] = '1a2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级：将 pending_tasks 表重命名为 tasks，并更新索引名称"""
    
    # 1. 重命名索引
    op.execute(sa.text("ALTER INDEX IF EXISTS idx_pending_task_type RENAME TO idx_task_type"))
    op.execute(sa.text("ALTER INDEX IF EXISTS idx_pending_task_status RENAME TO idx_task_status"))
    op.execute(sa.text("ALTER INDEX IF EXISTS idx_pending_task_assignee RENAME TO idx_task_assignee"))
    op.execute(sa.text("ALTER INDEX IF EXISTS idx_pending_task_priority RENAME TO idx_task_priority"))
    
    # 2. 重命名表
    op.execute(sa.text("ALTER TABLE pending_tasks RENAME TO tasks"))
    
    # 3. 更新表注释
    op.execute(sa.text("COMMENT ON TABLE tasks IS '任务表，记录所有任务记录'"))


def downgrade() -> None:
    """降级：将 tasks 表重命名回 pending_tasks，并恢复索引名称"""
    
    # 1. 重命名表
    op.execute(sa.text("ALTER TABLE tasks RENAME TO pending_tasks"))
    
    # 2. 恢复索引名称
    op.execute(sa.text("ALTER INDEX IF EXISTS idx_task_type RENAME TO idx_pending_task_type"))
    op.execute(sa.text("ALTER INDEX IF EXISTS idx_task_status RENAME TO idx_pending_task_status"))
    op.execute(sa.text("ALTER INDEX IF EXISTS idx_task_assignee RENAME TO idx_pending_task_assignee"))
    op.execute(sa.text("ALTER INDEX IF EXISTS idx_task_priority RENAME TO idx_pending_task_priority"))
    
    # 3. 恢复表注释
    op.execute(sa.text("COMMENT ON TABLE pending_tasks IS '待办任务表，记录系统发出的待处理任务'"))

