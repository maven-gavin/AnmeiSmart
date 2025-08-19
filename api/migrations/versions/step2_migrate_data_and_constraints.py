"""步骤2: 迁移数据并设置约束

Revision ID: step2_data_fix
Revises: step1_add_nullable_fields
Create Date: 2024-12-19 12:02:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'step2_data_fix'
down_revision = 'step1_add_nullable_fields'
branch_labels = None
depends_on = None


def upgrade():
    print("步骤2: 迁移数据并设置约束...")
    
    # 1. 迁移conversations表数据
    print("迁移 conversations 表数据...")
    
    try:
        # 设置默认会话类型
        op.execute("UPDATE conversations SET conv_type = 'single' WHERE conv_type IS NULL")
        print("  ✅ 设置默认会话类型")
        
        # 将customer_id设置为owner_id
        op.execute("UPDATE conversations SET owner_id = customer_id WHERE customer_id IS NOT NULL AND owner_id IS NULL")
        print("  ✅ 迁移owner_id数据")
        
        # 设置默认归档状态
        op.execute("UPDATE conversations SET is_archived = false WHERE is_archived IS NULL")
        print("  ✅ 设置默认归档状态")
        
        # 设置默认计数
        op.execute("UPDATE conversations SET message_count = 0 WHERE message_count IS NULL")
        op.execute("UPDATE conversations SET unread_count = 0 WHERE unread_count IS NULL")
        print("  ✅ 设置默认计数值")
        
    except Exception as e:
        print(f"  ❌ 数据迁移失败: {e}")
    
    # 2. 迁移messages表数据
    print("迁移 messages 表数据...")
    
    try:
        # 设置默认确认状态
        op.execute("UPDATE messages SET requires_confirmation = false WHERE requires_confirmation IS NULL")
        op.execute("UPDATE messages SET is_confirmed = true WHERE is_confirmed IS NULL")
        print("  ✅ 设置默认确认状态")
        
    except Exception as e:
        print(f"  ❌ messages数据迁移失败: {e}")
    
    # 3. 迁移upload_sessions表数据
    print("迁移 upload_sessions 表数据...")
    
    try:
        # 设置默认公开状态
        op.execute("UPDATE upload_sessions SET is_public = false WHERE is_public IS NULL")
        print("  ✅ 设置默认公开状态")
        
        # 设置默认业务类型
        op.execute("UPDATE upload_sessions SET business_type = 'message' WHERE business_type IS NULL")
        print("  ✅ 设置默认业务类型")
        
    except Exception as e:
        print(f"  ❌ upload_sessions数据迁移失败: {e}")
    
    # 4. 现在设置NOT NULL约束
    print("设置NOT NULL约束...")
    
    try:
        # conversations表约束
        op.alter_column('conversations', 'conv_type', nullable=False)
        op.alter_column('conversations', 'is_archived', nullable=False)
        op.alter_column('conversations', 'message_count', nullable=False)
        op.alter_column('conversations', 'unread_count', nullable=False)
        print("  ✅ 设置 conversations 表约束")
    except Exception as e:
        print(f"  ⚠️ conversations约束设置失败: {e}")
    
    try:
        # messages表约束
        op.alter_column('messages', 'requires_confirmation', nullable=False)
        op.alter_column('messages', 'is_confirmed', nullable=False)
        print("  ✅ 设置 messages 表约束")
    except Exception as e:
        print(f"  ⚠️ messages约束设置失败: {e}")
    
    try:
        # upload_sessions表约束
        op.alter_column('upload_sessions', 'is_public', nullable=False)
        print("  ✅ 设置 upload_sessions 表约束")
    except Exception as e:
        print(f"  ⚠️ upload_sessions约束设置失败: {e}")
    
    # 5. 创建索引
    print("创建索引...")
    
    try:
        op.create_index('idx_conversations_owner', 'conversations', ['owner_id'])
        print("  ✅ 创建 conversations.owner_id 索引")
    except Exception as e:
        print(f"  ⚠️ 索引创建失败: {e}")
    
    try:
        op.create_index('idx_conversations_type', 'conversations', ['conv_type'])
        print("  ✅ 创建 conversations.conv_type 索引")
    except Exception as e:
        print(f"  ⚠️ 索引创建失败: {e}")
    
    try:
        op.create_index('idx_messages_sender_dh', 'messages', ['sender_digital_human_id'])
        print("  ✅ 创建 messages.sender_digital_human_id 索引")
    except Exception as e:
        print(f"  ⚠️ 索引创建失败: {e}")
    
    # 6. 创建外键约束
    print("创建外键约束...")
    
    try:
        op.create_foreign_key('fk_conversations_owner', 'conversations', 'users', ['owner_id'], ['id'])
        print("  ✅ 创建 conversations.owner_id 外键")
    except Exception as e:
        print(f"  ⚠️ 外键创建失败: {e}")
    
    try:
        op.create_foreign_key('fk_messages_sender_dh', 'messages', 'digital_humans', ['sender_digital_human_id'], ['id'])
        print("  ✅ 创建 messages.sender_digital_human_id 外键")
    except Exception as e:
        print(f"  ⚠️ 外键创建失败: {e}")
    
    try:
        op.create_foreign_key('fk_messages_confirmed_by', 'messages', 'users', ['confirmed_by'], ['id'])
        print("  ✅ 创建 messages.confirmed_by 外键")
    except Exception as e:
        print(f"  ⚠️ 外键创建失败: {e}")
    
    print("\\n🎉 步骤2完成！")


def downgrade():
    print("回滚步骤2...")
    
    # 删除外键约束
    try:
        op.drop_constraint('fk_messages_confirmed_by', 'messages', type_='foreignkey')
        op.drop_constraint('fk_messages_sender_dh', 'messages', type_='foreignkey')
        op.drop_constraint('fk_conversations_owner', 'conversations', type_='foreignkey')
    except:
        pass
    
    # 删除索引
    try:
        op.drop_index('idx_messages_sender_dh', 'messages')
        op.drop_index('idx_conversations_type', 'conversations')
        op.drop_index('idx_conversations_owner', 'conversations')
    except:
        pass
    
    print("回滚完成")
