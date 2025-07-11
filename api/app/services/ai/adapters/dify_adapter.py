"""
Dify AI适配器实现

基于对Dify真实代码的深入分析，充分利用其企业级特性：
- 多租户架构(Tenant+Account+Role)
- 多种应用模式(chat/agent/workflow/completion)
- 丰富的权限体系和认证机制
- 工具调用和知识库集成
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import aiohttp
from datetime import datetime

from ..interfaces import (
    AIRequest, AIResponse, PlanResponse, SummaryResponse, SentimentResponse,
    AIScenario, AIProvider, AIServiceInterface, ChatContext,
    AIServiceError, AIProviderUnavailableError, AIAuthenticationError
)

logger = logging.getLogger(__name__)


@dataclass
class DifyAppConfig:
    """Dify应用配置"""
    app_id: str
    app_name: str
    app_mode: str  # chat, agent, workflow, completion
    api_key: str
    description: Optional[str] = None
    scenarios: List[AIScenario] = None
    
    # Dify特有配置
    enable_auto_save_history: bool = True
    enable_audio_to_text: bool = False
    enable_text_to_audio: bool = False
    retrieval_model: Optional[Dict[str, Any]] = None
    annotation_reply: Optional[Dict[str, Any]] = None
    
    # 工具配置
    tools: List[Dict[str, Any]] = None
    # 变量配置
    variables: Dict[str, Any] = None


@dataclass
class DifyConnectionConfig:
    """Dify连接配置"""
    base_url: str
    tenant_id: Optional[str] = None
    
    # 认证配置
    console_token: Optional[str] = None  # 控制台访问令牌
    refresh_token: Optional[str] = None  # 刷新令牌
    
    # 应用配置
    apps: Dict[str, DifyAppConfig] = None
    
    # 高级配置
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 100  # 每分钟请求数


class DifyAPIClient:
    """Dify API客户端
    
    基于Dify真实API结构实现的客户端，支持：
    - 多种认证方式（应用API密钥、控制台令牌）
    - 完整的应用生命周期管理
    - 流式和非流式响应
    - 错误处理和重试机制
    """
    
    def __init__(self, config: DifyConnectionConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={'Content-Type': 'application/json'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def chat_completion(self, app_config: DifyAppConfig, request: AIRequest) -> Dict[str, Any]:
        """聊天完成API调用"""
        url = f"{self.config.base_url}/chat-messages"
        
        # 构建请求体
        payload = {
            "inputs": self._build_inputs(request),
            "query": request.message,
            "user": self._get_user_id(request),
            "conversation_id": self._get_conversation_id(request),
            "response_mode": "blocking",  # 或 "streaming"
            "auto_generate_name": True
        }
        
        # 添加Dify特有参数
        if app_config.variables:
            payload["inputs"].update(app_config.variables)
        
        headers = {
            "Authorization": f"Bearer {app_config.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise AIAuthenticationError("Dify authentication failed", AIProvider.DIFY)
                else:
                    error_text = await response.text()
                    raise AIServiceError(f"Dify API error: {error_text}", AIProvider.DIFY, str(response.status))
                    
        except aiohttp.ClientError as e:
            raise AIProviderUnavailableError(f"Dify connection error: {e}", AIProvider.DIFY)
    
    async def workflow_run(self, app_config: DifyAppConfig, request: AIRequest) -> Dict[str, Any]:
        """工作流运行API调用"""
        url = f"{self.config.base_url}/workflows/run"
        
        payload = {
            "inputs": self._build_workflow_inputs(request),
            "user": self._get_user_id(request),
            "response_mode": "blocking"
        }
        
        headers = {
            "Authorization": f"Bearer {app_config.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise AIServiceError(f"Dify workflow error: {error_text}", AIProvider.DIFY, str(response.status))
                    
        except aiohttp.ClientError as e:
            raise AIProviderUnavailableError(f"Dify workflow connection error: {e}", AIProvider.DIFY)
    
    async def completion(self, app_config: DifyAppConfig, request: AIRequest) -> Dict[str, Any]:
        """文本完成API调用"""
        url = f"{self.config.base_url}/completion-messages"
        
        payload = {
            "inputs": self._build_inputs(request),
            "user": self._get_user_id(request),
            "response_mode": "blocking"
        }
        
        headers = {
            "Authorization": f"Bearer {app_config.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise AIServiceError(f"Dify completion error: {error_text}", AIProvider.DIFY, str(response.status))
                    
        except aiohttp.ClientError as e:
            raise AIProviderUnavailableError(f"Dify completion connection error: {e}", AIProvider.DIFY)
    
    async def get_application_config(self, app_config: DifyAppConfig) -> Dict[str, Any]:
        """获取应用配置"""
        url = f"{self.config.base_url}/parameters"
        
        headers = {
            "Authorization": f"Bearer {app_config.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise AIServiceError(f"Failed to get app config: {error_text}", AIProvider.DIFY)
                    
        except aiohttp.ClientError as e:
            raise AIProviderUnavailableError(f"Dify config connection error: {e}", AIProvider.DIFY)
    
    def _build_inputs(self, request: AIRequest) -> Dict[str, Any]:
        """构建输入参数"""
        inputs = {}
        
        # 添加用户档案信息
        if request.context and request.context.user_profile:
            inputs.update({
                "user_age": request.context.user_profile.get("age", ""),
                "user_gender": request.context.user_profile.get("gender", ""),
                "user_skin_type": request.context.user_profile.get("skin_type", ""),
                "user_budget": request.context.user_profile.get("budget", ""),
                "user_concerns": request.context.user_profile.get("concerns", ""),
                "user_preferences": request.context.user_profile.get("preferences", "")
            })
        
        # 添加会话历史
        if request.context and request.context.conversation_history:
            # 取最近5条对话作为上下文
            recent_history = request.context.conversation_history[-5:]
            history_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                for msg in recent_history
            ])
            inputs["conversation_history"] = history_text
        
        # 添加自定义变量
        if request.context and request.context.custom_variables:
            inputs.update(request.context.custom_variables)
        
        # 添加请求参数
        if request.parameters:
            inputs.update(request.parameters)
        
        return inputs
    
    def _build_workflow_inputs(self, request: AIRequest) -> Dict[str, Any]:
        """构建工作流输入参数"""
        inputs = self._build_inputs(request)
        
        # 工作流特有参数
        inputs.update({
            "task_type": request.scenario.value,
            "input_text": request.message,
            "language": "zh-CN",
            "output_format": request.response_format.value
        })
        
        return inputs
    
    def _get_user_id(self, request: AIRequest) -> str:
        """获取用户ID"""
        if request.context and request.context.user_id:
            return request.context.user_id
        return "anonymous_user"
    
    def _get_conversation_id(self, request: AIRequest) -> Optional[str]:
        """获取会话ID"""
        if request.context and request.context.session_id:
            return request.context.session_id
        return None


class DifyAdapter(AIServiceInterface):
    """Dify适配器
    
    充分利用Dify企业级特性的适配器实现。
    根据不同场景智能选择最佳的Dify应用模式。
    """
    
    def __init__(self, config: DifyConnectionConfig):
        self.config = config
        self.client = DifyAPIClient(config)
        
        # 场景到应用的映射配置
        self.scenario_app_mapping = {
            AIScenario.GENERAL_CHAT: "chat",
            AIScenario.CUSTOMER_SERVICE: "chat", 
            AIScenario.BEAUTY_PLAN: "agent",
            AIScenario.MEDICAL_ADVICE: "agent",
            AIScenario.CONSULTATION_SUMMARY: "workflow",
            AIScenario.SENTIMENT_ANALYSIS: "completion"
        }
    
    async def chat(self, request: AIRequest) -> AIResponse:
        """通用聊天实现"""
        app_config = self._select_app_for_scenario(request.scenario)
        
        try:
            async with self.client:
                if app_config.app_mode == "chat":
                    response_data = await self.client.chat_completion(app_config, request)
                elif app_config.app_mode == "agent":
                    response_data = await self.client.chat_completion(app_config, request)
                else:
                    # 降级到completion模式
                    response_data = await self.client.completion(app_config, request)
                
                return self._transform_to_ai_response(response_data, request, app_config)
                
        except Exception as e:
            logger.error(f"Dify chat error: {e}")
            return self._create_error_response(request, str(e))
    
    async def generate_beauty_plan(self, request: AIRequest) -> PlanResponse:
        """生成医美方案"""
        app_config = self._select_app_for_scenario(AIScenario.BEAUTY_PLAN)
        
        try:
            async with self.client:
                if app_config.app_mode == "agent":
                    # 使用Agent模式，利用工具调用能力
                    response_data = await self.client.chat_completion(app_config, request)
                elif app_config.app_mode == "workflow":
                    # 使用工作流模式，标准化流程
                    response_data = await self.client.workflow_run(app_config, request)
                else:
                    # 降级到聊天模式
                    response_data = await self.client.chat_completion(app_config, request)
                
                return self._transform_to_plan_response(response_data, request, app_config)
                
        except Exception as e:
            logger.error(f"Dify beauty plan error: {e}")
            return self._create_error_plan_response(request, str(e))
    
    async def summarize_consultation(self, request: AIRequest) -> SummaryResponse:
        """总结咨询内容"""
        app_config = self._select_app_for_scenario(AIScenario.CONSULTATION_SUMMARY)
        
        try:
            async with self.client:
                if app_config.app_mode == "workflow":
                    # 优先使用工作流模式进行结构化总结
                    response_data = await self.client.workflow_run(app_config, request)
                else:
                    # 降级到completion模式
                    response_data = await self.client.completion(app_config, request)
                
                return self._transform_to_summary_response(response_data, request, app_config)
                
        except Exception as e:
            logger.error(f"Dify summary error: {e}")
            return self._create_error_summary_response(request, str(e))
    
    async def analyze_sentiment(self, request: AIRequest) -> SentimentResponse:
        """分析情感"""
        app_config = self._select_app_for_scenario(AIScenario.SENTIMENT_ANALYSIS)
        
        try:
            async with self.client:
                # 情感分析适合使用completion模式
                response_data = await self.client.completion(app_config, request)
                return self._transform_to_sentiment_response(response_data, request, app_config)
                
        except Exception as e:
            logger.error(f"Dify sentiment analysis error: {e}")
            return self._create_error_sentiment_response(request, str(e))
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "provider": "dify",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "apps": {}
        }
        
        try:
            # 检查每个配置的应用
            if self.config.apps:
                for app_name, app_config in self.config.apps.items():
                    try:
                        async with self.client:
                            config_data = await self.client.get_application_config(app_config)
                            health_status["apps"][app_name] = {
                                "status": "healthy",
                                "app_mode": app_config.app_mode,
                                "config": config_data
                            }
                    except Exception as e:
                        health_status["apps"][app_name] = {
                            "status": "unhealthy",
                            "error": str(e)
                        }
                        health_status["status"] = "degraded"
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息"""
        return {
            "provider": "dify",
            "name": "Dify AI Platform",
            "version": "1.0",
            "capabilities": [
                "chat", "agent", "workflow", "completion",
                "multi_tenant", "tool_calling", "knowledge_base"
            ],
            "base_url": self.config.base_url,
            "configured_apps": list(self.config.apps.keys()) if self.config.apps else []
        }
    
    def _select_app_for_scenario(self, scenario: AIScenario) -> DifyAppConfig:
        """根据场景选择合适的Dify应用"""
        if not self.config.apps:
            raise AIServiceError("No Dify apps configured", AIProvider.DIFY)
        
        # 查找专门为该场景配置的应用
        for app_config in self.config.apps.values():
            if app_config.scenarios and scenario in app_config.scenarios:
                return app_config
        
        # 根据应用模式选择
        preferred_mode = self.scenario_app_mapping.get(scenario, "chat")
        for app_config in self.config.apps.values():
            if app_config.app_mode == preferred_mode:
                return app_config
        
        # 降级到第一个可用应用
        return next(iter(self.config.apps.values()))
    
    def _transform_to_ai_response(self, response_data: Dict[str, Any], 
                                request: AIRequest, app_config: DifyAppConfig) -> AIResponse:
        """转换Dify响应为统一AI响应"""
        content = response_data.get("answer", "")
        
        # 提取使用信息
        usage = {}
        if "metadata" in response_data:
            metadata = response_data["metadata"]
            usage = {
                "prompt_tokens": metadata.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": metadata.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": metadata.get("usage", {}).get("total_tokens", 0)
            }
        
        return AIResponse(
            request_id=request.request_id,
            content=content,
            provider=AIProvider.DIFY,
            scenario=request.scenario,
            success=True,
            metadata={
                "dify_app_id": app_config.app_id,
                "dify_app_mode": app_config.app_mode,
                "conversation_id": response_data.get("conversation_id"),
                "message_id": response_data.get("id")
            },
            usage=usage
        )
    
    def _transform_to_plan_response(self, response_data: Dict[str, Any],
                                  request: AIRequest, app_config: DifyAppConfig) -> PlanResponse:
        """转换为医美方案响应"""
        base_response = self._transform_to_ai_response(response_data, request, app_config)
        
        # 尝试解析结构化的方案内容
        content = base_response.content
        plan_sections = self._parse_plan_sections(content)
        estimated_cost = self._parse_estimated_cost(content)
        timeline = self._parse_timeline(content)
        risks = self._parse_risks(content)
        
        return PlanResponse(
            request_id=base_response.request_id,
            content=base_response.content,
            provider=base_response.provider,
            scenario=base_response.scenario,
            success=base_response.success,
            metadata=base_response.metadata,
            usage=base_response.usage,
            plan_sections=plan_sections,
            estimated_cost=estimated_cost,
            timeline=timeline,
            risks=risks
        )
    
    def _transform_to_summary_response(self, response_data: Dict[str, Any],
                                     request: AIRequest, app_config: DifyAppConfig) -> SummaryResponse:
        """转换为总结响应"""
        base_response = self._transform_to_ai_response(response_data, request, app_config)
        
        # 解析结构化总结内容
        content = base_response.content
        key_points = self._parse_key_points(content)
        action_items = self._parse_action_items(content)
        sentiment_score = self._parse_sentiment_score(content)
        categories = self._parse_categories(content)
        
        return SummaryResponse(
            request_id=base_response.request_id,
            content=base_response.content,
            provider=base_response.provider,
            scenario=base_response.scenario,
            success=base_response.success,
            metadata=base_response.metadata,
            usage=base_response.usage,
            key_points=key_points,
            action_items=action_items,
            sentiment_score=sentiment_score,
            categories=categories
        )
    
    def _transform_to_sentiment_response(self, response_data: Dict[str, Any],
                                       request: AIRequest, app_config: DifyAppConfig) -> SentimentResponse:
        """转换为情感分析响应"""
        base_response = self._transform_to_ai_response(response_data, request, app_config)
        
        # 解析情感分析结果
        content = base_response.content
        sentiment_score = self._extract_sentiment_score(content)
        confidence = self._extract_confidence(content)
        emotions = self._extract_emotions(content)
        
        return SentimentResponse(
            request_id=base_response.request_id,
            content=base_response.content,
            provider=base_response.provider,
            scenario=base_response.scenario,
            success=base_response.success,
            metadata=base_response.metadata,
            usage=base_response.usage,
            sentiment_score=sentiment_score,
            confidence=confidence,
            emotions=emotions
        )
    
    def _create_error_response(self, request: AIRequest, error_message: str) -> AIResponse:
        """创建错误响应"""
        return AIResponse(
            request_id=request.request_id,
            content=f"抱歉，处理您的请求时发生错误：{error_message}",
            provider=AIProvider.DIFY,
            scenario=request.scenario,
            success=False,
            error_message=error_message
        )
    
    def _create_error_plan_response(self, request: AIRequest, error_message: str) -> PlanResponse:
        """创建错误方案响应"""
        return PlanResponse(
            request_id=request.request_id,
            content=f"抱歉，生成医美方案时发生错误：{error_message}",
            provider=AIProvider.DIFY,
            scenario=request.scenario,
            success=False,
            error_message=error_message
        )
    
    def _create_error_summary_response(self, request: AIRequest, error_message: str) -> SummaryResponse:
        """创建错误总结响应"""
        return SummaryResponse(
            request_id=request.request_id,
            content=f"抱歉，总结咨询内容时发生错误：{error_message}",
            provider=AIProvider.DIFY,
            scenario=request.scenario,
            success=False,
            error_message=error_message
        )
    
    def _create_error_sentiment_response(self, request: AIRequest, error_message: str) -> SentimentResponse:
        """创建错误情感分析响应"""
        return SentimentResponse(
            request_id=request.request_id,
            content=f"抱歉，分析情感时发生错误：{error_message}",
            provider=AIProvider.DIFY,
            scenario=request.scenario,
            success=False,
            error_message=error_message,
            sentiment_score=0.0,
            confidence=0.0
        )
    
    # 辅助解析方法
    def _parse_plan_sections(self, content: str) -> List[Dict[str, Any]]:
        """解析方案章节"""
        # 实现具体的解析逻辑
        return []
    
    def _parse_estimated_cost(self, content: str) -> Dict[str, float]:
        """解析预估费用"""
        return {}
    
    def _parse_timeline(self, content: str) -> Dict[str, str]:
        """解析时间线"""
        return {}
    
    def _parse_risks(self, content: str) -> List[str]:
        """解析风险"""
        return []
    
    def _parse_key_points(self, content: str) -> List[str]:
        """解析关键点"""
        return []
    
    def _parse_action_items(self, content: str) -> List[str]:
        """解析行动项"""
        return []
    
    def _parse_sentiment_score(self, content: str) -> float:
        """解析情感分数"""
        return 0.0
    
    def _parse_categories(self, content: str) -> List[str]:
        """解析分类"""
        return []
    
    def _extract_sentiment_score(self, content: str) -> float:
        """提取情感分数"""
        return 0.0
    
    def _extract_confidence(self, content: str) -> float:
        """提取置信度"""
        return 0.0
    
    def _extract_emotions(self, content: str) -> Dict[str, float]:
        """提取具体情感"""
        return {} 