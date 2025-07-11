"""
AI Gateway Dify集成端到端测试

测试Dify在AI Gateway架构中的完整集成，包括：
- Gateway路由到Dify适配器
- 缓存和熔断器集成
- 多场景切换和降级
- 错误处理和恢复
- 性能监控和统计
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any

from app.services.ai.ai_gateway_service import AIGatewayService
from app.services.ai.gateway import AIGateway, AIRouter, AICache, CircuitBreaker
from app.services.ai.adapters.dify_adapter import DifyAdapter
from app.services.ai.interfaces import (
    AIRequest, AIResponse, AIScenario, AIProvider, ChatContext,
    AIServiceError, AIProviderUnavailableError
)


# ================ 测试fixture ================

@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    mock_session = MagicMock()
    return mock_session


@pytest.fixture
def ai_gateway_service(mock_db_session):
    """AI Gateway服务实例"""
    return AIGatewayService(mock_db_session)


@pytest.fixture
def sample_requests():
    """多种场景的示例请求"""
    return {
        "chat": AIRequest(
            request_id="chat-req-001",
            message="你好，我想了解医美服务",
            scenario=AIScenario.GENERAL_CHAT,
            user_id="user-001",
            session_id="session-001"
        ),
        "beauty_plan": AIRequest(
            request_id="plan-req-002",
            message="我想做面部提升，预算2万元",
            scenario=AIScenario.BEAUTY_PLAN,
            user_id="user-002",
            context=ChatContext(
                user_profile={
                    "age": 30,
                    "gender": "female",
                    "budget": "20000",
                    "concerns": ["anti_aging", "skin_tightening"]
                }
            )
        ),
        "consultation_summary": AIRequest(
            request_id="summary-req-003",
            message="总结今天的咨询内容...",
            scenario=AIScenario.CONSULTATION_SUMMARY,
            user_id="user-003"
        ),
        "sentiment": AIRequest(
            request_id="sentiment-req-004",
            message="我对今天的咨询非常满意",
            scenario=AIScenario.SENTIMENT_ANALYSIS,
            user_id="user-004"
        )
    }


@pytest.fixture
def mock_dify_responses():
    """模拟Dify各种响应"""
    return {
        "chat_success": AIResponse(
            request_id="chat-req-001",
            content="欢迎咨询安美智享！我是您的专属医美顾问，请问需要了解哪类项目？",
            provider=AIProvider.DIFY,
            scenario=AIScenario.GENERAL_CHAT,
            success=True,
            response_time=0.8,
            metadata={"dify_app_mode": "chat", "conversation_id": "conv-001"}
        ),
        "plan_success": AIResponse(
            request_id="plan-req-002", 
            content="# 面部提升方案\n\n## 推荐项目\n1. 热玛吉紧肤\n2. 超声刀提升\n\n## 预估费用\n总计：18,000-22,000元",
            provider=AIProvider.DIFY,
            scenario=AIScenario.BEAUTY_PLAN,
            success=True,
            response_time=1.2,
            metadata={"dify_app_mode": "agent", "tools_used": ["price_calculator"]}
        ),
        "error_response": AIResponse(
            request_id="error-req-005",
            content="抱歉，服务暂时不可用",
            provider=AIProvider.DIFY,
            scenario=AIScenario.GENERAL_CHAT,
            success=False,
            error_code="503",
            error_message="Dify服务连接失败"
        )
    }


# ================ AI Gateway集成测试 ================

class TestAIGatewayDifyIntegration:
    """测试AI Gateway与Dify的集成"""
    
    @pytest.mark.asyncio
    async def test_gateway_initialization_with_dify(self, ai_gateway_service):
        """测试Gateway初始化时正确注册Dify服务"""
        
        with patch('app.services.ai.ai_gateway_service.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                DIFY_API_BASE_URL="http://localhost:8000/v1",
                DIFY_CHAT_API_KEY="app-chat-key",
                DIFY_BEAUTY_API_KEY="app-beauty-key",
                DIFY_SUMMARY_API_KEY="app-summary-key"
            )
            
            # 重新初始化Gateway
            ai_gateway_service._initialize_gateway()
            
            assert ai_gateway_service.gateway is not None
            
            # 验证Dify提供商已注册
            assert AIProvider.DIFY in ai_gateway_service.gateway.service_instances
            assert isinstance(ai_gateway_service.gateway.service_instances[AIProvider.DIFY], DifyAdapter)
    
    @pytest.mark.asyncio
    async def test_gateway_routing_to_dify(self, ai_gateway_service, sample_requests, mock_dify_responses):
        """测试Gateway正确路由到Dify服务"""
        
        # Mock Gateway和Dify适配器
        with patch.object(ai_gateway_service.gateway, 'execute_request') as mock_execute:
            mock_execute.return_value = mock_dify_responses["chat_success"]
            
            response = await ai_gateway_service.chat(
                message="你好",
                user_id="user-001",
                session_id="session-001"
            )
            
            assert response.provider == AIProvider.DIFY
            assert response.success is True
            assert "医美顾问" in response.content
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scenario_based_routing(self, ai_gateway_service, sample_requests):
        """测试基于场景的智能路由"""
        
        with patch.object(ai_gateway_service.gateway.router, 'select_provider') as mock_select:
            mock_select.return_value = AIProvider.DIFY
            
            # 测试不同场景的路由
            scenarios_to_test = [
                AIScenario.GENERAL_CHAT,
                AIScenario.BEAUTY_PLAN,
                AIScenario.CONSULTATION_SUMMARY,
                AIScenario.SENTIMENT_ANALYSIS
            ]
            
            for scenario in scenarios_to_test:
                request = sample_requests[scenario.value.split('_')[0]]
                request.scenario = scenario
                
                with patch.object(ai_gateway_service.gateway, 'execute_request'):
                    await ai_gateway_service.gateway.execute_request(request)
                
                # 验证路由选择被调用
                mock_select.assert_called()
                call_args = mock_select.call_args[0][0]
                assert call_args.scenario == scenario
    
    @pytest.mark.asyncio
    async def test_caching_integration(self, ai_gateway_service, sample_requests, mock_dify_responses):
        """测试缓存集成"""
        
        chat_request = sample_requests["chat"]
        
        with patch.object(ai_gateway_service.gateway.cache, 'get') as mock_cache_get:
            with patch.object(ai_gateway_service.gateway.cache, 'set') as mock_cache_set:
                with patch.object(ai_gateway_service.gateway, '_execute_with_circuit_breaker') as mock_execute:
                    
                    # 第一次请求 - 缓存未命中
                    mock_cache_get.return_value = None
                    mock_execute.return_value = mock_dify_responses["chat_success"]
                    
                    response1 = await ai_gateway_service.gateway.execute_request(chat_request)
                    
                    # 验证缓存查询和设置
                    mock_cache_get.assert_called_once()
                    mock_cache_set.assert_called_once()
                    assert response1.provider == AIProvider.DIFY
                    
                    # 第二次请求 - 缓存命中
                    mock_cache_get.return_value = mock_dify_responses["chat_success"]
                    mock_cache_get.reset_mock()
                    mock_execute.reset_mock()
                    
                    response2 = await ai_gateway_service.gateway.execute_request(chat_request)
                    
                    # 验证缓存命中，没有调用实际服务
                    mock_cache_get.assert_called_once()
                    mock_execute.assert_not_called()
                    assert response2 == mock_dify_responses["chat_success"]
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_protection(self, ai_gateway_service, sample_requests):
        """测试熔断器保护"""
        
        chat_request = sample_requests["chat"]
        
        # Mock熔断器
        with patch.object(ai_gateway_service.gateway.circuit_breakers[AIProvider.DIFY], 'call_allowed') as mock_allowed:
            with patch.object(ai_gateway_service.gateway.circuit_breakers[AIProvider.DIFY], 'record_failure') as mock_record_failure:
                
                # 测试熔断器开启状态
                mock_allowed.return_value = False
                
                with pytest.raises(AIProviderUnavailableError) as exc_info:
                    await ai_gateway_service.gateway._execute_with_circuit_breaker(
                        AIProvider.DIFY, chat_request, 0.0
                    )
                
                assert "circuit breaker open" in str(exc_info.value).lower()
                
                # 测试熔断器关闭状态下的失败记录
                mock_allowed.return_value = True
                
                with patch.object(ai_gateway_service.gateway.service_instances[AIProvider.DIFY], 'chat') as mock_chat:
                    mock_chat.side_effect = Exception("Service error")
                    
                    with pytest.raises(Exception):
                        await ai_gateway_service.gateway._execute_with_circuit_breaker(
                            AIProvider.DIFY, chat_request, 0.0
                        )
                    
                    # 验证失败被记录
                    mock_record_failure.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, ai_gateway_service, sample_requests):
        """测试降级机制"""
        
        chat_request = sample_requests["chat"]
        
        with patch.object(ai_gateway_service.gateway, '_execute_with_circuit_breaker') as mock_execute:
            with patch.object(ai_gateway_service.gateway, '_handle_fallback') as mock_fallback:
                
                # 模拟主要服务失败
                mock_execute.side_effect = AIProviderUnavailableError("Dify不可用", AIProvider.DIFY)
                mock_fallback.return_value = AIResponse(
                    request_id=chat_request.request_id,
                    content="抱歉，服务暂时不可用，请稍后再试",
                    provider=AIProvider.OPENAI,
                    scenario=chat_request.scenario,
                    success=False
                )
                
                response = await ai_gateway_service.gateway.execute_request(chat_request)
                
                # 验证降级处理被调用
                mock_fallback.assert_called_once()
                assert not response.success
                assert "暂时不可用" in response.content
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, ai_gateway_service, sample_requests, mock_dify_responses):
        """测试性能监控"""
        
        chat_request = sample_requests["chat"]
        
        with patch.object(ai_gateway_service.gateway.router, 'update_stats') as mock_update_stats:
            with patch.object(ai_gateway_service.gateway, '_execute_with_circuit_breaker') as mock_execute:
                
                mock_execute.return_value = mock_dify_responses["chat_success"]
                
                await ai_gateway_service.gateway.execute_request(chat_request)
                
                # 验证统计更新被调用
                mock_update_stats.assert_called_once()
                call_args = mock_update_stats.call_args
                assert call_args[0][0] == AIProvider.DIFY  # 提供商
                assert call_args[0][1] is True  # 成功状态
                assert isinstance(call_args[0][2], float)  # 延迟时间
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self, ai_gateway_service):
        """测试健康检查集成"""
        
        with patch.object(ai_gateway_service.gateway.service_instances[AIProvider.DIFY], 'health_check') as mock_health:
            mock_health.return_value = {
                "provider": "dify",
                "status": "healthy",
                "apps": {
                    "general_chat": {"status": "healthy", "app_mode": "chat"},
                    "beauty_agent": {"status": "healthy", "app_mode": "agent"}
                }
            }
            
            health_status = await ai_gateway_service.get_health_status()
            
            assert "providers" in health_status
            assert AIProvider.DIFY.value in health_status["providers"]
            
            dify_health = health_status["providers"][AIProvider.DIFY.value]
            assert dify_health["health"]["status"] == "healthy"
            assert "apps" in dify_health["health"]


# ================ 端到端场景测试 ================

class TestEndToEndScenarios:
    """端到端场景测试"""
    
    @pytest.mark.asyncio
    async def test_complete_consultation_flow(self, ai_gateway_service, mock_dify_responses):
        """测试完整的咨询流程"""
        
        # 步骤1: 客户初始咨询
        with patch.object(ai_gateway_service.gateway, 'execute_request') as mock_execute:
            mock_execute.return_value = mock_dify_responses["chat_success"]
            
            initial_response = await ai_gateway_service.chat(
                message="我想了解面部年轻化的治疗方案",
                user_id="customer-001",
                session_id="consultation-session-001"
            )
            
            assert initial_response.success
            assert "医美顾问" in initial_response.content
        
        # 步骤2: 生成个性化方案
        with patch.object(ai_gateway_service.gateway, 'execute_request') as mock_execute:
            mock_execute.return_value = mock_dify_responses["plan_success"]
            
            plan_response = await ai_gateway_service.generate_beauty_plan(
                requirements="30岁女性，想要面部提升，预算2万",
                user_id="customer-001",
                user_profile={
                    "age": 30,
                    "gender": "female", 
                    "budget": "20000",
                    "concerns": ["anti_aging"]
                }
            )
            
            assert plan_response.success
            assert "面部提升方案" in plan_response.content
        
        # 步骤3: 总结咨询内容
        consultation_summary = await ai_gateway_service.summarize_consultation(
            conversation_text="客户咨询面部年轻化方案，年龄30岁，预算2万元...",
            user_id="consultant-001"
        )
        
        assert consultation_summary.success
        
        # 步骤4: 分析客户情感
        sentiment_analysis = await ai_gateway_service.analyze_sentiment(
            text="我对推荐的方案很满意，想要预约面诊",
            user_id="customer-001"
        )
        
        assert sentiment_analysis.success
        assert sentiment_analysis.sentiment_score > 0.5  # 正面情感
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self, ai_gateway_service):
        """测试错误恢复流程"""
        
        # 模拟服务故障
        with patch.object(ai_gateway_service.gateway, 'execute_request') as mock_execute:
            # 第一次调用失败
            mock_execute.side_effect = [
                AIProviderUnavailableError("Dify服务不可用", AIProvider.DIFY),
                AIResponse(  # 恢复后的成功响应
                    request_id="recovery-req-001",
                    content="服务已恢复，欢迎咨询",
                    provider=AIProvider.DIFY,
                    scenario=AIScenario.GENERAL_CHAT,
                    success=True
                )
            ]
            
            # 第一次请求失败
            with pytest.raises(AIProviderUnavailableError):
                await ai_gateway_service.chat(
                    message="测试消息",
                    user_id="test-user",
                    session_id="test-session"
                )
            
            # 第二次请求成功
            mock_execute.side_effect = None
            mock_execute.return_value = AIResponse(
                request_id="recovery-req-002",
                content="服务已恢复，欢迎咨询",
                provider=AIProvider.DIFY,
                scenario=AIScenario.GENERAL_CHAT,
                success=True
            )
            
            recovery_response = await ai_gateway_service.chat(
                message="测试恢复",
                user_id="test-user",
                session_id="test-session"
            )
            
            assert recovery_response.success
            assert "服务已恢复" in recovery_response.content
    
    @pytest.mark.asyncio
    async def test_high_load_scenario(self, ai_gateway_service, mock_dify_responses):
        """测试高负载场景"""
        
        # 并发请求数量
        concurrent_requests = 20
        
        async def single_request(request_id: int):
            """单个请求"""
            return await ai_gateway_service.chat(
                message=f"并发测试消息 {request_id}",
                user_id=f"user-{request_id}",
                session_id=f"session-{request_id}"
            )
        
        with patch.object(ai_gateway_service.gateway, 'execute_request') as mock_execute:
            mock_execute.return_value = mock_dify_responses["chat_success"]
            
            # 并发执行请求
            tasks = [single_request(i) for i in range(concurrent_requests)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证结果
            successful_responses = [r for r in responses if isinstance(r, AIResponse) and r.success]
            assert len(successful_responses) >= concurrent_requests * 0.8  # 至少80%成功率
            
            # 验证调用次数
            assert mock_execute.call_count == concurrent_requests


# ================ 配置和部署测试 ================

class TestConfigurationAndDeployment:
    """配置和部署测试"""
    
    def test_configuration_validation(self):
        """测试配置验证"""
        from app.services.ai.adapters.dify_adapter import DifyConnectionConfig, DifyAppConfig
        
        # 有效配置
        valid_config = DifyConnectionConfig(
            base_url="http://localhost:8000/v1",
            apps={
                "chat": DifyAppConfig(
                    app_id="app-001",
                    app_name="Test Chat",
                    app_mode="chat",
                    api_key="test-key"
                )
            }
        )
        
        assert valid_config.base_url.endswith("/v1")
        assert len(valid_config.apps) == 1
        assert valid_config.timeout == 30  # 默认值
    
    @pytest.mark.asyncio
    async def test_service_discovery(self, ai_gateway_service):
        """测试服务发现"""
        
        # 获取已注册的服务提供商
        providers = ai_gateway_service.gateway.service_instances.keys()
        
        assert AIProvider.DIFY in providers
        
        # 验证服务实例类型
        dify_instance = ai_gateway_service.gateway.service_instances[AIProvider.DIFY]
        assert isinstance(dify_instance, DifyAdapter)
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, ai_gateway_service, sample_requests):
        """测试优雅降级"""
        
        # 模拟部分服务不可用
        with patch.object(ai_gateway_service.gateway.service_instances[AIProvider.DIFY], 'chat') as mock_chat:
            mock_chat.side_effect = AIProviderUnavailableError("服务维护中", AIProvider.DIFY)
            
            # 配置OpenAI作为备选
            with patch.object(ai_gateway_service.gateway.router, 'select_provider') as mock_select:
                mock_select.return_value = AIProvider.OPENAI
                
                with patch.object(ai_gateway_service.gateway, '_handle_fallback') as mock_fallback:
                    mock_fallback.return_value = AIResponse(
                        request_id="fallback-001",
                        content="正在使用备选服务为您提供支持",
                        provider=AIProvider.OPENAI,
                        scenario=AIScenario.GENERAL_CHAT,
                        success=True
                    )
                    
                    response = await ai_gateway_service.gateway.execute_request(sample_requests["chat"])
                    
                    assert response.success
                    assert response.provider == AIProvider.OPENAI
                    assert "备选服务" in response.content 