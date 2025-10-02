#!/usr/bin/env python3
"""
Dify API 连接测试脚本

用于验证与 Dify Agent 的通信是否正常

使用方法:
    python scripts/test_dify_connection.py --agent-id <agent_config_id>
    或
    python scripts/test_dify_connection.py --api-key <api_key> --base-url <base_url>
"""

import asyncio
import argparse
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ai.infrastructure.dify_agent_client import DifyAgentClient, DifyAgentClientFactory
from app.core.database import get_db
from app.ai.infrastructure.db.agent_config import AgentConfig as AgentConfigModel


async def test_direct_connection(api_key: str, base_url: str):
    """直接测试 Dify API 连接"""
    print("=" * 80)
    print("🧪 Dify API 连接测试（直接模式）")
    print("=" * 80)
    print(f"Base URL: {base_url}")
    print(f"API Key: {'*' * 20}...{api_key[-8:] if len(api_key) > 8 else '***'}")
    print()
    
    client = DifyAgentClient(api_key=api_key, base_url=base_url)
    
    # 测试消息
    test_message = "你好，这是一条测试消息，请简短回复。"
    test_user = "test_user_12345"
    
    print(f"📝 测试消息: {test_message}")
    print(f"👤 用户标识: {test_user}")
    print()
    print("🚀 开始流式对话...")
    print("-" * 80)
    
    try:
        chunk_count = 0
        message_parts = []
        conversation_id = None
        
        async for chunk in client.stream_chat(
            message=test_message,
            user=test_user,
            conversation_id=None
        ):
            chunk_count += 1
            chunk_str = chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk
            
            # 打印前 5 个 chunk
            if chunk_count <= 5:
                print(f"📦 Chunk {chunk_count}: {chunk_str[:200]}")
            
            # 解析消息内容
            if chunk_str.startswith('data: '):
                try:
                    import json
                    data = json.loads(chunk_str[6:])
                    event_type = data.get('event')
                    
                    if event_type == 'message':
                        answer = data.get('answer', '')
                        if answer:
                            message_parts.append(answer)
                    
                    if data.get('conversation_id') and not conversation_id:
                        conversation_id = data.get('conversation_id')
                        print(f"✅ 获得 conversation_id: {conversation_id}")
                    
                    if event_type == 'message_end':
                        print(f"✅ 消息结束事件")
                        metadata = data.get('metadata', {})
                        usage = metadata.get('usage', {})
                        if usage:
                            print(f"📊 Token 使用:")
                            print(f"   - prompt_tokens: {usage.get('prompt_tokens')}")
                            print(f"   - completion_tokens: {usage.get('completion_tokens')}")
                            print(f"   - total_tokens: {usage.get('total_tokens')}")
                    
                    if event_type == 'error':
                        print(f"❌ 错误事件: {data.get('message')}")
                        
                except json.JSONDecodeError:
                    pass
        
        print("-" * 80)
        print(f"✅ 流式对话完成")
        print(f"   总 chunks: {chunk_count}")
        print(f"   conversation_id: {conversation_id}")
        print()
        
        if message_parts:
            full_message = ''.join(message_parts)
            print("💬 完整回复:")
            print("-" * 80)
            print(full_message)
            print("-" * 80)
        
        print()
        print("🎉 测试成功！")
        return True
        
    except Exception as e:
        print()
        print("❌ 测试失败！")
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_from_database(agent_config_id: str):
    """从数据库加载配置并测试"""
    print("=" * 80)
    print("🧪 Dify API 连接测试（数据库模式）")
    print("=" * 80)
    print(f"Agent Config ID: {agent_config_id}")
    print()
    
    db = next(get_db())
    try:
        # 从数据库加载配置
        agent_config = db.query(AgentConfigModel).filter(
            AgentConfigModel.id == agent_config_id
        ).first()
        
        if not agent_config:
            print(f"❌ 未找到 Agent 配置: {agent_config_id}")
            return False
        
        print(f"✅ 找到 Agent 配置:")
        print(f"   名称: {agent_config.name}")
        print(f"   Base URL: {agent_config.base_url}")
        print(f"   启用: {agent_config.enabled}")
        print()
        
        if not agent_config.enabled:
            print(f"⚠️  警告: Agent 配置未启用")
        
        # 创建客户端
        factory = DifyAgentClientFactory()
        client = factory.create_client(agent_config)
        
        # 使用直接连接模式测试
        return await test_direct_connection(
            api_key=agent_config.api_key,
            base_url=agent_config.base_url
        )
        
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='测试 Dify API 连接')
    
    # 模式选择
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--agent-id', type=str, help='从数据库加载的 Agent Config ID')
    group.add_argument('--direct', action='store_true', help='使用直接连接模式')
    
    # 直接连接参数
    parser.add_argument('--api-key', type=str, help='Dify API Key（直接模式）')
    parser.add_argument('--base-url', type=str, help='Dify Base URL（直接模式）')
    
    args = parser.parse_args()
    
    if args.agent_id:
        # 数据库模式
        result = asyncio.run(test_from_database(args.agent_id))
    elif args.direct:
        # 直接连接模式
        if not args.api_key or not args.base_url:
            print("❌ 直接模式需要 --api-key 和 --base-url 参数")
            sys.exit(1)
        result = asyncio.run(test_direct_connection(args.api_key, args.base_url))
    
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()

