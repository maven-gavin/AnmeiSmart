"""
AI Gateway服务统一入口

为AnmeiSmart业务层提供简洁的AI服务调用接口。
隐藏底层复杂性，提供高级业务方法。
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from .interfaces import (
    AIRequest, AIResponse, PlanResponse, SummaryResponse, SentimentResponse,
    AIScenario, AIProvider, ChatContext
)
from .gateway import (
    AIGateway, AIRouter, AICache, CircuitBreakerConfig, 
    ProviderConfig, CacheConfig, RoutingStrategy
)
from .adapters.dify_adapter import DifyAdapter, DifyConnectionConfig, DifyAppConfig
from .adapters.openai_adapter import OpenAIAdapter, OpenAIConfig
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
        
        # 注册Dify服务
        try:
            dify_config = self._create_dify_config()
            if dify_config:
                dify_adapter = DifyAdapter(dify_config)
                self.gateway.register_service(AIProvider.DIFY, dify_adapter)
                
                # 注册Dify提供商配置
                provider_config = ProviderConfig(
                    provider=AIProvider.DIFY,
                    service_class=DifyAdapter,
                    weight=3,
                    scenarios=[
                        AIScenario.BEAUTY_PLAN,
                        AIScenario.CONSULTATION_SUMMARY,
                        AIScenario.GENERAL_CHAT,
                        AIScenario.CUSTOMER_SERVICE
                    ],
                    enabled=True
                )
                self.gateway.router.register_provider(provider_config)
                logger.info("Registered Dify provider")
        except Exception as e:
            logger.warning(f"Failed to register Dify provider: {e}")
        
        # 注册OpenAI服务作为备选
        try:
            openai_config = self._create_openai_config()
            if openai_config:
                openai_adapter = OpenAIAdapter(openai_config)
                self.gateway.register_service(AIProvider.OPENAI, openai_adapter)
                
                # 注册OpenAI提供商配置
                provider_config = ProviderConfig(
                    provider=AIProvider.OPENAI,
                    service_class=OpenAIAdapter,
                    weight=1,
                    scenarios=[
                        AIScenario.GENERAL_CHAT,
                        AIScenario.SENTIMENT_ANALYSIS,
                        AIScenario.BEAUTY_PLAN,
                        AIScenario.CONSULTATION_SUMMARY
                    ],
                    enabled=True,
                    fallback_providers=[]
                )
                self.gateway.router.register_provider(provider_config)
                logger.info("Registered OpenAI provider")
        except Exception as e:
            logger.warning(f"Failed to register OpenAI provider: {e}")
    
    def _create_dify_config(self) -> Optional[DifyConnectionConfig]:
        """创建Dify配置"""
        try:
            # 首先尝试从数据库加载配置
            dify_settings = self._get_dify_settings_from_db()
            
            if dify_settings and dify_settings.get("enabled"):
                base_url = dify_settings["base_url"]
                apps = {}
                
                # 配置不同的Dify应用
                if dify_settings["apps"].get("chat"):
                    chat_config = dify_settings["apps"]["chat"]
                    apps["general_chat"] = DifyAppConfig(
                        app_id=chat_config.get("app_id", "dify-chat-app"),
                        app_name="通用聊天助手",
                        app_mode="chat",
                        api_key=chat_config["api_key"],
                        scenarios=[AIScenario.GENERAL_CHAT, AIScenario.CUSTOMER_SERVICE]
                    )
                
                if dify_settings["apps"].get("beauty"):
                    beauty_config = dify_settings["apps"]["beauty"]
                    apps["beauty_agent"] = DifyAppConfig(
                        app_id=beauty_config.get("app_id", "dify-beauty-agent"), 
                        app_name="医美方案专家",
                        app_mode="agent",
                        api_key=beauty_config["api_key"],
                        scenarios=[AIScenario.BEAUTY_PLAN, AIScenario.MEDICAL_ADVICE]
                    )
                
                if dify_settings["apps"].get("summary"):
                    summary_config = dify_settings["apps"]["summary"]
                    apps["summary_workflow"] = DifyAppConfig(
                        app_id=summary_config.get("app_id", "dify-summary-workflow"),
                        app_name="咨询总结工作流",
                        app_mode="workflow", 
                        api_key=summary_config["api_key"],
                        scenarios=[AIScenario.CONSULTATION_SUMMARY]
                    )
                
                if apps:
                    logger.info(f"从数据库加载Dify配置，包含{len(apps)}个应用")
                    return DifyConnectionConfig(
                        base_url=base_url,
                        apps=apps,
                        timeout=dify_settings.get("timeout_seconds", 30),
                        max_retries=dify_settings.get("max_retries", 3)
                    )
            
            # 如果数据库中没有配置，不再从环境变量加载
            logger.warning("No Dify configuration found in database. Please configure via admin panel at /admin/settings")
            return None
        except Exception as e:
            logger.error(f"Failed to create Dify config: {e}")
            return None
    
    def _create_openai_config(self) -> Optional[OpenAIConfig]:
        """创建OpenAI配置"""
        try:
            api_key = getattr(self.settings, 'OPENAI_API_KEY', '')
            if not api_key:
                return None
                
            return OpenAIConfig(
                api_key=api_key,
                api_base=getattr(self.settings, 'OPENAI_API_BASE_URL', 'https://api.openai.com/v1'),
                model=getattr(self.settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                max_tokens=2000,
                temperature=0.7,
                timeout=30,
                max_retries=3
            )
        except Exception as e:
            logger.error(f"Failed to create OpenAI config: {e}")
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
    
    async def generate_beauty_plan(self, requirements: str, user_id: str,
                                 user_profile: Dict[str, Any]) -> PlanResponse:
        """生成医美方案"""
        if not self.gateway:
            raise Exception("AI Gateway not initialized")
        
        context = ChatContext(
            user_id=user_id,
            session_id=f"plan_{user_id}_{int(time.time())}",
            user_profile=user_profile
        )
        
        request = AIRequest(
            scenario=AIScenario.BEAUTY_PLAN,
            message=requirements,
            context=context,
            parameters={"plan_type": "comprehensive", "include_cost": True}
        )
        
        return await self.gateway.execute_request(request)
    
    async def summarize_consultation(self, conversation_text: str, 
                                   user_id: str) -> SummaryResponse:
        """总结咨询内容"""
        if not self.gateway:
            raise Exception("AI Gateway not initialized")
        
        context = ChatContext(
            user_id=user_id,
            session_id=f"summary_{user_id}_{int(time.time())}"
        )
        
        request = AIRequest(
            scenario=AIScenario.CONSULTATION_SUMMARY,
            message=conversation_text,
            context=context,
            parameters={"summary_type": "detailed", "include_sentiment": True}
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
        
        return await self.gateway.execute_request(request)
    
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
    
    def _get_dify_settings_from_db(self) -> Optional[Dict[str, Any]]:
        """从数据库获取Dify设置"""
        try:
            from app.services.dify_config_service import get_current_dify_settings
            return get_current_dify_settings()
        except Exception as e:
            logger.error(f"从数据库获取Dify设置失败: {e}")
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