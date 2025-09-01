"""
Dify服务实现
提供与Dify API的集成能力
"""

import os
import logging
import json
import httpx
from typing import Dict, Any, Optional, List, AsyncGenerator
from uuid import uuid4
from datetime import datetime

from app.core.config import get_settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

class DifyService:
    """Dify服务客户端"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Dify客户端
        
        Args:
            config: 可选的配置参数，用于覆盖环境变量
        """
        # 从配置或环境变量获取设置
        self.api_key = config.get("api_key") if config else os.environ.get("DIFY_API_KEY", "")
        self.api_base_url = config.get("api_base_url") if config else os.environ.get("DIFY_API_BASE_URL", "http://localhost/v1")
        self.app_id = config.get("app_id") if config else os.environ.get("DIFY_APP_ID", "")
        
        # 验证配置
        if not self.api_key or not self.app_id:
            logger.warning("Dify服务配置不完整，服务可能不可用")
        else:
            logger.info(f"Dify服务初始化成功，应用ID: {self.app_id}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self.api_key or not self.app_id or not self.api_base_url:
            return False
        
        try:
            # 复用DifyAPIClient的连接测试逻辑
            from .dify_client import DifyAPIClient
            client = DifyAPIClient(self.api_base_url, self.api_key)
            result = await client.test_connection()
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Dify健康检查失败: {e}")
            return False
    
    async def generate_response(self, query: str, conversation_history: Optional[List[Dict[str, Any]]] = None, 
                                streaming: bool = False) -> Dict[str, Any]:
        """
        调用Dify API生成回复
        
        Args:
            query: 用户问题
            conversation_history: 对话历史记录
            streaming: 是否使用流式响应
            
        Returns:
            包含AI回复内容的字典
        """
        if not self.api_key or not self.app_id:
            return {
                "id": f"ai_msg_{uuid4().hex}",
                "content": "Dify服务未配置，无法生成回复。",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # 构建请求体
            request_data = {
                "inputs": {
                    "query": query
                },
                "response_mode": "streaming" if streaming else "blocking",
                "user": "user-123"  # 可以使用实际用户ID
            }
            
            # 添加对话历史（如果Dify API支持）
            if conversation_history:
                # 假设Dify期望的历史记录格式，可能需要根据实际API调整
                history_messages = []
                for message in conversation_history:
                    if message.get("sender_type") == "ai":
                        history_messages.append({
                            "role": "assistant",
                            "content": message.get("content", "")
                        })
                    else:
                        history_messages.append({
                            "role": "user",
                            "content": message.get("content", "")
                        })
                
                request_data["conversation_id"] = conversation_history[0].get("conversation_id") if conversation_history else None
            
            # 发送请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            if streaming:
                return await self._handle_streaming_response(request_data, headers)
            else:
                return await self._handle_blocking_response(request_data, headers)
                
        except Exception as e:
            logger.error(f"Dify API调用异常: {str(e)}")
            return {
                "id": f"ai_msg_{uuid4().hex}",
                "content": "抱歉，AI服务暂时不可用，请稍后再试。",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_blocking_response(self, request_data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """处理阻塞式API响应"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base_url}/chat/completions",
                headers=headers,
                json=request_data
            )
            
            if response.status_code != 200:
                logger.error(f"Dify API调用失败: {response.status_code} {response.text}")
                return {
                    "id": f"ai_msg_{uuid4().hex}",
                    "content": "抱歉，AI服务暂时不可用，请稍后再试。",
                    "timestamp": datetime.now().isoformat()
                }
            
            response_data = response.json()
            ai_response = response_data.get("answer", "")
            
            return {
                "id": response_data.get("id", f"ai_msg_{uuid4().hex}"),
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_streaming_response(self, request_data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """处理流式API响应"""
        full_response = ""
        response_id = f"ai_msg_{uuid4().hex}"
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", f"{self.api_base_url}/chat/completions", 
                                        headers=headers, json=request_data) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Dify API流式调用失败: {response.status_code} {error_text}")
                        return {
                            "id": response_id,
                            "content": "抱歉，AI服务暂时不可用，请稍后再试。",
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    # 处理流式响应
                    buffer = b""
                    async for chunk in response.aiter_bytes():
                        buffer += chunk
                        
                        # 尝试从缓冲区中提取完整的JSON对象
                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            if line.strip():
                                try:
                                    if line.startswith(b"data: "):
                                        line = line[6:]  # 去掉"data: "前缀
                                    
                                    # 跳过心跳消息
                                    if line.strip() == b":keepalive":
                                        continue
                                        
                                    chunk_data = json.loads(line)
                                    
                                    # 如果有错误消息
                                    if "error" in chunk_data:
                                        logger.error(f"Dify流式响应错误: {chunk_data['error']}")
                                        continue
                                    
                                    # 提取内容
                                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                                        delta = chunk_data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            content = delta["content"]
                                            full_response += content
                                    
                                    # 提取ID
                                    if "id" in chunk_data and not response_id:
                                        response_id = chunk_data["id"]
                                        
                                except json.JSONDecodeError:
                                    logger.warning(f"无法解析JSON: {line}")
                                except Exception as e:
                                    logger.error(f"处理流式响应时出错: {str(e)}")
        
        except Exception as e:
            logger.error(f"流式请求处理异常: {str(e)}")
            return {
                "id": response_id,
                "content": full_response or "抱歉，AI服务暂时不可用，请稍后再试。",
                "timestamp": datetime.now().isoformat()
            }
        
        # 返回完整响应
        return {
            "id": response_id,
            "content": full_response,
            "timestamp": datetime.now().isoformat()
        }
    
    async def generate_streaming_response(self, query: str, 
                                          conversation_history: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[str, None]:
        """
        生成流式响应，用于WebSocket实时传输
        
        Args:
            query: 用户问题
            conversation_history: 对话历史
            
        Yields:
            响应文本片段
        """
        if not self.api_key or not self.app_id:
            yield "Dify服务未配置，无法生成回复。"
            return
        
        try:
            # 构建请求体
            request_data = {
                "inputs": {
                    "query": query
                },
                "response_mode": "streaming",
                "user": "user-123"  # 使用实际用户ID
            }
            
            # 添加对话历史
            if conversation_history:
                # 根据Dify API要求格式化历史记录
                history_messages = []
                for message in conversation_history:
                    if message.get("sender_type") == "ai":
                        history_messages.append({
                            "role": "assistant",
                            "content": message.get("content", "")
                        })
                    else:
                        history_messages.append({
                            "role": "user",
                            "content": message.get("content", "")
                        })
                
                request_data["conversation_id"] = conversation_history[0].get("conversation_id") if conversation_history else None
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 发送流式请求
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", f"{self.api_base_url}/chat/completions", 
                                        headers=headers, json=request_data) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Dify API流式调用失败: {response.status_code} {error_text}")
                        yield "抱歉，AI服务暂时不可用，请稍后再试。"
                        return
                    
                    # 处理流式响应
                    buffer = b""
                    async for chunk in response.aiter_bytes():
                        buffer += chunk
                        
                        # 尝试从缓冲区中提取完整的JSON对象
                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            if line.strip():
                                try:
                                    if line.startswith(b"data: "):
                                        line = line[6:]  # 去掉"data: "前缀
                                    
                                    # 跳过心跳消息
                                    if line.strip() == b":keepalive":
                                        continue
                                        
                                    chunk_data = json.loads(line)
                                    
                                    # 如果有错误消息
                                    if "error" in chunk_data:
                                        logger.error(f"Dify流式响应错误: {chunk_data['error']}")
                                        continue
                                    
                                    # 提取内容
                                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                                        delta = chunk_data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            content = delta["content"]
                                            yield content
                                        
                                except json.JSONDecodeError:
                                    logger.warning(f"无法解析JSON: {line}")
                                except Exception as e:
                                    logger.error(f"处理流式响应时出错: {str(e)}")
        
        except Exception as e:
            logger.error(f"流式生成异常: {str(e)}")
            yield "抱歉，AI服务暂时不可用，请稍后再试。" 