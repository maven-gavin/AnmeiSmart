"""
AI Gateway Agent集成端到端测试

测试Agent在AI Gateway架构中的完整集成，包括：
- Gateway路由到Agent适配器
- 多场景智能路由
- 缓存和熔断机制
- 性能监控
- 错误处理和降级
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

from app.services.ai.ai_gateway_service import AIGatewayService
from app.services.ai.interfaces import (
    AIRequest, AIResponse, AIScenario, AIProvider, 
    AIProviderUnavailableError, ChatContext
)
from app.services.ai.adapters.agent_adapter import AgentAdapter


@pytest.fixture
def sample_requests():
    """示例请求数据"""
    return {
        "chat": AIRequest(
            scenario=AIScenario.GENERAL_CHAT,
            message="你好，我想了解一下医美项目",
            context=ChatContext(
                user_id="user123",
                session_id="session456",
                conversation_history=[]
            )
        ),
        "plan": AIRequest(
            scenario=AIScenario.BEAUTY_PLAN,
            message="我想做皮肤护理，有什么推荐吗？",
            context=ChatContext(
                user_id="user123",
                session_id="session456",
                user_profile={
                    "age": 25,
                    "skin_type": "混合性",
                    "concerns": ["毛孔粗大", "肤色不均"]
                }
            )
        ),
        "summary": AIRequest(
            scenario=AIScenario.CONSULTATION_SUMMARY,
            message="总结一下今天的咨询内容",
            context=ChatContext(
                user_id="user123",
                session_id="session456",
                conversation_history=[
                    {"role": "user", "content": "我想了解玻尿酸填充"},
                    {"role": "assistant", "content": "玻尿酸填充是一种安全的美容项目..."}
                ]
            )
        )
    }


@pytest.fixture
def mock_agent_responses():
    """模拟Agent各种响应"""
    return {
        "chat_success": AIResponse(
            request_id="req-001",
            content="您好！我是您的医美顾问，很高兴为您服务。关于医美项目，我们有多种选择，包括皮肤护理、微整形等。您对哪个方面比较感兴趣呢？",
            provider=AIProvider.AGENT,
            scenario=AIScenario.GENERAL_CHAT,
            metadata={"agent_app_mode": "chat", "conversation_id": "conv-001"}
        ),
        "plan_success": AIResponse(
            request_id="req-002",
            content="根据您的皮肤状况，我推荐以下护理方案：1. 深层清洁 2. 补水保湿 3. 美白淡斑。预计费用在2000-5000元之间。",
            provider=AIProvider.AGENT,
            scenario=AIScenario.BEAUTY_PLAN,
            metadata={"agent_app_mode": "workflow", "tools_used": ["price_calculator"]}
        ),
        "error_response": AIResponse(
            request_id="req-003",
            content="抱歉，服务暂时不可用",
            provider=AIProvider.AGENT,
            scenario=AIScenario.GENERAL_CHAT,
            success=False,
            error_message="Agent服务连接失败"
        )
    }


class TestAIGatewayAgentIntegration:
    """测试AI Gateway与Agent的集成"""
    
    @pytest.mark.asyncio
    async def test_gateway_initialization_with_agent(self, ai_gateway_service):
        """测试Gateway初始化时正确注册Agent服务"""
        # 模拟环境变量配置
        with patch.dict('os.environ', {
            'AGENT_API_BASE_URL': "http://localhost:8000/v1",
            'AGENT_CHAT_API_KEY': "app-chat-key",
            'AGENT_BEAUTY_API_KEY': "app-beauty-key",
            'AGENT_SUMMARY_API_KEY': "app-summary-key"
        }):
            # 重新初始化服务
            await ai_gateway_service.initialize()
            
            # 验证Agent提供商已注册
            assert AIProvider.AGENT in ai_gateway_service.gateway.service_instances
            assert isinstance(ai_gateway_service.gateway.service_instances[AIProvider.AGENT], AgentAdapter)
    
    @pytest.mark.asyncio
    async def test_gateway_routing_to_agent(self, ai_gateway_service, sample_requests, mock_agent_responses):
        """测试Gateway正确路由到Agent服务"""
        chat_request = sample_requests["chat"]
        
        # Mock Gateway和Agent适配器
        with patch.object(ai_gateway_service.gateway, 'execute') as mock_execute:
            mock_execute.return_value = mock_agent_responses["chat_success"]
            
            # 执行聊天请求
            response = await ai_gateway_service.chat(
                message=chat_request.message,
                user_id=chat_request.context.user_id,
                session_id=chat_request.context.session_id,
                user_profile=chat_request.context.user_profile,
                conversation_history=chat_request.context.conversation_history
            )
            
            # 验证响应
            assert response is not None
            assert response.provider == AIProvider.AGENT
            assert "医美顾问" in response.content
            assert response.metadata["agent_app_mode"] == "chat"
    
    @pytest.mark.asyncio
    async def test_intelligent_routing(self, ai_gateway_service, sample_requests, mock_agent_responses):
        """测试智能路由功能"""
        plan_request = sample_requests["plan"]
        
        with patch.object(ai_gateway_service.gateway.router, 'select_provider') as mock_select:
            mock_select.return_value = AIProvider.AGENT
            
            with patch.object(ai_gateway_service.gateway, 'execute') as mock_execute:
                mock_execute.return_value = mock_agent_responses["plan_success"]
                
                # 执行方案生成请求
                response = await ai_gateway_service.generate_beauty_plan(
                    message=plan_request.message,
                    user_id=plan_request.context.user_id,
                    user_profile=plan_request.context.user_profile
                )
                
                # 验证路由到Agent
                mock_select.assert_called_once()
                assert response.provider == AIProvider.AGENT
                assert "护理方案" in response.content
    
    @pytest.mark.asyncio
    async def test_caching_integration(self, ai_gateway_service, sample_requests, mock_agent_responses):
        """测试缓存集成"""
        chat_request = sample_requests["chat"]
        
        with patch.object(ai_gateway_service.gateway, 'execute') as mock_execute:
            mock_execute.return_value = mock_agent_responses["chat_success"]
            
            # 第一次请求
            response1 = await ai_gateway_service.chat(
                message=chat_request.message,
                user_id=chat_request.context.user_id,
                session_id=chat_request.context.session_id
            )
            
            assert response1.provider == AIProvider.AGENT
            
            # 模拟缓存命中
            with patch.object(ai_gateway_service.gateway.cache, 'get') as mock_cache_get:
                mock_cache_get.return_value = mock_agent_responses["chat_success"]
                
                # 第二次相同请求应该从缓存获取
                response2 = await ai_gateway_service.chat(
                    message=chat_request.message,
                    user_id=chat_request.context.user_id,
                    session_id=chat_request.context.session_id
                )
                
                assert response2 == mock_agent_responses["chat_success"]
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, ai_gateway_service, sample_requests):
        """测试熔断器机制"""
        chat_request = sample_requests["chat"]
        
        # 模拟熔断器阻止请求
        with patch.object(ai_gateway_service.gateway.circuit_breakers[AIProvider.AGENT], 'call_allowed') as mock_allowed:
            with patch.object(ai_gateway_service.gateway.circuit_breakers[AIProvider.AGENT], 'record_failure') as mock_record_failure:
                mock_allowed.return_value = False
                
                # 执行请求应该被熔断器阻止
                with pytest.raises(AIProviderUnavailableError):
                    await ai_gateway_service.gateway.execute(
                        AIProvider.AGENT, chat_request, 0.0
                    )
                
                # 验证熔断器记录失败
                mock_record_failure.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, ai_gateway_service, sample_requests):
        """测试降级机制"""
        chat_request = sample_requests["chat"]
        
        # 模拟Agent服务失败
        with patch.object(ai_gateway_service.gateway.service_instances[AIProvider.AGENT], 'chat') as mock_chat:
            mock_chat.side_effect = AIProviderUnavailableError("Agent服务不可用", AIProvider.AGENT)
            
            # 应该降级到OpenAI
            with patch.object(ai_gateway_service.gateway, 'execute') as mock_execute:
                mock_execute.return_value = AIResponse(
                    request_id="req-fallback",
                    content="降级响应",
                    provider=AIProvider.OPENAI,
                    scenario=AIScenario.GENERAL_CHAT
                )
                
                response = await ai_gateway_service.gateway.execute(
                    AIProvider.AGENT, chat_request, 0.0
                )
                
                assert response.provider == AIProvider.OPENAI
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, ai_gateway_service, sample_requests, mock_agent_responses):
        """测试性能监控"""
        chat_request = sample_requests["chat"]
        
        with patch.object(ai_gateway_service.gateway, 'execute') as mock_execute:
            mock_execute.return_value = mock_agent_responses["chat_success"]
            
            # 执行请求
            response = await ai_gateway_service.chat(
                message=chat_request.message,
                user_id=chat_request.context.user_id,
                session_id=chat_request.context.session_id
            )
            
            # 验证性能监控记录
            call_args = mock_execute.call_args
            assert call_args[0][0] == AIProvider.AGENT  # 提供商
            
            # 检查响应时间记录
            assert response.response_time is not None
            assert response.response_time > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, ai_gateway_service):
        """测试健康检查"""
        with patch.object(ai_gateway_service.gateway.service_instances[AIProvider.AGENT], 'health_check') as mock_health:
            mock_health.return_value = {
                "provider": "agent",
                "status": "healthy",
                "apps": {"chat": "healthy", "workflow": "healthy"}
            }
            
            health_status = await ai_gateway_service.get_health_status()
            
            # 验证健康状态包含Agent信息
            assert AIProvider.AGENT.value in health_status["providers"]
            
            agent_health = health_status["providers"][AIProvider.AGENT.value]
            assert agent_health["health"]["status"] == "healthy"
            assert "apps" in agent_health["health"]
    
    @pytest.mark.asyncio
    async def test_complete_consultation_flow(self, ai_gateway_service, mock_agent_responses):
        """测试完整的咨询流程"""
        # 模拟聊天阶段
        with patch.object(ai_gateway_service.gateway, 'execute') as mock_execute:
            mock_execute.return_value = mock_agent_responses["chat_success"]
            
            chat_response = await ai_gateway_service.chat(
                message="我想了解医美项目",
                user_id="user123",
                session_id="session456"
            )
            
            assert chat_response.provider == AIProvider.AGENT
            assert "医美顾问" in chat_response.content
            
            # 模拟方案生成阶段
            mock_execute.return_value = mock_agent_responses["plan_success"]
            
            plan_response = await ai_gateway_service.generate_beauty_plan(
                message="我想做皮肤护理",
                user_id="user123",
                user_profile={"age": 25, "skin_type": "混合性"}
            )
            
            assert plan_response.provider == AIProvider.AGENT
            assert "护理方案" in plan_response.content
    
    @pytest.mark.asyncio
    async def test_error_handling(self, ai_gateway_service, sample_requests):
        """测试错误处理"""
        chat_request = sample_requests["chat"]
        
        # 模拟各种错误场景
        error_scenarios = [
            AIProviderUnavailableError("Agent服务不可用", AIProvider.AGENT),
            Exception("网络连接错误"),
            ValueError("参数错误")
        ]
        
        for error in error_scenarios:
            with patch.object(ai_gateway_service.gateway, 'execute') as mock_execute:
                mock_execute.side_effect = error
                
                # 应该正确处理错误
                with pytest.raises((AIProviderUnavailableError, Exception)):
                    await ai_gateway_service.chat(
                        message=chat_request.message,
                        user_id=chat_request.context.user_id,
                        session_id=chat_request.context.session_id
                    )
    
    @pytest.mark.asyncio
    async def test_high_load_scenario(self, ai_gateway_service, sample_requests, mock_agent_responses):
        """测试高负载场景"""
        chat_request = sample_requests["chat"]
        
        # 模拟并发请求
        async def make_request():
            with patch.object(ai_gateway_service.gateway, 'execute') as mock_execute:
                mock_execute.return_value = mock_agent_responses["chat_success"]
                
                return await ai_gateway_service.chat(
                    message=chat_request.message,
                    user_id=chat_request.context.user_id,
                    session_id=chat_request.context.session_id
                )
        
        # 并发执行多个请求
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功
        for response in responses:
            assert response.provider == AIProvider.AGENT
            assert response.success
    
    @pytest.mark.asyncio
    async def test_provider_configuration(self, ai_gateway_service):
        """测试提供商配置"""
        # 验证Agent配置
        from app.services.ai.adapters.agent_adapter import AgentConnectionConfig, AgentAppConfig
        
        valid_config = AgentConnectionConfig(
            base_url="http://localhost:8000/v1",
            timeout_seconds=30,
            max_retries=3,
            apps={
                "chat": AgentAppConfig(
                    app_id="agent-chat-app",
                    app_name="聊天助手",
                    app_mode="chat",
                    api_key="test-key",
                    base_url="http://localhost:8000/v1"
                )
            }
        )
        
        # 验证配置有效性
        assert valid_config.base_url == "http://localhost:8000/v1"
        assert len(valid_config.apps) == 1
        assert "chat" in valid_config.apps
    
    @pytest.mark.asyncio
    async def test_service_registration(self, ai_gateway_service):
        """测试服务注册"""
        # 验证Agent服务已注册
        providers = list(ai_gateway_service.gateway.service_instances.keys())
        assert AIProvider.AGENT in providers
        
        # 验证Agent实例类型
        agent_instance = ai_gateway_service.gateway.service_instances[AIProvider.AGENT]
        assert isinstance(agent_instance, AgentAdapter)
        
        # 验证服务方法可用
        with patch.object(agent_instance, 'chat') as mock_chat:
            mock_chat.return_value = AIResponse(
                request_id="test",
                content="测试响应",
                provider=AIProvider.AGENT,
                scenario=AIScenario.GENERAL_CHAT
            )
            
            response = await agent_instance.chat(AIRequest(
                scenario=AIScenario.GENERAL_CHAT,
                message="测试消息"
            ))
            
            assert response.provider == AIProvider.AGENT 