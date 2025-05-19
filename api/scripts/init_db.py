#!/usr/bin/env python
"""
安美智享智能医美服务系统 - 数据库初始化脚本
用于创建数据库表和初始化基础数据
"""
import os
import sys
import asyncio
import argparse
from sqlalchemy import inspect
from typing import List, Dict, Any
from pathlib import Path

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from sqlalchemy.orm import Session
    from alembic.config import Config
    from alembic import command
    from app.crud import crud_user
    from app.core.config import get_settings
    from app.schemas.user import UserCreate
    from app.db.base import Base, engine, SessionLocal
    # 导入所有模型以确保Base.metadata完整
    from app.db.models import user, chat, system
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有必要的依赖已安装: pip install -r requirements.txt")
    sys.exit(1)

settings = get_settings()

# 预定义角色列表
PREDEFINED_ROLES = [
    {"name": "customer", "description": "顾客角色"},
    {"name": "doctor", "description": "医生角色"},
    {"name": "consultant", "description": "医美顾问角色"},
    {"name": "operator", "description": "运营角色"},
    {"name": "admin", "description": "系统管理员角色"},
]

# 系统用户列表
SYSTEM_USERS = [
    {
        "email": "superadmin@anmeismart.com",
        "username": "superadmin",
        "password": "SuperAdmin@123456",
        "roles": ["admin","operator","consultant","doctor","customer"],
        "phone": "13918924040",
        "is_admin": True
    },
    {
        "email": "admin@anmeismart.com",
        "username": "admin",
        "password": "Admin@123456",
        "roles": ["admin"],
        "phone": "13918924041",
        "is_admin": True
    },
]

def print_banner():
    """打印脚本横幅"""
    print("=" * 60)
    print("安美智享智能医美服务系统 - 数据库初始化工具")
    print("=" * 60)
    print("\n此工具将初始化数据库表结构和创建初始数据。")
    print("请确保已创建了数据库。")
    print("\n开始初始化...")

def print_success():
    """打印成功消息"""
    print("\n初始化完成！您现在可以启动API服务:")
    print("cd .. && uvicorn main:app --reload")

async def create_roles(db: Session) -> None:
    """创建预定义角色"""
    print("创建角色...")
    for role_data in PREDEFINED_ROLES:
        role = await crud_user.get_role_by_name(db, name=role_data["name"])
        if not role:
            print(f"  - 创建角色: {role_data['name']}")
            await crud_user.create_role(db, name=role_data["name"], description=role_data["description"])
        else:
            print(f"  - 角色已存在: {role_data['name']}")

async def create_user(db: Session, user_data: Dict[str, Any]) -> None:
    """创建单个用户"""
    is_admin = user_data.pop("is_admin", False)
    
    user = await crud_user.get_by_email(db, email=user_data["email"])
    if not user:
        print(f"  - 创建用户: {user_data['email']}")
        user_in = UserCreate(**user_data)
        await crud_user.create(db, obj_in=user_in)
    else:
        print(f"  - 用户已存在: {user_data['email']}")

async def create_system_users(db: Session) -> None:
    """创建系统用户"""
    print("\n创建系统用户...")
    for user_data in SYSTEM_USERS:
        await create_user(db, user_data)

async def init_db_async(db: Session) -> None:
    """异步初始化数据库"""
    print("开始初始化数据库表和数据...")
    
    # 创建预定义角色
    await create_roles(db)
    
    # 创建系统用户
    await create_system_users(db)
    
    print("\n数据库初始化完成!")

def check_table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def setup_alembic_config():
    """配置Alembic"""
    # 获取项目根目录的绝对路径
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # alembic.ini文件路径
    alembic_ini_path = os.path.join(project_root, "alembic.ini")
    
    # 检查文件是否存在
    if not os.path.exists(alembic_ini_path):
        print(f"错误: 未找到alembic.ini文件: {alembic_ini_path}")
        print("创建默认的alembic.ini文件...")
        
        default_ini = """[alembic]
script_location = migrations
prepend_sys_path = .

sqlalchemy.url = {database_url}

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""".format(database_url=settings.DATABASE_URL)
        
        with open(alembic_ini_path, "w") as f:
            f.write(default_ini)
        print(f"已创建默认alembic.ini文件: {alembic_ini_path}")
    
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

def apply_migrations():
    """应用数据库迁移"""
    print("应用数据库迁移...")
    try:
        # 配置Alembic
        alembic_cfg = setup_alembic_config()
        
        # 执行迁移
        command.upgrade(alembic_cfg, "head")
        print("数据库迁移完成")
        return True
    except Exception as e:
        print(f"应用数据库迁移时出错: {e}")
        return False

def create_initial_migration():
    """创建初始迁移"""
    print("创建初始迁移...")
    try:
        # 配置Alembic
        alembic_cfg = setup_alembic_config()
        
        # 获取项目根目录的绝对路径
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # 确保我们在项目根目录执行命令
        original_dir = os.getcwd()
        os.chdir(project_root)
        
        # 检查是否已有迁移文件
        from alembic.script import ScriptDirectory
        script = ScriptDirectory.from_config(alembic_cfg)
        
        if not script.get_revisions():
            print("没有发现现有迁移，创建初始迁移...")
            # 配置自动迁移
            migrations_dir = alembic_cfg.get_main_option("script_location")
            env_py_path = os.path.join(migrations_dir, "env.py")
            
            if os.path.exists(env_py_path):
                update_env_file(env_py_path)
            
            # 创建迁移
            command.revision(alembic_cfg, message="初始数据库结构", autogenerate=True)
            print("初始迁移文件已生成")
            
            # 应用迁移
            command.upgrade(alembic_cfg, "head")
            print("初始迁移已应用")
        else:
            print("已有迁移文件，跳过创建初始迁移")
        
        # 恢复原始工作目录
        os.chdir(original_dir)
        
        return True
    except Exception as e:
        print(f"创建初始迁移时出错: {e}")
        return False

def create_tables() -> None:
    """创建数据库表"""
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")

def init_db(db: Session, force_recreate: bool = False, use_migrations: bool = True) -> None:
    """初始化数据库
    
    Args:
        db: 数据库会话
        force_recreate: 是否强制重新创建表结构
        use_migrations: 是否使用迁移系统而不是直接创建表
    """
    try:
        # 检查表是否已存在
        tables_exist = check_table_exists("users") and check_table_exists("roles")
        
        if use_migrations:
            print("使用迁移系统初始化数据库...")
            if force_recreate:
                print("强制模式: 重新创建所有表...")
                # 在强制模式下，直接创建表而不使用迁移
                create_tables()
            elif not tables_exist:
                print("首次初始化: 创建迁移并应用...")
                if not create_initial_migration():
                    print("迁移创建失败，使用传统方式创建表...")
                    create_tables()
            else:
                print("数据库表已存在，应用迁移...")
                if not apply_migrations():
                    print("迁移失败，使用传统方式更新表结构...")
                    create_tables()
        else:
            print("使用传统方式初始化数据库...")
            if force_recreate or not tables_exist:
                if force_recreate:
                    print("强制模式: 重新创建所有表...")
                else:
                    print("首次初始化: 创建所有表...")
                create_tables()
            else:
                print("数据库表已存在，跳过创建...")
        
        # 运行异步初始化函数
        asyncio.run(init_db_async(db))
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        sys.exit(1)

def main():
    """脚本入口"""
    # 添加命令行参数
    parser = argparse.ArgumentParser(description="数据库初始化脚本")
    parser.add_argument("--force", action="store_true", help="强制重新创建表结构")
    parser.add_argument("--migrate-only", action="store_true", help="仅应用迁移，不初始化数据")
    parser.add_argument("--no-migrations", action="store_true", help="不使用迁移系统，直接创建表")
    args = parser.parse_args()
    
    print_banner()
    
    try:
        db = SessionLocal()
        # 检查数据库类型
        is_sqlite = "sqlite" in settings.DATABASE_URL.lower()
        if is_sqlite:
            print("使用SQLite数据库进行初始化")
        else:
            print(f"使用数据库: {settings.DATABASE_URL}")
        
        if args.migrate_only:
            # 仅应用迁移
            apply_migrations()
        else:
            # 正常初始化
            init_db(db, args.force, not args.no_migrations)
            
        print_success()
    except Exception as e:
        print(f"\n初始化过程中发生错误: {e}")
        print("请检查配置和连接信息后重试。")
        sys.exit(1)

if __name__ == "__main__":
    main() 