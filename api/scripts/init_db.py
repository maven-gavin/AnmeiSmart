#!/usr/bin/env python
"""
安美智享智能服务系统 - 数据库初始化脚本
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
        # 导入数据库初始化函数，它会自动导入所有模型
        from app.common.deps.database import init_db as db_init
        db_init()
        logger.info("成功创建数据库表")
    except Exception as e:
        logger.error(f"创建数据库表时出错: {e}")
        raise

def create_initial_roles():
    """创建初始角色"""
    try:
        # 导入角色相关模块
        from app.common.deps.database import create_initial_roles as db_create_roles
        db_create_roles()
        logger.info("成功创建初始角色")
    except Exception as e:
        logger.error(f"创建初始角色时出错: {e}")
        raise

def create_initial_system_settings():
    """创建系统初始设置"""
    try:
        # 导入系统设置相关模块
        from app.common.deps.database import create_initial_system_settings as db_create_settings
        db_create_settings()
        logger.info("成功创建系统设置")
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
        from app.common.deps.database import engine, Base
        
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