"""步骤1: 添加可空字段

Revision ID: step1_add_nullable_fields
Revises: add_dh_participants
Create Date: 2024-12-19 12:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'step1_add_nullable_fields'
down_revision = 'add_dh_participants'
branch_labels = None
depends_on = None


def upgrade():
    print("步骤1: 添加可空字段...")
    
    # 1. 为conversations表添加可空字段
    print("为 conversations 表添加字段...")
    
    try:
        op.add_column('conversations', sa.Column('conv_type', sa.String(50), nullable=True, comment='会话类型'))
        print("  ✅ 添加 conv_type 字段")
    except Exception as e:
        print(f"  ⚠️ conv_type 字段: {e}")
    
    try:
        op.add_column('conversations', sa.Column('owner_id', sa.String(36), nullable=True, comment='会话所有者用户ID'))
        print("  ✅ 添加 owner_id 字段")
    except Exception as e:
        print(f"  ⚠️ owner_id 字段: {e}")
    
    try:
        op.add_column('conversations', sa.Column('is_archived', sa.Boolean(), nullable=True, comment='是否已归档'))
        print("  ✅ 添加 is_archived 字段")
    except Exception as e:
        print(f"  ⚠️ is_archived 字段: {e}")
    
    try:
        op.add_column('conversations', sa.Column('message_count', sa.Integer(), nullable=True, comment='消息总数'))
        print("  ✅ 添加 message_count 字段")
    except Exception as e:
        print(f"  ⚠️ message_count 字段: {e}")
    
    try:
        op.add_column('conversations', sa.Column('unread_count', sa.Integer(), nullable=True, comment='未读消息数'))
        print("  ✅ 添加 unread_count 字段")
    except Exception as e:
        print(f"  ⚠️ unread_count 字段: {e}")
    
    try:
        op.add_column('conversations', sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True, comment='最后消息时间'))
        print("  ✅ 添加 last_message_at 字段")
    except Exception as e:
        print(f"  ⚠️ last_message_at 字段: {e}")
    
    # 2. 为messages表添加字段
    print("为 messages 表添加字段...")
    
    try:
        op.add_column('messages', sa.Column('sender_digital_human_id', sa.String(36), nullable=True, comment='发送者数字人ID'))
        print("  ✅ 添加 sender_digital_human_id 字段")
    except Exception as e:
        print(f"  ⚠️ sender_digital_human_id 字段: {e}")
    
    try:
        op.add_column('messages', sa.Column('requires_confirmation', sa.Boolean(), nullable=True, comment='是否需要确认'))
        print("  ✅ 添加 requires_confirmation 字段")
    except Exception as e:
        print(f"  ⚠️ requires_confirmation 字段: {e}")
    
    try:
        op.add_column('messages', sa.Column('is_confirmed', sa.Boolean(), nullable=True, comment='是否已确认'))
        print("  ✅ 添加 is_confirmed 字段")
    except Exception as e:
        print(f"  ⚠️ is_confirmed 字段: {e}")
    
    try:
        op.add_column('messages', sa.Column('confirmed_by', sa.String(36), nullable=True, comment='确认人ID'))
        print("  ✅ 添加 confirmed_by 字段")
    except Exception as e:
        print(f"  ⚠️ confirmed_by 字段: {e}")
    
    try:
        op.add_column('messages', sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True, comment='确认时间'))
        print("  ✅ 添加 confirmed_at 字段")
    except Exception as e:
        print(f"  ⚠️ confirmed_at 字段: {e}")
    
    # 3. 修改upload_sessions表
    print("修改 upload_sessions 表...")
    
    # 先添加新字段
    try:
        op.add_column('upload_sessions', sa.Column('content_type', sa.String(100), nullable=True, comment='文件MIME类型'))
        print("  ✅ 添加 content_type 字段")
    except Exception as e:
        print(f"  ⚠️ content_type 字段: {e}")
    
    try:
        op.add_column('upload_sessions', sa.Column('file_extension', sa.String(10), nullable=True, comment='文件扩展名'))
        print("  ✅ 添加 file_extension 字段")
    except Exception as e:
        print(f"  ⚠️ file_extension 字段: {e}")
    
    try:
        op.add_column('upload_sessions', sa.Column('business_type', sa.String(50), nullable=True, comment='业务类型'))
        print("  ✅ 添加 business_type 字段")
    except Exception as e:
        print(f"  ⚠️ business_type 字段: {e}")
    
    try:
        op.add_column('upload_sessions', sa.Column('business_id', sa.String(36), nullable=True, comment='关联的业务对象ID'))
        print("  ✅ 添加 business_id 字段")
    except Exception as e:
        print(f"  ⚠️ business_id 字段: {e}")
    
    try:
        op.add_column('upload_sessions', sa.Column('is_public', sa.Boolean(), nullable=True, comment='是否公开访问'))
        print("  ✅ 添加 is_public 字段")
    except Exception as e:
        print(f"  ⚠️ is_public 字段: {e}")
    
    try:
        op.add_column('upload_sessions', sa.Column('access_token', sa.String(64), nullable=True, comment='访问令牌'))
        print("  ✅ 添加 access_token 字段")
    except Exception as e:
        print(f"  ⚠️ access_token 字段: {e}")
    
    try:
        op.add_column('upload_sessions', sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间'))
        print("  ✅ 添加 expires_at 字段")
    except Exception as e:
        print(f"  ⚠️ expires_at 字段: {e}")
    
    print("\\n🎉 步骤1完成！")


def downgrade():
    print("回滚步骤1...")
    
    # 删除upload_sessions新字段
    try:
        op.drop_column('upload_sessions', 'expires_at')
        op.drop_column('upload_sessions', 'access_token')
        op.drop_column('upload_sessions', 'is_public')
        op.drop_column('upload_sessions', 'business_id')
        op.drop_column('upload_sessions', 'business_type')
        op.drop_column('upload_sessions', 'file_extension')
        op.drop_column('upload_sessions', 'content_type')
    except:
        pass
    
    # 删除messages新字段
    try:
        op.drop_column('messages', 'confirmed_at')
        op.drop_column('messages', 'confirmed_by')
        op.drop_column('messages', 'is_confirmed')
        op.drop_column('messages', 'requires_confirmation')
        op.drop_column('messages', 'sender_digital_human_id')
    except:
        pass
    
    # 删除conversations新字段
    try:
        op.drop_column('conversations', 'last_message_at')
        op.drop_column('conversations', 'unread_count')
        op.drop_column('conversations', 'message_count')
        op.drop_column('conversations', 'is_archived')
        op.drop_column('conversations', 'owner_id')
        op.drop_column('conversations', 'conv_type')
    except:
        pass
