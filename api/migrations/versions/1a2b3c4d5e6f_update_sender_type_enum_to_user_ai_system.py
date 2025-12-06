"""更新 sender_type 枚举为 user/ai/system

Revision ID: 1a2b3c4d5e6f
Revises: 7e61fced6500
Create Date: 2025-12-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, None] = "7e61fced6500"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  """升级：将 messages.sender_type 从 chat/system 调整为 user/ai/system"""
  bind = op.get_bind()

  # 1. 创建新的枚举类型 sender_type_new
  new_enum = postgresql.ENUM("user", "ai", "system", name="sender_type_new")
  new_enum.create(bind, checkfirst=True)

  # 2. 先移除旧默认值（chat），避免类型切换时报默认值类型不匹配
  op.execute("ALTER TABLE messages ALTER COLUMN sender_type DROP DEFAULT")

  # 3. 将列类型切换到新的枚举，并把历史 chat 值迁移为 user
  op.execute(
    """
    ALTER TABLE messages
    ALTER COLUMN sender_type
    TYPE sender_type_new
    USING (
      CASE sender_type::text
        WHEN 'chat' THEN 'user'
        ELSE sender_type::text
      END
    )::sender_type_new
    """
  )

  # 4. 将旧的 sender_type 类型重命名并用新的替换
  op.execute("ALTER TYPE sender_type RENAME TO sender_type_old")
  op.execute("ALTER TYPE sender_type_new RENAME TO sender_type")

  # 5. 删除旧类型
  op.execute("DROP TYPE sender_type_old")

  # 6. 设置新的默认值 user
  op.execute("ALTER TABLE messages ALTER COLUMN sender_type SET DEFAULT 'user'")


def downgrade() -> None:
  """降级：将 messages.sender_type 从 user/ai/system 回退为 chat/system"""
  bind = op.get_bind()

  # 1. 创建旧的枚举类型 sender_type_old(chat/system)
  old_enum = postgresql.ENUM("chat", "system", name="sender_type_old")
  old_enum.create(bind, checkfirst=True)

  # 2. 先移除当前默认值（user），避免类型切换时报默认值类型不匹配
  op.execute("ALTER TABLE messages ALTER COLUMN sender_type DROP DEFAULT")

  # 3. 将列类型切换回旧的枚举：
  #    - user 和 ai 都回退为 chat
  #    - system 保持 system
  op.execute(
    """
    ALTER TABLE messages
    ALTER COLUMN sender_type
    TYPE sender_type_old
    USING (
      CASE sender_type::text
        WHEN 'user' THEN 'chat'
        WHEN 'ai' THEN 'chat'
        ELSE sender_type::text
      END
    )::sender_type_old
    """
  )

  # 4. 将当前 sender_type 类型重命名，并用旧类型替换
  op.execute("ALTER TYPE sender_type RENAME TO sender_type_new")
  op.execute("ALTER TYPE sender_type_old RENAME TO sender_type")

  # 5. 删除新的类型
  op.execute("DROP TYPE sender_type_new")

  # 6. 恢复默认值 chat
  op.execute("ALTER TABLE messages ALTER COLUMN sender_type SET DEFAULT 'chat'")


