"""
Dify集成测试套件

全面测试AI Gateway中的Dify集成功能，包括：
- Dify适配器的所有功能
- 不同应用模式（chat/agent/workflow/completion）
- 场景路由和降级机制
- 错误处理和恢复
- 健康检查和监控
- 配置验证和管理
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List
import aiohttp
from datetime import datetime

from app.services.ai.adapters.dify_adapter import (
    DifyAdapter, DifyConnectionConfig, DifyAppConfig, DifyAPIClient
)
from app.services.ai.interfaces import (
    AIRequest, AIResponse, PlanResponse, SummaryResponse, SentimentResponse,
    AIScenario, AIProvider, ChatContext, ResponseFormat,
    AIServiceError, AIProviderUnavailableError, AIAuthenticationError
)


# ================ 测试数据和fixture ================

@pytest.fixture
def mock_dify_apps():
    """模拟Dify应用配置"""
    return {
        "general_chat": DifyAppConfig(
            app_id="dify-chat-001",
            app_name="通用聊天助手",
            app_mode="chat",
            api_key="app-chat-key-001",
            scenarios=[AIScenario.GENERAL_CHAT, AIScenario.CUSTOMER_SERVICE]
        ),
        "beauty_agent": DifyAppConfig(
            app_id="dify-agent-002", 
            app_name="医美方案专家",
            app_mode="agent",
            api_key="app-agent-key-002",
            scenarios=[AIScenario.BEAUTY_PLAN, AIScenario.MEDICAL_ADVICE],
            tools=[
                {"name": "price_calculator", "enabled": True},
                {"name": "risk_assessor", "enabled": True}
            ],
            variables={"consultation_type": "beauty", "language": "zh-CN"}
        ),
        "summary_workflow": DifyAppConfig(
            app_id="dify-workflow-003",
            app_name="咨询总结工作流",
            app_mode="workflow", 
            api_key="app-workflow-key-003",
            scenarios=[AIScenario.CONSULTATION_SUMMARY]
        ),
        "sentiment_completion": DifyAppConfig(
            app_id="dify-completion-004",
            app_name="情感分析引擎",
            app_mode="completion",
            api_key="app-completion-key-004",
            scenarios=[AIScenario.SENTIMENT_ANALYSIS]
        )
    }


@pytest.fixture
def dify_config(mock_dify_apps):
    """Dify连接配置"""
    return DifyConnectionConfig(
        base_url="http://localhost:8000/v1",
        tenant_id="test-tenant-001",
        apps=mock_dify_apps,
        timeout=30,
        max_retries=3,
        rate_limit=100
    )


@pytest.fixture
def sample_ai_request():
    """示例AI请求"""
    return AIRequest(
        request_id="test-req-001",
        message="我想了解双眼皮手术的相关信息",
        scenario=AIScenario.BEAUTY_PLAN,
        context=ChatContext(
            user_id="user-001",
            session_id="session-001",
            user_profile={
                "age": 25,
                "gender": "female",
                "skin_type": "mixed",
                "concerns": ["eyelid_surgery"],
                "budget": "10000-20000"
            },
            conversation_history=[
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "您好！欢迎咨询医美服务"}
            ]
        ),
        response_format=ResponseFormat.JSON
    )


@pytest.fixture
def mock_dify_api_responses():
    """模拟Dify API响应"""
    return {
        "chat_response": {
            "id": "msg-chat-001",
            "answer": "根据您的需求，双眼皮手术是个不错的选择。我建议您考虑埋线法，这种方法恢复期短，效果自然...",
            "conversation_id": "conv-001",
            "created_at": "2024-01-15T10:30:00Z",
            "metadata": {
                "usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 200,
                    "total_tokens": 350
                }
            }
        },
        "agent_response": {
            "id": "msg-agent-002",
            "answer": "经过综合分析，我为您定制了以下医美方案：\\n\\n## 眼部提升方案\\n\\n### 推荐项目\\n1. 双眼皮成型术（埋线法）\\n2. 开眼角微调\\n\\n### 预估费用\\n- 总计：15,000-18,000元\\n\\n### 恢复时间\\n- 消肿期：7-10天\\n- 完全恢复：1-3个月",
            "conversation_id": "conv-002", 
            "tool_calls": [
                {"tool": "price_calculator", "result": {"total_cost": 16500}},
                {"tool": "risk_assessor", "result": {"risk_level": "low"}}
            ],
            "metadata": {
                "usage": {"total_tokens": 450}
            }
        },
        "workflow_response": {
            "id": "workflow-run-003",
            "data": {
                "outputs": {
                    "summary": "本次咨询客户主要关心双眼皮手术，年龄25岁，预算充足，建议埋线法",
                    "key_points": ["双眼皮手术", "埋线法优先", "预算15-20k", "恢复期关注"],
                    "action_items": ["安排面诊", "提供案例", "制定详细方案"],
                    "sentiment_score": 0.75
                }
            },
            "status": "succeeded",
            "metadata": {"usage": {"total_tokens": 280}}
        },
        "completion_response": {
            "id": "completion-004",
            "answer": "情感分析结果：积极 (0.82)",
            "metadata": {
                "usage": {"total_tokens": 120},
                "analysis": {
                    "sentiment": "positive",
                    "confidence": 0.92,
                    "emotions": {"期待": 0.6, "信任": 0.5, "好奇": 0.4}
                }
            }
        },
        "error_response": {
            "error": {
                "type": "invalid_api_key",
                "message": "Invalid API key provided"
            }
        }
    }


# ================ DifyAPIClient 测试 ================

class TestDifyAPIClient:
    """测试Dify API客户端"""
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self, dify_config):
        """测试客户端上下文管理器"""
        client = DifyAPIClient(dify_config)
        
        async with client:
            assert client.session is not None
            assert isinstance(client.session, aiohttp.ClientSession)
        
        # 验证会话已关闭
        assert client.session.closed
    
    @pytest.mark.asyncio
    async def test_chat_completion_success(self, dify_config, mock_dify_apps, sample_ai_request, mock_dify_api_responses):
        """测试聊天完成API成功调用"""
        client = DifyAPIClient(dify_config)
        app_config = mock_dify_apps["general_chat"]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # 模拟成功响应
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_dify_api_responses["chat_response"])
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with client:
                result = await client.chat_completion(app_config, sample_ai_request)
            
            # 验证请求参数
            call_args = mock_post.call_args
            assert call_args[1]["json"]["query"] == sample_ai_request.message
            assert call_args[1]["json"]["user"] == sample_ai_request.user_id
            assert call_args[1]["headers"]["Authorization"] == f"Bearer {app_config.api_key}"
            
            # 验证响应
            assert result["id"] == "msg-chat-001"
            assert "双眼皮手术" in result["answer"]
    
    @pytest.mark.asyncio
    async def test_chat_completion_auth_error(self, dify_config, mock_dify_apps, sample_ai_request):
        """测试认证失败"""
        client = DifyAPIClient(dify_config)
        app_config = mock_dify_apps["general_chat"]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # 模拟认证失败
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value="Unauthorized")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with client:
                with pytest.raises(AIAuthenticationError) as exc_info:
                    await client.chat_completion(app_config, sample_ai_request)
                
                assert exc_info.value.provider == AIProvider.DIFY
                assert "authentication failed" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_workflow_run_success(self, dify_config, mock_dify_apps, sample_ai_request, mock_dify_api_responses):
        """测试工作流运行成功"""
        client = DifyAPIClient(dify_config)
        app_config = mock_dify_apps["summary_workflow"]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_dify_api_responses["workflow_response"])
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with client:
                result = await client.workflow_run(app_config, sample_ai_request)
            
            # 验证工作流输入参数
            call_args = mock_post.call_args
            inputs = call_args[1]["json"]["inputs"]
            assert inputs["task_type"] == sample_ai_request.scenario.value
            assert inputs["input_text"] == sample_ai_request.message
            
            # 验证响应
            assert result["status"] == "succeeded"
            assert "summary" in result["data"]["outputs"]
    
    @pytest.mark.asyncio
    async def test_completion_success(self, dify_config, mock_dify_apps, sample_ai_request, mock_dify_api_responses):
        """测试文本完成成功"""
        client = DifyAPIClient(dify_config)
        app_config = mock_dify_apps["sentiment_completion"]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_dify_api_responses["completion_response"])
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with client:
                result = await client.completion(app_config, sample_ai_request)
            
            assert result["answer"] == "情感分析结果：积极 (0.82)"
    
    @pytest.mark.asyncio
    async def test_get_application_config(self, dify_config, mock_dify_apps):
        """测试获取应用配置"""
        client = DifyAPIClient(dify_config)
        app_config = mock_dify_apps["general_chat"]
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "app_id": app_config.app_id,
                "name": app_config.app_name,
                "mode": app_config.app_mode,
                "enabled": True
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with client:
                result = await client.get_application_config(app_config)
            
            assert result["app_id"] == app_config.app_id
            assert result["mode"] == app_config.app_mode
    
    @pytest.mark.asyncio
    async def test_connection_error(self, dify_config, mock_dify_apps, sample_ai_request):
        """测试连接错误"""
        client = DifyAPIClient(dify_config)
        app_config = mock_dify_apps["general_chat"]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = aiohttp.ClientError("Connection failed")
            
            async with client:
                with pytest.raises(AIProviderUnavailableError) as exc_info:
                    await client.chat_completion(app_config, sample_ai_request)
                
                assert "connection error" in str(exc_info.value).lower()
    
    def test_build_inputs(self, dify_config, sample_ai_request):
        """测试输入参数构建"""
        client = DifyAPIClient(dify_config)
        
        inputs = client._build_inputs(sample_ai_request)
        
        # 验证用户档案信息
        assert inputs["user_age"] == 25
        assert inputs["user_gender"] == "female"
        assert inputs["user_skin_type"] == "mixed"
        assert inputs["user_budget"] == "10000-20000"
        
        # 验证对话历史
        assert "conversation_history" in inputs
        assert "你好" in inputs["conversation_history"]
        assert "欢迎咨询" in inputs["conversation_history"]
    
    def test_build_workflow_inputs(self, dify_config, sample_ai_request):
        """测试工作流输入参数构建"""
        client = DifyAPIClient(dify_config)
        
        inputs = client._build_workflow_inputs(sample_ai_request)
        
        # 验证工作流特有参数
        assert inputs["task_type"] == sample_ai_request.scenario.value
        assert inputs["input_text"] == sample_ai_request.message
        assert inputs["language"] == "zh-CN"
        assert inputs["output_format"] == sample_ai_request.response_format.value


# ================ DifyAdapter 测试 ================

class TestDifyAdapter:
    """测试Dify适配器"""
    
    def test_adapter_initialization(self, dify_config):
        """测试适配器初始化"""
        adapter = DifyAdapter(dify_config)
        
        assert adapter.config == dify_config
        assert isinstance(adapter.client, DifyAPIClient)
        assert len(adapter.scenario_app_mapping) == 6
        
        # 验证场景映射
        assert adapter.scenario_app_mapping[AIScenario.GENERAL_CHAT] == "chat"
        assert adapter.scenario_app_mapping[AIScenario.BEAUTY_PLAN] == "agent"
        assert adapter.scenario_app_mapping[AIScenario.CONSULTATION_SUMMARY] == "workflow"
        assert adapter.scenario_app_mapping[AIScenario.SENTIMENT_ANALYSIS] == "completion"
    
    def test_select_app_for_scenario(self, dify_config, mock_dify_apps):
        """测试场景应用选择"""
        adapter = DifyAdapter(dify_config)
        
        # 测试直接场景匹配
        beauty_app = adapter._select_app_for_scenario(AIScenario.BEAUTY_PLAN)
        assert beauty_app.app_id == "dify-agent-002"
        assert beauty_app.app_mode == "agent"
        
        # 测试通用聊天匹配
        chat_app = adapter._select_app_for_scenario(AIScenario.GENERAL_CHAT)
        assert chat_app.app_id == "dify-chat-001"
        assert chat_app.app_mode == "chat"
        
        # 测试客服场景（应该匹配到聊天应用）
        service_app = adapter._select_app_for_scenario(AIScenario.CUSTOMER_SERVICE)
        assert service_app.app_id == "dify-chat-001"
    
    def test_select_app_no_config(self, mock_dify_apps):
        """测试无应用配置时的错误处理"""
        empty_config = DifyConnectionConfig(
            base_url="http://localhost:8000/v1",
            apps={}
        )
        adapter = DifyAdapter(empty_config)
        
        with pytest.raises(AIServiceError) as exc_info:
            adapter._select_app_for_scenario(AIScenario.GENERAL_CHAT)
        
        assert "No Dify apps configured" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_chat_success(self, dify_config, sample_ai_request, mock_dify_api_responses):
        """测试聊天功能成功"""
        adapter = DifyAdapter(dify_config)
        
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            mock_chat.return_value = mock_dify_api_responses["chat_response"]
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    response = await adapter.chat(sample_ai_request)
            
            assert isinstance(response, AIResponse)
            assert response.success is True
            assert response.provider == AIProvider.DIFY
            assert response.scenario == sample_ai_request.scenario
            assert "双眼皮手术" in response.content
            assert response.metadata["dify_app_mode"] == "agent"
    
    @pytest.mark.asyncio
    async def test_generate_beauty_plan_agent_mode(self, dify_config, sample_ai_request, mock_dify_api_responses):
        """测试医美方案生成（Agent模式）"""
        adapter = DifyAdapter(dify_config)
        
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            mock_chat.return_value = mock_dify_api_responses["agent_response"]
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    response = await adapter.generate_beauty_plan(sample_ai_request)
            
            assert isinstance(response, PlanResponse)
            assert response.success is True
            assert "眼部提升方案" in response.content
            assert response.estimated_cost is not None
            assert response.timeline is not None
    
    @pytest.mark.asyncio
    async def test_summarize_consultation_workflow_mode(self, dify_config, sample_ai_request, mock_dify_api_responses):
        """测试咨询总结（工作流模式）"""
        adapter = DifyAdapter(dify_config)
        summary_request = AIRequest(
            request_id="summary-req-001",
            message="客户咨询双眼皮手术的完整对话内容...",
            scenario=AIScenario.CONSULTATION_SUMMARY,
            user_id="user-001"
        )
        
        with patch.object(adapter.client, 'workflow_run') as mock_workflow:
            mock_workflow.return_value = mock_dify_api_responses["workflow_response"]
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    response = await adapter.summarize_consultation(summary_request)
            
            assert isinstance(response, SummaryResponse)
            assert response.success is True
            assert len(response.key_points) > 0
            assert len(response.action_items) > 0
            assert response.sentiment_score == 0.75
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_completion_mode(self, dify_config, sample_ai_request, mock_dify_api_responses):
        """测试情感分析（文本完成模式）"""
        adapter = DifyAdapter(dify_config)
        sentiment_request = AIRequest(
            request_id="sentiment-req-001",
            message="我对这个治疗方案很满意！",
            scenario=AIScenario.SENTIMENT_ANALYSIS,
            user_id="user-001"
        )
        
        with patch.object(adapter.client, 'completion') as mock_completion:
            mock_completion.return_value = mock_dify_api_responses["completion_response"]
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    response = await adapter.analyze_sentiment(sentiment_request)
            
            assert isinstance(response, SentimentResponse)
            assert response.success is True
            assert response.sentiment_score == 0.82
            assert response.confidence == 0.92
            assert "期待" in response.emotions
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, dify_config, mock_dify_apps):
        """测试健康检查（所有应用健康）"""
        adapter = DifyAdapter(dify_config)
        
        mock_app_configs = {
            "general_chat": {"status": "healthy", "mode": "chat"},
            "beauty_agent": {"status": "healthy", "mode": "agent"},
            "summary_workflow": {"status": "healthy", "mode": "workflow"},
            "sentiment_completion": {"status": "healthy", "mode": "completion"}
        }
        
        with patch.object(adapter.client, 'get_application_config') as mock_get_config:
            def side_effect(app_config):
                return mock_app_configs.get(app_config.app_name.split()[0].lower(), {})
            
            mock_get_config.side_effect = side_effect
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    health = await adapter.health_check()
            
            assert health["status"] == "healthy"
            assert health["provider"] == "dify"
            assert len(health["apps"]) == 4
            
            for app_name, app_status in health["apps"].items():
                assert app_status["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_partial_failure(self, dify_config, mock_dify_apps):
        """测试健康检查（部分应用失败）"""
        adapter = DifyAdapter(dify_config)
        
        call_count = 0
        def mock_get_config_side_effect(app_config):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # 第二个应用失败
                raise AIServiceError("App not accessible", AIProvider.DIFY)
            return {"status": "healthy", "mode": app_config.app_mode}
        
        with patch.object(adapter.client, 'get_application_config') as mock_get_config:
            mock_get_config.side_effect = mock_get_config_side_effect
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    health = await adapter.health_check()
            
            assert health["status"] == "degraded"
            assert len(health["apps"]) == 4
            
            # 检查失败的应用
            failed_apps = [name for name, status in health["apps"].items() 
                          if status["status"] == "unhealthy"]
            assert len(failed_apps) == 1
    
    @pytest.mark.asyncio
    async def test_get_provider_info(self, dify_config):
        """测试获取提供商信息"""
        adapter = DifyAdapter(dify_config)
        
        info = await adapter.get_provider_info()
        
        assert info["provider"] == "dify"
        assert info["name"] == "Dify AI Platform"
        assert "chat" in info["capabilities"]
        assert "agent" in info["capabilities"]
        assert "workflow" in info["capabilities"]
        assert "multi_tenant" in info["capabilities"]
        assert info["base_url"] == dify_config.base_url
        assert len(info["configured_apps"]) == 4
    
    @pytest.mark.asyncio
    async def test_error_handling_and_fallback(self, dify_config, sample_ai_request):
        """测试错误处理和降级"""
        adapter = DifyAdapter(dify_config)
        
        # 模拟API调用失败
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            mock_chat.side_effect = AIProviderUnavailableError("Dify service down", AIProvider.DIFY)
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    response = await adapter.chat(sample_ai_request)
            
            # 应该返回错误响应而不是抛出异常
            assert isinstance(response, AIResponse)
            assert response.success is False
            assert "Dify service down" in response.content
    
    def test_transform_responses(self, dify_config, sample_ai_request, mock_dify_api_responses):
        """测试响应转换功能"""
        adapter = DifyAdapter(dify_config)
        app_config = dify_config.apps["beauty_agent"]
        
        # 测试转换为AI响应
        ai_response = adapter._transform_to_ai_response(
            mock_dify_api_responses["chat_response"], 
            sample_ai_request, 
            app_config
        )
        assert isinstance(ai_response, AIResponse)
        assert ai_response.metadata["dify_app_id"] == app_config.app_id
        assert ai_response.usage["total_tokens"] == 350
        
        # 测试转换为方案响应
        plan_response = adapter._transform_to_plan_response(
            mock_dify_api_responses["agent_response"],
            sample_ai_request,
            app_config
        )
        assert isinstance(plan_response, PlanResponse)
        assert plan_response.estimated_cost is not None
        
        # 测试转换为总结响应
        summary_response = adapter._transform_to_summary_response(
            mock_dify_api_responses["workflow_response"],
            sample_ai_request,
            app_config
        )
        assert isinstance(summary_response, SummaryResponse)
        assert len(summary_response.key_points) > 0
        
        # 测试转换为情感响应
        sentiment_response = adapter._transform_to_sentiment_response(
            mock_dify_api_responses["completion_response"],
            sample_ai_request,
            app_config
        )
        assert isinstance(sentiment_response, SentimentResponse)
        assert sentiment_response.sentiment_score > 0


# ================ 集成测试 ================

class TestDifyIntegration:
    """Dify集成综合测试"""
    
    @pytest.mark.asyncio
    async def test_scenario_routing(self, dify_config, mock_dify_api_responses):
        """测试场景智能路由"""
        adapter = DifyAdapter(dify_config)
        
        test_scenarios = [
            (AIScenario.GENERAL_CHAT, "chat_completion", "chat_response"),
            (AIScenario.BEAUTY_PLAN, "chat_completion", "agent_response"),
            (AIScenario.CONSULTATION_SUMMARY, "workflow_run", "workflow_response"),
            (AIScenario.SENTIMENT_ANALYSIS, "completion", "completion_response")
        ]
        
        for scenario, expected_method, response_key in test_scenarios:
            request = AIRequest(
                request_id=f"test-{scenario.value}",
                message=f"Test message for {scenario.value}",
                scenario=scenario,
                user_id="test-user"
            )
            
            with patch.object(adapter.client, expected_method) as mock_method:
                mock_method.return_value = mock_dify_api_responses[response_key]
                
                with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                    with patch.object(adapter.client, '__aexit__', return_value=None):
                        if scenario == AIScenario.GENERAL_CHAT:
                            response = await adapter.chat(request)
                        elif scenario == AIScenario.BEAUTY_PLAN:
                            response = await adapter.generate_beauty_plan(request)
                        elif scenario == AIScenario.CONSULTATION_SUMMARY:
                            response = await adapter.summarize_consultation(request)
                        elif scenario == AIScenario.SENTIMENT_ANALYSIS:
                            response = await adapter.analyze_sentiment(request)
                
                assert response.success is True
                assert response.scenario == scenario
                mock_method.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_configuration_validation(self):
        """测试配置验证"""
        # 测试空配置
        empty_config = DifyConnectionConfig(base_url="", apps={})
        adapter = DifyAdapter(empty_config)
        
        with pytest.raises(AIServiceError):
            adapter._select_app_for_scenario(AIScenario.GENERAL_CHAT)
        
        # 测试无效URL配置
        invalid_config = DifyConnectionConfig(
            base_url="invalid-url",
            apps={"test": DifyAppConfig(
                app_id="test", app_name="test", app_mode="chat", api_key="test"
            )}
        )
        adapter = DifyAdapter(invalid_config)
        
        request = AIRequest(
            request_id="test",
            message="test",
            scenario=AIScenario.GENERAL_CHAT,
            user_id="test"
        )
        
        # 应该能正常初始化，但API调用会失败
        assert adapter._select_app_for_scenario(AIScenario.GENERAL_CHAT) is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, dify_config, mock_dify_api_responses):
        """测试并发请求处理"""
        adapter = DifyAdapter(dify_config)
        
        # 创建多个并发请求
        requests = [
            AIRequest(
                request_id=f"concurrent-{i}",
                message=f"并发测试消息 {i}",
                scenario=AIScenario.GENERAL_CHAT,
                user_id=f"user-{i}"
            )
            for i in range(5)
        ]
        
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            mock_chat.return_value = mock_dify_api_responses["chat_response"]
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    # 并发执行
                    tasks = [adapter.chat(req) for req in requests]
                    responses = await asyncio.gather(*tasks)
            
            # 验证所有请求都成功
            assert len(responses) == 5
            for response in responses:
                assert response.success is True
                assert response.provider == AIProvider.DIFY
            
            # 验证API调用次数
            assert mock_chat.call_count == 5
    
    @pytest.mark.asyncio
    async def test_rate_limiting_handling(self, dify_config, sample_ai_request):
        """测试速率限制处理"""
        adapter = DifyAdapter(dify_config)
        
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            # 模拟速率限制错误
            mock_chat.side_effect = AIServiceError("Rate limit exceeded", AIProvider.DIFY, "429")
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    response = await adapter.chat(sample_ai_request)
            
            # 应该返回错误响应
            assert response.success is False
            assert "Rate limit exceeded" in response.content
    
    @pytest.mark.asyncio
    async def test_app_mode_fallback(self, dify_config, sample_ai_request, mock_dify_api_responses):
        """测试应用模式降级"""
        adapter = DifyAdapter(dify_config)
        
        # 模拟agent模式失败，降级到chat模式
        with patch.object(adapter, '_select_app_for_scenario') as mock_select:
            # 返回一个chat模式的应用配置
            chat_app = dify_config.apps["general_chat"]
            mock_select.return_value = chat_app
            
            with patch.object(adapter.client, 'chat_completion') as mock_chat:
                mock_chat.return_value = mock_dify_api_responses["chat_response"]
                
                with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                    with patch.object(adapter.client, '__aexit__', return_value=None):
                        response = await adapter.generate_beauty_plan(sample_ai_request)
                
                # 即使请求医美方案，也应该能通过chat模式处理
                assert response.success is True
                assert isinstance(response, PlanResponse)
    
    @pytest.mark.asyncio
    async def test_metadata_and_usage_tracking(self, dify_config, sample_ai_request, mock_dify_api_responses):
        """测试元数据和使用量跟踪"""
        adapter = DifyAdapter(dify_config)
        
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            mock_chat.return_value = mock_dify_api_responses["chat_response"]
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    response = await adapter.chat(sample_ai_request)
            
            # 验证元数据
            assert "dify_app_id" in response.metadata
            assert "dify_app_mode" in response.metadata
            assert "conversation_id" in response.metadata
            assert "message_id" in response.metadata
            
            # 验证使用量信息
            assert response.usage is not None
            assert response.usage["total_tokens"] == 350
            assert response.usage["prompt_tokens"] == 150
            assert response.usage["completion_tokens"] == 200


# ================ 性能和压力测试 ================

class TestDifyPerformance:
    """Dify性能测试"""
    
    @pytest.mark.asyncio
    async def test_high_concurrency_load(self, dify_config, mock_dify_api_responses):
        """测试高并发负载"""
        adapter = DifyAdapter(dify_config)
        
        # 创建大量并发请求
        num_requests = 50
        requests = [
            AIRequest(
                request_id=f"load-test-{i}",
                message=f"负载测试消息 {i}",
                scenario=AIScenario.GENERAL_CHAT,
                user_id=f"load-user-{i}"
            )
            for i in range(num_requests)
        ]
        
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            # 模拟不同响应时间
            async def mock_response(*args, **kwargs):
                await asyncio.sleep(0.01)  # 模拟10ms延迟
                return mock_dify_api_responses["chat_response"]
            
            mock_chat.side_effect = mock_response
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    start_time = asyncio.get_event_loop().time()
                    
                    # 批量处理
                    batch_size = 10
                    all_responses = []
                    
                    for i in range(0, num_requests, batch_size):
                        batch = requests[i:i + batch_size]
                        batch_tasks = [adapter.chat(req) for req in batch]
                        batch_responses = await asyncio.gather(*batch_tasks)
                        all_responses.extend(batch_responses)
                    
                    end_time = asyncio.get_event_loop().time()
                    total_time = end_time - start_time
            
            # 验证性能指标
            assert len(all_responses) == num_requests
            success_count = sum(1 for r in all_responses if r.success)
            success_rate = success_count / num_requests
            
            assert success_rate >= 0.95  # 至少95%成功率
            assert total_time < 10.0  # 总时间不超过10秒
            
            # 计算QPS
            qps = num_requests / total_time
            assert qps > 5  # 至少5 QPS
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, dify_config, mock_dify_api_responses):
        """测试内存使用稳定性"""
        import gc
        import psutil
        import os
        
        adapter = DifyAdapter(dify_config)
        process = psutil.Process(os.getpid())
        
        # 记录初始内存
        initial_memory = process.memory_info().rss
        
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            mock_chat.return_value = mock_dify_api_responses["chat_response"]
            
            with patch.object(adapter.client, '__aenter__', return_value=adapter.client):
                with patch.object(adapter.client, '__aexit__', return_value=None):
                    # 执行多轮请求
                    for round_num in range(10):
                        requests = [
                            AIRequest(
                                request_id=f"memory-test-{round_num}-{i}",
                                message=f"内存测试消息 {round_num}-{i}",
                                scenario=AIScenario.GENERAL_CHAT,
                                user_id=f"memory-user-{i}"
                            )
                            for i in range(20)
                        ]
                        
                        tasks = [adapter.chat(req) for req in requests]
                        responses = await asyncio.gather(*tasks)
                        
                        # 验证响应
                        assert all(r.success for r in responses)
                        
                        # 强制垃圾回收
                        gc.collect()
        
        # 检查最终内存使用
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长不应超过50MB
        assert memory_increase < 50 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 