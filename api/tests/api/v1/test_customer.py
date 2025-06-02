"""
客户端点测试 - 全面的功能和权限测试
"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, Generator, List
from httpx import AsyncClient
import pytest_asyncio
from datetime import datetime
import uuid

from app.db.models.user import User, Role
from app.db.models.customer import Customer, CustomerProfile
from app.services import user_service
from app.core.security import create_access_token
from app.schemas.user import UserCreate
from app.schemas.customer import CustomerProfileCreate, CustomerProfileUpdate, RiskNote
from app.db.uuid_utils import profile_id, customer_id

# === 测试数据固定装置 ===

def unique_email(base_email: str) -> str:
    """生成唯一邮箱地址"""
    unique_id = str(uuid.uuid4())[:8]
    name, domain = base_email.split('@')
    return f"{name}_{unique_id}@{domain}"

def unique_phone(base_phone: str) -> str:
    """生成唯一电话号码"""
    unique_suffix = str(uuid.uuid4().int)[:4]
    return f"{base_phone[:-4]}{unique_suffix}"

@pytest_asyncio.fixture
async def admin_user_data() -> Dict:
    """管理员测试数据"""
    return {
        "email": unique_email("admin@example.com"),
        "username": "管理员",
        "password": "Admin123456!",
        "roles": ["admin"]
    }

@pytest_asyncio.fixture
async def consultant_user_data() -> Dict:
    """顾问测试数据"""
    return {
        "email": unique_email("consultant@example.com"),
        "username": "测试顾问",
        "password": "Consultant123!",
        "roles": ["consultant"]
    }

@pytest_asyncio.fixture
async def doctor_user_data() -> Dict:
    """医生测试数据"""
    return {
        "email": unique_email("doctor@example.com"),
        "username": "测试医生",
        "password": "Doctor123!",
        "roles": ["doctor"]
    }

@pytest_asyncio.fixture
async def customer_user_data() -> Dict:
    """客户测试数据"""
    return {
        "email": unique_email("customer@example.com"),
        "username": "测试客户",
        "password": "Customer123!",
        "phone": unique_phone("13800138000"),
        "roles": ["customer"]
    }

@pytest_asyncio.fixture
async def another_customer_data() -> Dict:
    """另一个客户测试数据"""
    return {
        "email": unique_email("customer2@example.com"),
        "username": "客户2",
        "password": "Customer123!",
        "phone": unique_phone("13800138001"),
        "roles": ["customer"]
    }

# === Token 固定装置 ===

@pytest_asyncio.fixture
async def admin_token(db: Session, admin_user_data: Dict) -> str:
    """创建管理员用户并返回token"""
    admin_in = UserCreate(**admin_user_data)
    admin = await user_service.create(db, obj_in=admin_in)
    return create_access_token(admin.id)

@pytest_asyncio.fixture
async def consultant_token(db: Session, consultant_user_data: Dict) -> str:
    """创建顾问用户并返回token"""
    consultant_in = UserCreate(**consultant_user_data)
    consultant = await user_service.create(db, obj_in=consultant_in)
    return create_access_token(consultant.id)

@pytest_asyncio.fixture
async def doctor_token(db: Session, doctor_user_data: Dict) -> str:
    """创建医生用户并返回token"""
    doctor_in = UserCreate(**doctor_user_data)
    doctor = await user_service.create(db, obj_in=doctor_in)
    return create_access_token(doctor.id)

@pytest_asyncio.fixture
async def customer_token(db: Session, customer_user_data: Dict) -> str:
    """创建客户用户并返回token"""
    customer_in = UserCreate(**customer_user_data)
    customer = await user_service.create(db, obj_in=customer_in)
    return create_access_token(customer.id)

@pytest_asyncio.fixture
async def another_customer_token(db: Session, another_customer_data: Dict) -> str:
    """创建另一个客户用户并返回token"""
    customer_in = UserCreate(**another_customer_data)
    customer = await user_service.create(db, obj_in=customer_in)
    return create_access_token(customer.id)

# === 客户数据固定装置 ===

@pytest_asyncio.fixture
async def customer_with_profile(db: Session, customer_user_data: Dict, customer_token: str) -> Dict:
    """创建带档案的客户"""
    # 获取刚创建的客户用户（通过邮箱查找）
    customer_user = db.query(User).filter(User.email == customer_user_data["email"]).first()
    
    # 创建Customer记录
    customer = Customer(
        id=customer_id(),
        user_id=customer_user.id,
        medical_history="无特殊病史",
        allergies="花粉过敏",
        preferences="偏好中医治疗"
    )
    db.add(customer)
    
    # 创建CustomerProfile记录
    profile = CustomerProfile(
        id=profile_id(),
        customer_id=customer_user.id,
        medical_history="详细病史记录",
        allergies="花粉、海鲜过敏",
        preferences="偏好中医治疗，不喜欢西药",
        tags="VIP,高血压",
        risk_notes=[
            {"type": "血压", "description": "高血压需要定期监测", "level": "medium"},
            {"type": "过敏", "description": "对海鲜严重过敏", "level": "high"}
        ]
    )
    db.add(profile)
    db.commit()
    
    return {
        "customer_id": customer_user.id,
        "customer": customer,
        "profile": profile,
        "token": customer_token
    }

@pytest_asyncio.fixture
async def multiple_customers(db: Session, customer_user_data: Dict, another_customer_data: Dict, consultant_token: str, customer_token: str, another_customer_token: str) -> List[Dict]:
    """创建多个客户用于列表测试"""
    customers_data = []
    
    # 创建第一个客户
    customer1 = db.query(User).filter(User.email == customer_user_data["email"]).first()
    
    customer_entity1 = Customer(
        id=customer_id(),
        user_id=customer1.id,
        medical_history="高血压病史",
        allergies="无",
        preferences="偏好中医"
    )
    db.add(customer_entity1)
    
    # 创建第二个客户
    customer2 = db.query(User).filter(User.email == another_customer_data["email"]).first()
    
    customer_entity2 = Customer(
        id=customer_id(),
        user_id=customer2.id,
        medical_history="糖尿病病史",
        allergies="花粉",
        preferences="偏好西医"
    )
    db.add(customer_entity2)
    
    db.commit()
    
    return [
        {"user": customer1, "customer": customer_entity1},
        {"user": customer2, "customer": customer_entity2}
    ]

# === 客户列表测试 ===

@pytest.mark.asyncio
async def test_get_customers_as_consultant(async_client: AsyncClient, consultant_token: str, multiple_customers: List[Dict]):
    """测试顾问获取客户列表"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    
    response = await async_client.get(
        "/api/v1/customers/",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    
    # 验证返回数据结构
    customer = data[0]
    assert "id" in customer
    assert "name" in customer
    assert "avatar" in customer
    assert "is_online" in customer
    assert "last_message" in customer
    assert "unread_count" in customer
    assert "tags" in customer
    assert "priority" in customer
    assert "updated_at" in customer

@pytest.mark.asyncio
async def test_get_customers_as_doctor(async_client: AsyncClient, doctor_token: str, multiple_customers: List[Dict]):
    """测试医生获取客户列表"""
    headers = {"Authorization": f"Bearer {doctor_token}"}
    
    response = await async_client.get(
        "/api/v1/customers/",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_customers_as_admin(async_client: AsyncClient, admin_token: str, multiple_customers: List[Dict]):
    """测试管理员获取客户列表"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = await async_client.get(
        "/api/v1/customers/",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_customers_as_customer_forbidden(async_client: AsyncClient, customer_token: str):
    """测试客户用户无权访问客户列表"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    response = await async_client.get(
        "/api/v1/customers/",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "无权访问客户列表" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_customers_with_pagination(async_client: AsyncClient, consultant_token: str, multiple_customers: List[Dict]):
    """测试客户列表分页"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    
    response = await async_client.get(
        "/api/v1/customers/?skip=0&limit=1",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 1

@pytest.mark.asyncio
async def test_get_customers_invalid_pagination(async_client: AsyncClient, consultant_token: str):
    """测试无效的分页参数"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    
    # 测试负数skip
    response = await async_client.get(
        "/api/v1/customers/?skip=-1",
        headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # 测试超大limit
    response = await async_client.get(
        "/api/v1/customers/?limit=101",
        headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# === 客户详情测试 ===

@pytest.mark.asyncio
async def test_get_customer_as_consultant(async_client: AsyncClient, consultant_token: str, customer_with_profile: Dict):
    """测试顾问获取客户详情"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    response = await async_client.get(
        f"/api/v1/customers/{customer_id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_id"] == customer_id
    assert "username" in data
    assert "email" in data
    assert "medical_history" in data
    assert "allergies" in data
    assert "preferences" in data

@pytest.mark.asyncio
async def test_get_customer_self(async_client: AsyncClient, customer_with_profile: Dict):
    """测试客户获取自己的信息"""
    headers = {"Authorization": f"Bearer {customer_with_profile['token']}"}
    customer_id = customer_with_profile["customer_id"]
    
    response = await async_client.get(
        f"/api/v1/customers/{customer_id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_id"] == customer_id

@pytest.mark.asyncio
async def test_get_customer_other_customer_forbidden(async_client: AsyncClient, another_customer_token: str, customer_with_profile: Dict):
    """测试客户无权访问其他客户信息"""
    headers = {"Authorization": f"Bearer {another_customer_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    response = await async_client.get(
        f"/api/v1/customers/{customer_id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "无权访问此客户信息" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_customer_not_found(async_client: AsyncClient, consultant_token: str):
    """测试获取不存在的客户"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    
    response = await async_client.get(
        "/api/v1/customers/nonexistent",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "客户不存在" in response.json()["detail"]

# === 客户档案测试 ===

@pytest.mark.asyncio
async def test_get_customer_profile_as_consultant(async_client: AsyncClient, consultant_token: str, customer_with_profile: Dict):
    """测试顾问获取客户档案"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    response = await async_client.get(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert "basicInfo" in data
    assert "medical_history" in data
    assert "allergies" in data
    assert "preferences" in data
    assert "tags" in data
    assert "riskNotes" in data
    assert isinstance(data["tags"], list)
    assert isinstance(data["riskNotes"], list)

@pytest.mark.asyncio
async def test_get_customer_profile_self(async_client: AsyncClient, customer_with_profile: Dict):
    """测试客户获取自己的档案"""
    headers = {"Authorization": f"Bearer {customer_with_profile['token']}"}
    customer_id = customer_with_profile["customer_id"]
    
    response = await async_client.get(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "basicInfo" in data
    assert data["basicInfo"]["name"] is not None

@pytest.mark.asyncio
async def test_get_customer_profile_forbidden(async_client: AsyncClient, another_customer_token: str, customer_with_profile: Dict):
    """测试无权访问其他客户档案"""
    headers = {"Authorization": f"Bearer {another_customer_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    response = await async_client.get(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "无权访问客户档案" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_customer_profile_not_found(async_client: AsyncClient, consultant_token: str):
    """测试获取不存在客户的档案"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    
    response = await async_client.get(
        "/api/v1/customers/nonexistent/profile",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "客户不存在" in response.json()["detail"]

# === 创建客户档案测试 ===

@pytest.mark.asyncio
async def test_create_customer_profile_as_consultant(async_client: AsyncClient, consultant_token: str, db: Session):
    """测试顾问创建客户档案"""
    # 先创建一个没有档案的客户
    customer_data = {
        "email": "newcustomer@test.com",
        "username": "新客户",
        "password": "Customer123!",
        "roles": ["customer"]
    }
    customer_in = UserCreate(**customer_data)
    customer_user = await user_service.create(db, obj_in=customer_in)
    
    # 创建Customer记录
    customer = Customer(
        id=customer_id(),
        user_id=customer_user.id,
        medical_history="无",
        allergies="无",
        preferences="无"
    )
    db.add(customer)
    db.commit()
    
    headers = {"Authorization": f"Bearer {consultant_token}"}
    profile_data = {
        "medical_history": "高血压病史3年",
        "allergies": "青霉素过敏",
        "preferences": "偏好中医治疗",
        "tags": "VIP,高血压"
    }
    
    response = await async_client.post(
        f"/api/v1/customers/{customer_user.id}/profile",
        headers=headers,
        json=profile_data
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["medical_history"] == profile_data["medical_history"]
    assert data["allergies"] == profile_data["allergies"]
    assert data["preferences"] == profile_data["preferences"]
    assert "VIP" in data["tags"]
    assert "高血压" in data["tags"]

@pytest.mark.asyncio
async def test_create_customer_profile_already_exists(async_client: AsyncClient, consultant_token: str, customer_with_profile: Dict):
    """测试创建已存在的客户档案"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    profile_data = {
        "medical_history": "新的病史",
        "allergies": "新的过敏",
        "preferences": "新的偏好",
        "tags": "新标签"
    }
    
    response = await async_client.post(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers,
        json=profile_data
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "客户档案已存在" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_customer_profile_customer_not_found(async_client: AsyncClient, consultant_token: str):
    """测试为不存在的客户创建档案"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    
    profile_data = {
        "medical_history": "病史",
        "allergies": "过敏",
        "preferences": "偏好",
        "tags": "标签"
    }
    
    response = await async_client.post(
        "/api/v1/customers/nonexistent/profile",
        headers=headers,
        json=profile_data
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "客户不存在" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_customer_profile_forbidden(async_client: AsyncClient, another_customer_token: str, customer_with_profile: Dict):
    """测试无权限创建客户档案"""
    headers = {"Authorization": f"Bearer {another_customer_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    profile_data = {
        "medical_history": "病史",
        "allergies": "过敏",
        "preferences": "偏好",
        "tags": "标签"
    }
    
    response = await async_client.post(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers,
        json=profile_data
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "无权创建客户档案" in response.json()["detail"]

# === 更新客户档案测试 ===

@pytest.mark.asyncio
async def test_update_customer_profile_as_consultant(async_client: AsyncClient, consultant_token: str, customer_with_profile: Dict):
    """测试顾问更新客户档案"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    update_data = {
        "medical_history": "更新的病史信息",
        "allergies": "更新的过敏信息",
        "preferences": "更新的偏好信息",
        "tags": "VIP,高血压,糖尿病",
        "risk_notes": [
            {
                "type": "血压",
                "description": "高血压需要每日监测",
                "level": "high"
            },
            {
                "type": "血糖",
                "description": "血糖偏高需要注意饮食",
                "level": "medium"
            }
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers,
        json=update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["medical_history"] == update_data["medical_history"]
    assert data["allergies"] == update_data["allergies"]
    assert data["preferences"] == update_data["preferences"]
    assert "VIP" in data["tags"]
    assert "糖尿病" in data["tags"]
    assert len(data["riskNotes"]) == 2
    assert data["riskNotes"][0]["level"] == "high"

@pytest.mark.asyncio
async def test_update_customer_profile_self(async_client: AsyncClient, customer_with_profile: Dict):
    """测试客户更新自己的档案"""
    headers = {"Authorization": f"Bearer {customer_with_profile['token']}"}
    customer_id = customer_with_profile["customer_id"]
    
    update_data = {
        "preferences": "更新的个人偏好"
    }
    
    response = await async_client.put(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers,
        json=update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["preferences"] == update_data["preferences"]

@pytest.mark.asyncio
async def test_update_customer_profile_partial(async_client: AsyncClient, consultant_token: str, customer_with_profile: Dict):
    """测试部分更新客户档案"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    # 只更新医疗历史
    update_data = {
        "medical_history": "只更新医疗历史"
    }
    
    response = await async_client.put(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers,
        json=update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["medical_history"] == update_data["medical_history"]
    # 其他字段应该保持不变
    assert data["allergies"] is not None
    assert data["preferences"] is not None

@pytest.mark.asyncio
async def test_update_customer_profile_not_found(async_client: AsyncClient, consultant_token: str):
    """测试更新不存在的客户档案"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    
    update_data = {
        "medical_history": "更新的病史"
    }
    
    response = await async_client.put(
        "/api/v1/customers/nonexistent/profile",
        headers=headers,
        json=update_data
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "客户不存在" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_customer_profile_forbidden(async_client: AsyncClient, another_customer_token: str, customer_with_profile: Dict):
    """测试无权限更新客户档案"""
    headers = {"Authorization": f"Bearer {another_customer_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    update_data = {
        "medical_history": "尝试更新的病史"
    }
    
    response = await async_client.put(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers,
        json=update_data
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "无权更新客户档案" in response.json()["detail"]

# === 数据验证测试 ===

@pytest.mark.asyncio
async def test_create_profile_invalid_data(async_client: AsyncClient, consultant_token: str, db: Session):
    """测试创建档案时的数据验证"""
    # 创建一个测试客户
    customer_data = {
        "email": "validation@test.com",
        "username": "验证客户",
        "password": "Customer123!",
        "roles": ["customer"]
    }
    customer_in = UserCreate(**customer_data)
    customer_user = await user_service.create(db, obj_in=customer_in)
    
    customer = Customer(
        id=customer_id(),
        user_id=customer_user.id,
        medical_history="无",
        allergies="无",
        preferences="无"
    )
    db.add(customer)
    db.commit()
    
    headers = {"Authorization": f"Bearer {consultant_token}"}
    
    # 测试空的医疗历史（应该允许）
    profile_data = {
        "medical_history": "",
        "allergies": "无",
        "preferences": "无",
        "tags": ""
    }
    
    response = await async_client.post(
        f"/api/v1/customers/{customer_user.id}/profile",
        headers=headers,
        json=profile_data
    )
    
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.asyncio
async def test_update_profile_invalid_risk_notes(async_client: AsyncClient, consultant_token: str, customer_with_profile: Dict):
    """测试更新档案时的风险提示验证"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    # 测试无效的风险等级
    update_data = {
        "risk_notes": [
            {
                "type": "血压",
                "description": "高血压",
                "level": "invalid_level"  # 无效等级
            }
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers,
        json=update_data
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# === 权限边界测试 ===

@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    """测试未授权访问"""
    # 不带token的请求
    response = await async_client.get("/api/v1/customers/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_invalid_token_access(async_client: AsyncClient):
    """测试无效token访问"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = await async_client.get("/api/v1/customers/", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# === 性能和边界测试 ===

@pytest.mark.asyncio
async def test_large_profile_data(async_client: AsyncClient, consultant_token: str, customer_with_profile: Dict):
    """测试大量数据的档案更新"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    customer_id = customer_with_profile["customer_id"]
    
    # 创建大量标签和风险提示
    large_tags = ",".join([f"标签{i}" for i in range(50)])
    large_risk_notes = [
        {
            "type": f"风险类型{i}",
            "description": f"这是风险描述{i}" * 10,  # 较长的描述
            "level": "medium"
        }
        for i in range(10)
    ]
    
    update_data = {
        "medical_history": "详细的医疗历史" * 100,  # 长文本
        "allergies": "详细的过敏信息" * 50,
        "preferences": "详细的偏好信息" * 50,
        "tags": large_tags,
        "risk_notes": large_risk_notes
    }
    
    response = await async_client.put(
        f"/api/v1/customers/{customer_id}/profile",
        headers=headers,
        json=update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tags"]) == 50
    assert len(data["riskNotes"]) == 10 