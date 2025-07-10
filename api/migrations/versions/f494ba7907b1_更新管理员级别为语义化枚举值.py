"""更新管理员级别为语义化枚举值

Revision ID: f494ba7907b1
Revises: 723c0cbcec54
Create Date: 2025-07-10 21:30:43.267330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f494ba7907b1'
down_revision: Union[str, None] = '723c0cbcec54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    更新管理员级别为语义化枚举值：
    1. 将NULL值更新为'basic'
    2. 设置列默认值为'basic' 
    3. 添加检查约束确保只允许有效的枚举值
    """
    # 步骤1: 更新现有的NULL值为'basic'
    op.execute("UPDATE administrators SET admin_level = 'basic' WHERE admin_level IS NULL")
    
    # 步骤2: 修改列的默认值
    op.alter_column('administrators', 'admin_level',
                    existing_type=sa.String(),
                    server_default='basic',
                    existing_nullable=True)
    
    # 步骤3: 添加检查约束确保只允许有效的枚举值
    op.create_check_constraint(
        'ck_administrators_admin_level_valid',
        'administrators',
        "admin_level IN ('basic', 'advanced', 'super')"
    )


def downgrade() -> None:
    """
    回滚管理员级别更改：
    1. 移除检查约束
    2. 恢复默认值为NULL
    """
    # 步骤1: 移除检查约束
    op.drop_constraint('ck_administrators_admin_level_valid', 'administrators', type_='check')
    
    # 步骤2: 恢复列的默认值为NULL
    op.alter_column('administrators', 'admin_level',
                    existing_type=sa.String(),
                    server_default=None,
                    existing_nullable=True)
