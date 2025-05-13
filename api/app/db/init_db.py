import asyncio
import sys
from sqlalchemy.orm import Session

from app.crud import crud_user
from app.core.config import get_settings
from app.models.user import UserCreate
from app.db.base import Base, engine

settings = get_settings()

# 预定义角色
PREDEFINED_ROLES = [
    {"name": "advisor", "description": "医美顾问角色"},
    {"name": "doctor", "description": "医生角色"},
    {"name": "customer", "description": "顾客角色"},
    {"name": "operator", "description": "运营角色"},
    {"name": "admin", "description": "系统管理员角色"},
]

# 预定义用户
MOCK_USERS = [
    {
        "email": "zhang@example.com",
        "username": "张医生",
        "password": "123456@Test",
        "roles": ["doctor", "advisor"],
        "phone": "13800138001",
        "avatar": "/avatars/doctor1.png"
    },
    {
        "email": "li@example.com",
        "username": "李顾问",
        "password": "123456@Test",
        "roles": ["advisor"],
        "phone": "13900139001",
        "avatar": "/avatars/advisor1.png"
    },
    {
        "email": "wang@example.com",
        "username": "王运营",
        "password": "123456@Test",
        "roles": ["operator"],
        "phone": "13700137001",
        "avatar": "/avatars/operator1.png"
    },
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

async def init_db_async(db: Session) -> None:
    """异步初始化数据库"""
    print("开始初始化数据库表和数据...")
    
    # 创建预定义角色
    print("创建角色...")
    for role_data in PREDEFINED_ROLES:
        role = await crud_user.get_role_by_name(db, name=role_data["name"])
        if not role:
            print(f"  - 创建角色: {role_data['name']}")
            await crud_user.create_role(db, name=role_data["name"], description=role_data["description"])
        else:
            print(f"  - 角色已存在: {role_data['name']}")
    
    # 创建初始管理员用户
    print("\n创建管理员用户...")
    admin_user = await crud_user.get_by_email(db, email="admin@anmeismart.com")
    if not admin_user:
        print("  - 创建管理员用户: admin@anmeismart.com")
        admin_in = UserCreate(
            email="admin@anmeismart.com",
            username="admin",
            password="Admin@123456",
            roles=["admin"]
        )
        await crud_user.create(db, obj_in=admin_in)
    else:
        print("  - 管理员用户已存在: admin@anmeismart.com")
    
    # 创建初始测试用户
    print("\n创建测试用户...")
    test_users = [
        UserCreate(
            email="advisor@anmeismart.com",
            username="advisor",
            password="Test@123456",
            roles=["advisor"]
        ),
        UserCreate(
            email="doctor@anmeismart.com",
            username="doctor",
            password="Test@123456",
            roles=["doctor"]
        ),
        UserCreate(
            email="customer@anmeismart.com",
            username="customer",
            password="Test@123456",
            roles=["customer"]
        ),
    ]
    
    for user_in in test_users:
        user = await crud_user.get_by_email(db, email=user_in.email)
        if not user:
            print(f"  - 创建测试用户: {user_in.email}")
            await crud_user.create(db, obj_in=user_in)
        else:
            print(f"  - 测试用户已存在: {user_in.email}")
    
    # 创建前端模拟数据的用户
    print("\n创建前端模拟用户...")
    for user_data in MOCK_USERS:
        user = await crud_user.get_by_email(db, email=user_data["email"])
        if not user:
            print(f"  - 创建模拟用户: {user_data['email']}")
            user_in = UserCreate(
                email=user_data["email"],
                username=user_data["username"],
                password=user_data["password"],
                phone=user_data["phone"],
                avatar=user_data["avatar"],
                roles=user_data["roles"]
            )
            await crud_user.create(db, obj_in=user_in)
        else:
            print(f"  - 模拟用户已存在: {user_data['email']}")
    
    print("\n数据库初始化完成!")

def init_db(db: Session) -> None:
    """同步包装初始化数据库函数"""
    try:
        # 创建所有表
        print("创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("数据库表创建完成")
        
        # 运行异步初始化函数
        asyncio.run(init_db_async(db))
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        sys.exit(1)

def main():
    """脚本入口"""
    from app.db.base import SessionLocal
    db = SessionLocal()
    init_db(db)

if __name__ == "__main__":
    main() 