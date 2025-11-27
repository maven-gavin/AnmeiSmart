"""修改sender_type枚举值添加chat类型

Revision ID: 0f8b7de14744
Revises: 655edaab4479
Create Date: 2025-11-27 20:18:27.739324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f8b7de14744'
down_revision: Union[str, None] = '655edaab4479'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """修改sender_type枚举值，简化为chat和system两种类型"""
    conn = op.get_bind()
    
    # 1. 创建新的枚举类型（只包含chat和system）
    op.execute(sa.text("CREATE TYPE sender_type_new AS ENUM ('chat', 'system')"))
    
    # 2. 添加临时列用于存储新枚举值
    op.add_column('messages', sa.Column('sender_type_temp', sa.Enum('chat', 'system', name='sender_type_new'), nullable=True))
    
    # 3. 将旧枚举值转换为新枚举值
    # system保持不变，其他所有值都转换为chat
    op.execute(sa.text("""
        UPDATE messages 
        SET sender_type_temp = CASE 
            WHEN sender_type::text = 'system' THEN 'system'::sender_type_new
            ELSE 'chat'::sender_type_new
        END
    """))
    
    # 4. 删除旧列
    op.drop_column('messages', 'sender_type')
    
    # 5. 重命名新列为原列名
    op.alter_column('messages', 'sender_type_temp', new_column_name='sender_type', nullable=False)
    
    # 6. 删除旧枚举类型，重命名新枚举类型
    op.execute(sa.text("DROP TYPE IF EXISTS sender_type"))
    op.execute(sa.text("ALTER TYPE sender_type_new RENAME TO sender_type"))
    
    # 7. 设置默认值
    op.alter_column('messages', 'sender_type', server_default=sa.text("'chat'::sender_type"))


def downgrade() -> None:
    """回滚：恢复旧的枚举类型"""
    conn = op.get_bind()
    
    # 1. 创建旧的枚举类型
    op.execute(sa.text("CREATE TYPE sender_type_old AS ENUM ('customer', 'consultant', 'doctor', 'system', 'digital_human')"))
    
    # 2. 将chat值映射回customer
    op.execute(sa.text("""
        UPDATE messages 
        SET sender_type = 'customer'::sender_type_old 
        WHERE sender_type = 'chat'
    """))
    
    # 3. 修改列使用旧枚举类型
    op.execute(sa.text("ALTER TABLE messages ALTER COLUMN sender_type TYPE sender_type_old USING sender_type::text::sender_type_old"))
    
    # 4. 删除新枚举类型，重命名旧枚举类型
    op.execute(sa.text("DROP TYPE IF EXISTS sender_type"))
    op.execute(sa.text("ALTER TYPE sender_type_old RENAME TO sender_type"))
    
    # 5. 移除默认值
    op.alter_column('messages', 'sender_type', server_default=None)
