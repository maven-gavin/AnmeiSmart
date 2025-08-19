"""步骤3: 清理upload_sessions表，移除conversation_id

Revision ID: step3_cleanup_upload
Revises: step2_data_fix
Create Date: 2024-12-19 12:03:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'step3_cleanup_upload'
down_revision = 'step2_data_fix'
branch_labels = None
depends_on = None


def upgrade():
    print("步骤3: 清理 upload_sessions 表...")
    
    # 删除conversation_id字段及其约束
    try:
        # 先删除外键约束
        op.drop_constraint('upload_sessions_conversation_id_fkey', 'upload_sessions', type_='foreignkey')
        print("  ✅ 删除 conversation_id 外键约束")
    except Exception as e:
        print(f"  ⚠️ 删除外键约束失败: {e}")
    
    try:
        # 删除字段
        op.drop_column('upload_sessions', 'conversation_id')
        print("  ✅ 删除 conversation_id 字段")
    except Exception as e:
        print(f"  ⚠️ 删除字段失败: {e}")
    
    print("\\n🎉 步骤3完成！upload_sessions 表现在是独立的上传组件")


def downgrade():
    print("回滚步骤3...")
    
    # 重新添加conversation_id字段
    try:
        op.add_column('upload_sessions', sa.Column('conversation_id', sa.String(36), nullable=True))
        op.create_foreign_key('upload_sessions_conversation_id_fkey', 'upload_sessions', 'conversations', ['conversation_id'], ['id'])
    except:
        pass
