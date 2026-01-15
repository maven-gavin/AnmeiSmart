#!/usr/bin/env python
"""
安美智享智能服务系统 - 数据扩展初始化脚本
用于初始化测试和示例数据
"""

import os
import sys

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 先导入 bcrypt 补丁修复 passlib 问题
from app.core.bcrypt_patch import *

import asyncio
import logging
import argparse
from sqlalchemy import inspect
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from sqlalchemy.orm import Session
    from app.identity_access.models.user import User, Role, Operator, Admin
    from app.identity_access.enums import AdminLevel
    from app.customer.models.customer import Customer, CustomerProfile
    from app.common.deps.database import get_db, engine
    from app.identity_access.schemas.user import UserCreate, OperatorBase, AdminBase
    from app.customer.schemas.customer import CustomerBase
    from app.common.deps.uuid_utils import (
        user_id
    )
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有必要的依赖已安装: pip install -r requirements.txt")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 示例测试用户数据 - 确保ID格式一致
MOCK_USERS = [
    # 运营示例数据
    {
        "id": user_id(),  # 使用函数生成统一格式的ID
        "email": "wang@example.com",
        "username": "王运营",
        "password": "123456@Test",
        "roles": ["operator"],
        "phone": "13700137001",
        "avatar": "/avatars/operator1.png",
        "operator_info": OperatorBase(
            department="市场部",
            responsibilities="负责内容审核与活动策划"
        )
    },
    # 客户示例数据
    {
        "id": user_id(),  # 使用函数生成统一格式的ID
        "email": "customer1@example.com",
        "username": "李小姐",
        "password": "123456@Test",
        "roles": ["customer"],
        "phone": "13812345678",
        "avatar": "/avatars/user1.png",
        "customer_info": CustomerBase(
            medical_history="无重大疾病史",
            allergies="对某些抗生素过敏",
            preferences="偏好自然风格"
        )
    },
    {
        "id": user_id(),  # 使用函数生成统一格式的ID
        "email": "customer2@example.com",
        "username": "王先生",
        "password": "123456@Test",
        "roles": ["customer"],
        "phone": "13987654321",
        "avatar": "/avatars/user2.png",
        "customer_info": CustomerBase(
            medical_history="高血压史",
            allergies="无",
            preferences="偏好韩式风格"
        )
    }
]

def print_banner():
    """打印脚本横幅"""
    print("=" * 60)
    print("安美智享智能服务系统 - 测试数据初始化工具")
    print("=" * 60)
    print("\n此工具将初始化系统需要的测试和示例数据。")
    print("请确保已运行 init_db.py 初始化了基础数据和表结构。")
    print("\n开始初始化测试数据...")

def print_success():
    """打印成功消息"""
    print("\n测试数据初始化完成！")

def check_extension_tables_exist():
    """检查扩展表是否存在
    
    Returns:
        bool: 扩展表是否存在
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    required_tables = [
        "users", "roles", "user_roles", "customers", 
        "operators", "admins", "system_settings"
    ]
    
    for table in required_tables:
        if table not in tables:
            logger.warning(f"必要的表未找到: {table}")
            return False
    
    logger.info("所有必要的表都存在")
    return True

async def create_mock_users(db: Session, force_update: bool = False) -> Dict[str, User]:
    """创建测试用户数据
    
    Args:
        db: 数据库会话
        force_update: 是否强制更新现有数据
        
    Returns:
        Dict[str, User]: 用户ID到用户对象的映射
    """
    logger.info("创建测试用户数据")
    
    users_map = {}  # 用于存储用户ID到用户对象的映射
    
    for user_data in MOCK_USERS:
        # 提取角色和扩展信息
        user_id_value = user_data.pop("id", None) or user_id()
        roles = user_data.get("roles", ["customer"])
        customer_info = user_data.pop("customer_info", None)
        operator_info = user_data.pop("operator_info", None)
        admin_info = user_data.pop("admin_info", None)
        
        # 检查用户是否存在（直接使用数据库模型）
        user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if not user:
            logger.info(f"创建测试用户: {user_data['email']}")
            
            # 直接创建用户模型
            from app.core.password_utils import get_password_hash
            user = User(
                id=user_id_value,
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=get_password_hash(user_data["password"]),
                phone=user_data.get("phone"),
                avatar=user_data.get("avatar"),
                is_active=True
            )
            
            # 添加角色
            role_objects = []
            for role_name in user_data.get("roles", []):
                role = db.query(Role).filter(Role.name == role_name).first()
                if role:
                    role_objects.append(role)
            user.roles = role_objects
            
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            logger.info(f"测试用户已存在: {user_data['email']}")
            
        # 添加扩展信息
        await update_user_extended_info(
            db, user, 
            customer_info, 
            operator_info, admin_info,
            force_update
        )
        
        # 将用户添加到映射
        users_map[user_id_value] = user
    
    logger.info("测试用户创建完成")
    return users_map

async def update_user_extended_info(
    db: Session, 
    user: User, 
    customer_info: Optional[CustomerBase] = None,
    operator_info: Optional[OperatorBase] = None,
    admin_info: Optional[AdminBase] = None,
    force_update: bool = False
) -> None:
    """更新用户的扩展信息
    
    Args:
        db: 数据库会话
        user: 用户对象
        customer_info: 客户信息
        operator_info: 运营人员信息
        admin_info: 管理员信息
        force_update: 是否强制更新现有数据
    """
    # 安全地获取角色列表
    try:
        # 如果roles是对象列表（有name属性）
        roles = [role.name for role in user.roles]
    except AttributeError:
        # 如果roles是字符串列表或其他格式
        if isinstance(user.roles, list):
            roles = user.roles if all(isinstance(r, str) for r in user.roles) else []
        else:
            roles = []
    
    # 更新客户信息
    if "customer" in roles and customer_info:
        # 使用单独的函数处理客户信息
        await update_customer_info(db, user.id, customer_info, force_update)
        
    # 更新运营人员信息
    if "operator" in roles and operator_info and (not user.operator or force_update):
        if not user.operator:
            operator = Operator(user_id=user.id)
            db.add(operator)
            logger.info(f"  - 添加运营人员扩展信息")
        else:
            operator = user.operator
            logger.info(f"  - 更新运营人员扩展信息")
            
        for key, value in operator_info.model_dump().items():
            if value is not None:
                setattr(operator, key, value)
        
    # 更新管理员信息
    if "admin" in roles and admin_info and (not user.admin or force_update):
        if not user.admin:
            admin = Admin(user_id=user.id)
            db.add(admin)
            logger.info(f"  - 添加管理员扩展信息")
        else:
            admin = user.admin
            logger.info(f"  - 更新管理员扩展信息")
            
        for key, value in admin_info.model_dump().items():
            if value is not None:
                setattr(admin, key, value)
                
    db.commit()

async def update_customer_info(
    db: Session,
    user_id: str,
    customer_info: CustomerBase,
    force_update: bool = False
) -> None:
    """更新客户信息
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        customer_info: 客户信息
        force_update: 是否强制更新现有数据
    """
    # 查找现有客户信息
    customer = db.query(Customer).filter(Customer.user_id == user_id).first()
    
    # 如果不存在或强制更新
    if not customer:
        customer = Customer(user_id=user_id)
        db.add(customer)
        logger.info(f"  - 添加客户扩展信息")
    elif force_update:
        logger.info(f"  - 更新客户扩展信息")
    else:
        return  # 如果存在且不强制更新，则不做任何操作
    
    # 更新客户信息
    for key, value in customer_info.model_dump().items():
        if value is not None:
            setattr(customer, key, value)
    
    db.commit()

async def create_system_test_data(db: Session) -> None:
    """创建系统测试数据，比如聊天记录、系统设置等"""
    logger.info("创建系统测试数据")
        
    logger.info("系统测试数据创建完成")

async def seed_db_async(force_update: bool = False) -> None:
    """异步数据库种子函数
    
    Args:
        force_update: 是否强制更新现有数据
    """
    # 检查扩展表是否存在
    if not check_extension_tables_exist():
        logger.error("扩展表不存在，请先运行 init_db.py 初始化基础数据和表结构")
        return
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建测试用户数据
        await create_mock_users(db, force_update)
        
        # 创建系统测试数据
        await create_system_test_data(db)
        
    except Exception as e:
        logger.error(f"初始化数据时出错: {e}")
        raise
    finally:
        db.close()

def seed_db(force_update: bool = False) -> None:
    """数据库种子函数
    
    Args:
        force_update: 是否强制更新现有数据
    """
    # 运行异步函数
    asyncio.run(seed_db_async(force_update))

def main():
    """脚本入口函数"""
    parser = argparse.ArgumentParser(description="数据扩展初始化工具")
    parser.add_argument("--force", action="store_true", help="强制更新现有测试数据")
    parser.add_argument("--clean", action="store_true", help="清除现有测试数据后重新创建")
    args = parser.parse_args()
    
    try:
        # 执行数据库种子函数
        seed_db(args.force)
        
        print("\n数据扩展初始化完成！")
        print("现在可以启动API服务: cd .. && uvicorn main:app --reload")
        
    except Exception as e:
        print(f"\n初始化过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 