"""
AI Gateway核心组件

实现智能路由、熔断保护、缓存优化和监控功能的AI服务网关。
基于企业级微服务架构设计，确保高可用性和可观测性。
"""

import time
import logging
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .interfaces import (
    AIRequest, AIResponse, AIScenario, AIProvider, AIServiceInterface,
    AIProviderUnavailableError
)

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """路由策略枚举"""
    ROUND_ROBIN = "round_robin"         # 轮询
    LEAST_LATENCY = "least_latency"     # 最低延迟
    WEIGHTED = "weighted"               # 权重分配
    SCENARIO_BASED = "scenario_based"   # 基于场景
    HEALTH_BASED = "health_based"       # 基于健康状态


class CircuitState(Enum):
    """熔断器状态枚举"""
    CLOSED = "closed"       # 关闭状态（正常）
    OPEN = "open"           # 开启状态（熔断）
    HALF_OPEN = "half_open" # 半开状态（尝试恢复）


@dataclass
class ProviderConfig:
    """AI服务提供商配置"""
    provider: AIProvider
    service_class: Type[AIServiceInterface]
    weight: int = 1
    max_tokens: Optional[int] = None
    rate_limit_per_minute: int = 100
    timeout_seconds: int = 30
    enabled: bool = True
    fallback_providers: List[AIProvider] = field(default_factory=list)
    scenarios: List[AIScenario] = field(default_factory=list)  # 支持的场景


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5          # 失败阈值
    timeout_seconds: int = 60           # 熔断超时时间
    half_open_max_calls: int = 3        # 半开状态最大调用次数
    success_threshold: int = 2          # 恢复成功阈值


@dataclass 
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl_seconds: int = 300             # 缓存过期时间
    max_size: int = 1000               # 最大缓存条目数
    cache_scenarios: List[AIScenario] = field(default_factory=list)


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(self, provider: AIProvider, config: CircuitBreakerConfig):
        self.provider = provider
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
    def call_allowed(self) -> bool:
        """检查是否允许调用"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        else:  # HALF_OPEN
            return self.half_open_calls < self.config.half_open_max_calls
    
    def record_success(self):
        """记录成功调用"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._reset()
        else:
            self.failure_count = 0
    
    def record_failure(self):
        """记录失败调用"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif (self.state == CircuitState.CLOSED and 
              self.failure_count >= self.config.failure_threshold):
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if not self.last_failure_time:
            return False
        return (datetime.now() - self.last_failure_time).seconds >= self.config.timeout_seconds
    
    def _reset(self):
        """重置熔断器"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0


class AICache:
    """AI响应缓存"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, Dict[str, Any]] = {}
        
    async def get(self, cache_key: str) -> Optional[AIResponse]:
        """获取缓存响应"""
        if not self.config.enabled:
            return None
            
        if cache_key not in self.cache:
            return None
            
        cache_entry = self.cache[cache_key]
        if self._is_expired(cache_entry):
            del self.cache[cache_key]
            return None
            
        logger.info(f"Cache hit for key: {cache_key}")
        return cache_entry['response']
    
    async def set(self, cache_key: str, response: AIResponse):
        """设置缓存响应"""
        if not self.config.enabled:
            return
            
        if response.scenario not in self.config.cache_scenarios:
            return
            
        # 清理过期缓存
        self._cleanup_expired()
        
        # 检查缓存大小限制
        if len(self.cache) >= self.config.max_size:
            self._evict_oldest()
            
        self.cache[cache_key] = {
            'response': response,
            'timestamp': datetime.now(),
            'access_count': 0
        }
        
        logger.info(f"Cached response for key: {cache_key}")
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """检查缓存是否过期"""
        timestamp = cache_entry['timestamp']
        return (datetime.now() - timestamp).seconds > self.config.ttl_seconds
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_oldest(self):
        """移除最旧的缓存条目"""
        if not self.cache:
            return
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k]['timestamp']
        )
        del self.cache[oldest_key]


class AIRouter:
    """AI服务路由器"""
    
    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.SCENARIO_BASED):
        self.strategy = strategy
        self.provider_configs: Dict[AIProvider, ProviderConfig] = {}
        self.provider_stats: Dict[AIProvider, Dict[str, Any]] = {}
        
    def register_provider(self, config: ProviderConfig):
        """注册AI服务提供商"""
        self.provider_configs[config.provider] = config
        self.provider_stats[config.provider] = {
            'total_calls': 0,
            'success_calls': 0,
            'avg_latency': 0.0,
            'last_call_time': None,
            'error_rate': 0.0
        }
        logger.info(f"Registered provider: {config.provider.value}")
    
    async def select_provider(self, request: AIRequest) -> AIProvider:
        """选择最佳的AI服务提供商"""
        if self.strategy == RoutingStrategy.SCENARIO_BASED:
            return self._select_by_scenario(request.scenario)
        elif self.strategy == RoutingStrategy.LEAST_LATENCY:
            return self._select_by_latency()
        elif self.strategy == RoutingStrategy.WEIGHTED:
            return self._select_by_weight()
        elif self.strategy == RoutingStrategy.HEALTH_BASED:
            return self._select_by_health()
        else:  # ROUND_ROBIN
            return self._select_round_robin()
    
    def _select_by_scenario(self, scenario: AIScenario) -> AIProvider:
        """基于场景选择提供商"""
        suitable_providers = [
            provider for provider, config in self.provider_configs.items()
            if config.enabled and (not config.scenarios or scenario in config.scenarios)
        ]
        
        if not suitable_providers:
            # 降级到任意可用提供商
            suitable_providers = [
                provider for provider, config in self.provider_configs.items()
                if config.enabled
            ]
        
        if not suitable_providers:
            raise AIProviderUnavailableError("No available providers")
        
        # 在合适的提供商中选择最佳的
        return self._select_best_from_list(suitable_providers)
    
    def _select_by_latency(self) -> AIProvider:
        """基于延迟选择提供商"""
        available_providers = self._get_available_providers()
        if not available_providers:
            raise AIProviderUnavailableError("No available providers")
            
        return min(
            available_providers,
            key=lambda p: self.provider_stats[p]['avg_latency']
        )
    
    def _select_by_weight(self) -> AIProvider:
        """基于权重选择提供商"""
        available_providers = self._get_available_providers()
        if not available_providers:
            raise AIProviderUnavailableError("No available providers")
        
        total_weight = sum(
            self.provider_configs[p].weight for p in available_providers
        )
        
        import random
        target = random.randint(1, total_weight)
        current_weight = 0
        
        for provider in available_providers:
            current_weight += self.provider_configs[provider].weight
            if current_weight >= target:
                return provider
        
        return available_providers[0]
    
    def _select_by_health(self) -> AIProvider:
        """基于健康状态选择提供商"""
        available_providers = self._get_available_providers()
        if not available_providers:
            raise AIProviderUnavailableError("No available providers")
        
        # 选择错误率最低的提供商
        return min(
            available_providers,
            key=lambda p: self.provider_stats[p]['error_rate']
        )
    
    def _select_round_robin(self) -> AIProvider:
        """轮询选择提供商"""
        available_providers = self._get_available_providers()
        if not available_providers:
            raise AIProviderUnavailableError("No available providers")
        
        # 简单轮询实现
        min_calls = min(
            self.provider_stats[p]['total_calls'] for p in available_providers
        )
        
        for provider in available_providers:
            if self.provider_stats[provider]['total_calls'] == min_calls:
                return provider
        
        return available_providers[0]
    
    def _select_best_from_list(self, providers: List[AIProvider]) -> AIProvider:
        """从提供商列表中选择最佳的"""
        if len(providers) == 1:
            return providers[0]
        
        # 综合考虑延迟和错误率
        def score(provider: AIProvider) -> float:
            stats = self.provider_stats[provider]
            latency_score = 1.0 / (1.0 + stats['avg_latency'])
            error_score = 1.0 - stats['error_rate']
            return latency_score * 0.6 + error_score * 0.4
        
        return max(providers, key=score)
    
    def _get_available_providers(self) -> List[AIProvider]:
        """获取可用的提供商列表"""
        return [
            provider for provider, config in self.provider_configs.items()
            if config.enabled
        ]
    
    def update_stats(self, provider: AIProvider, success: bool, latency: float):
        """更新提供商统计信息"""
        stats = self.provider_stats[provider]
        stats['total_calls'] += 1
        stats['last_call_time'] = datetime.now()
        
        if success:
            stats['success_calls'] += 1
        
        # 更新平均延迟（指数移动平均）
        alpha = 0.1
        if stats['avg_latency'] == 0:
            stats['avg_latency'] = latency
        else:
            stats['avg_latency'] = alpha * latency + (1 - alpha) * stats['avg_latency']
        
        # 更新错误率
        stats['error_rate'] = 1.0 - (stats['success_calls'] / stats['total_calls'])


class AIGateway:
    """AI服务网关
    
    整合路由、熔断、缓存和监控功能的统一AI服务入口。
    """
    
    def __init__(self, 
                 router: AIRouter,
                 cache: AICache,
                 circuit_breaker_config: CircuitBreakerConfig):
        self.router = router
        self.cache = cache
        self.circuit_breakers: Dict[AIProvider, CircuitBreaker] = {}
        self.cb_config = circuit_breaker_config
        self.service_instances: Dict[AIProvider, AIServiceInterface] = {}
        
    def register_service(self, provider: AIProvider, service: AIServiceInterface):
        """注册AI服务实例"""
        self.service_instances[provider] = service
        self.circuit_breakers[provider] = CircuitBreaker(provider, self.cb_config)
        logger.info(f"Registered service for provider: {provider.value}")
    
    async def execute_request(self, request: AIRequest) -> AIResponse:
        """执行AI请求"""
        start_time = time.time()
        
        try:
            # 1. 检查缓存
            cached_response = await self.cache.get(request.cache_key)
            if cached_response:
                logger.info(f"Cache hit for request: {request.request_id}")
                return cached_response
            
            # 2. 选择提供商
            primary_provider = await self.router.select_provider(request)
            
            # 3. 执行请求（带熔断保护）
            response = await self._execute_with_circuit_breaker(
                primary_provider, request, start_time
            )
            
            # 4. 缓存结果
            await self.cache.set(request.cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Gateway request failed: {e}", exc_info=True)
            # 尝试降级处理
            return await self._handle_fallback(request, str(e))
    
    async def _execute_with_circuit_breaker(self, 
                                          provider: AIProvider, 
                                          request: AIRequest,
                                          start_time: float) -> AIResponse:
        """带熔断保护的请求执行"""
        circuit_breaker = self.circuit_breakers.get(provider)
        if not circuit_breaker:
            raise AIProviderUnavailableError(f"No circuit breaker for provider: {provider}")
        
        if not circuit_breaker.call_allowed():
            raise AIProviderUnavailableError(f"Circuit breaker open for provider: {provider}")
        
        try:
            service = self.service_instances.get(provider)
            if not service:
                raise AIProviderUnavailableError(f"No service instance for provider: {provider}")
            
            # 根据场景调用相应方法
            if request.scenario == AIScenario.GENERAL_CHAT:
                response = await service.chat(request)
            elif request.scenario == AIScenario.SENTIMENT_ANALYSIS:
                response = await service.analyze_sentiment(request)
            else:
                response = await service.chat(request)  # 默认降级到聊天
            
            # 记录成功
            latency = time.time() - start_time
            response.response_time = latency
            circuit_breaker.record_success()
            self.router.update_stats(provider, True, latency)
            
            logger.info(f"Request successful: {request.request_id} via {provider.value}")
            return response
            
        except Exception as e:
            # 记录失败
            circuit_breaker.record_failure()
            latency = time.time() - start_time
            self.router.update_stats(provider, False, latency)
            
            logger.error(f"Request failed: {request.request_id} via {provider.value}: {e}")
            raise
    
    async def _handle_fallback(self, request: AIRequest, error_message: str) -> AIResponse:
        """处理降级逻辑"""
        # 返回基本的错误响应
        return AIResponse(
            request_id=request.request_id,
            content=f"很抱歉，AI服务暂时不可用。错误信息：{error_message}",
            provider=AIProvider.DIFY,  # 默认提供商
            scenario=request.scenario,
            success=False,
            error_message=error_message
        )
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取网关健康状态"""
        provider_health = {}
        
        for provider, service in self.service_instances.items():
            try:
                health = await service.health_check()
                circuit_state = self.circuit_breakers[provider].state.value
                stats = self.router.provider_stats[provider]
                
                provider_health[provider.value] = {
                    "health": health,
                    "circuit_state": circuit_state,
                    "stats": stats
                }
            except Exception as e:
                provider_health[provider.value] = {
                    "health": {"status": "unhealthy", "error": str(e)},
                    "circuit_state": "unknown",
                    "stats": {}
                }
        
        return {
            "gateway_status": "healthy",
            "providers": provider_health,
            "cache_stats": {
                "size": len(self.cache.cache),
                "max_size": self.cache.config.max_size,
                "hit_rate": self._calculate_cache_hit_rate()
            }
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        # 这里可以实现更复杂的命中率统计
        return 0.85  # 示例值 