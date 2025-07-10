#!/usr/bin/env python3
"""
Dify集成测试脚本
测试Dify连接配置和Agent管理功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.base import get_db
from app.services.ai.dify_connection_service import DifyConnectionService
from app.services.ai.agent_manager import get_agent_manager
from app.db.models.system import AgentType


async def test_connection_and_sync(connection_service, conn):
    """测试连接并同步应用"""
    print(f"   测试连接 {conn.name}...")
    result = await connection_service.test_connection(conn.id)
    print(f"   {'✅ 连接成功' if result['success'] else '❌ 连接失败: ' + result['message']}")
    
    if result['success']:
        # 同步应用
        print(f"   同步应用...")
        sync_result = await connection_service.sync_apps(conn.id)
        if sync_result['success']:
            print(f"   ✅ 同步成功，发现 {len(sync_result['apps'])} 个应用")
            
            # 显示前3个应用
            for i, app in enumerate(sync_result['apps'][:3]):
                print(f"     {i+1}. {app['name']} ({app['mode']}) - {app['description'][:50]}...")
        else:
            print(f"   ❌ 同步失败: {sync_result['message']}")


async def test_agent_type(agent_manager, agent_type):
    """测试特定类型的Agent"""
    print(f"\n   测试 {agent_type.value} Agent:")
    agents = agent_manager.list_agents_by_type(agent_type)
    print(f"   📊 找到 {len(agents)} 个配置的Agent")
    
    for agent in agents:
        print(f"     - {agent['name']} ({'默认' if agent['is_default'] else '普通'}) - {agent['connection_name']}")
    
    # 尝试获取Agent实例
    agent_instance = agent_manager.get_agent_by_type(agent_type)
    if agent_instance:
        print(f"   ✅ 成功获取 {agent_type.value} Agent实例")
        
        # 测试健康检查
        health = await agent_instance.health_check()
        print(f"   {'✅ Agent健康检查通过' if health else '❌ Agent健康检查失败'}")
        
        if health:
            # 测试简单对话
            print(f"   💬 测试对话...")
            try:
                response = await agent_instance.generate_response("你好，请介绍一下你的功能", [])
                print(f"   ✅ 对话测试成功: {response.get('content', '')[:100]}...")
            except Exception as e:
                print(f"   ❌ 对话测试失败: {e}")
    else:
        print(f"   ⚠️  未找到可用的 {agent_type.value} Agent")

async def test_dify_integration():
    """测试Dify集成功能"""
    print("🚀 开始测试Dify集成功能...")
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 1. 测试Dify连接服务
        print("\n📡 测试Dify连接服务...")
        connection_service = DifyConnectionService(db)
        
        # 获取现有连接
        connections = connection_service.get_connections()
        print(f"✅ 当前有 {len(connections)} 个Dify连接")
        
        for conn in connections:
            print(f"   - {conn.name}: {conn.api_base_url} ({'默认' if conn.is_default else '普通'})")
            
            # 测试连接并同步应用
            await test_connection_and_sync(connection_service, conn)
        
        # 2. 测试Agent管理器
        print("\n🤖 测试Agent管理器...")
        agent_manager = get_agent_manager(db)
        
        # 测试各种Agent类型
        agent_types = [
            AgentType.GENERAL_CHAT,
            AgentType.BEAUTY_PLAN,
            AgentType.CONSULTATION,
            AgentType.CUSTOMER_SERVICE,
            AgentType.MEDICAL_ADVICE
        ]
        
        for agent_type in agent_types:
            await test_agent_type(agent_manager, agent_type)
        
        print("\n🎉 Dify集成测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def print_usage():
    """打印使用说明"""
    print("""
🔧 Dify集成测试工具

使用方法：
  python test_dify_integration.py

测试内容：
  1. Dify连接配置测试
  2. 应用同步测试
  3. Agent管理器测试
  4. Agent实例健康检查
  5. 简单对话测试

注意事项：
  - 确保数据库连接正常
  - 确保已配置Dify连接
  - 确保Dify服务可访问
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_usage()
    else:
        print("🧪 Dify集成功能测试")
        print("================")
        asyncio.run(test_dify_integration()) 