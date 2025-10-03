"""
Dify Agent 客户端封装
基于官方 dify-client SDK 设计，使用 httpx 实现完全异步的 API 通信
"""

import logging
import json
from typing import Optional, Dict, Any, AsyncIterator, List
import httpx

from app.ai.infrastructure.db.agent_config import AgentConfig as AgentConfigModel

logger = logging.getLogger(__name__)


class DifyClient:
    """
    Dify 客户端基类
    提供与 Dify API 的基础通信能力
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.dify.ai/v1"):
        """
        初始化 Dify 客户端
        
        Args:
            api_key: Dify API 密钥
            base_url: Dify API 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def _send_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> httpx.Response:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法 (GET, POST, DELETE 等)
            endpoint: API 端点路径
            json_data: JSON 请求体
            params: URL 查询参数
            stream: 是否流式响应
        
        Returns:
            HTTP 响应对象
        """
        url = f"{self.base_url}{endpoint}"
        timeout = 300.0 if stream else 30.0
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method,
                url,
                headers=self.headers,
                json=json_data,
                params=params
            )
            response.raise_for_status()
            return response
    
    async def _send_request_with_files(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any],
        files: Dict[str, Any]
    ) -> httpx.Response:
        """
        发送带文件的 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点路径
            data: 表单数据
            files: 文件字典
        
        Returns:
            HTTP 响应对象
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                data=data,
                files=files
            )
            response.raise_for_status()
            return response
    
    async def message_feedback(
        self,
        message_id: str,
        rating: str,
        user: str
    ) -> Dict[str, Any]:
        """
        提交消息反馈
        
        Args:
            message_id: 消息ID
            rating: 评分 ('like' 或 'dislike')
            user: 用户标识
        
        Returns:
            反馈结果
        """
        data = {"rating": rating, "user": user}
        response = await self._send_request(
            "POST",
            f"/messages/{message_id}/feedbacks",
            json_data=data
        )
        return response.json()
    
    async def get_application_parameters(self, user: str) -> Dict[str, Any]:
        """
        获取应用参数
        
        Args:
            user: 用户标识
        
        Returns:
            应用参数数据
        """
        params = {"user": user}
        response = await self._send_request("GET", "/parameters", params=params)
        return response.json()
    
    async def file_upload(
        self,
        user: str,
        files: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        上传文件
        
        Args:
            user: 用户标识
            files: 文件字典，格式 {'file': (filename, file_content, mime_type)}
        
        Returns:
            上传结果，包含 upload_file_id
        """
        data = {"user": user}
        response = await self._send_request_with_files(
            "POST",
            "/files/upload",
            data=data,
            files=files
        )
        return response.json()
    
    async def text_to_audio(
        self,
        text: str,
        user: str,
        streaming: bool = False
    ) -> Dict[str, Any]:
        """
        文本转语音
        
        Args:
            text: 文本内容
            user: 用户标识
            streaming: 是否流式返回
        
        Returns:
            音频数据或流
        """
        data = {"text": text, "user": user, "streaming": streaming}
        response = await self._send_request("POST", "/text-to-audio", json_data=data)
        return response.json()
    
    async def get_meta(self, user: str) -> Dict[str, Any]:
        """
        获取应用元数据
        
        Args:
            user: 用户标识
        
        Returns:
            元数据信息
        """
        params = {"user": user}
        response = await self._send_request("GET", "/meta", params=params)
        return response.json()


class CompletionClient(DifyClient):
    """
    Dify Completion 客户端
    用于 Completion 类型的应用
    """
    
    async def create_completion_message(
        self,
        inputs: Dict[str, Any],
        response_mode: str,
        user: str,
        files: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[bytes]:
        """
        创建 Completion 消息
        
        Args:
            inputs: 输入参数
            response_mode: 响应模式 ('streaming' 或 'blocking')
            user: 用户标识
            files: 文件列表（可选）
        
        Yields:
            SSE 格式的字节流（streaming 模式）
        """
        data = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": user,
            "files": files
        }
        
        url = f"{self.base_url}/completion-messages"
        stream = (response_mode == "streaming")
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                if stream:
                    async with client.stream("POST", url, headers=self.headers, json=data) as response:
                        response.raise_for_status()
                        buffer = ""
                        async for line in response.aiter_lines():
                            if not line.strip():
                                if buffer:
                                    yield (buffer + "\n\n").encode('utf-8')
                                    buffer = ""
                            else:
                                buffer = line
                        if buffer:
                            yield (buffer + "\n\n").encode('utf-8')
                else:
                    response = await client.post(url, headers=self.headers, json=data)
                    response.raise_for_status()
                    yield json.dumps(response.json()).encode('utf-8')
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"Dify API 返回错误: status={e.response.status_code}")
            error_message = f"data: {json.dumps({'event': 'error', 'status': e.response.status_code, 'message': str(e)})}\n\n"
            yield error_message.encode('utf-8')
        except Exception as e:
            logger.error(f"请求失败: {str(e)}", exc_info=True)
            error_message = f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            yield error_message.encode('utf-8')


class ChatClient(DifyClient):
    """
    Dify Chat 客户端
    用于 Chat 类型的应用（Agent 对话）
    """
    
    async def create_chat_message(
        self,
        query: str,
        user: str,
        inputs: Optional[Dict[str, Any]] = None,
        response_mode: str = "streaming",
        conversation_id: Optional[str] = None,
        files: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[bytes]:
        """
        创建聊天消息（流式响应）
        
        Args:
            query: 用户查询内容
            user: 用户标识符
            inputs: 输入参数，默认为空字典
            response_mode: 响应模式，streaming（流式）或 blocking（阻塞）
            conversation_id: 会话ID，用于多轮对话
            files: 文件列表（用于视觉模型等场景）
        
        Yields:
            SSE 格式的字节流
        """
        data = {
            "inputs": inputs or {},
            "query": query,
            "user": user,
            "response_mode": response_mode,
            "files": files
        }
        
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        url = f"{self.base_url}/chat-messages"
        stream = (response_mode == "streaming")
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                if stream:
                    async with client.stream("POST", url, headers=self.headers, json=data) as response:
                        response.raise_for_status()
                        buffer = ""
                        async for line in response.aiter_lines():
                            if not line.strip():
                                if buffer:
                                    yield (buffer + "\n\n").encode('utf-8')
                                    buffer = ""
                            else:
                                buffer = line
                        if buffer:
                            yield (buffer + "\n\n").encode('utf-8')
                else:
                    response = await client.post(url, headers=self.headers, json=data)
                    response.raise_for_status()
                    yield json.dumps(response.json()).encode('utf-8')
                        
        except httpx.HTTPStatusError as e:
            logger.error(f"Dify API 返回错误: status={e.response.status_code}")
            error_message = f"data: {json.dumps({'event': 'error', 'status': e.response.status_code, 'message': str(e)})}\n\n"
            yield error_message.encode('utf-8')
        except Exception as e:
            logger.error(f"请求失败: {str(e)}", exc_info=True)
            error_message = f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            yield error_message.encode('utf-8')
    
    async def get_suggested(self, message_id: str, user: str) -> Dict[str, Any]:
        """
        获取建议问题
        
        Args:
            message_id: 消息ID
            user: 用户标识
        
        Returns:
            建议问题列表
        """
        params = {"user": user}
        response = await self._send_request(
            "GET",
            f"/messages/{message_id}/suggested",
            params=params
        )
        return response.json()
    
    async def stop_message(self, task_id: str, user: str) -> Dict[str, Any]:
        """
        停止消息生成
        
        Args:
            task_id: 任务ID
            user: 用户标识
        
        Returns:
            停止结果
        """
        data = {"user": user}
        response = await self._send_request(
            "POST",
            f"/chat-messages/{task_id}/stop",
            json_data=data
        )
        return response.json()
    
    async def get_conversations(
        self,
        user: str,
        last_id: Optional[str] = None,
        limit: Optional[int] = None,
        pinned: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        获取会话列表
        
        Args:
            user: 用户标识符
            last_id: 上次请求的最后一个会话ID，用于分页
            limit: 返回数量限制
            pinned: 是否只返回置顶会话
        
        Returns:
            会话列表数据
        """
        params = {
            "user": user,
            "last_id": last_id,
            "limit": limit,
            "pinned": pinned
        }
        # 移除 None 值
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await self._send_request("GET", "/conversations", params=params)
        return response.json()
    
    async def get_conversation_messages(
        self,
        user: str,
        conversation_id: Optional[str] = None,
        first_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取会话消息历史
        
        Args:
            user: 用户标识符
            conversation_id: 会话ID
            first_id: 第一条消息ID，用于分页
            limit: 返回数量限制
        
        Returns:
            消息历史数据
        """
        params = {"user": user}
        
        if conversation_id:
            params["conversation_id"] = conversation_id
        if first_id:
            params["first_id"] = first_id
        if limit:
            params["limit"] = limit
        
        response = await self._send_request("GET", "/messages", params=params)
        return response.json()
    
    async def rename_conversation(
        self,
        conversation_id: str,
        name: str,
        user: str,
        auto_generate: bool = False
    ) -> Dict[str, Any]:
        """
        重命名会话
        
        Args:
            conversation_id: 会话ID
            name: 新名称
            user: 用户标识符
            auto_generate: 是否自动生成名称
        
        Returns:
            更新后的会话数据
        """
        data = {"name": name, "auto_generate": auto_generate, "user": user}
        response = await self._send_request(
            "POST",
            f"/conversations/{conversation_id}/name",
            json_data=data
        )
        return response.json()
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user: str
    ) -> Dict[str, Any]:
        """
        删除会话
        
        Args:
            conversation_id: 会话ID
            user: 用户标识
        
        Returns:
            删除结果
        """
        data = {"user": user}
        response = await self._send_request(
            "DELETE",
            f"/conversations/{conversation_id}",
            json_data=data
        )
        return response.json()
    
    async def audio_to_text(
        self,
        audio_file: Any,
        user: str
    ) -> Dict[str, Any]:
        """
        语音转文字
        
        Args:
            audio_file: 音频文件
            user: 用户标识
        
        Returns:
            转换后的文本
        """
        data = {"user": user}
        files = {"audio_file": audio_file}
        response = await self._send_request_with_files(
            "POST",
            "/audio-to-text",
            data=data,
            files=files
        )
        return response.json()


class WorkflowClient(DifyClient):
    """
    Dify Workflow 客户端
    用于 Workflow 类型的应用
    """
    
    async def run(
        self,
        inputs: Dict[str, Any],
        response_mode: str = "streaming",
        user: str = "abc-123"
    ) -> AsyncIterator[bytes]:
        """
        运行工作流
        
        Args:
            inputs: 输入参数
            response_mode: 响应模式
            user: 用户标识
        
        Yields:
            工作流执行结果
        """
        data = {"inputs": inputs, "response_mode": response_mode, "user": user}
        url = f"{self.base_url}/workflows/run"
        stream = (response_mode == "streaming")
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                if stream:
                    async with client.stream("POST", url, headers=self.headers, json=data) as response:
                        response.raise_for_status()
                        buffer = ""
                        async for line in response.aiter_lines():
                            if not line.strip():
                                if buffer:
                                    yield (buffer + "\n\n").encode('utf-8')
                                    buffer = ""
                            else:
                                buffer = line
                        if buffer:
                            yield (buffer + "\n\n").encode('utf-8')
                else:
                    response = await client.post(url, headers=self.headers, json=data)
                    response.raise_for_status()
                    yield json.dumps(response.json()).encode('utf-8')
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}", exc_info=True)
            error_message = f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            yield error_message.encode('utf-8')
    
    async def stop(self, task_id: str, user: str) -> Dict[str, Any]:
        """
        停止工作流执行
        
        Args:
            task_id: 任务ID
            user: 用户标识
        
        Returns:
            停止结果
        """
        data = {"user": user}
        response = await self._send_request(
            "POST",
            f"/workflows/tasks/{task_id}/stop",
            json_data=data
        )
        return response.json()
    
    async def get_result(self, workflow_run_id: str) -> Dict[str, Any]:
        """
        获取工作流执行结果
        
        Args:
            workflow_run_id: 工作流运行ID
        
        Returns:
            执行结果
        """
        response = await self._send_request("GET", f"/workflows/run/{workflow_run_id}")
        return response.json()


class KnowledgeBaseClient(DifyClient):
    """
    Dify 知识库客户端
    用于管理知识库和文档
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.dify.ai/v1",
        dataset_id: Optional[str] = None
    ):
        """
        初始化知识库客户端
        
        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            dataset_id: 数据集ID（可选）
        """
        super().__init__(api_key=api_key, base_url=base_url)
        self.dataset_id = dataset_id
    
    def _get_dataset_id(self) -> str:
        """获取数据集ID，如果未设置则抛出异常"""
        if self.dataset_id is None:
            raise ValueError("dataset_id is not set")
        return self.dataset_id
    
    async def create_dataset(self, name: str) -> Dict[str, Any]:
        """创建数据集"""
        response = await self._send_request("POST", "/datasets", json_data={"name": name})
        return response.json()
    
    async def list_datasets(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """列出数据集"""
        response = await self._send_request("GET", f"/datasets?page={page}&limit={page_size}")
        return response.json()
    
    async def delete_dataset(self) -> Dict[str, Any]:
        """删除当前数据集"""
        url = f"/datasets/{self._get_dataset_id()}"
        response = await self._send_request("DELETE", url)
        return response.json()
    
    async def create_document_by_text(
        self,
        name: str,
        text: str,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """通过文本创建文档"""
        data = {
            "indexing_technique": "high_quality",
            "process_rule": {"mode": "automatic"},
            "name": name,
            "text": text
        }
        if extra_params:
            data.update(extra_params)
        
        url = f"/datasets/{self._get_dataset_id()}/document/create_by_text"
        response = await self._send_request("POST", url, json_data=data)
        return response.json()
    
    async def list_documents(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """列出文档"""
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["limit"] = page_size
        if keyword is not None:
            params["keyword"] = keyword
        
        url = f"/datasets/{self._get_dataset_id()}/documents"
        response = await self._send_request("GET", url, params=params)
        return response.json()
    
    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """删除文档"""
        url = f"/datasets/{self._get_dataset_id()}/documents/{document_id}"
        response = await self._send_request("DELETE", url)
        return response.json()


class DifyAgentClientFactory:
    """
    Dify Agent 客户端工厂
    根据 Agent 配置创建客户端实例
    """
    
    @staticmethod
    def create_client(agent_config: AgentConfigModel) -> ChatClient:
        """
        创建 Dify Chat 客户端（用于 Agent 对话）
        
        Args:
            agent_config: Agent 配置模型
        
        Returns:
            ChatClient 实例
        
        Raises:
            ValueError: 配置缺少必要参数
        """
        api_key = agent_config.api_key
        if not api_key:
            raise ValueError(f"Agent 配置缺少 API Key: {agent_config.id}")
        
        return ChatClient(
            api_key=api_key,
            base_url=agent_config.base_url
        )
    
    @staticmethod
    def create_client_from_db(agent_config_id: str, db) -> ChatClient:
        """
        从数据库加载配置并创建客户端
        
        Args:
            agent_config_id: Agent 配置ID
            db: 数据库会话
        
        Returns:
            ChatClient 实例
        
        Raises:
            ValueError: 配置不存在或未启用
        """
        agent_config = db.query(AgentConfigModel).filter(
            AgentConfigModel.id == agent_config_id,
            AgentConfigModel.enabled == True
        ).first()
        
        if not agent_config:
            raise ValueError(f"Agent 配置不存在或未启用: {agent_config_id}")
        
        return DifyAgentClientFactory.create_client(agent_config)


# 类型别名，保持向后兼容
DifyAgentClient = ChatClient
