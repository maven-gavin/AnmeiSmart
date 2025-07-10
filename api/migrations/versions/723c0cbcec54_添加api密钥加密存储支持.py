"""添加API密钥加密存储支持

Revision ID: 723c0cbcec54
Revises: 47c29cbf8818
Create Date: 2025-07-10 16:24:42.260930

"""
from typing import Sequence, Union
import sys
import os
from pathlib import Path

from alembic import op
import sqlalchemy as sa

# 添加项目路径到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# revision identifiers, used by Alembic.
revision: str = '723c0cbcec54'
down_revision: Union[str, None] = '47c29cbf8818'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def encrypt_existing_api_keys():
    """加密现有的API密钥"""
    try:
        # 导入加密工具
        from app.core.encryption import get_encryption
        
        encryption = get_encryption()
        connection = op.get_bind()
        
        # 1. 加密 DifyConnection 表中的API密钥
        result = connection.execute(sa.text("""
            SELECT id, api_key FROM dify_connections 
            WHERE api_key IS NOT NULL AND api_key != ''
        """))
        
        dify_rows = result.fetchall()
        for row in dify_rows:
            connection_id, api_key = row
            
            # 检查是否已加密
            if not encryption.is_encrypted(api_key):
                encrypted_key = encryption.encrypt(api_key)
                connection.execute(sa.text("""
                    UPDATE dify_connections 
                    SET api_key = :encrypted_key 
                    WHERE id = :connection_id
                """), {"encrypted_key": encrypted_key, "connection_id": connection_id})
                print(f"已加密 DifyConnection {connection_id} 的API密钥")
        
        # 2. 加密 AIModelConfig 表中的API密钥
        result = connection.execute(sa.text("""
            SELECT id, api_key FROM ai_model_configs 
            WHERE api_key IS NOT NULL AND api_key != ''
        """))
        
        model_rows = result.fetchall()
        for row in model_rows:
            model_id, api_key = row
            
            # 检查是否已加密
            if not encryption.is_encrypted(api_key):
                encrypted_key = encryption.encrypt(api_key)
                connection.execute(sa.text("""
                    UPDATE ai_model_configs 
                    SET api_key = :encrypted_key 
                    WHERE id = :model_id
                """), {"encrypted_key": encrypted_key, "model_id": model_id})
                print(f"已加密 AIModelConfig {model_id} 的API密钥")
        
        print(f"API密钥加密完成：DifyConnection {len(dify_rows)} 条，AIModelConfig {len(model_rows)} 条")
        
    except Exception as e:
        print(f"加密API密钥时出错: {e}")
        # 不抛出异常，允许迁移继续（但会记录警告）
        print("警告：API密钥加密失败，请手动检查并加密")


def decrypt_existing_api_keys():
    """解密现有的API密钥（回滚时使用）"""
    try:
        # 导入加密工具
        from app.core.encryption import get_encryption
        
        encryption = get_encryption()
        connection = op.get_bind()
        
        # 1. 解密 DifyConnection 表中的API密钥
        result = connection.execute(sa.text("""
            SELECT id, api_key FROM dify_connections 
            WHERE api_key IS NOT NULL AND api_key != ''
        """))
        
        dify_rows = result.fetchall()
        for row in dify_rows:
            connection_id, api_key = row
            
            # 检查是否已加密
            if encryption.is_encrypted(api_key):
                decrypted_key = encryption.decrypt(api_key)
                connection.execute(sa.text("""
                    UPDATE dify_connections 
                    SET api_key = :decrypted_key 
                    WHERE id = :connection_id
                """), {"decrypted_key": decrypted_key, "connection_id": connection_id})
                print(f"已解密 DifyConnection {connection_id} 的API密钥")
        
        # 2. 解密 AIModelConfig 表中的API密钥
        result = connection.execute(sa.text("""
            SELECT id, api_key FROM ai_model_configs 
            WHERE api_key IS NOT NULL AND api_key != ''
        """))
        
        model_rows = result.fetchall()
        for row in model_rows:
            model_id, api_key = row
            
            # 检查是否已加密
            if encryption.is_encrypted(api_key):
                decrypted_key = encryption.decrypt(api_key)
                connection.execute(sa.text("""
                    UPDATE ai_model_configs 
                    SET api_key = :decrypted_key 
                    WHERE id = :model_id
                """), {"decrypted_key": decrypted_key, "model_id": model_id})
                print(f"已解密 AIModelConfig {model_id} 的API密钥")
        
        print(f"API密钥解密完成：DifyConnection {len(dify_rows)} 条，AIModelConfig {len(model_rows)} 条")
        
    except Exception as e:
        print(f"解密API密钥时出错: {e}")
        print("警告：API密钥解密失败，请手动检查")


def upgrade() -> None:
    # 1. 首先加密现有的API密钥
    print("开始加密现有API密钥...")
    encrypt_existing_api_keys()
    
    # 2. 更新表注释
    op.alter_column('ai_model_configs', 'api_key',
               existing_type=sa.TEXT(),
               comment='API密钥（非Dify时必填，加密存储）',
               existing_comment='API密钥（非Dify时必填）',
               existing_nullable=True)
    op.alter_column('dify_connections', 'api_key',
               existing_type=sa.TEXT(),
               comment='Dify API密钥（加密存储）',
               existing_comment='Dify API密钥（应加密存储）',
               existing_nullable=False)
    
    print("API密钥加密存储支持已添加")


def downgrade() -> None:
    # 1. 先解密现有的API密钥
    print("开始解密现有API密钥...")
    decrypt_existing_api_keys()
    
    # 2. 恢复表注释
    op.alter_column('dify_connections', 'api_key',
               existing_type=sa.TEXT(),
               comment='Dify API密钥（应加密存储）',
               existing_comment='Dify API密钥（加密存储）',
               existing_nullable=False)
    op.alter_column('ai_model_configs', 'api_key',
               existing_type=sa.TEXT(),
               comment='API密钥（非Dify时必填）',
               existing_comment='API密钥（非Dify时必填，加密存储）',
               existing_nullable=True)
    
    print("API密钥加密存储支持已移除")
