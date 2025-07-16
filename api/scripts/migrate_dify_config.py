#!/usr/bin/env python3
"""
将Dify环境变量配置迁移到数据库的脚本
运行此脚本后，系统将使用数据库中的配置而不是环境变量
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.base import get_db
from app.db.models.system import DifyConfig
from app.core.config import get_settings

def migrate_env_to_db():
    """将环境变量配置迁移到数据库"""
    
    print("🔄 开始迁移Dify配置...")
    
    # 获取数据库连接
    db = next(get_db())
    settings = get_settings()
    
    try:
        # 检查是否已有配置
        existing_config = db.query(DifyConfig).first()
        if existing_config:
            print("⚠️  数据库中已存在Dify配置，跳过迁移")
            print(f"   现有配置: {existing_config.config_name}")
            return
        
        # 获取环境变量配置
        base_url = settings.DIFY_API_BASE_URL
        chat_api_key = settings.DIFY_CHAT_API_KEY
        beauty_api_key = settings.DIFY_BEAUTY_API_KEY
        summary_api_key = settings.DIFY_SUMMARY_API_KEY
        
        # 检查是否有有效的配置
        if not any([chat_api_key, beauty_api_key, summary_api_key]):
            print("❌ 环境变量中没有找到有效的Dify API Key")
            print("   请先配置以下环境变量：")
            print("   - DIFY_CHAT_API_KEY")
            print("   - DIFY_BEAUTY_API_KEY") 
            print("   - DIFY_SUMMARY_API_KEY")
            return
        
        # 创建数据库配置
        new_config = DifyConfig(
            config_name="默认Dify配置",
            base_url=base_url,
            description="从环境变量迁移的配置",
            enabled=True,
            timeout_seconds=30,
            max_retries=3
        )
        
        # 设置应用配置
        if chat_api_key:
            new_config.chat_app_id = "dify-chat-app"
            new_config.chat_api_key = chat_api_key
            print(f"✅ 迁移聊天应用配置")
        
        if beauty_api_key:
            new_config.beauty_app_id = "dify-beauty-agent"
            new_config.beauty_api_key = beauty_api_key
            print(f"✅ 迁移医美方案专家配置")
        
        if summary_api_key:
            new_config.summary_app_id = "dify-summary-workflow"
            new_config.summary_api_key = summary_api_key
            print(f"✅ 迁移咨询总结工作流配置")
        
        # 保存到数据库
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        
        print(f"🎉 配置迁移成功！")
        print(f"   配置ID: {new_config.id}")
        print(f"   配置名称: {new_config.config_name}")
        print(f"   基础URL: {new_config.base_url}")
        print(f"   状态: {'启用' if new_config.enabled else '禁用'}")
        
        # 重载AI Gateway配置
        try:
            from app.services.dify_config_service import reload_ai_gateway_with_new_config
            reload_ai_gateway_with_new_config()
            print("🔄 AI Gateway配置已重载")
        except Exception as e:
            print(f"⚠️  AI Gateway重载失败: {e}")
            print("   请重启服务以应用新配置")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_config():
    """创建示例配置"""
    
    print("🔄 创建示例Dify配置...")
    
    db = next(get_db())
    
    try:
        # 检查是否已有配置
        existing_config = db.query(DifyConfig).first()
        if existing_config:
            print("⚠️  数据库中已存在Dify配置，跳过创建")
            return
        
        # 创建示例配置
        sample_config = DifyConfig(
            config_name="示例Dify配置",
            base_url="http://localhost/v1",
            description="这是一个示例配置，请在管理界面中修改为实际的API Key",
            chat_app_id="dify-chat-app",
            beauty_app_id="dify-beauty-agent",
            summary_app_id="dify-summary-workflow",
            enabled=False,  # 默认禁用
            timeout_seconds=30,
            max_retries=3
        )
        
        # 注意：不设置API Key，需要用户在界面中配置
        
        db.add(sample_config)
        db.commit()
        db.refresh(sample_config)
        
        print(f"✅ 示例配置创建成功！")
        print(f"   配置ID: {sample_config.id}")
        print(f"   状态: 禁用（请在管理界面中配置API Key并启用）")
        print(f"   访问: http://localhost:3000/admin/settings 进行配置")
        
    except Exception as e:
        print(f"❌ 创建示例配置失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Dify配置迁移脚本")
    parser.add_argument("--sample", action="store_true", help="创建示例配置而不是迁移")
    
    args = parser.parse_args()
    
    if args.sample:
        create_sample_config()
    else:
        migrate_env_to_db()
    
    print("\n📝 后续步骤：")
    print("1. 访问 http://localhost:3000/admin/settings 管理Dify配置")
    print("2. 配置完成后，AI辅助方案生成功能将使用真实的Dify服务")
    print("3. 无需重启服务，配置更改立即生效") 