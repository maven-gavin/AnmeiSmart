#!/usr/bin/env python
"""
安美智享智能医美服务系统 - 数据扩展初始化脚本
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
    from app.identity_access.models.user import User, Role, Doctor, Consultant, Operator, Administrator
    from app.identity_access.enums import AdminLevel
    from app.customer.infrastructure.db.customer import Customer, CustomerProfile
    from app.db.base import get_db, engine
    # from app.services import user_service as crud_user  # 已重构为DDD架构，不再需要
    from app.identity_access.schemas.user import UserCreate, DoctorBase, ConsultantBase, OperatorBase, AdministratorBase
    from app.customer.schemas.customer import CustomerBase
    from app.db.uuid_utils import (
        user_id, role_id, conversation_id, message_id, profile_id, system_id, model_id
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
    # 医生示例数据
    {
        "id": user_id(),  # 使用函数生成统一格式的ID
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
        "id": user_id(),  # 使用函数生成统一格式的ID
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
    print("安美智享智能医美服务系统 - 测试数据初始化工具")
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
        "users", "roles", "user_roles", "customers", "doctors", "consultants", 
        "operators", "administrators", "system_settings"
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
        doctor_info = user_data.pop("doctor_info", None)
        consultant_info = user_data.pop("consultant_info", None)
        customer_info = user_data.pop("customer_info", None)
        operator_info = user_data.pop("operator_info", None)
        administrator_info = user_data.pop("administrator_info", None)
        
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
            doctor_info, consultant_info, customer_info, 
            operator_info, administrator_info,
            force_update
        )
        
        # 将用户添加到映射
        users_map[user_id_value] = user
    
    logger.info("测试用户创建完成")
    return users_map

async def update_user_extended_info(
    db: Session, 
    user: User, 
    doctor_info: Optional[DoctorBase] = None,
    consultant_info: Optional[ConsultantBase] = None,
    customer_info: Optional[CustomerBase] = None,
    operator_info: Optional[OperatorBase] = None,
    administrator_info: Optional[AdministratorBase] = None,
    force_update: bool = False
) -> None:
    """更新用户的扩展信息
    
    Args:
        db: 数据库会话
        user: 用户对象
        doctor_info: 医生信息
        consultant_info: 顾问信息
        customer_info: 客户信息
        operator_info: 运营人员信息
        administrator_info: 管理员信息
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
    
    # 更新医生信息
    if "doctor" in roles and doctor_info and (not user.doctor or force_update):
        if not user.doctor:
            doctor = Doctor(user_id=user.id)
            db.add(doctor)
            logger.info(f"  - 添加医生扩展信息")
        else:
            doctor = user.doctor
            logger.info(f"  - 更新医生扩展信息")
            
        for key, value in doctor_info.model_dump().items():
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
            
        for key, value in consultant_info.model_dump().items():
            if value is not None:
                setattr(consultant, key, value)
        
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
    if "administrator" in roles and administrator_info and (not user.administrator or force_update):
        if not user.administrator:
            administrator = Administrator(user_id=user.id)
            db.add(administrator)
            logger.info(f"  - 添加管理员扩展信息")
        else:
            administrator = user.administrator
            logger.info(f"  - 更新管理员扩展信息")
            
        for key, value in administrator_info.model_dump().items():
            if value is not None:
                setattr(administrator, key, value)
                
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
    
    # 创建测试会话数据
    await create_test_conversations(db)
    
    logger.info("系统测试数据创建完成")

async def create_test_conversations(db: Session) -> None:
    """
    创建测试会话和消息数据
    """
    from app.chat.infrastructure.db.chat import Conversation, Message
    from app.customer.infrastructure.db.customer import CustomerProfile
    from app.db.uuid_utils import conversation_id, message_id, profile_id
    from datetime import datetime, timedelta
    
    logger.info("创建测试会话和消息数据")
    
    # 获取测试客户用户
    customer1 = db.query(User).filter(User.email == "customer1@example.com").first()
    customer2 = db.query(User).filter(User.email == "customer2@example.com").first()
    
    # 获取AI助手ID - 使用统一的ID生成方式
    ai_id = user_id()
    
    # 获取顾问
    consultant = db.query(User).filter(User.email == "li@example.com").first()
    
    if not customer1 or not customer2:
        logger.warning("找不到测试客户用户，跳过创建会话数据")
        return
    
    if not consultant:
        logger.warning("找不到顾问用户，跳过创建含顾问的消息")
    
    # 创建AI用户（如果不存在）
    ai_user = db.query(User).filter(User.username == "AI助手").first()
    if not ai_user:
        logger.info("创建AI助手用户")
        ai_user = User(
            id=ai_id,  # 使用统一生成的ID
            email="ai@example.com",
            username="AI助手",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # 密码: 123456@Test
            avatar="/avatars/ai.png",
            is_active=True
        )
        db.add(ai_user)
        db.commit()
        db.refresh(ai_user)  # 刷新以获取数据库分配的ID
        ai_id = ai_user.id
    else:
        ai_id = ai_user.id
    
    logger.info(f"AI助手ID: {ai_id}")
    
    # 创建或获取客户信息
    customer1_info = db.query(Customer).filter(Customer.user_id == customer1.id).first()
    customer2_info = db.query(Customer).filter(Customer.user_id == customer2.id).first()
    
    if not customer1_info or not customer2_info:
        logger.warning("找不到测试客户扩展信息，无法创建档案")
        return
    
    # 创建或获取客户档案
    profile1 = db.query(CustomerProfile).filter(CustomerProfile.customer_id == customer1.id).first()
    if not profile1:
        logger.info(f"为客户 {customer1.username} 创建档案")
        
        # 李小姐的风险提示
        risk_notes = [
            {
                "type": "药物过敏",
                "description": "对青霉素有过敏反应，建议避免使用含青霉素的药物",
                "level": "high"
            },
            {
                "type": "敏感肌肤",
                "description": "皮肤较敏感，过去对某些护肤品有过敏反应",
                "level": "medium"
            }
        ]
        
        # 将咨询历史存储在 risk_notes 中
        risk_notes.append({
            "type": "咨询历史",
            "description": "历史咨询记录",
            "level": "low",
            "consultation_history": [
                {
                    "date": "2023-05-15",
                    "type": "面部护理",
                    "description": "咨询了敏感肌肤的护理方案，推荐了温和型护肤品，避免含有酒精和香料的产品。建议早晚使用温和洁面乳，保湿霜，以及防晒霜。"
                },
                {
                    "date": "2023-07-22",
                    "type": "双眼皮咨询",
                    "description": "讨论了双眼皮手术的可行性，分析了埋线双眼皮和切开双眼皮的利弊。基于客户眼部条件，建议考虑切开双眼皮以获得更持久的效果。安排了与整形外科医生的面诊。"
                },
                {
                    "date": "2023-10-08",
                    "type": "术后复查",
                    "description": "双眼皮手术后复查，恢复情况良好，轻微水肿属于正常现象。建议继续按医嘱护理，避免剧烈运动，定期复查。"
                }
            ]
        })
        
        profile1 = CustomerProfile(
            id=profile_id(),
            customer_id=customer1.id,
            medical_history="无重大疾病史，2年前做过双眼皮手术",
            allergies="对青霉素过敏",
            preferences="偏好自然风格，不喜欢夸张效果",
            tags="双眼皮,鼻整形,敏感肌",
            risk_notes=risk_notes
        )
        db.add(profile1)
    
    profile2 = db.query(CustomerProfile).filter(CustomerProfile.customer_id == customer2.id).first()
    if not profile2:
        logger.info(f"为客户 {customer2.username} 创建档案")
        
        # 王先生的风险提示
        risk_notes = [
            {
                "type": "高血压",
                "description": "客户有高血压病史，当前处于药物控制状态，医美操作时需注意血压监测",
                "level": "medium"
            }
        ]
        
        # 将咨询历史存储在 risk_notes 中
        risk_notes.append({
            "type": "咨询历史",
            "description": "历史咨询记录",
            "level": "low",
            "consultation_history": [
                {
                    "date": "2023-06-10",
                    "type": "瘦脸针咨询",
                    "description": "咨询了瘦脸针的效果和持续时间。针对客户脸型和需求，建议在咬肌部位注射肉毒素，预计效果可持续4-6个月。已告知可能的副作用和注意事项。"
                },
                {
                    "date": "2023-11-30",
                    "type": "皮肤保养",
                    "description": "客户面部出现干燥和细纹问题，制定了针对性的护肤方案。建议使用含有透明质酸和肽的产品，早晚各一次，并进行适当的皮肤补水治疗。"
                }
            ]
        })
        
        profile2 = CustomerProfile(
            id=profile_id(),
            customer_id=customer2.id,
            medical_history="有高血压，定期服药控制",
            allergies="无已知过敏",
            preferences="喜欢韩式风格，追求精致效果",
            tags="瘦脸针,玻尿酸,皮肤保养",
            risk_notes=risk_notes
        )
        db.add(profile2)
    
    db.commit()
    
    # 创建测试会话
    conv1 = db.query(Conversation).filter(
        Conversation.customer_id == customer1.id,
        Conversation.title == "面部护理咨询"
    ).first()
    
    if not conv1:
        logger.info(f"为客户 {customer1.username} 创建测试会话")
        conv1 = Conversation(
            id=conversation_id(),
            title="面部护理咨询",
            customer_id=customer1.id,
            is_active=True
        )
        db.add(conv1)
        db.commit()
        
        # 添加测试消息 - 使用新的结构化内容格式
        messages1 = [
            {
                "sender_id": customer1.id,
                "sender_type": "customer",
                "content": {"text": "你好，我想咨询一下面部护理的问题"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(hours=2)
            },
            {
                "sender_id": ai_id,
                "sender_type": "ai",
                "content": {"text": "您好！很高兴为您提供面部护理方面的咨询。请问您有什么具体的问题或者困扰吗？"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(hours=2, minutes=1)
            },
            {
                "sender_id": customer1.id,
                "sender_type": "customer",
                "content": {"text": "我的皮肤比较敏感，想知道有什么适合敏感肌的护肤品推荐"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(hours=2, minutes=3)
            },
            {
                "sender_id": ai_id,
                "sender_type": "ai",
                "content": {"text": "针对敏感肌肤，我建议您选择温和无刺激的产品。以下是几点建议：\n\n"
                           "1. 选择标有\"适合敏感肌\"的产品\n"
                           "2. 避免含有酒精、香料和色素的产品\n"
                           "3. 寻找含有芦荟、燕麦、神经酰胺等成分的产品\n"
                           "4. 优先考虑医学护肤品牌如薇诺娜、理肤泉、雅漾等\n\n"
                           "使用新产品时，建议先在手腕内侧做皮肤测试，观察24小时无不良反应后再使用。"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(hours=2, minutes=4)
            },
            {
                "sender_id": customer1.id,
                "sender_type": "customer",
                "content": {
                    "text": "这是我的皮肤照片，请您看一下",
                    "media_info": {
                        "url": "http://example.com/uploads/skin_photo_001.jpg",
                        "name": "skin_photo_001.jpg",
                        "mime_type": "image/jpeg",
                        "size_bytes": 125440,
                        "metadata": {"width": 800, "height": 600}
                    }
                },
                "type": "media",
                "timestamp": datetime.now() - timedelta(hours=1, minutes=30),
                "extra_metadata": {"upload_method": "file_picker"}
            },
            {
                "sender_id": ai_id,
                "sender_type": "ai",
                "content": {"text": "从您提供的照片可以看出，您的皮肤确实比较敏感，有轻微的泛红现象。建议您使用温和的护肤产品，避免过度清洁。"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(hours=1, minutes=25)
            },
            {
                "sender_id": customer1.id,
                "sender_type": "customer",
                "content": {"text": "谢谢建议，我还想问一下敏感肌是否适合做果酸换肤？"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(hours=1)
            },
            {
                "sender_id": ai_id,
                "sender_type": "ai",
                "content": {"text": "关于敏感肌是否适合果酸换肤，需要谨慎考虑：\n\n"
                           "敏感肌肤通常不建议直接使用高浓度果酸产品，风险较高。但在专业医师指导下，低浓度的果酸处理是可能的。\n\n"
                           "建议：\n"
                           "1. 先咨询专业皮肤科医生\n"
                           "2. 从最低浓度(5%-10%)开始尝试\n"
                           "3. 进行皮肤耐受性测试\n"
                           "4. 注意做好防晒措施\n\n"
                           "如果您确实想尝试果酸换肤，我们医疗中心可以安排专业医师为您评估皮肤状况后，制定个性化的温和换肤方案。"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(hours=1, minutes=1)
            }
        ]
        
        for msg_data in messages1:
            msg = Message(
                id=message_id(),
                conversation_id=conv1.id,
                **msg_data
            )
            db.add(msg)
        
        db.commit()
    
    # 创建第二个测试会话
    conv2 = db.query(Conversation).filter(
        Conversation.customer_id == customer2.id,
        Conversation.title == "瘦脸针咨询"
    ).first()
    
    if not conv2:
        logger.info(f"为客户 {customer2.username} 创建测试会话")
        conv2 = Conversation(
            id=conversation_id(),
            title="瘦脸针咨询",
            customer_id=customer2.id,
            is_active=True
        )
        db.add(conv2)
        db.commit()
        
        # 添加测试消息
        messages2 = [
            {
                "sender_id": customer2.id,
                "sender_type": "customer",
                "content": {"text": "你好，我想了解一下瘦脸针的相关信息"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(days=1, hours=3)
            },
            {
                "sender_id": ai_id,
                "sender_type": "ai",
                "content": {"text": "您好！很高兴为您提供瘦脸针的相关信息。瘦脸针主要是注射肉毒素，通过减弱咬肌的收缩力来达到瘦脸效果。请问您有什么具体想了解的呢？"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(days=1, hours=3, minutes=1)
            },
            {
                "sender_id": customer2.id,
                "sender_type": "customer",
                "content": {"text": "瘦脸针的效果能维持多久？有什么副作用吗？"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(days=1, hours=3, minutes=3)
            },
            {
                "sender_id": ai_id,
                "sender_type": "ai",
                "content": {"text": "关于瘦脸针：\n\n"
                           "效果持续时间：\n"
                           "- 一般持续4-6个月\n"
                           "- 个体差异较大，首次注射可能时间短些\n"
                           "- 多次注射后效果可能延长\n\n"
                           "可能的副作用：\n"
                           "- 注射部位暂时肿胀、淤青\n"
                           "- 少数人可能出现不对称\n"
                           "- 极少数情况下有头痛、过敏反应\n"
                           "- 个别出现口水减少\n\n"
                           "注意事项：\n"
                           "- 孕妇、哺乳期女性不建议使用\n"
                           "- 神经肌肉疾病患者禁用\n"
                           "- 注射后24小时内避免按摩注射区域\n"
                           "- 2周内避免剧烈运动\n\n"
                           "您有其他关于瘦脸针的问题吗？"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(days=1, hours=3, minutes=4)
            }
        ]
        
        # 仅当顾问存在时添加顾问消息
        if consultant:
            messages2.append({
                "sender_id": consultant.id,
                "sender_type": "consultant",
                "content": {"text": "您好！我是李顾问，很高兴为您提供更专业的咨询服务。注意到您对瘦脸针很感兴趣，我们医疗中心近期有瘦脸针优惠活动，可以为您提供个性化方案和价格咨询。如果您有意向，可以预约面诊，我将亲自为您服务。"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(days=1, hours=2)
            })
            
            messages2.append({
                "sender_id": customer2.id,
                "sender_type": "customer",
                "content": {"text": "谢谢顾问，我想再多了解一下，瘦脸针和瘦脸导入哪个效果更好呢？"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(days=1, hours=1)
            })
            
            messages2.append({
                "sender_id": ai_id,
                "sender_type": "ai",
                "content": {"text": "瘦脸针与瘦脸导入的比较：\n\n瘦脸针(肉毒素注射)：\n- 原理：通过肌肉松弛达到瘦脸效果\n- 适用人群：咬肌发达者\n- 见效时间：7-14天开始见效\n- 持久性：4-6个月\n- 优势：效果明显，过程快速\n- 风险：需要专业医生操作\n\n瘦脸导入(电离子导入)：\n- 原理：通过电流促进活性成分吸收\n- 适用人群：轻度浮肿、想保养的人群\n- 见效时间：需多次治疗累积\n- 持久性：需持续保养\n- 优势：无创、舒适、风险低\n- 风险：效果相对温和\n\n选择建议：\n- 咬肌发达选择瘦脸针\n- 轻度改善选择导入技术\n- 最佳效果可考虑组合使用\n\n建议您与专业医生面诊评估，根据您的脸型特点选择最适合的方案。"},
                "type": "text",
                "timestamp": datetime.now() - timedelta(days=1, hours=1, minutes=1)
            })
            
            messages2.append({
                "sender_id": consultant.id,
                "sender_type": "consultant",
                "content": {
                    "system_event_type": "takeover",
                    "status": "completed",
                    "details": {
                        "from": "ai",
                        "to": "consultant",
                        "reason": "客户需要专业咨询服务"
                    }
                },
                "type": "system",
                "timestamp": datetime.now() - timedelta(days=1, hours=2, minutes=1)
            })
        
        for msg_data in messages2:
            msg = Message(
                id=message_id(),
                conversation_id=conv2.id,
                **msg_data
            )
            db.add(msg)
        
        db.commit()
    
    logger.info("测试会话和消息数据创建完成")

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