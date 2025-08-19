"""
Agent集成测试套件

全面测试AI Gateway中的Agent集成功能，包括：
- Agent适配器的所有功能
- 不同应用模式（chat/agent/workflow/completion）
- 场景路由和降级机制
- 错误处理和恢复
- 健康检查和监控
- 配置验证和管理
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from app.services.ai.adapters.agent_adapter import (
    AgentAdapter, AgentConnectionConfig, AgentAppConfig, AgentAPIClient
)
from app.services.ai.ai_gateway_service import (
    AIProvider, AIRequest, AIResponse, PlanResponse, SummaryResponse, SentimentResponse,
    AIScenario, AIAuthenticationError, AIServiceError, AIProviderUnavailableError
)


# ================ 测试数据和fixture ================

@pytest.fixture
def mock_agent_apps():
    """模拟Agent应用配置"""
    return {
        "general_chat": AgentAppConfig(
            app_id="agent-chat-001",
            app_name="通用聊天助手",
            app_mode="chat",
            api_key="app-chat-key-001",
            scenarios=[AIScenario.GENERAL_CHAT, AIScenario.CUSTOMER_SERVICE]
        ),
        "beauty_agent": AgentAppConfig(
            app_id="agent-agent-002", 
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
        "summary_workflow": AgentAppConfig(
            app_id="agent-workflow-003",
            app_name="咨询总结工作流",
            app_mode="workflow", 
            api_key="app-workflow-key-003",
            scenarios=[AIScenario.CONSULTATION_SUMMARY]
        ),
        "sentiment_completion": AgentAppConfig(
            app_id="agent-completion-004",
            app_name="情感分析引擎",
            app_mode="completion",
            api_key="app-completion-key-004",
            scenarios=[AIScenario.SENTIMENT_ANALYSIS]
        )
    }


@pytest.fixture
def agent_config(mock_agent_apps):
    """Agent连接配置"""
    return AgentConnectionConfig(
        base_url="http://localhost:8000/v1",
        tenant_id="test-tenant-001",
        apps=mock_agent_apps,
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
        user_id="user-001"
    )


@pytest.fixture
def mock_agent_api_responses():
    """模拟Agent API响应"""
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
        }
    }


# ================ AgentAPIClient 测试 ================

class TestAgentAPIClient:
    """测试Agent API客户端"""
    
    @pytest.mark.asyncio
    async def test_chat_completion_success(self, agent_config, mock_agent_apps, sample_ai_request, mock_agent_api_responses):
        """测试聊天完成API成功调用"""
        client = AgentAPIClient(agent_config)
        app_config = mock_agent_apps["general_chat"]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # 模拟成功响应
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_agent_api_responses["chat_response"])
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.chat_completion(app_config, sample_ai_request)
            
            # 验证响应
            assert result["id"] == "msg-chat-001"
            assert "双眼皮手术" in result["answer"]
    
    @pytest.mark.asyncio
    async def test_chat_completion_auth_error(self, agent_config, mock_agent_apps, sample_ai_request):
        """测试认证失败"""
        client = AgentAPIClient(agent_config)
        app_config = mock_agent_apps["general_chat"]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # 模拟认证失败
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value="Unauthorized")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(AIAuthenticationError) as exc_info:
                await client.chat_completion(app_config, sample_ai_request)
            
            assert exc_info.value.provider == AIProvider.AGENT
            assert "authentication failed" in str(exc_info.value).lower()


# ================ AgentAdapter 测试 ================

class TestAgentAdapter:
    """测试Agent适配器"""
    
    def test_adapter_initialization(self, agent_config):
        """测试适配器初始化"""
        adapter = AgentAdapter(agent_config)
        
        assert adapter.config == agent_config
        assert isinstance(adapter.client, AgentAPIClient)
        assert len(adapter.scenario_app_mapping) == 6
        
        # 验证场景映射
        assert adapter.scenario_app_mapping[AIScenario.GENERAL_CHAT] == "chat"
        assert adapter.scenario_app_mapping[AIScenario.BEAUTY_PLAN] == "agent"
        assert adapter.scenario_app_mapping[AIScenario.CONSULTATION_SUMMARY] == "workflow"
        assert adapter.scenario_app_mapping[AIScenario.SENTIMENT_ANALYSIS] == "completion"
    
    def test_select_app_for_scenario(self, agent_config, mock_agent_apps):
        """测试场景应用选择"""
        adapter = AgentAdapter(agent_config)
        
        # 测试直接场景匹配
        beauty_app = adapter._select_app_for_scenario(AIScenario.BEAUTY_PLAN)
        assert beauty_app.app_id == "agent-agent-002"
        assert beauty_app.app_mode == "agent"
        
        # 测试通用聊天匹配
        chat_app = adapter._select_app_for_scenario(AIScenario.GENERAL_CHAT)
        assert chat_app.app_id == "agent-chat-001"
        assert chat_app.app_mode == "chat"
    
    @pytest.mark.asyncio
    async def test_chat_success(self, agent_config, sample_ai_request, mock_agent_api_responses):
        """测试聊天功能成功"""
        adapter = AgentAdapter(agent_config)
        
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            mock_chat.return_value = mock_agent_api_responses["chat_response"]
            
            response = await adapter.chat(sample_ai_request)
            
            assert isinstance(response, AIResponse)
            assert response.success is True
            assert response.provider == AIProvider.AGENT
            assert response.scenario == sample_ai_request.scenario
            assert "双眼皮手术" in response.content
    
    @pytest.mark.asyncio
    async def test_generate_beauty_plan_agent_mode(self, agent_config, sample_ai_request, mock_agent_api_responses):
        """测试医美方案生成（Agent模式）"""
        adapter = AgentAdapter(agent_config)
        
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            mock_chat.return_value = mock_agent_api_responses["agent_response"]
            
            response = await adapter.generate_beauty_plan(sample_ai_request)
            
            assert isinstance(response, PlanResponse)
            assert response.success is True
            assert "眼部提升方案" in response.content
    
    @pytest.mark.asyncio
    async def test_summarize_consultation_workflow_mode(self, agent_config, sample_ai_request, mock_agent_api_responses):
        """测试咨询总结（工作流模式）"""
        adapter = AgentAdapter(agent_config)
        summary_request = AIRequest(
            request_id="summary-req-001",
            message="客户咨询双眼皮手术的完整对话内容...",
            scenario=AIScenario.CONSULTATION_SUMMARY,
            user_id="user-001"
        )
        
        with patch.object(adapter.client, 'workflow_run') as mock_workflow:
            mock_workflow.return_value = mock_agent_api_responses["workflow_response"]
            
            response = await adapter.summarize_consultation(summary_request)
            
            assert isinstance(response, SummaryResponse)
            assert response.success is True
            assert len(response.key_points) > 0
            assert len(response.action_items) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_completion_mode(self, agent_config, sample_ai_request, mock_agent_api_responses):
        """测试情感分析（文本完成模式）"""
        adapter = AgentAdapter(agent_config)
        sentiment_request = AIRequest(
            request_id="sentiment-req-001",
            message="我对这个治疗方案很满意！",
            scenario=AIScenario.SENTIMENT_ANALYSIS,
            user_id="user-001"
        )
        
        with patch.object(adapter.client, 'completion') as mock_completion:
            mock_completion.return_value = mock_agent_api_responses["completion_response"]
            
            response = await adapter.analyze_sentiment(sentiment_request)
            
            assert isinstance(response, SentimentResponse)
            assert response.success is True
            assert response.sentiment_score == 0.82
    
    @pytest.mark.asyncio
    async def test_health_check(self, agent_config, mock_agent_apps):
        """测试健康检查"""
        adapter = AgentAdapter(agent_config)
        
        with patch.object(adapter.client, 'get_application_config') as mock_get_config:
            mock_get_config.return_value = {"status": "healthy", "mode": "chat"}
            
            health = await adapter.health_check()
            
            assert health["status"] == "healthy"
            assert health["provider"] == "agent"
    
    @pytest.mark.asyncio
    async def test_get_provider_info(self, agent_config):
        """测试获取提供商信息"""
        adapter = AgentAdapter(agent_config)
        
        info = await adapter.get_provider_info()
        
        assert info["provider"] == "agent"
        assert info["name"] == "Agent AI Platform"
        assert "chat" in info["capabilities"]
        assert "agent" in info["capabilities"]
        assert "workflow" in info["capabilities"]
        assert info["base_url"] == agent_config.base_url


# ================ 集成测试 ================

class TestAgentIntegration:
    """Agent集成综合测试"""
    
    @pytest.mark.asyncio
    async def test_scenario_routing(self, agent_config, mock_agent_api_responses):
        """测试场景智能路由"""
        adapter = AgentAdapter(agent_config)
        
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
                mock_method.return_value = mock_agent_api_responses[response_key]
                
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
    async def test_error_handling_and_fallback(self, agent_config, sample_ai_request):
        """测试错误处理和降级"""
        adapter = AgentAdapter(agent_config)
        
        # 模拟API调用失败
        with patch.object(adapter.client, 'chat_completion') as mock_chat:
            mock_chat.side_effect = AIProviderUnavailableError("Agent service down", AIProvider.AGENT)
            
            response = await adapter.chat(sample_ai_request)
            
            # 应该返回错误响应而不是抛出异常
            assert isinstance(response, AIResponse)
            assert response.success is False
            assert "Agent service down" in response.content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
