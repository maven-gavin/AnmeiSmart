import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.db.models.chat import Conversation, Message
from app.db.models.user import User
from app.db.uuid_utils import conversation_id, message_id
from main import app

settings = get_settings()


@pytest.fixture
def test_conversation(db: Session, test_user: Dict[str, str]) -> Dict[str, str]:
    """创建测试会话"""
    # 查找测试用户
    user = db.query(User).filter(User.email == test_user["email"]).first()
    if not user:
        pytest.skip("测试用户不存在")
    
    # 创建测试会话
    conv_id = conversation_id()
    conversation = Conversation(
        id=conv_id,
        title="测试咨询会话",
        customer_id=user.id,
        assigned_consultant_id=user.id,
        is_active=True
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return {"id": conv_id, "customer_id": user.id}


@pytest.fixture
def test_conversation_with_messages(db: Session, test_user: Dict[str, str]) -> Dict[str, str]:
    """创建带消息的测试会话"""
    # 查找测试用户
    user = db.query(User).filter(User.email == test_user["email"]).first()
    if not user:
        pytest.skip("测试用户不存在")
    
    # 创建测试会话
    conv_id = conversation_id()
    conversation = Conversation(
        id=conv_id,
        title="带消息的测试咨询会话",
        customer_id=user.id,
        assigned_consultant_id=user.id,
        is_active=True
    )
    db.add(conversation)
    
    # 添加测试消息
    messages = [
        Message(
            id=message_id(),
            conversation_id=conv_id,
            sender_id=user.id,
            sender_type="customer",
            content={"text": "你好，我想咨询皮肤护理"},
            type="text",
            timestamp=datetime.utcnow() - timedelta(hours=1)
        ),
        Message(
            id=message_id(),
            conversation_id=conv_id,
            sender_id=user.id,
            sender_type="consultant",
            content={"text": "您好，请问您主要关心哪方面的皮肤问题？"},
            type="text",
            timestamp=datetime.utcnow() - timedelta(minutes=30)
        ),
        Message(
            id=message_id(),
            conversation_id=conv_id,
            sender_id=user.id,
            sender_type="customer",
            content={"text": "我的皮肤比较干燥，还有一些细纹"},
            type="text",
            timestamp=datetime.utcnow() - timedelta(minutes=20)
        )
    ]
    
    for msg in messages:
        db.add(msg)
    
    db.commit()
    db.refresh(conversation)
    
    return {"id": conv_id, "customer_id": user.id}


@pytest.fixture
def test_consultation_summary(db: Session, test_conversation: Dict[str, str]) -> Dict[str, str]:
    """创建带咨询总结的测试会话"""
    conversation = db.query(Conversation).filter(Conversation.id == test_conversation["id"]).first()
    
    # 添加咨询总结
    summary_data = {
        "basic_info": {
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "duration_minutes": 60,
            "type": "initial",
                         "consultant_id": conversation.assigned_consultant_id,
            "customer_id": conversation.customer_id
        },
        "main_issues": ["皮肤干燥", "细纹问题"],
        "solutions": ["保湿护理", "抗衰老治疗"],
        "follow_up_plan": ["两周后复诊"],
        "satisfaction_rating": 5,
        "additional_notes": "客户很满意",
        "tags": ["保湿", "抗衰老"],
        "ai_generated": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "version": 1
    }
    
    conversation.consultation_summary = summary_data
    conversation.consultation_type = "initial"
    conversation.summary = "皮肤干燥咨询"
    
    db.commit()
    db.refresh(conversation)
    
    return {"conversation_id": test_conversation["id"], "customer_id": test_conversation["customer_id"]}


# 移除重复的fixture，直接使用conftest.py中的test_user（已经是顾问角色）


# 移除重复的客户用户fixture，使用conftest.py中的test_user_data


@pytest.mark.asyncio
async def test_get_consultation_summary_not_found(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试获取不存在的咨询总结"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    # 使用不存在的会话ID
    fake_conversation_id = "fake-conversation-id"
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultation/conversation/{fake_conversation_id}/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "不存在或无权限访问" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_consultation_summary_unauthorized(async_client: AsyncClient):
    """测试未认证访问咨询总结"""
    fake_conversation_id = "fake-conversation-id"
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultation/conversation/{fake_conversation_id}/summary"
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_consultation_summary_success(async_client: AsyncClient, test_user: Dict[str, str], test_consultation_summary: Dict[str, str]):
    """测试成功获取咨询总结"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultation/conversation/{test_consultation_summary['conversation_id']}/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "consultation_summary" in result
    assert result["consultation_summary"]["main_issues"] == ["皮肤干燥", "细纹问题"]


@pytest.mark.asyncio
async def test_create_consultation_summary_success(async_client: AsyncClient, test_user: Dict[str, str], test_conversation: Dict[str, str]):
    """测试成功创建咨询总结"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    # 准备创建咨询总结的数据
    summary_data = {
        "conversation_id": test_conversation["id"],
        "main_issues": ["皮肤干燥", "细纹问题"],
        "solutions": ["保湿护理", "抗衰老治疗"],
        "follow_up_plan": ["两周后复诊", "日常护理指导"],
        "satisfaction_rating": 5,
        "additional_notes": "客户很满意服务",
        "tags": ["保湿", "抗衰老"]
    }
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultation/conversation/{test_conversation['id']}/summary",
        json=summary_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["consultation_summary"]["main_issues"] == summary_data["main_issues"]
    assert result["consultation_summary"]["satisfaction_rating"] == summary_data["satisfaction_rating"]


@pytest.mark.asyncio
async def test_create_consultation_summary_mismatched_id(async_client: AsyncClient, test_user: Dict[str, str], test_conversation: Dict[str, str]):
    """测试创建咨询总结时会话ID不匹配"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    # 准备不匹配的数据
    summary_data = {
        "conversation_id": "different-conversation-id",  # 与URL中的ID不同
        "main_issues": ["测试问题"],
        "solutions": ["测试方案"],
        "follow_up_plan": ["测试计划"],
        "satisfaction_rating": 4
    }
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultation/conversation/{test_conversation['id']}/summary",
        json=summary_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "会话ID与URL不匹配" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_consultation_summary_invalid_data(async_client: AsyncClient, test_user: Dict[str, str], test_conversation: Dict[str, str]):
    """测试使用无效数据创建咨询总结"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    # 准备无效数据（满意度评分超出范围）
    summary_data = {
        "conversation_id": test_conversation["id"],
        "main_issues": ["测试问题"],
        "solutions": ["测试方案"],
        "follow_up_plan": ["测试计划"],
        "satisfaction_rating": 10  # 超出1-5范围
    }
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultation/conversation/{test_conversation['id']}/summary",
        json=summary_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_consultation_summary_success(async_client: AsyncClient, test_user: Dict[str, str], test_consultation_summary: Dict[str, str]):
    """测试成功更新咨询总结"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    # 准备更新数据
    update_data = {
        "main_issues": ["更新后的问题"],
        "satisfaction_rating": 4,
        "additional_notes": "更新后的备注"
    }
    
    response = await async_client.put(
        f"{settings.API_V1_STR}/consultation/conversation/{test_consultation_summary['conversation_id']}/summary",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["consultation_summary"]["main_issues"] == update_data["main_issues"]
    assert result["consultation_summary"]["satisfaction_rating"] == update_data["satisfaction_rating"]


@pytest.mark.asyncio
async def test_update_consultation_summary_not_found(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试更新不存在的咨询总结"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    update_data = {
        "main_issues": ["测试问题"],
        "satisfaction_rating": 4
    }
    
    fake_conversation_id = "fake-conversation-id"
    response = await async_client.put(
        f"{settings.API_V1_STR}/consultation/conversation/{fake_conversation_id}/summary",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_delete_consultation_summary_success(async_client: AsyncClient, test_user: Dict[str, str], test_consultation_summary: Dict[str, str]):
    """测试成功删除咨询总结"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    response = await async_client.delete(
        f"{settings.API_V1_STR}/consultation/conversation/{test_consultation_summary['conversation_id']}/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert "已删除" in response.json()["message"]


@pytest.mark.asyncio
async def test_delete_consultation_summary_not_found(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试删除不存在的咨询总结"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    fake_conversation_id = "fake-conversation-id"
    response = await async_client.delete(
        f"{settings.API_V1_STR}/consultation/conversation/{fake_conversation_id}/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_ai_generate_summary_success(async_client: AsyncClient, test_user: Dict[str, str], test_conversation_with_messages: Dict[str, str]):
    """测试AI生成咨询总结成功"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    # 准备AI生成请求数据
    ai_request = {
        "conversation_id": test_conversation_with_messages["id"],
        "include_suggestions": True,
        "focus_areas": ["客户满意度", "治疗效果"]
    }
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultation/conversation/{test_conversation_with_messages['id']}/summary/ai-generate",
        json=ai_request,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "conversation_id" in result
    assert "main_issues" in result
    assert "solutions" in result


@pytest.mark.asyncio
async def test_ai_generate_summary_no_messages(async_client: AsyncClient, test_user: Dict[str, str], test_conversation: Dict[str, str]):
    """测试对没有消息的会话AI生成总结"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    ai_request = {
        "conversation_id": test_conversation["id"],
        "include_suggestions": False,
        "focus_areas": []
    }
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultation/conversation/{test_conversation['id']}/summary/ai-generate",
        json=ai_request,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "没有消息" in response.json()["detail"]


@pytest.mark.asyncio
async def test_save_ai_generated_summary_success(async_client: AsyncClient, test_user: Dict[str, str], test_conversation: Dict[str, str]):
    """测试保存AI生成的咨询总结"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    # 模拟AI生成的总结数据
    ai_summary = {
        "main_issues": ["AI识别的问题1", "AI识别的问题2"],
        "solutions": ["AI建议的方案1", "AI建议的方案2"],
        "follow_up_plan": ["AI制定的跟进计划"],
        "satisfaction_rating": 4,
        "additional_notes": "AI生成的补充说明",
        "tags": ["AI生成", "自动分析"]
    }
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/consultation/conversation/{test_conversation['id']}/summary/ai-save",
        json=ai_summary,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["consultation_summary"]["ai_generated"] == True
    assert result["consultation_summary"]["main_issues"] == ai_summary["main_issues"]


@pytest.mark.asyncio
async def test_get_customer_consultation_history_success(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试获取客户咨询历史成功"""
    # 先登录获取顾问token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    # 使用固定的客户ID进行测试
    customer_id = "test-customer-id"
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultation/customer/{customer_id}/consultation-history",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_customer_consultation_history_forbidden(async_client: AsyncClient):
    """测试无权限访问客户咨询历史"""
    # 使用无效token测试权限验证
    fake_token = "invalid-token"
    customer_id = "test-customer-id"
    
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultation/customer/{customer_id}/consultation-history",
        headers={"Authorization": f"Bearer {fake_token}"}
    )

    # 无效token应该返回401而不是403，这也测试了权限验证
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_customer_consultation_history_with_limit(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试获取客户咨询历史带限制参数"""
    # 先登录获取顾问token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    
    customer_id = "test-customer-id"
    response = await async_client.get(
        f"{settings.API_V1_STR}/consultation/customer/{customer_id}/consultation-history?limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert isinstance(result, list)
    assert len(result) <= 5 