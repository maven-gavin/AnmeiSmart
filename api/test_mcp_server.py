"""测试MCP Server功能的脚本"""
import asyncio
import aiohttp
import json
import hashlib
import base64
import secrets
from urllib.parse import urlencode


def base64url_sha256(data: str) -> str:
    """计算PKCE code challenge"""
    digest = hashlib.sha256(data.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')


async def test_mcp_server():
    """测试MCP Server的完整流程"""
    base_url = "http://localhost:8000/api/v1/mcp"
    server_code = "default"  # 假设有一个默认的工具分组
    
    async with aiohttp.ClientSession() as session:
        print("=== 测试OAuth发现 ===")
        
        # 1. 测试OAuth发现
        async with session.get("http://localhost:8000/.well-known/oauth-authorization-server") as resp:
            print(f"OAuth发现状态: {resp.status}")
            if resp.status == 200:
                metadata = await resp.json()
                print(f"OAuth元数据: {json.dumps(metadata, indent=2)}")
            else:
                print(f"OAuth发现失败: {await resp.text()}")
                return
        
        print("\n=== 测试客户端注册 ===")
        
        # 2. 注册客户端
        client_data = {
            "client_name": "Test MCP Client",
            "redirect_uris": ["http://localhost:8000/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"]
        }
        
        async with session.post(f"{base_url}/oauth/register", json=client_data) as resp:
            print(f"客户端注册状态: {resp.status}")
            if resp.status == 200:
                client_info = await resp.json()
                print(f"客户端信息: {json.dumps(client_info, indent=2)}")
                client_id = client_info["client_id"]
            else:
                print(f"客户端注册失败: {await resp.text()}")
                return
        
        print("\n=== 测试PKCE授权流程 ===")
        
        # 3. 生成PKCE参数
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = base64url_sha256(code_verifier)
        state = secrets.token_urlsafe(16)
        
        print(f"PKCE参数:")
        print(f"  code_verifier: {code_verifier}")
        print(f"  code_challenge: {code_challenge}")
        print(f"  state: {state}")
        
        # 4. 先获取授权页面，然后模拟授权提交
        # 构建授权URL
        auth_params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": "http://localhost:8000/callback",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        auth_url = f"{base_url}/oauth/authorize?{urlencode(auth_params)}"
        
        # 直接模拟授权提交（跳过UI交互）
        auth_data = {
            "api_key": "test_api_key_123",
            "client_id": client_id,
            "redirect_uri": "http://localhost:8000/callback",
            "state": state,
            "code_challenge": code_challenge
        }
        
        async with session.post(f"{base_url}/oauth/authorize", data=auth_data) as resp:
            print(f"授权提交状态: {resp.status}")
            if resp.status == 302:
                location = resp.headers.get("Location")
                print(f"重定向URL: {location}")
                
                # 从重定向URL中提取授权码
                if "code=" in location:
                    auth_code = location.split("code=")[1].split("&")[0]
                    print(f"授权码: {auth_code}")
                else:
                    print("未找到授权码")
                    return
            else:
                print(f"授权失败: {await resp.text()}")
                return
        
        print("\n=== 测试令牌交换 ===")
        
        # 5. 交换访问令牌
        token_data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": auth_code,
            "code_verifier": code_verifier,
            "redirect_uri": "http://localhost:8000/callback"
        }
        
        async with session.post(f"{base_url}/oauth/token", data=token_data) as resp:
            print(f"令牌交换状态: {resp.status}")
            if resp.status == 200:
                tokens = await resp.json()
                print(f"令牌信息: {json.dumps(tokens, indent=2)}")
                access_token = tokens["access_token"]
            else:
                print(f"令牌交换失败: {await resp.text()}")
                return
        
        print("\n=== 测试MCP协议 ===")
        
        # 6. MCP初始化
        headers = {"Authorization": f"Bearer {access_token}"}
        
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "Test Client", "version": "1.0.0"}
            }
        }
        
        async with session.post(f"{base_url}/server/{server_code}/mcp", 
                              json=init_request, headers=headers) as resp:
            print(f"MCP初始化状态: {resp.status}")
            if resp.status == 200:
                init_response = await resp.json()
                print(f"初始化响应: {json.dumps(init_response, indent=2)}")
                
                # 获取会话ID
                session_id = resp.headers.get("X-MCP-Session-ID")
                if session_id:
                    print(f"会话ID: {session_id}")
                    headers["X-MCP-Session-ID"] = session_id
            else:
                print(f"MCP初始化失败: {await resp.text()}")
                return
        
        # 7. 获取工具列表
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        async with session.post(f"{base_url}/server/{server_code}/mcp", 
                              json=list_request, headers=headers) as resp:
            print(f"工具列表状态: {resp.status}")
            if resp.status == 200:
                tools_response = await resp.json()
                print(f"工具列表: {json.dumps(tools_response, indent=2)}")
            else:
                print(f"获取工具列表失败: {await resp.text()}")
        
        # 8. 调用工具（如果有的话）
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "echo_tool",  # 假设有一个回显工具
                "arguments": {"message": "Hello MCP Server!"}
            }
        }
        
        async with session.post(f"{base_url}/server/{server_code}/mcp", 
                              json=call_request, headers=headers) as resp:
            print(f"工具调用状态: {resp.status}")
            if resp.status == 200:
                call_response = await resp.json()
                print(f"工具调用响应: {json.dumps(call_response, indent=2)}")
            else:
                print(f"工具调用失败: {await resp.text()}")
        
        print("\n=== 测试完成 ===")


if __name__ == "__main__":
    print("开始测试MCP Server...")
    asyncio.run(test_mcp_server())
