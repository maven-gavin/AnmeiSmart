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
    
    def __init__(self, api_key: str, base_url: str):
        """
        初始化 Dify Agent 客户端
        
        Args:
            api_key: Dify API 密钥
            base_url: Dify 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"Dify Agent 客户端已初始化: {base_url}")
    
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
            
            # 构建请求数据
            data = {
                "inputs": inputs or {},
                "query": message,
                "user": user,
                "response_mode": "streaming"
            }
            
            if conversation_id:
                data["conversation_id"] = conversation_id
            
            # 使用 httpx 进行流式请求
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat-messages",
                    headers=self.headers,
                    json=data
                ) as response:
                    response.raise_for_status()
                    
                    # 流式读取响应
                    async for line in response.aiter_lines():
                        if line:
                            # 转发 SSE 格式的数据
                            yield (line + "\n").encode('utf-8')
                
        except httpx.HTTPError as e:
            logger.error(f"流式对话 HTTP 错误: {e}", exc_info=True)
            error_message = f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            yield error_message.encode('utf-8')
        except Exception as e:
            logger.error(f"流式对话失败: {e}", exc_info=True)
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
            base_url=agent_config.base_url
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

