#!/usr/bin/env python
"""
安美智享智能医美服务系统 - 数据扩展初始化脚本
用于初始化系统需要的更复杂或高级的数据
"""
import os
import sys
import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from sqlalchemy.orm import Session
    from app.db.models.user import User, Role, Customer, Doctor, Consultant, Operator, Administrator
    from app.db.base import get_db
    from app.crud import crud_user
    from app.schemas.user import UserCreate, CustomerBase, DoctorBase, ConsultantBase, OperatorBase, AdministratorBase
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有必要的依赖已安装: pip install -r requirements.txt")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 示例扩展用户数据
EXTENDED_USERS = [
    {
        "email": "superadmin@anmeismart.com",
        "username": "超级管理员",
        "doctor_info": DoctorBase(
            specialization="全科",
            certification="高级医师资格证",
            license_number="SUPER123"
        ),
        "consultant_info": ConsultantBase(
            expertise="全面咨询",
            performance_metrics="顶级顾问"
        ),
        "customer_info": CustomerBase(
            medical_history="无",
            allergies="无",
            preferences="全面了解"
        ),
        "operator_info": OperatorBase(
            department="管理部",
            responsibilities="系统管理与运营"
        ),
        "administrator_info": AdministratorBase(
            admin_level=3,
            access_permissions="full_access"
        )
    },
    {
        "email": "zhang@example.com",
        "username": "张医生",
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
    {
        "email": "li@example.com",
        "username": "李顾问",
        "consultant_info": ConsultantBase(
            expertise="皮肤护理",
            performance_metrics="资深顾问"
        )
    },
    {
        "email": "wang@example.com",
        "username": "王运营",
        "operator_info": OperatorBase(
            department="市场部",
            responsibilities="负责内容审核与活动策划"
        )
    },
    {
        "email": "customer1@example.com",
        "username": "李小姐",
        "customer_info": CustomerBase(
            medical_history="无重大疾病史",
            allergies="对某些抗生素过敏",
            preferences="偏好自然风格"
        )
    },
    {
        "email": "customer2@example.com",
        "username": "王先生",
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
    print("安美智享智能医美服务系统 - 数据扩展初始化工具")
    print("=" * 60)
    print("\n此工具将初始化系统需要的高级数据。")
    print("请确保已运行 init_db.py 初始化了基础数据和表结构。")
    print("\n开始初始化扩展数据...")

def print_success():
    """打印成功消息"""
    print("\n扩展数据初始化完成！")

async def create_extended_users(db: Session) -> None:
    """创建扩展用户数据"""
    logger.info("创建扩展用户数据")
    
    for user_data in EXTENDED_USERS:
        user = await crud_user.get_by_email(db, email=user_data["email"])
        if not user:
            logger.info(f"用户不存在，无法添加扩展信息: {user_data['email']}")
            continue
            
        logger.info(f"为用户添加扩展信息: {user_data['email']}")
        
        # 提取各类扩展信息
        doctor_info = user_data.get("doctor_info")
        consultant_info = user_data.get("consultant_info")
        customer_info = user_data.get("customer_info")
        operator_info = user_data.get("operator_info")
        administrator_info = user_data.get("administrator_info")
        
        # 更新扩展表信息
        roles = [role.name for role in user.roles]
        
        # 更新医生信息
        if "doctor" in roles and doctor_info and not user.doctor:
            doctor = Doctor(user_id=user.id)
            for key, value in doctor_info.dict().items():
                if value is not None:
                    setattr(doctor, key, value)
            db.add(doctor)
            logger.info(f"  - 添加医生扩展信息")
            
        # 更新顾问信息
        if "consultant" in roles and consultant_info and not user.consultant:
            consultant = Consultant(user_id=user.id)
            for key, value in consultant_info.dict().items():
                if value is not None:
                    setattr(consultant, key, value)
            db.add(consultant)
            logger.info(f"  - 添加顾问扩展信息")
            
        # 更新顾客信息
        if "customer" in roles and customer_info and not user.customer:
            customer = Customer(user_id=user.id)
            for key, value in customer_info.dict().items():
                if value is not None:
                    setattr(customer, key, value)
            db.add(customer)
            logger.info(f"  - 添加顾客扩展信息")
            
        # 更新运营人员信息
        if "operator" in roles and operator_info and not user.operator:
            operator = Operator(user_id=user.id)
            for key, value in operator_info.dict().items():
                if value is not None:
                    setattr(operator, key, value)
            db.add(operator)
            logger.info(f"  - 添加运营人员扩展信息")
            
        # 更新管理员信息
        if "admin" in roles and administrator_info and not user.administrator:
            administrator = Administrator(user_id=user.id)
            for key, value in administrator_info.dict().items():
                if value is not None:
                    setattr(administrator, key, value)
            db.add(administrator)
            logger.info(f"  - 添加管理员扩展信息")
    
    # 提交所有更改
    db.commit()
    logger.info("扩展用户信息添加完成")

async def migrate_existing_users(db: Session) -> None:
    """迁移现有用户到新的数据库结构"""
    logger.info("开始迁移现有用户数据")
    
    # 获取所有用户
    users = db.query(User).all()
    migrated_count = 0
    
    for user in users:
        # 检查用户角色并创建相应的扩展表记录
        roles = [role.name for role in user.roles]
        
        # 对于顾客角色
        if "customer" in roles and not user.customer:
            customer = Customer(user_id=user.id)
            db.add(customer)
            migrated_count += 1
            logger.info(f"为用户 {user.username} 创建顾客扩展表记录")
        
        # 对于医生角色
        if "doctor" in roles and not user.doctor:
            doctor = Doctor(user_id=user.id)
            db.add(doctor)
            migrated_count += 1
            logger.info(f"为用户 {user.username} 创建医生扩展表记录")
        
        # 对于顾问角色
        if "consultant" in roles and not user.consultant:
            consultant = Consultant(user_id=user.id)
            db.add(consultant)
            migrated_count += 1
            logger.info(f"为用户 {user.username} 创建顾问扩展表记录")
        
        # 对于运营人员角色
        if "operator" in roles and not user.operator:
            operator = Operator(user_id=user.id)
            db.add(operator)
            migrated_count += 1
            logger.info(f"为用户 {user.username} 创建运营人员扩展表记录")
        
        # 对于管理员角色
        if "admin" in roles and not user.administrator:
            administrator = Administrator(user_id=user.id)
            db.add(administrator)
            migrated_count += 1
            logger.info(f"为用户 {user.username} 创建管理员扩展表记录")
    
    # 提交所有更改
    if migrated_count > 0:
        db.commit()
        logger.info(f"用户数据迁移完成，共处理 {migrated_count} 条记录")
    else:
        logger.info("没有需要迁移的用户数据")

async def seed_db_async() -> None:
    """异步初始化扩展数据"""
    logger.info("初始化系统扩展数据")
    
    # 获取数据库会话
    db = next(get_db())
    
    # 迁移现有用户数据
    await migrate_existing_users(db)
    
    # 创建扩展用户
    await create_extended_users(db)
    
    logger.info("系统扩展数据初始化完成")

def seed_db() -> None:
    """同步包装初始化扩展数据函数"""
    try:
        asyncio.run(seed_db_async())
    except Exception as e:
        logger.error(f"初始化扩展数据时出错: {e}")
        raise e

def main():
    """脚本入口点"""
    print_banner()
    
    try:
        seed_db()
        print_success()
    except Exception as e:
        print(f"\n初始化扩展数据过程中发生错误: {e}")
        print("请检查配置和连接信息后重试。")
        sys.exit(1)

if __name__ == "__main__":
    main() 