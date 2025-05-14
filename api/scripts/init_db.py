#!/usr/bin/env python
"""
安美智享智能医美服务系统 - 数据库初始化脚本
用于创建数据库表和初始化基础数据
"""
import os
import sys
import asyncio
from typing import List, Dict, Any
from pathlib import Path

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from sqlalchemy.orm import Session
    from app.crud import crud_user
    from app.core.config import get_settings
    from app.schemas.user import UserCreate
    from app.db.base import Base, engine, SessionLocal
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
    {
        "email": "li@example.com",
        "username": "李顾问",
        "password": "123456@Test",
        "roles": ["consultant"],
        "phone": "13900139001",
        "avatar": "/avatars/consultant1.png"
    },
    {
        "email": "zhang@example.com",
        "username": "张医生",
        "password": "123456@Test",
        "roles": ["doctor", "consultant"],
        "phone": "13800138001",
        "avatar": "/avatars/doctor1.png"
    },
    {
        "email": "wang@example.com",
        "username": "王运营",
        "password": "123456@Test",
        "roles": ["operator"],
        "phone": "13700137001",
        "avatar": "/avatars/operator1.png"
    },
]

# 模拟用户列表
MOCK_USERS = [
    {
        "email": "customer1@example.com",
        "username": "李小姐",
        "password": "123456@Test",
        "roles": ["customer"],
        "phone": "13812345678",
        "avatar": "/avatars/user1.png"
    },
    {
        "email": "customer2@example.com",
        "username": "王先生",
        "password": "123456@Test",
        "roles": ["customer"],
        "phone": "13987654321",
        "avatar": "/avatars/user2.png"
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

async def create_mock_users(db: Session) -> None:
    """创建模拟用户"""
    print("\n创建模拟用户...")
    for user_data in MOCK_USERS:
        await create_user(db, user_data)

async def init_db_async(db: Session) -> None:
    """异步初始化数据库"""
    print("开始初始化数据库表和数据...")
    
    # 创建预定义角色
    await create_roles(db)
    
    # 创建系统用户
    await create_system_users(db)
    
    # 创建模拟用户
    await create_mock_users(db)
    
    print("\n数据库初始化完成!")

def create_tables() -> None:
    """创建数据库表"""
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")

def init_db(db: Session) -> None:
    """同步包装初始化数据库函数"""
    try:
        # 创建所有表
        create_tables()
        
        # 运行异步初始化函数
        asyncio.run(init_db_async(db))
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        sys.exit(1)

def main():
    """脚本入口"""
    print_banner()
    
    try:
        db = SessionLocal()
        init_db(db)
        print_success()
    except Exception as e:
        print(f"\n初始化过程中发生错误: {e}")
        print("请检查配置和连接信息后重试。")
        sys.exit(1)

if __name__ == "__main__":
    main() 