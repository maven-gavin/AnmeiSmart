#!/usr/bin/env python3
"""
Dify API 原始请求测试

直接使用 httpx 发送请求，不依赖任何封装，用于最底层的调试

使用方法:
    python scripts/test_dify_raw.py
    
    然后根据提示输入:
    - Dify Base URL (例如: http://localhost/v1 或 https://api.dify.ai/v1)
    - API Key
    - 测试消息（可选，默认: "你好"）
"""

import asyncio
import httpx
import json
import sys


async def test_raw_dify_api():
    """最原始的 Dify API 测试"""
    print("=" * 80)
    print("🧪 Dify API 原始请求测试")
    print("=" * 80)
    print()
    
    # 交互式输入
    base_url = input("Base URL (例: http://localhost/v1): ").strip().rstrip('/')
    api_key = input("API Key: ").strip()
    message = input("测试消息 [默认: 你好]: ").strip() or "你好"
    
    print()
    print("📋 配置信息:")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {'*' * 20}...{api_key[-8:] if len(api_key) > 8 else '***'}")
    print(f"   测试消息: {message}")
    print()
    
    # 构建请求
    url = f"{base_url}/chat-messages"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": {},
        "query": message,
        "response_mode": "streaming",
        "user": "test_user",
        "conversation_id": ""
    }
    
    print("🌐 HTTP 请求详情:")
    print(f"   URL: {url}")
    print(f"   Method: POST")
    print(f"   Headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}, indent=2)}")
    print(f"   Body: {json.dumps(data, ensure_ascii=False, indent=2)}")
    print()
    print("🚀 开始发送请求...")
    print("-" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", url, headers=headers, json=data) as response:
                print(f"📡 响应状态码: {response.status_code}")
                print(f"📡 响应头:")
                for key, value in response.headers.items():
                    print(f"   {key}: {value}")
                print()
                
                if response.status_code != 200:
                    print(f"❌ HTTP 错误: {response.status_code}")
                    body = await response.aread()
                    print(f"响应体: {body.decode('utf-8')}")
                    return False
                
                print("✅ 响应正常，开始读取流式数据...")
                print("-" * 80)
                
                line_count = 0
                message_parts = []
                conversation_id = None
                
                async for line in response.aiter_lines():
                    line_count += 1
                    
                    if line_count <= 5:
                        print(f"[行 {line_count:03d}] {line}")
                    elif line_count % 10 == 0:
                        print(f"[已接收 {line_count} 行...]")
                    
                    # 解析 SSE 数据
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            event_type = data.get('event')
                            
                            if event_type == 'message':
                                answer = data.get('answer', '')
                                if answer:
                                    message_parts.append(answer)
                                    print(f"💬 [{answer}]", end='', flush=True)
                            
                            if data.get('conversation_id') and not conversation_id:
                                conversation_id = data.get('conversation_id')
                                print(f"\n✅ conversation_id: {conversation_id}")
                            
                            if event_type == 'message_end':
                                print(f"\n✅ 消息结束")
                                metadata = data.get('metadata', {})
                                usage = metadata.get('usage', {})
                                if usage:
                                    print(f"📊 Token 使用: {usage.get('total_tokens')} tokens")
                            
                            if event_type == 'error':
                                print(f"\n❌ 错误: {data.get('message')}")
                        
                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  JSON 解析失败: {e}")
                            print(f"   原始数据: {line}")
                
                print()
                print("-" * 80)
                print(f"✅ 流式读取完成")
                print(f"   总行数: {line_count}")
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
    
    except httpx.HTTPStatusError as e:
        print()
        print("❌ HTTP 状态码错误")
        print(f"   状态码: {e.response.status_code}")
        print(f"   URL: {e.request.url}")
        try:
            print(f"   响应体: {e.response.json()}")
        except:
            print(f"   响应体（原始）: {e.response.text}")
        return False
    
    except httpx.RequestError as e:
        print()
        print("❌ 请求失败")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        return False
    
    except Exception as e:
        print()
        print("❌ 发生未预期错误")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print()
    print("=" * 80)
    print("  Dify API 原始请求测试工具")
    print("  用于最底层的 API 调试")
    print("=" * 80)
    print()
    
    result = asyncio.run(test_raw_dify_api())
    
    print()
    print("=" * 80)
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)

