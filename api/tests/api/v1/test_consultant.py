import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, List
import uuid
from datetime import datetime

from app.core.config import get_settings
from main import app

settings = get_settings()


@pytest.fixture
def test_customer_data():
    """测试客户数据 - 使用数据库中真实存在的客户"""
    return {
        "id": "usr_26523bbee44b4ea3ace34ea4bc8526f8",  # 使用真实的客户ID
        "name": "李小姐",  # 使用真实的客户姓名
        "age": 28,
        "gender": "female",
        "concerns": ["面部紧致", "抗衰老"],
        "budget": 50000.0
    }


@pytest.fixture
def test_plan_create_data(test_customer_data):
    """创建方案测试数据"""
    return {
        "customer_id": test_customer_data["id"],
        "customer_name": test_customer_data["name"],
        "customer_profile": {
            "age": test_customer_data["age"],
            "gender": test_customer_data["gender"],
            "concerns": test_customer_data["concerns"],
            "budget": test_customer_data["budget"],
            "expected_results": "希望看起来更年轻"
        },
        "projects": [
            {
                "id": str(uuid.uuid4()),
                "name": "面部提升术",
                "description": "通过手术方式改善面部松弛",
                "cost": 25000.0,
                "duration": "2-3小时",
                "recovery_time": "2-3周",
                "expected_results": "面部紧致度提升60%",
                "risks": ["肿胀", "疼痛", "感染风险"]
            }
        ],
        "estimated_timeframe": "1个月",
        "notes": "客户对手术接受度较高"
    }


@pytest.fixture
def test_plan_update_data():
    """更新方案测试数据"""
    return {
        "status": "SHARED",  # 修改为大写，与数据库枚举一致
        "notes": "已与客户分享方案，等待反馈",
        "estimated_timeframe": "6周"
    }


@pytest.fixture
def test_recommendation_request_data(test_customer_data):
    """推荐请求测试数据"""
    return {
        "customer_id": test_customer_data["id"],
        "customer_profile": {
            "age": test_customer_data["age"],
            "gender": test_customer_data["gender"],
            "concerns": test_customer_data["concerns"],
            "budget": test_customer_data["budget"],
            "expected_results": "面部年轻化"
        },
        "preferences": {
            "risk_tolerance": "medium",
            "recovery_time_preference": "moderate"
        }
    }


async def get_auth_headers(async_client: AsyncClient, test_user: Dict[str, str]) -> Dict[str, str]:
    """获取认证头信息"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    response = await async_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_all_plans(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试获取所有个性化方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/plans",
        headers=headers
    )
    
    assert response.status_code == 200
    plans = response.json()
    assert isinstance(plans, list)


@pytest.mark.asyncio
async def test_get_all_plans_with_consultant_filter(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试根据顾问ID筛选方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/plans?consultant_id=test-consultant-id",
        headers=headers
    )
    
    assert response.status_code == 200
    plans = response.json()
    assert isinstance(plans, list)


@pytest.mark.asyncio
async def test_create_plan_success(async_client: AsyncClient, test_user: Dict[str, str], test_plan_create_data: Dict):
    """测试成功创建个性化方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultant/plans",
        json=test_plan_create_data,
        headers=headers
    )
    
    assert response.status_code == 200
    plan = response.json()
    assert plan["customer_id"] == test_plan_create_data["customer_id"]
    assert plan["customer_name"] == test_plan_create_data["customer_name"]
    assert plan["status"] == "DRAFT"
    assert "id" in plan
    assert "created_at" in plan
    
    # 保存创建的方案ID，供后续测试使用
    return plan["id"]


@pytest.mark.asyncio
async def test_create_plan_invalid_data(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试使用无效数据创建方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    invalid_data = {
        "customer_name": "",  # 空名称
        "projects": []
    }
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultant/plans",
        json=invalid_data,
        headers=headers
    )
    
    assert response.status_code == 422  # 验证错误


@pytest.mark.asyncio
async def test_get_plan_by_id_success(async_client: AsyncClient, test_user: Dict[str, str], test_plan_create_data: Dict):
    """测试根据ID获取方案详情"""
    headers = await get_auth_headers(async_client, test_user)
    
    # 先创建一个方案
    create_response = await async_client.post(
        f"{settings.API_V1_STR}/consultant/plans",
        json=test_plan_create_data,
        headers=headers
    )
    assert create_response.status_code == 200
    plan_id = create_response.json()["id"]
    
    # 获取方案详情
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/plans/{plan_id}",
        headers=headers
    )
    
    assert response.status_code == 200
    plan = response.json()
    assert plan["id"] == plan_id
    assert plan["customer_name"] == test_plan_create_data["customer_name"]


@pytest.mark.asyncio
async def test_get_plan_by_id_not_found(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试获取不存在的方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    non_existent_id = str(uuid.uuid4())
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/plans/{non_existent_id}",
        headers=headers
    )
    
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_customer_plans(async_client: AsyncClient, test_user: Dict[str, str], test_plan_create_data: Dict):
    """测试获取客户的所有方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    # 先创建一个方案
    create_response = await async_client.post(
        f"{settings.API_V1_STR}/consultant/plans",
        json=test_plan_create_data,
        headers=headers
    )
    assert create_response.status_code == 200
    
    customer_id = test_plan_create_data["customer_id"]
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/customers/{customer_id}/plans",
        headers=headers
    )
    
    assert response.status_code == 200
    plans = response.json()
    assert isinstance(plans, list)


@pytest.mark.asyncio
async def test_update_plan_success(async_client: AsyncClient, test_user: Dict[str, str], test_plan_create_data: Dict, test_plan_update_data: Dict):
    """测试成功更新方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    # 先创建一个方案
    create_response = await async_client.post(
        f"{settings.API_V1_STR}/consultant/plans",
        json=test_plan_create_data,
        headers=headers
    )
    assert create_response.status_code == 200
    plan_id = create_response.json()["id"]
    
    # 更新方案
    response = await async_client.put(
        f"{settings.API_V1_STR}/consultant/plans/{plan_id}",
        json=test_plan_update_data,
        headers=headers
    )
    
    assert response.status_code == 200
    updated_plan = response.json()
    assert updated_plan["id"] == plan_id
    assert updated_plan["status"] == test_plan_update_data["status"]
    assert updated_plan["notes"] == test_plan_update_data["notes"]


@pytest.mark.asyncio
async def test_update_plan_not_found(async_client: AsyncClient, test_user: Dict[str, str], test_plan_update_data: Dict):
    """测试更新不存在的方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    non_existent_id = str(uuid.uuid4())
    response = await async_client.put(
        f"{settings.API_V1_STR}/consultant/plans/{non_existent_id}",
        json=test_plan_update_data,
        headers=headers
    )
    
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_plan_success(async_client: AsyncClient, test_user: Dict[str, str], test_plan_create_data: Dict):
    """测试成功删除方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    # 先创建一个方案
    create_response = await async_client.post(
        f"{settings.API_V1_STR}/consultant/plans",
        json=test_plan_create_data,
        headers=headers
    )
    assert create_response.status_code == 200
    plan_id = create_response.json()["id"]
    
    # 删除方案
    response = await async_client.delete(
        f"{settings.API_V1_STR}/consultant/plans/{plan_id}",
        headers=headers
    )
    
    assert response.status_code == 200
    assert "删除成功" in response.json()["message"]
    
    # 验证方案已被删除
    get_response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/plans/{plan_id}",
        headers=headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_plan_not_found(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试删除不存在的方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    non_existent_id = str(uuid.uuid4())
    response = await async_client.delete(
        f"{settings.API_V1_STR}/consultant/plans/{non_existent_id}",
        headers=headers
    )
    
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_project_types(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试获取项目类型"""
    headers = await get_auth_headers(async_client, test_user)
    
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/project-types",
        headers=headers
    )
    
    assert response.status_code == 200
    project_types = response.json()
    assert isinstance(project_types, list)


@pytest.mark.asyncio
async def test_get_project_types_inactive_included(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试获取项目类型（包含非激活的）"""
    headers = await get_auth_headers(async_client, test_user)
    
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/project-types?active_only=false",
        headers=headers
    )
    
    assert response.status_code == 200
    project_types = response.json()
    assert isinstance(project_types, list)


@pytest.mark.asyncio
async def test_get_project_templates(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试获取项目模板"""
    headers = await get_auth_headers(async_client, test_user)
    
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/project-templates",
        headers=headers
    )
    
    assert response.status_code == 200
    templates = response.json()
    assert isinstance(templates, list)


@pytest.mark.asyncio
async def test_get_project_templates_by_category(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试根据分类获取项目模板"""
    headers = await get_auth_headers(async_client, test_user)
    
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/project-templates?category=面部整形",
        headers=headers
    )
    
    assert response.status_code == 200
    templates = response.json()
    assert isinstance(templates, list)


@pytest.mark.asyncio
async def test_generate_recommendations_success(async_client: AsyncClient, test_user: Dict[str, str], test_recommendation_request_data: Dict):
    """测试成功生成推荐方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultant/recommendations",
        json=test_recommendation_request_data,
        headers=headers
    )
    
    assert response.status_code == 200
    recommendation = response.json()
    assert "recommended_projects" in recommendation
    assert "total_estimated_cost" in recommendation
    assert "confidence_score" in recommendation
    assert "reasoning" in recommendation
    assert isinstance(recommendation["recommended_projects"], list)
    assert isinstance(recommendation["total_estimated_cost"], (int, float))
    assert 0 <= recommendation["confidence_score"] <= 1


@pytest.mark.asyncio
async def test_generate_recommendations_invalid_data(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试使用无效数据生成推荐"""
    headers = await get_auth_headers(async_client, test_user)
    
    invalid_request = {
        "customer_id": "",  # 空ID
        "customer_profile": {}  # 空档案
    }
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultant/recommendations",
        json=invalid_request,
        headers=headers
    )
    
    assert response.status_code == 422  # 验证错误


@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    """测试未授权访问"""
    # 不提供认证头信息
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/plans"
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_access(async_client: AsyncClient):
    """测试使用无效token访问"""
    headers = {"Authorization": "Bearer invalid_token"}
    
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/plans",
        headers=headers
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio 
async def test_create_plan_with_complex_profile(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试创建包含复杂客户档案的方案"""
    headers = await get_auth_headers(async_client, test_user)
    
    complex_plan_data = {
        "customer_id": "usr_26523bbee44b4ea3ace34ea4bc8526f8",  # 使用真实客户ID
        "customer_name": "李小姐",  # 使用真实客户姓名
        "customer_profile": {
            "age": 35,
            "gender": "female",
            "concerns": ["皱纹", "松弛", "色斑", "毛孔粗大"],
            "budget": 80000.0,
            "expected_results": "全面年轻化改善"
        },
        "projects": [
            {
                "id": str(uuid.uuid4()),
                "name": "光子嫩肤",
                "description": "改善肌肤质地和色斑",
                "cost": 15000.0,
                "duration": "1小时",
                "recovery_time": "1周",
                "expected_results": "肌肤亮白，色斑淡化50%",
                "risks": ["轻微红肿", "干燥"]
            },
            {
                "id": str(uuid.uuid4()),
                "name": "热玛吉紧致",
                "description": "射频紧致提升",
                "cost": 35000.0,
                "duration": "2小时",
                "recovery_time": "无",
                "expected_results": "皮肤紧致度提升40%",
                "risks": ["疼痛", "轻微肿胀"]
            }
        ],
        "estimated_timeframe": "3个月",
        "notes": "建议分两次进行，间隔1个月"
    }
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultant/plans",
        json=complex_plan_data,
        headers=headers
    )
    
    assert response.status_code == 200
    plan = response.json()
    assert len(plan["projects"]) == 2
    assert plan["total_cost"] == 50000.0  # 15000 + 35000
    assert plan["customer_profile"]["concerns"] == complex_plan_data["customer_profile"]["concerns"]


@pytest.mark.asyncio
async def test_plan_status_workflow(async_client: AsyncClient, test_user: Dict[str, str], test_plan_create_data: Dict):
    """测试方案状态流转工作流"""
    headers = await get_auth_headers(async_client, test_user)
    
    # 1. 创建方案（draft状态）
    create_response = await async_client.post(
        f"{settings.API_V1_STR}/consultant/plans",
        json=test_plan_create_data,
        headers=headers
    )
    assert create_response.status_code == 200
    plan_id = create_response.json()["id"]
    assert create_response.json()["status"] == "DRAFT"
    
    # 2. 分享方案（shared状态）
    share_update = {"status": "SHARED", "notes": "已发送给客户"}
    share_response = await async_client.put(
        f"{settings.API_V1_STR}/consultant/plans/{plan_id}",
        json=share_update,
        headers=headers
    )
    assert share_response.status_code == 200
    assert share_response.json()["status"] == "SHARED"
    
    # 3. 客户接受方案（accepted状态）
    accept_update = {"status": "ACCEPTED", "notes": "客户已接受方案"}
    accept_response = await async_client.put(
        f"{settings.API_V1_STR}/consultant/plans/{plan_id}",
        json=accept_update,
        headers=headers
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == "ACCEPTED"


@pytest.mark.asyncio
async def test_bulk_operations_consistency(async_client: AsyncClient, test_user: Dict[str, str], test_plan_create_data: Dict):
    """测试批量操作的数据一致性"""
    headers = await get_auth_headers(async_client, test_user)
    
    # 创建多个方案
    plan_ids = []
    for i in range(3):
        plan_data = test_plan_create_data.copy()
        plan_data["customer_name"] = f"测试客户{i+1}"  # 只修改客户姓名，保持相同的customer_id
        
        response = await async_client.post(
            f"{settings.API_V1_STR}/consultant/plans",
            json=plan_data,
            headers=headers
        )
        assert response.status_code == 200
        plan_ids.append(response.json()["id"])
    
    # 验证所有方案都能正确获取
    all_plans_response = await async_client.get(
        f"{settings.API_V1_STR}/consultant/plans",
        headers=headers
    )
    assert all_plans_response.status_code == 200
    all_plans = all_plans_response.json()
    
    # 验证创建的方案都在列表中
    created_plan_ids = [plan["id"] for plan in all_plans if plan["id"] in plan_ids]
    assert len(created_plan_ids) == 3 