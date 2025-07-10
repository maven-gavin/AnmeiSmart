"""优化数据库模型_添加枚举类型_索引_约束_统一命名

Revision ID: 47c29cbf8818
Revises: 10be17e34d15
Create Date: 2025-07-10 16:07:19.580874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47c29cbf8818'
down_revision: Union[str, None] = '10be17e34d15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### 数据迁移优化 - 正确处理字段重命名 ###
    
    # 1. AIModelConfig 表字段迁移
    # 先添加新字段为可空
    op.add_column('ai_model_configs', sa.Column('model_name', sa.String(length=255), nullable=True, comment='模型名称'))
    op.add_column('ai_model_configs', sa.Column('api_key', sa.Text(), nullable=True, comment='API密钥（非Dify时必填）'))
    op.add_column('ai_model_configs', sa.Column('base_url', sa.String(length=1024), nullable=True, comment='API基础URL（非Dify时必填）'))
    op.add_column('ai_model_configs', sa.Column('max_tokens', sa.Integer(), nullable=True, comment='最大Token数'))
    
    # 数据迁移：复制旧字段值到新字段
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE ai_model_configs 
        SET 
            model_name = "modelName",
            api_key = "apiKey", 
            base_url = "baseUrl",
            max_tokens = CASE 
                WHEN "maxTokens" ~ '^[0-9]+$' THEN CAST("maxTokens" AS INTEGER)
                ELSE 2000 
            END
        WHERE model_name IS NULL
    """))
    
    # 填充boolean字段的默认值
    connection.execute(sa.text("""
        UPDATE ai_model_configs 
        SET 
            enabled = COALESCE(enabled, true),
            is_default_for_type = COALESCE(is_default_for_type, false)
    """))
    
    # 设置新字段为非空
    op.alter_column('ai_model_configs', 'model_name', nullable=False)
    
    # 设置其他字段约束
    op.alter_column('ai_model_configs', 'enabled',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_comment='是否启用')
    op.alter_column('ai_model_configs', 'is_default_for_type',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_comment='是否为该类型的默认模型')
    
    # 添加索引和约束
    op.create_index('idx_ai_model_agent_type_default', 'ai_model_configs', ['agent_type', 'is_default_for_type'], unique=False)
    op.create_index('idx_ai_model_dify_connection', 'ai_model_configs', ['dify_connection_id'], unique=False)
    op.create_index('idx_ai_model_provider_enabled', 'ai_model_configs', ['provider', 'enabled'], unique=False)
    op.create_unique_constraint('uq_default_agent_per_type', 'ai_model_configs', ['agent_type', 'is_default_for_type'])
    
    # 删除外键和旧字段
    op.drop_constraint('ai_model_configs_system_settings_id_fkey', 'ai_model_configs', type_='foreignkey')
    op.drop_column('ai_model_configs', 'appId')
    op.drop_column('ai_model_configs', 'baseUrl')
    op.drop_column('ai_model_configs', 'apiKey')
    op.drop_column('ai_model_configs', 'maxTokens')
    op.drop_column('ai_model_configs', 'modelName')
    op.drop_column('ai_model_configs', 'system_settings_id')
    
    # 2. DifyConnection 表优化
    # 填充boolean字段的默认值
    connection.execute(sa.text("""
        UPDATE dify_connections 
        SET 
            is_active = COALESCE(is_active, true),
            is_default = COALESCE(is_default, false)
    """))
    
    op.alter_column('dify_connections', 'api_key',
               existing_type=sa.TEXT(),
               comment='Dify API密钥（应加密存储）',
               existing_comment='Dify API密钥',
               existing_nullable=False)
    op.alter_column('dify_connections', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_comment='是否为活跃连接')
    op.alter_column('dify_connections', 'is_default',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_comment='是否为默认连接')
    
    # 更新sync_status字段为枚举类型
    # 先创建枚举类型
    op.execute("CREATE TYPE syncstatus AS ENUM ('NOT_SYNCED', 'SYNCING', 'SUCCESS', 'FAILED')")
    
    # 更新现有数据到新的枚举值
    connection.execute(sa.text("""
        UPDATE dify_connections 
        SET sync_status = CASE 
            WHEN sync_status = '未同步' THEN 'NOT_SYNCED'
            WHEN sync_status LIKE '成功同步%' THEN 'SUCCESS'
            WHEN sync_status LIKE '同步失败%' THEN 'FAILED'
            ELSE 'NOT_SYNCED'
        END
    """))
    
    # 修改字段类型为枚举 - 使用USING转换
    op.execute("""
        ALTER TABLE dify_connections 
        ALTER COLUMN sync_status TYPE syncstatus 
        USING sync_status::syncstatus
    """)
    
    # 设置字段为非空
    op.alter_column('dify_connections', 'sync_status', nullable=False)
    
    # 添加索引和约束
    op.create_index('idx_dify_connections_active_default', 'dify_connections', ['is_active', 'is_default'], unique=False)
    op.create_index('idx_dify_connections_sync_status', 'dify_connections', ['sync_status'], unique=False)
    op.create_unique_constraint('uq_default_connection', 'dify_connections', ['is_default'])
    
    # 3. SystemSettings 表字段迁移
    # 先添加新字段
    op.add_column('system_settings', sa.Column('site_name', sa.String(length=255), nullable=True, comment='站点名称'))
    op.add_column('system_settings', sa.Column('logo_url', sa.String(length=1024), nullable=True, comment='站点Logo URL'))
    op.add_column('system_settings', sa.Column('default_model_id', sa.String(length=255), nullable=True, comment='默认AI模型ID'))
    op.add_column('system_settings', sa.Column('maintenance_mode', sa.Boolean(), nullable=True, comment='维护模式开关'))
    op.add_column('system_settings', sa.Column('user_registration_enabled', sa.Boolean(), nullable=True, comment='是否允许用户注册'))
    
    # 数据迁移
    connection.execute(sa.text("""
        UPDATE system_settings 
        SET 
            site_name = "siteName",
            logo_url = "logoUrl",
            default_model_id = "defaultModelId",
            maintenance_mode = COALESCE("maintenanceMode", false),
            user_registration_enabled = COALESCE("userRegistrationEnabled", true)
        WHERE site_name IS NULL
    """))
    
    # 设置非空约束
    op.alter_column('system_settings', 'site_name', nullable=False)
    op.alter_column('system_settings', 'maintenance_mode', nullable=False)
    op.alter_column('system_settings', 'user_registration_enabled', nullable=False)
    
    # 删除旧字段
    op.drop_column('system_settings', 'userRegistrationEnabled')
    op.drop_column('system_settings', 'maintenanceMode')
    op.drop_column('system_settings', 'logoUrl')
    op.drop_column('system_settings', 'defaultModelId')
    op.drop_column('system_settings', 'siteName')


def downgrade() -> None:
    # ### 回滚逻辑 ###
    
    # 1. 恢复 SystemSettings 旧字段
    op.add_column('system_settings', sa.Column('siteName', sa.VARCHAR(length=255), autoincrement=False, nullable=False, comment='站点名称'))
    op.add_column('system_settings', sa.Column('defaultModelId', sa.VARCHAR(length=255), autoincrement=False, nullable=True, comment='默认AI模型ID'))
    op.add_column('system_settings', sa.Column('logoUrl', sa.VARCHAR(length=1024), autoincrement=False, nullable=True, comment='站点Logo URL'))
    op.add_column('system_settings', sa.Column('maintenanceMode', sa.BOOLEAN(), autoincrement=False, nullable=True, comment='维护模式开关'))
    op.add_column('system_settings', sa.Column('userRegistrationEnabled', sa.BOOLEAN(), autoincrement=False, nullable=True, comment='是否允许用户注册'))
    
    # 数据回滚
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE system_settings 
        SET 
            "siteName" = site_name,
            "logoUrl" = logo_url,
            "defaultModelId" = default_model_id,
            "maintenanceMode" = maintenance_mode,
            "userRegistrationEnabled" = user_registration_enabled
    """))
    
    op.drop_column('system_settings', 'user_registration_enabled')
    op.drop_column('system_settings', 'maintenance_mode')
    op.drop_column('system_settings', 'default_model_id')
    op.drop_column('system_settings', 'logo_url')
    op.drop_column('system_settings', 'site_name')
    
    # 2. 恢复 DifyConnection
    op.drop_constraint('uq_default_connection', 'dify_connections', type_='unique')
    op.drop_index('idx_dify_connections_sync_status', table_name='dify_connections')
    op.drop_index('idx_dify_connections_active_default', table_name='dify_connections')
    
    # 先将枚举值转回字符串
    connection.execute(sa.text("""
        UPDATE dify_connections 
        SET sync_status = CASE 
            WHEN sync_status = 'NOT_SYNCED' THEN '未同步'
            WHEN sync_status = 'SUCCESS' THEN '同步成功'
            WHEN sync_status = 'FAILED' THEN '同步失败'
            ELSE '未同步'
        END::text
    """))
    
    op.alter_column('dify_connections', 'sync_status',
               existing_type=sa.Enum('NOT_SYNCED', 'SYNCING', 'SUCCESS', 'FAILED', name='syncstatus'),
               type_=sa.VARCHAR(length=50),
               nullable=True,
               existing_comment='同步状态')
    
    # 删除枚举类型
    op.execute("DROP TYPE syncstatus")
    
    op.alter_column('dify_connections', 'is_default',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_comment='是否为默认连接')
    op.alter_column('dify_connections', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_comment='是否为活跃连接')
    op.alter_column('dify_connections', 'api_key',
               existing_type=sa.TEXT(),
               comment='Dify API密钥',
               existing_comment='Dify API密钥（应加密存储）',
               existing_nullable=False)
    
    # 3. 恢复 AIModelConfig
    op.add_column('ai_model_configs', sa.Column('system_settings_id', sa.VARCHAR(length=36), autoincrement=False, nullable=True, comment='系统设置ID'))
    op.add_column('ai_model_configs', sa.Column('modelName', sa.VARCHAR(length=255), autoincrement=False, nullable=False, comment='模型名称'))
    op.add_column('ai_model_configs', sa.Column('maxTokens', sa.VARCHAR(), autoincrement=False, nullable=True, comment='最大Token数'))
    op.add_column('ai_model_configs', sa.Column('apiKey', sa.TEXT(), autoincrement=False, nullable=True, comment='API密钥（非Dify时必填）'))
    op.add_column('ai_model_configs', sa.Column('baseUrl', sa.VARCHAR(length=1024), autoincrement=False, nullable=True, comment='API基础URL（非Dify时必填）'))
    op.add_column('ai_model_configs', sa.Column('appId', sa.VARCHAR(length=255), autoincrement=False, nullable=True, comment='应用ID（已废弃，使用dify_app_id）'))
    
    # 数据回滚
    connection.execute(sa.text("""
        UPDATE ai_model_configs 
        SET 
            "modelName" = model_name,
            "apiKey" = api_key,
            "baseUrl" = base_url,
            "maxTokens" = max_tokens::text
    """))
    
    op.create_foreign_key('ai_model_configs_system_settings_id_fkey', 'ai_model_configs', 'system_settings', ['system_settings_id'], ['id'])
    op.drop_constraint('uq_default_agent_per_type', 'ai_model_configs', type_='unique')
    op.drop_index('idx_ai_model_provider_enabled', table_name='ai_model_configs')
    op.drop_index('idx_ai_model_dify_connection', table_name='ai_model_configs')
    op.drop_index('idx_ai_model_agent_type_default', table_name='ai_model_configs')
    op.alter_column('ai_model_configs', 'is_default_for_type',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_comment='是否为该类型的默认模型')
    op.alter_column('ai_model_configs', 'enabled',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_comment='是否启用')
    op.drop_column('ai_model_configs', 'max_tokens')
    op.drop_column('ai_model_configs', 'base_url')
    op.drop_column('ai_model_configs', 'api_key')
    op.drop_column('ai_model_configs', 'model_name')
