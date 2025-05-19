#!/usr/bin/env python
"""
安美智享智能医美服务系统 - 数据扩展初始化脚本
用于初始化测试和示例数据
"""
import os
import sys
import asyncio
import logging
import argparse
from sqlalchemy import inspect
from typing import Dict, Any, List
from pathlib import Path

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from sqlalchemy.orm import Session
    from app.db.models.user import User, Role, Customer, Doctor, Consultant, Operator, Administrator
    from app.db.base import get_db, engine
    from app.crud import crud_user
    from app.schemas.user import UserCreate, CustomerBase, DoctorBase, ConsultantBase, OperatorBase, AdministratorBase
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有必要的依赖已安装: pip install -r requirements.txt")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 示例测试用户数据
MOCK_USERS = [
    # 医生示例数据
    {
        "email": "zhang@example.com",
        "username": "张医生",
        "password": "123456@Test",
        "roles": ["doctor", "consultant"],
        "phone": "13800138001",
        "avatar": "/avatars/doctor1.png",
        "doctor_info": DoctorBase(
            specialization="整形外科",
            certification="医师资格证",
            license_number="DOC123456"
        ),
        "consultant_info": ConsultantBase(
            expertise="面部整形咨询",
            performance_metrics="高级顾问"
        )
    },
    # 顾问示例数据
    {
        "email": "li@example.com",
        "username": "李顾问",
        "password": "123456@Test",
        "roles": ["consultant"],
        "phone": "13900139001",
        "avatar": "/avatars/consultant1.png",
        "consultant_info": ConsultantBase(
            expertise="皮肤护理",
            performance_metrics="资深顾问"
        )
    },
    # 运营示例数据
    {
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
    # 顾客示例数据
    {
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
    print("安美智享智能医美服务系统 - 测试数据初始化工具")
    print("=" * 60)
    print("\n此工具将初始化系统需要的测试和示例数据。")
    print("请确保已运行 init_db.py 初始化了基础数据和表结构。")
    print("\n开始初始化测试数据...")

def print_success():
    """打印成功消息"""
    print("\n测试数据初始化完成！")

def check_extension_tables_exist() -> bool:
    """检查扩展表是否存在"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    required_tables = ["customers", "doctors", "consultants", "operators", "administrators"]
    return all(table in tables for table in required_tables)

async def create_mock_users(db: Session, force_update: bool = False) -> None:
    """创建测试用户数据
    
    Args:
        db: 数据库会话
        force_update: 是否强制更新现有数据
    """
    logger.info("创建测试用户数据")
    
    for user_data in MOCK_USERS:
        # 提取角色和扩展信息
        roles = user_data.get("roles", ["customer"])
        doctor_info = user_data.pop("doctor_info", None)
        consultant_info = user_data.pop("consultant_info", None)
        customer_info = user_data.pop("customer_info", None)
        operator_info = user_data.pop("operator_info", None)
        administrator_info = user_data.pop("administrator_info", None)
        
        # 检查用户是否存在
        user = await crud_user.get_by_email(db, email=user_data["email"])
        
        if not user:
            logger.info(f"创建测试用户: {user_data['email']}")
            user_in = UserCreate(**user_data)
            user = await crud_user.create(db, obj_in=user_in)
        else:
            logger.info(f"测试用户已存在: {user_data['email']}")
            
        # 添加扩展信息
        await update_user_extended_info(
            db, user, 
            doctor_info, consultant_info, customer_info, 
            operator_info, administrator_info,
            force_update
        )
    
    logger.info("测试用户创建完成")

async def update_user_extended_info(
    db: Session, 
    user: User, 
    doctor_info: DoctorBase = None,
    consultant_info: ConsultantBase = None,
    customer_info: CustomerBase = None,
    operator_info: OperatorBase = None,
    administrator_info: AdministratorBase = None,
    force_update: bool = False
) -> None:
    """更新用户的扩展信息
    
    Args:
        db: 数据库会话
        user: 用户对象
        doctor_info: 医生信息
        consultant_info: 顾问信息
        customer_info: 顾客信息
        operator_info: 运营人员信息
        administrator_info: 管理员信息
        force_update: 是否强制更新现有数据
    """
    roles = [role.name for role in user.roles]
    
    # 更新医生信息
    if "doctor" in roles and doctor_info and (not user.doctor or force_update):
        if not user.doctor:
            doctor = Doctor(user_id=user.id)
            db.add(doctor)
            logger.info(f"  - 添加医生扩展信息")
        else:
            doctor = user.doctor
            logger.info(f"  - 更新医生扩展信息")
            
        for key, value in doctor_info.dict().items():
            if value is not None:
                setattr(doctor, key, value)
        
    # 更新顾问信息
    if "consultant" in roles and consultant_info and (not user.consultant or force_update):
        if not user.consultant:
            consultant = Consultant(user_id=user.id)
            db.add(consultant)
            logger.info(f"  - 添加顾问扩展信息")
        else:
            consultant = user.consultant
            logger.info(f"  - 更新顾问扩展信息")
            
        for key, value in consultant_info.dict().items():
            if value is not None:
                setattr(consultant, key, value)
        
    # 更新顾客信息
    if "customer" in roles and customer_info and (not user.customer or force_update):
        if not user.customer:
            customer = Customer(user_id=user.id)
            db.add(customer)
            logger.info(f"  - 添加顾客扩展信息")
        else:
            customer = user.customer
            logger.info(f"  - 更新顾客扩展信息")
            
        for key, value in customer_info.dict().items():
            if value is not None:
                setattr(customer, key, value)
        
    # 更新运营人员信息
    if "operator" in roles and operator_info and (not user.operator or force_update):
        if not user.operator:
            operator = Operator(user_id=user.id)
            db.add(operator)
            logger.info(f"  - 添加运营人员扩展信息")
        else:
            operator = user.operator
            logger.info(f"  - 更新运营人员扩展信息")
            
        for key, value in operator_info.dict().items():
            if value is not None:
                setattr(operator, key, value)
        
    # 更新管理员信息
    if "admin" in roles and administrator_info and (not user.administrator or force_update):
        if not user.administrator:
            administrator = Administrator(user_id=user.id)
            db.add(administrator)
            logger.info(f"  - 添加管理员扩展信息")
        else:
            administrator = user.administrator
            logger.info(f"  - 更新管理员扩展信息")
            
        for key, value in administrator_info.dict().items():
            if value is not None:
                setattr(administrator, key, value)
                
    # 提交更改
    db.commit()
    db.refresh(user)

async def create_system_test_data(db: Session) -> None:
    """创建系统测试数据，比如聊天记录、系统设置等"""
    logger.info("创建系统测试数据")
    
    # 在这里添加创建系统测试数据的代码
    # 例如创建示例聊天记录、示例系统设置等
    
    logger.info("系统测试数据创建完成")

async def seed_db_async(force_update: bool = False) -> None:
    """异步初始化测试数据
    
    Args:
        force_update: 是否强制更新现有数据
    """
    logger.info("初始化系统测试数据")
    
    # 获取数据库会话
    db = next(get_db())
    
    # 检查扩展表是否存在
    if not check_extension_tables_exist():
        logger.error("扩展表不存在，请先运行 init_db.py 应用迁移")
        return
    
    # 创建测试用户
    await create_mock_users(db, force_update)
    
    # 创建系统测试数据
    await create_system_test_data(db)
    
    logger.info("系统测试数据初始化完成")

def seed_db(force_update: bool = False) -> None:
    """同步包装初始化测试数据函数
    
    Args:
        force_update: 是否强制更新现有数据
    """
    try:
        asyncio.run(seed_db_async(force_update))
    except Exception as e:
        logger.error(f"初始化测试数据时出错: {e}")
        raise e

def main():
    """脚本入口点"""
    # 添加命令行参数
    parser = argparse.ArgumentParser(description="测试数据初始化脚本")
    parser.add_argument("--force", action="store_true", help="强制更新现有数据")
    parser.add_argument("--clean", action="store_true", help="清除现有测试数据后重新创建")
    args = parser.parse_args()
    
    print_banner()
    
    try:
        if args.clean:
            # 在此添加清除测试数据的代码
            print("清除现有测试数据...")
            # TODO: 实现清除测试数据的功能
            
        seed_db(args.force)
        print_success()
    except Exception as e:
        print(f"\n初始化测试数据过程中发生错误: {e}")
        print("请检查配置和连接信息后重试。")
        sys.exit(1)

if __name__ == "__main__":
    main() 