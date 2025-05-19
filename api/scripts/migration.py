#!/usr/bin/env python
"""
安美智享智能医美服务系统 - 数据库迁移脚本
用于生成和管理数据库迁移
"""
import os
import sys
import argparse
from pathlib import Path

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from sqlalchemy.orm import Session
    from alembic.config import Config
    from alembic import command
    from app.db.base import Base, engine
    from app.core.config import get_settings
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有必要的依赖已安装: pip install -r requirements.txt")
    sys.exit(1)

settings = get_settings()

def print_banner():
    """打印脚本横幅"""
    print("=" * 60)
    print("安美智享智能医美服务系统 - 数据库迁移工具")
    print("=" * 60)
    print("\n此工具用于管理数据库结构的变更。")
    print("\n可用命令:")
    print("  create  - 创建新的迁移")
    print("  upgrade - 应用迁移到最新版本")
    print("  history - 显示迁移历史")
    print("  downgrade - 回滚到指定版本")
    print("  detect - 检测模型变更")

def setup_alembic_config():
    """配置Alembic"""
    # 获取项目根目录的绝对路径
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # alembic.ini文件路径
    alembic_ini_path = os.path.join(project_root, "alembic.ini")
    
    # 检查文件是否存在
    if not os.path.exists(alembic_ini_path):
        print(f"错误: 未找到alembic.ini文件: {alembic_ini_path}")
        print("请确保在项目根目录中存在alembic.ini文件")
        sys.exit(1)
    
    # 创建配置
    alembic_cfg = Config(alembic_ini_path)
    
    # 指定migrations目录的绝对路径
    migrations_dir = os.path.join(project_root, "migrations")
    
    # 检查migrations目录是否存在
    if not os.path.exists(migrations_dir):
        print(f"创建migrations目录: {migrations_dir}")
        try:
            os.makedirs(migrations_dir, exist_ok=True)
            # 初始化目录结构
            print("初始化Alembic环境...")
            os.chdir(project_root)  # 切换到项目根目录
            command.init(alembic_cfg, migrations_dir)
            print("Alembic环境已初始化")
            
            # 更新env.py来使用Base.metadata
            env_py_path = os.path.join(migrations_dir, "env.py")
            if os.path.exists(env_py_path):
                update_env_file(env_py_path)
        except Exception as e:
            print(f"创建migrations目录时出错: {e}")
            sys.exit(1)
    
    # 设置脚本位置
    alembic_cfg.set_main_option("script_location", migrations_dir)
    
    return alembic_cfg

def update_env_file(env_py_path):
    """更新env.py文件以支持自动迁移"""
    try:
        with open(env_py_path, "r", encoding="utf-8") as file:
            content = file.read()
        
        # 替换target_metadata = None为实际模型元数据
        if "target_metadata = None" in content:
            import_statement = (
                "import sys\n"
                "sys.path.insert(0, '.')\n"
                "# 导入所有模型确保元数据完整\n"
                "from app.db.base import Base\n"
                "from app.db.models import user, chat, system # 确保导入所有模型模块\n"
            )
            content = content.replace("target_metadata = None", 
                                     import_statement + "target_metadata = Base.metadata")
            
            with open(env_py_path, "w", encoding="utf-8") as file:
                file.write(content)
            print("已更新env.py以支持自动迁移")
    except Exception as e:
        print(f"更新env.py文件时出错: {e}")

def create_migration(message, auto=True):
    """创建新的迁移
    
    Args:
        message: 迁移说明
        auto: 是否自动生成迁移
    """
    print(f"创建新的迁移: {message}")
    alembic_cfg = setup_alembic_config()
    
    # 获取项目根目录的绝对路径
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # 确保我们在项目根目录执行命令
    original_dir = os.getcwd()
    os.chdir(project_root)
    
    if auto:
        # 配置自动迁移
        # 更新env.py来使用Base.metadata
        migrations_dir = alembic_cfg.get_main_option("script_location")
        env_py_path = os.path.join(migrations_dir, "env.py")
        
        if os.path.exists(env_py_path):
            update_env_file(env_py_path)
        
        try:
            command.revision(alembic_cfg, message=message, autogenerate=True)
            print("迁移文件已生成")
        except Exception as e:
            print(f"创建迁移时出错: {e}")
    else:
        try:
            command.revision(alembic_cfg, message=message)
            print("空白迁移文件已生成")
        except Exception as e:
            print(f"创建迁移时出错: {e}")
    
    # 恢复原始工作目录
    os.chdir(original_dir)
    
    print("迁移已创建，请检查migrations/versions目录下的迁移文件")

def upgrade_database(revision="head"):
    """升级数据库到指定版本
    
    Args:
        revision: 目标版本，默认为最新版本(head)
    """
    print(f"升级数据库到版本: {revision}")
    
    # 获取项目根目录的绝对路径
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # 确保我们在项目根目录执行命令
    original_dir = os.getcwd()
    os.chdir(project_root)
    
    alembic_cfg = setup_alembic_config()
    
    try:
        command.upgrade(alembic_cfg, revision)
        print("数据库升级完成")
    except Exception as e:
        print(f"升级数据库时出错: {e}")
    
    # 恢复原始工作目录
    os.chdir(original_dir)

def downgrade_database(revision):
    """回滚数据库到指定版本
    
    Args:
        revision: 目标版本
    """
    print(f"回滚数据库到版本: {revision}")
    
    # 获取项目根目录的绝对路径
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # 确保我们在项目根目录执行命令
    original_dir = os.getcwd()
    os.chdir(project_root)
    
    alembic_cfg = setup_alembic_config()
    
    try:
        command.downgrade(alembic_cfg, revision)
        print("数据库回滚完成")
    except Exception as e:
        print(f"回滚数据库时出错: {e}")
    
    # 恢复原始工作目录
    os.chdir(original_dir)

def show_history():
    """显示迁移历史"""
    print("显示迁移历史")
    
    # 获取项目根目录的绝对路径
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # 确保我们在项目根目录执行命令
    original_dir = os.getcwd()
    os.chdir(project_root)
    
    alembic_cfg = setup_alembic_config()
    
    try:
        command.history(alembic_cfg)
    except Exception as e:
        print(f"显示迁移历史时出错: {e}")
    
    # 恢复原始工作目录
    os.chdir(original_dir)

def detect_changes():
    """检测模型变更"""
    print("检测数据库模型变更...")
    
    # 获取项目根目录的绝对路径
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # 确保我们在项目根目录执行命令
    original_dir = os.getcwd()
    os.chdir(project_root)
    
    alembic_cfg = setup_alembic_config()
    
    try:
        # 使用上下文管理器为Alembic脚本创建环境
        from alembic.script import ScriptDirectory
        from alembic.runtime.environment import EnvironmentContext
        from alembic.operations import Operations
        from alembic.migration import MigrationContext
        from sqlalchemy import engine_from_config
        
        # 导入元数据以确保所有模型已加载
        from app.db.base import Base, engine
        from app.db.models import user, chat, system  # 导入所有模型模块
        
        # 获取连接
        connection = engine.connect()
        
        # 创建迁移上下文
        migration_context = MigrationContext.configure(
            connection,
            opts={
                'compare_type': True,
                'compare_server_default': True,
            }
        )
        
        # 比较元数据与数据库
        from alembic.autogenerate import compare_metadata
        models_metadata = Base.metadata
        
        # 检测变更
        diffs = compare_metadata(migration_context, models_metadata)
        
        # 关闭连接
        connection.close()
        
        # 输出结果
        if diffs:
            print("\n检测到以下模型变更:")
            for diff in diffs:
                print(f"  - {diff}")
            print("\n您可以运行以下命令创建迁移：")
            print("  python migration.py create --message \"自动迁移:模型更新\"")
            return True
        else:
            print("\n未检测到模型变更，数据库结构与模型一致。")
            return False
            
    except Exception as e:
        print(f"检测模型变更时出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 恢复原始工作目录
        os.chdir(original_dir)

def main():
    """脚本入口"""
    # 添加命令行参数
    parser = argparse.ArgumentParser(description="数据库迁移脚本")
    parser.add_argument("command", choices=["create", "upgrade", "downgrade", "history", "detect"], 
                        help="执行的命令")
    parser.add_argument("--message", help="迁移说明")
    parser.add_argument("--revision", help="目标版本")
    parser.add_argument("--manual", action="store_true", help="手动创建迁移而不是自动检测")
    args = parser.parse_args()
    
    print_banner()
    
    try:
        if args.command == "create":
            if not args.message:
                print("错误: 创建迁移需要指定--message参数")
                sys.exit(1)
            create_migration(args.message, not args.manual)
        elif args.command == "upgrade":
            revision = args.revision or "head"
            upgrade_database(revision)
        elif args.command == "downgrade":
            if not args.revision:
                print("错误: 回滚迁移需要指定--revision参数")
                sys.exit(1)
            downgrade_database(args.revision)
        elif args.command == "history":
            show_history()
        elif args.command == "detect":
            changes_detected = detect_changes()
            if changes_detected:
                print("\n检测到模型变更！")
                print("您可以运行以下命令创建迁移：")
                print("  python migration.py create --message \"自动迁移:模型更新\"")
            else:
                print("\n未检测到模型变更。")
    except Exception as e:
        print(f"\n执行命令时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 