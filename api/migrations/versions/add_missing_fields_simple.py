"""添加缺失字段（简化版）

Revision ID: add_missing_fields_simple
Revises: recreate_tables_safe
Create Date: 2024-12-19 12:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_missing_fields_simple'
down_revision = 'recreate_tables_safe'
branch_labels = None
depends_on = None


def upgrade():
    print("添加缺失字段...")
    
    # 为conversation_participants表添加缺失字段
    print("为 conversation_participants 表添加缺失字段...")
    
    try:
        op.add_column('conversation_participants', sa.Column('left_at', sa.DateTime(timezone=True), nullable=True, comment='离开时间'))
        print("  ✅ 添加 left_at 字段")
    except Exception as e:
        print(f"  ⚠️ left_at 字段: {e}")
    
    try:
        op.add_column('conversation_participants', sa.Column('is_muted', sa.Boolean(), nullable=False, default=False, comment='个人免打扰'))
        print("  ✅ 添加 is_muted 字段")
    except Exception as e:
        print(f"  ⚠️ is_muted 字段: {e}")
    
    try:
        op.add_column('conversation_participants', sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True, comment='最后阅读时间'))
        print("  ✅ 添加 last_read_at 字段")
    except Exception as e:
        print(f"  ⚠️ last_read_at 字段: {e}")
    
    print("\\n🎉 缺失字段添加完成！")


def downgrade():
    print("回滚缺失字段...")
    
    # 删除添加的字段
    try:
        op.drop_column('conversation_participants', 'last_read_at')
        op.drop_column('conversation_participants', 'is_muted')
        op.drop_column('conversation_participants', 'left_at')
    except:
        pass
    
    print("回滚完成")
