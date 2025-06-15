#!/usr/bin/env python3
import asyncio
import httpx
import json
import uuid

async def test_create_plan():
    """测试创建方案API"""
    
    # 登录获取token
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 登录
        login_data = {
            "username": "li@example.com",
            "password": "123456@Test"
        }
        
        login_response = await client.post("/api/v1/auth/login", data=login_data)
        print(f"登录状态: {login_response.status_code}")
        print(f"登录响应: {login_response.json()}")
        
        if login_response.status_code != 200:
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试数据
        test_plan_create_data = {
            "customer_id": str(uuid.uuid4()),
            "customer_name": "张小美",
            "customer_profile": {
                "age": 28,
                "gender": "female",
                "concerns": ["面部紧致", "抗衰老"],
                "budget": 50000.0,
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
        
        # 创建方案
        create_response = await client.post(
            "/api/v1/consultant/plans",
            json=test_plan_create_data,
            headers=headers
        )
        
        print(f"创建方案状态: {create_response.status_code}")
        print(f"创建方案响应: {create_response.text}")
        
        if create_response.status_code != 200:
            print(f"错误详情: {create_response.json()}")

if __name__ == "__main__":
    asyncio.run(test_create_plan()) 