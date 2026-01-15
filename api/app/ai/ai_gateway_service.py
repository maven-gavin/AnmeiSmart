"""
AI Gateway服务统一入口

为AnmeiSmart业务层提供简洁的AI服务调用接口。
隐藏底层复杂性，提供高级业务方法。
"""

import logging
import time
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from .interfaces import (
    AIRequest, AIResponse, SummaryResponse, SentimentResponse,
    AIScenario, AIProvider, ChatContext
)
from .gateway import (
    AIGateway, AIRouter, AICache, CircuitBreakerConfig, 
    ProviderConfig, CacheConfig, RoutingStrategy
)
from .adapters.agent_adapter import AgentAdapter, AgentConnectionConfig, AgentAppConfig
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AIGatewayService:
    """AI Gateway服务
    
    为业务层提供统一的AI能力调用接口。
    自动处理路由、熔断、缓存等底层逻辑。
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.gateway: Optional[AIGateway] = None
        self._initialize_gateway()
    
    def _initialize_gateway(self):
        """初始化AI Gateway"""
        try:
            # 创建路由器
            router = AIRouter(strategy=RoutingStrategy.SCENARIO_BASED)
            
            # 创建缓存
            cache_config = CacheConfig(
                enabled=True,
                ttl_seconds=300,
                max_size=1000,
                cache_scenarios=[
                    AIScenario.GENERAL_CHAT,
                    AIScenario.SENTIMENT_ANALYSIS
                ]
            )
            cache = AICache(cache_config)
            
            # 创建熔断器配置
            circuit_config = CircuitBreakerConfig(
                failure_threshold=5,
                timeout_seconds=60,
                half_open_max_calls=3,
                success_threshold=2
            )
            
            # 创建Gateway
            self.gateway = AIGateway(router, cache, circuit_config)
            
            # 注册服务提供商
            self._register_providers()
            
            logger.info("AI Gateway initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Gateway: {e}")
            self.gateway = None
    
    def _register_providers(self):
        """注册AI服务提供商"""
        if not self.gateway:
            return
        
        # 注册Agent服务
        try:
            agent_config = self._create_agent_config()
            if agent_config:
                agent_adapter = AgentAdapter(agent_config)
                self.gateway.register_service(AIProvider.AGENT, agent_adapter)
                
                # 注册Agent提供商配置
                provider_config = ProviderConfig(
                    provider=AIProvider.AGENT,
                    service_class=AgentAdapter,
                    weight=3,
                    scenarios=[
                        AIScenario.GENERAL_CHAT,
                        AIScenario.CUSTOMER_SERVICE
                    ],
                    enabled=True
                )
                self.gateway.router.register_provider(provider_config)
                logger.info("Registered Agent provider")
        except Exception as e:
            logger.warning(f"Failed to register Agent provider: {e}")
    
    def _create_agent_config(self) -> Optional[AgentConnectionConfig]:
        """创建Agent配置"""
        try:
            # 首先尝试从数据库加载配置
            agent_settings = self._get_agent_settings_from_db()
            
            if agent_settings and agent_settings.get("enabled"):
                base_url = agent_settings["base_url"]
                apps = {}
                
                # 配置不同的Agent应用
                if agent_settings["apps"].get("chat"):
                    chat_config = agent_settings["apps"]["chat"]
                    apps["general_chat"] = AgentAppConfig(
                        app_id=chat_config.get("app_id", "agent-chat-app"),
                        app_name="通用聊天助手",
                        app_mode="chat",
                        api_key=chat_config["api_key"],
                        base_url=base_url,
                        timeout_seconds=agent_settings.get("timeout_seconds", 30),
                        max_retries=agent_settings.get("max_retries", 3)
                    )
                
                if agent_settings["apps"].get("summary"):
                    summary_config = agent_settings["apps"]["summary"]
                    apps["summary_workflow"] = AgentAppConfig(
                        app_id=summary_config.get("app_id", "agent-summary-workflow"),
                        app_name="咨询总结工作流",
                        app_mode="workflow", 
                        api_key=summary_config["api_key"],
                        base_url=base_url,
                        timeout_seconds=agent_settings.get("timeout_seconds", 30),
                        max_retries=agent_settings.get("max_retries", 3)
                    )
                
                if apps:
                    logger.info(f"从数据库加载Agent配置，包含{len(apps)}个应用")
                    return AgentConnectionConfig(
                        base_url=base_url,
                        timeout_seconds=agent_settings.get("timeout_seconds", 30),
                        max_retries=agent_settings.get("max_retries", 3),
                        apps=apps
                    )
            
            # 如果数据库中没有配置，不再从环境变量加载
            logger.warning("No Agent configuration found in database. Please configure via admin panel at /admin/settings")
            return None
        except Exception as e:
            logger.error(f"Failed to create Agent config: {e}")
            return None
    
    async def chat(self, message: str, user_id: str, session_id: str, 
                  user_profile: Optional[Dict[str, Any]] = None,
                  conversation_history: Optional[List[Dict[str, str]]] = None) -> AIResponse:
        """通用聊天"""
        if not self.gateway:
            raise Exception("AI Gateway not initialized")
        
        context = ChatContext(
            user_id=user_id,
            session_id=session_id,
            user_profile=user_profile,
            conversation_history=conversation_history or []
        )
        
        request = AIRequest(
            scenario=AIScenario.GENERAL_CHAT,
            message=message,
            context=context
        )
        
        return await self.gateway.execute_request(request)
    
    async def analyze_sentiment(self, text: str, user_id: str) -> SentimentResponse:
        """分析文本情感"""
        if not self.gateway:
            raise Exception("AI Gateway not initialized")
        
        context = ChatContext(
            user_id=user_id,
            session_id=f"sentiment_{user_id}_{int(time.time())}"
        )
        
        request = AIRequest(
            scenario=AIScenario.SENTIMENT_ANALYSIS,
            message=text,
            context=context
        )
        
        # 获取基础响应并转换为 SentimentResponse
        base_response = await self.gateway.execute_request(request)
        
        # 转换为 SentimentResponse
        return SentimentResponse(
            request_id=base_response.request_id,
            content=base_response.content,
            provider=base_response.provider,
            scenario=base_response.scenario,
            success=base_response.success,
            error_message=base_response.error_message,
            metadata=base_response.metadata,
            usage=base_response.usage,
            response_time=base_response.response_time,
            timestamp=base_response.timestamp,
            # SentimentResponse 特有字段可以从 metadata 中解析
            sentiment_score=base_response.metadata.get("sentiment_score", 0.0) if base_response.metadata else 0.0,
            confidence=base_response.metadata.get("confidence", 0.0) if base_response.metadata else 0.0,
            emotions=base_response.metadata.get("emotions") if base_response.metadata else None
        )
    
    async def customer_service_chat(self, message: str, user_id: str,
                                  session_id: str, 
                                  conversation_history: Optional[List[Dict[str, str]]] = None) -> AIResponse:
        """客服聊天"""
        if not self.gateway:
            raise Exception("AI Gateway not initialized")
        
        context = ChatContext(
            user_id=user_id,
            session_id=session_id,
            conversation_history=conversation_history or []
        )
        
        request = AIRequest(
            scenario=AIScenario.CUSTOMER_SERVICE,
            message=message,
            context=context
        )
        
        return await self.gateway.execute_request(request)
    
    async def medical_advice(self, question: str, user_id: str,
                           user_profile: Optional[Dict[str, Any]] = None) -> AIResponse:
        """医疗建议"""
        if not self.gateway:
            raise Exception("AI Gateway not initialized")
        
        context = ChatContext(
            user_id=user_id,
            session_id=f"medical_{user_id}_{int(time.time())}",
            user_profile=user_profile
        )
        
        request = AIRequest(
            scenario=AIScenario.MEDICAL_ADVICE,
            message=question,
            context=context
        )
        
        return await self.gateway.execute_request(request)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取AI Gateway健康状态"""
        if not self.gateway:
            return {"status": "unhealthy", "error": "Gateway not initialized"}
        
        return await self.gateway.get_health_status()
    
    def reload_configuration(self):
        """重新加载配置"""
        logger.info("Reloading AI Gateway configuration")
        self._initialize_gateway()
    
    def _get_agent_settings_from_db(self) -> Optional[Dict[str, Any]]:
        """从数据库获取Agent设置"""
        try:
            from app.services.agent_config_service import get_current_agent_settings
            return get_current_agent_settings()
        except Exception as e:
            logger.error(f"从数据库获取Agent设置失败: {e}")
            return None


# 全局实例
_gateway_service: Optional[AIGatewayService] = None


def get_ai_gateway_service(db: Session) -> AIGatewayService:
    """获取AI Gateway服务实例"""
    global _gateway_service
    
    if _gateway_service is None:
        _gateway_service = AIGatewayService(db)
    
    return _gateway_service


def reload_ai_gateway_service():
    """重新加载AI Gateway服务"""
    global _gateway_service
    
    if _gateway_service:
        _gateway_service.reload_configuration()
    else:
        logger.warning("AI Gateway service not initialized yet") 