#!/usr/bin/env python
"""
安美智享智能医美服务系统 - 数据库初始化脚本
用于初始化数据库表结构和基本系统数据
"""

import os
import sys
import logging
import argparse
from sqlalchemy.sql import text

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """初始化数据库表结构"""
    try:
        # 导入所有模型以确保它们被包含在Base.metadata中
        from app.common.infrastructure.db.base_model import BaseModel
        from app.identity_access.infrastructure.db.user import User, Role
        from app.customer.infrastructure.db.customer import Customer, CustomerProfile
        from app.chat.infrastructure.db.chat import Conversation, Message
        from app.system.infrastructure.db.system import SystemSettings, AIModelConfig
        
        # 导入和使用Base以创建所有表
        from app.db.base import Base, engine
        Base.metadata.create_all(bind=engine)
        logger.info("成功创建数据库表")
    except Exception as e:
        logger.error(f"创建数据库表时出错: {e}")
        raise

def create_initial_roles():
    """创建初始角色"""
    try:
        # 导入角色相关模块
        from app.db.base import SessionLocal
        from app.identity_access.infrastructure.db.user import Role
        from app.db.uuid_utils import role_id
        
        # 创建数据库会话
        db = SessionLocal()
        try:
            # 检查角色是否存在
            existing_roles = db.query(Role).all()
            if existing_roles:
                logger.info(f"已存在 {len(existing_roles)} 个角色，跳过创建初始角色")
                return
            
            # 定义基础角色
            roles = [
                Role(id=role_id(), name="customer", description="客户"),
                Role(id=role_id(), name="doctor", description="医生"),
                Role(id=role_id(), name="consultant", description="顾问"),
                Role(id=role_id(), name="operator", description="管理员"),
                Role(id=role_id(), name="administrator", description="系统管理员")
            ]
            
            # 添加角色到数据库
            db.add_all(roles)
            db.commit()
            logger.info(f"成功创建 {len(roles)} 个初始角色")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"创建初始角色时出错: {e}")
        raise

def create_initial_system_settings():
    """创建系统初始设置"""
    try:
        # 导入系统设置相关模块
        from app.db.base import SessionLocal
        from app.system.infrastructure.db.system import SystemSettings, AIModelConfig
        from app.db.uuid_utils import system_id, model_id

        # 创建数据库会话
        db = SessionLocal()
        try:
            # 检查系统设置是否已存在
            existing_settings = db.query(SystemSettings).first()
            if existing_settings:
                logger.info(f"系统设置已存在，跳过创建初始设置")
                return
            
            # 创建系统设置
            settings_id = system_id()
            system_settings = SystemSettings(
                id=settings_id,
                siteName="安美智能咨询系统",
                logoUrl="/logo.png",
                defaultModelId="GPT-4",
                maintenanceMode=False,
                userRegistrationEnabled=True
            )
            db.add(system_settings)
            db.commit()
            db.refresh(system_settings)
            
            # 创建AI模型配置
            default_model = AIModelConfig(
                id=model_id(),
                modelName="GPT-4",
                apiKey="sk-••••••••••••••••••••••••",  # 实际部署时应使用环境变量
                baseUrl="https://api.openai.com/v1",
                maxTokens="2000",
                temperature=0.7,
                enabled=True,
                provider="openai",
                system_settings_id=settings_id
            )
            db.add(default_model)
            db.commit()
            
            logger.info("成功创建系统设置")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"创建系统设置时出错: {e}")
        raise

def initialize_database(drop_all=False):
    """初始化数据库
    
    Args:
        drop_all: 是否删除所有表后重新创建
    """
    try:
        logger.info("开始初始化数据库")
        
        # 调用init_db函数
        from app.db.base import engine, Base, SessionLocal
        
        if drop_all:
            logger.info("删除所有现有表")
            # 使用 CASCADE 选项删除所有表
            with engine.connect() as connection:
                # 关闭外键约束检查
                connection.execute(text("SET session_replication_role = 'replica';"))
                
                # 使用原始 SQL 批量删除所有表，忽略依赖关系
                # 这会自动处理依赖关系问题
                connection.execute(text("DROP SCHEMA public CASCADE;"))
                connection.execute(text("CREATE SCHEMA public;"))
                
                # 恢复默认权限
                connection.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
                connection.execute(text("GRANT ALL ON SCHEMA public TO public;"))
                
                # 删除alembic版本表，强制重新开始迁移
                try:
                    connection.execute(text("DROP TABLE IF EXISTS alembic_version;"))
                except Exception:
                    pass  # 忽略错误，可能表不存在
                
                # 恢复外键约束检查
                connection.execute(text("SET session_replication_role = 'origin';"))
                
                # 提交事务
                connection.commit()
        
        # 创建表
        logger.info("创建数据库表")
        init_db()
        
        # 创建初始角色
        logger.info("创建初始角色")
        create_initial_roles()
        
        # 创建系统设置
        logger.info("创建系统设置")
        create_initial_system_settings()
        
        logger.info("数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"初始化数据库时出错: {e}")
        return False

def apply_migrations():
    """应用数据库迁移"""
    try:
        logger.info("开始应用数据库迁移")
        
        # 导入并运行迁移脚本
        migration_script = os.path.join(os.path.dirname(__file__), "migration.py")
        
        # 构建命令并执行
        import subprocess
        result = subprocess.run(
            [sys.executable, migration_script, "upgrade"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("数据库迁移成功应用")
            return True
        else:
            logger.error(f"应用数据库迁移时出错: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"运行数据库迁移时出错: {e}")
        return False

def main():
    """脚本入口函数"""
    parser = argparse.ArgumentParser(description="数据库初始化工具")
    parser.add_argument("--drop-all", action="store_true", help="删除所有表后重新创建")
    parser.add_argument("--migrate-only", action="store_true", help="仅执行迁移，不初始化数据")
    parser.add_argument("--no-migrations", action="store_true", help="不使用迁移系统")
    args = parser.parse_args()
    
    # 如果只执行迁移
    if args.migrate_only:
        success = apply_migrations()
        sys.exit(0 if success else 1)
    
    # 执行完整初始化
    success = initialize_database(args.drop_all)
    
    # 如果初始化成功且不禁用迁移
    if success and not args.no_migrations:
        migration_success = apply_migrations()
        success = success and migration_success
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 