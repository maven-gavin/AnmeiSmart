"""初始数据库状态

Revision ID: 719fe9f5395e
Revises: 
Create Date: 2024-05-19 11:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '719fe9f5395e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 这是初始化迁移，所有表已经存在，不需要做任何操作
    pass


def downgrade() -> None:
    # 理论上可以删除所有表，但建议不要实现此方法
    # 以防止意外删除所有数据
    raise NotImplementedError("不支持回滚初始数据库状态") 