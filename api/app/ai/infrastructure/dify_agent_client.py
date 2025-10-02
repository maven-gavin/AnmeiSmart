"""
Dify Agent 客户端封装
提供与 Dify Agent API 的统一通信接口
"""

import logging
import json
from typing import Optional, Dict, Any, AsyncIterator
import httpx
from sqlalchemy.orm import Session

from app.ai.infrastructure.db.agent_config import AgentConfig as AgentConfigModel

logger = logging.getLogger(__name__)


class DifyAgentClient:
    """
    Dify Agent 客户端
    封装与单个 Dify Agent 应用的通信
    """
    
    def __init__(self, api_key: str, base_url: str, app_id: Optional[str] = None):
        """
        初始化 Dify Agent 客户端
        
        Args:
            api_key: Dify API 密钥
            base_url: Dify 基础 URL
            app_id: Dify 应用 ID（可选）
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.app_id = app_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"Dify Agent 客户端已初始化: {base_url}")
        if app_id:
            logger.info(f"   app_id: {app_id}")
    
    async def stream_chat(
        self,
        message: str,
        user: str,
        conversation_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[bytes]:
        """
        流式对话
        
        Args:
            message: 用户消息
            user: 用户标识
            conversation_id: 会话ID（可选）
            inputs: 额外输入参数（可选）
        
        Yields:
            SSE 格式的字节流
        """
        try:
            logger.info(f"开始流式对话: user={user}, conversation_id={conversation_id}")
            
            # 构建请求数据（完全符合 Dify API 规范）
            data = {
                "inputs": inputs or {},
                "query": message,
                "user": user,
                "response_mode": "streaming"
            }
            
            if conversation_id:
                data["conversation_id"] = conversation_id
            
            # 完整的请求 URL
            full_url = f"{self.base_url}/chat-messages"
            
            # 详细日志
            logger.info(f"🌐 准备发送 HTTP 请求到 Dify:")
            logger.info(f"   URL: {full_url}")
            logger.info(f"   Method: POST")
            logger.info(f"   Headers: Authorization=Bearer ***...{self.api_key[-8:]}")
            logger.info(f"   Body: {json.dumps(data, ensure_ascii=False)[:500]}...")
            
            # 使用 httpx 进行流式请求
            async with httpx.AsyncClient(timeout=300.0) as client:
                logger.info(f"🚀 开始发送请求...")
                async with client.stream(
                    "POST",
                    full_url,
                    headers=self.headers,
                    json=data
                ) as response:
                    logger.info(f"📡 收到响应: status_code={response.status_code}")
                    response.raise_for_status()
                    logger.info(f"✅ 响应状态正常，开始读取流式数据...")
                    
                    # 流式读取响应
                    line_count = 0
                    buffer = ""
                    async for line in response.aiter_lines():
                        line_count += 1
                        
                        # 调试日志：前几行详细输出
                        if line_count <= 3:
                            logger.info(f"📦 第 {line_count} 行原始数据: [{line}]")
                        
                        # SSE 事件以空行分隔
                        if not line.strip():
                            if buffer:
                                # 完整的 SSE 事件：data: {...}\n\n
                                yield (buffer + "\n\n").encode('utf-8')
                                if line_count <= 3:
                                    logger.info(f"✅ 发送 SSE 事件: {buffer[:200]}...")
                                buffer = ""
                        else:
                            buffer = line
                    
                    # 处理最后一个事件（如果有）
                    if buffer:
                        yield (buffer + "\n\n").encode('utf-8')
                    
                    logger.info(f"✅ 流式读取完成，共 {line_count} 行")
                
        except httpx.HTTPStatusError as e:
            # HTTP 状态码错误（4xx, 5xx）
            logger.error("=" * 80)
            logger.error(f"❌ Dify API 返回错误状态码")
            logger.error(f"   状态码: {e.response.status_code}")
            logger.error(f"   URL: {e.request.url}")
            logger.error(f"   请求方法: {e.request.method}")
            try:
                response_body = e.response.text
                logger.error(f"   响应体: {response_body}")
                # 尝试解析 JSON 错误信息
                error_data = e.response.json()
                logger.error(f"   错误详情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                logger.error(f"   响应体（原始）: {e.response.content}")
            logger.error("=" * 80)
            
            error_message = f"data: {json.dumps({'event': 'error', 'status': e.response.status_code, 'message': str(e)})}\n\n"
            yield error_message.encode('utf-8')
            
        except httpx.RequestError as e:
            # 网络请求错误（连接失败、超时等）
            logger.error("=" * 80)
            logger.error(f"❌ Dify API 请求失败")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {str(e)}")
            logger.error(f"   URL: {e.request.url if hasattr(e, 'request') else 'N/A'}")
            logger.error("=" * 80, exc_info=True)
            
            error_message = f"data: {json.dumps({'event': 'error', 'message': f'请求失败: {str(e)}'})}\n\n"
            yield error_message.encode('utf-8')
            
        except Exception as e:
            # 其他未预期的错误
            logger.error("=" * 80)
            logger.error(f"❌ 流式对话发生未预期错误")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {str(e)}")
            logger.error("=" * 80, exc_info=True)
            
            error_message = f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            yield error_message.encode('utf-8')
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        user: str
    ) -> Dict[str, Any]:
        """
        获取会话消息历史
        
        Args:
            conversation_id: 会话ID
            user: 用户标识
        
        Returns:
            消息历史数据
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    params={
                        "conversation_id": conversation_id,
                        "user": user
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"获取消息历史失败: {e}", exc_info=True)
            raise


class DifyAgentClientFactory:
    """
    Dify Agent 客户端工厂
    根据 Agent 配置创建客户端实例
    """
    
    def create_client(
        self,
        agent_config: AgentConfigModel
    ) -> DifyAgentClient:
        """
        创建 Dify Agent 客户端
        
        Args:
            agent_config: Agent 配置模型
        
        Returns:
            DifyAgentClient 实例
        """
        # 获取解密后的 API Key
        api_key = agent_config.api_key
        if not api_key:
            raise ValueError(f"Agent 配置缺少 API Key: {agent_config.id}")
        
        return DifyAgentClient(
            api_key=api_key,
            base_url=agent_config.base_url,
            app_id=agent_config.app_id
        )
    
    def create_client_from_db(
        self,
        agent_config_id: str,
        db: Session
    ) -> DifyAgentClient:
        """
        从数据库加载配置并创建客户端
        
        Args:
            agent_config_id: Agent 配置ID
            db: 数据库会话
        
        Returns:
            DifyAgentClient 实例
        """
        agent_config = db.query(AgentConfigModel).filter(
            AgentConfigModel.id == agent_config_id,
            AgentConfigModel.enabled == True
        ).first()
        
        if not agent_config:
            raise ValueError(f"Agent 配置不存在或未启用: {agent_config_id}")
        
        return self.create_client(agent_config)

