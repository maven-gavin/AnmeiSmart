"""
OpenAI适配器实现

作为Dify的备选方案，提供可靠的降级能力。
支持GPT-3.5/GPT-4模型，具备完整的医美领域prompt优化。
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional
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
class OpenAIConfig:
    """OpenAI配置"""
    api_key: str
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3


class OpenAIAdapter(AIServiceInterface):
    """OpenAI适配器
    
    提供医美领域优化的prompt和完整的降级能力。
    """
    
    def __init__(self, config: OpenAIConfig):
        self.config = config
        
        # 医美领域优化的系统prompt
        self.system_prompts = {
            AIScenario.GENERAL_CHAT: """你是安美智享的专业医美顾问助手。你需要：
1. 以专业、友好的态度回答医美相关问题
2. 提供准确的医美知识和建议
3. 引导用户使用系统的各项功能
4. 注意医疗安全，必要时建议咨询专业医生""",
            
            AIScenario.BEAUTY_PLAN: """你是专业的医美方案制定专家。请根据用户信息制定个性化方案：
1. 仔细分析用户的年龄、肤质、预算等基本信息
2. 了解用户的美容目标和期望效果
3. 制定科学、安全、个性化的医美方案
4. 包含详细的治疗步骤、预期效果、注意事项
5. 提供费用预估和时间安排
6. 说明可能的风险和副作用""",
            
            AIScenario.CONSULTATION_SUMMARY: """你是专业的咨询分析师。请分析咨询对话并生成结构化总结：
1. 提取关键信息：用户需求、关注点、预算等
2. 分析用户意向和决策倾向
3. 总结咨询要点和建议方案
4. 识别需要跟进的事项
5. 评估客户满意度和意向程度""",
            
            AIScenario.SENTIMENT_ANALYSIS: """你是情感分析专家。请分析文本的情感倾向：
1. 识别整体情感倾向（正面/负面/中性）
2. 给出情感强度评分（-1到1之间）
3. 识别具体情感类型（满意、担心、兴奋、犹豫等）
4. 分析情感变化趋势
5. 提供置信度评估""",
            
            AIScenario.CUSTOMER_SERVICE: """你是专业的客服助手。请提供优质的客户服务：
1. 耐心解答用户疑问
2. 提供准确的产品和服务信息
3. 协助处理用户问题和投诉
4. 引导用户完成相关操作
5. 必要时转接人工客服""",
            
            AIScenario.MEDICAL_ADVICE: """你是医美医疗顾问。请提供专业建议：
1. 基于医学知识提供建议
2. 强调安全性和科学性
3. 说明风险和注意事项
4. 建议咨询专业医生
5. 不做具体诊断，仅提供参考意见"""
        }
    
    async def chat(self, request: AIRequest) -> AIResponse:
        """通用聊天实现"""
        messages = self._build_messages(request)
        
        try:
            response_data = await self._call_openai_api(messages, request)
            return self._transform_to_ai_response(response_data, request)
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return self._create_error_response(request, str(e))
    
    async def generate_beauty_plan(self, request: AIRequest) -> PlanResponse:
        """生成医美方案"""
        # 使用专门的方案生成prompt
        messages = self._build_plan_messages(request)
        
        try:
            response_data = await self._call_openai_api(messages, request, temperature=0.5)
            base_response = self._transform_to_ai_response(response_data, request)
            
            # 解析方案内容
            plan_data = self._parse_beauty_plan(base_response.content)
            
            return PlanResponse(
                request_id=base_response.request_id,
                content=base_response.content,
                provider=base_response.provider,
                scenario=base_response.scenario,
                success=base_response.success,
                metadata=base_response.metadata,
                usage=base_response.usage,
                plan_sections=plan_data.get("sections", []),
                estimated_cost=plan_data.get("cost", {}),
                timeline=plan_data.get("timeline", {}),
                risks=plan_data.get("risks", [])
            )
        except Exception as e:
            logger.error(f"OpenAI beauty plan error: {e}")
            return self._create_error_plan_response(request, str(e))
    
    async def summarize_consultation(self, request: AIRequest) -> SummaryResponse:
        """总结咨询内容"""
        messages = self._build_summary_messages(request)
        
        try:
            response_data = await self._call_openai_api(messages, request, temperature=0.3)
            base_response = self._transform_to_ai_response(response_data, request)
            
            # 解析总结内容
            summary_data = self._parse_consultation_summary(base_response.content)
            
            return SummaryResponse(
                request_id=base_response.request_id,
                content=base_response.content,
                provider=base_response.provider,
                scenario=base_response.scenario,
                success=base_response.success,
                metadata=base_response.metadata,
                usage=base_response.usage,
                key_points=summary_data.get("key_points", []),
                action_items=summary_data.get("action_items", []),
                sentiment_score=summary_data.get("sentiment_score", 0.0),
                categories=summary_data.get("categories", [])
            )
        except Exception as e:
            logger.error(f"OpenAI summary error: {e}")
            return self._create_error_summary_response(request, str(e))
    
    async def analyze_sentiment(self, request: AIRequest) -> SentimentResponse:
        """分析情感"""
        messages = self._build_sentiment_messages(request)
        
        try:
            response_data = await self._call_openai_api(messages, request, temperature=0.1)
            base_response = self._transform_to_ai_response(response_data, request)
            
            # 解析情感分析结果
            sentiment_data = self._parse_sentiment_analysis(base_response.content)
            
            return SentimentResponse(
                request_id=base_response.request_id,
                content=base_response.content,
                provider=base_response.provider,
                scenario=base_response.scenario,
                success=base_response.success,
                metadata=base_response.metadata,
                usage=base_response.usage,
                sentiment_score=sentiment_data.get("score", 0.0),
                confidence=sentiment_data.get("confidence", 0.0),
                emotions=sentiment_data.get("emotions", {})
            )
        except Exception as e:
            logger.error(f"OpenAI sentiment analysis error: {e}")
            return self._create_error_sentiment_response(request, str(e))
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 发送简单的测试请求
            test_messages = [{"role": "user", "content": "Hello"}]
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.config.model,
                        "messages": test_messages,
                        "max_tokens": 10
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return {
                            "provider": "openai",
                            "status": "healthy",
                            "model": self.config.model,
                            "api_base": self.config.api_base,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "provider": "openai",
                            "status": "unhealthy",
                            "error": f"API returned {response.status}: {error_text}",
                            "timestamp": datetime.now().isoformat()
                        }
        except Exception as e:
            return {
                "provider": "openai",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息"""
        return {
            "provider": "openai",
            "name": "OpenAI GPT",
            "model": self.config.model,
            "capabilities": [
                "chat", "completion", "text_generation",
                "sentiment_analysis", "summarization"
            ],
            "api_base": self.config.api_base,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
    
    async def _call_openai_api(self, messages: List[Dict[str, str]], 
                             request: AIRequest, 
                             temperature: Optional[float] = None) -> Dict[str, Any]:
        """调用OpenAI API"""
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": temperature or request.temperature or self.config.temperature,
            "user": request.context.user_id if request.context else "anonymous"
        }
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.config.max_retries):
                try:
                    async with session.post(
                        f"{self.config.api_base}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.config.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 401:
                            raise AIAuthenticationError("OpenAI authentication failed", AIProvider.OPENAI)
                        elif response.status == 429:
                            # 速率限制，等待后重试
                            if attempt < self.config.max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            raise AIRateLimitError("OpenAI rate limit exceeded", AIProvider.OPENAI)
                        else:
                            error_text = await response.text()
                            raise AIServiceError(f"OpenAI API error: {error_text}", 
                                               AIProvider.OPENAI, str(response.status))
                except aiohttp.ClientError as e:
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise AIProviderUnavailableError(f"OpenAI connection error: {e}", AIProvider.OPENAI)
        
        raise AIProviderUnavailableError("OpenAI API failed after all retries", AIProvider.OPENAI)
    
    def _build_messages(self, request: AIRequest) -> List[Dict[str, str]]:
        """构建通用消息"""
        messages = []
        
        # 添加系统prompt
        system_prompt = self.system_prompts.get(request.scenario, self.system_prompts[AIScenario.GENERAL_CHAT])
        messages.append({"role": "system", "content": system_prompt})
        
        # 添加用户上下文信息
        if request.context and request.context.user_profile:
            context_info = self._build_context_info(request.context.user_profile)
            messages.append({"role": "system", "content": f"用户信息：{context_info}"})
        
        # 添加对话历史
        if request.context and request.context.conversation_history:
            for msg in request.context.conversation_history[-5:]:  # 最近5条
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # 添加当前消息
        messages.append({"role": "user", "content": request.message})
        
        return messages
    
    def _build_plan_messages(self, request: AIRequest) -> List[Dict[str, str]]:
        """构建方案生成消息"""
        messages = [
            {"role": "system", "content": self.system_prompts[AIScenario.BEAUTY_PLAN]},
            {"role": "system", "content": """
请按以下格式输出医美方案：

## 用户分析
- 基本信息：年龄、肤质、预算等
- 美容目标：期望效果描述

## 推荐方案
### 方案一：[方案名称]
- 治疗项目：具体项目列表
- 预期效果：详细描述
- 治疗周期：时间安排
- 预估费用：具体金额

### 方案二：[备选方案]
（如有）

## 注意事项
- 术前准备
- 术后护理
- 可能风险

## 后续建议
- 跟进计划
- 保养建议
"""}
        ]
        
        # 添加用户信息
        if request.context and request.context.user_profile:
            user_info = self._format_user_profile(request.context.user_profile)
            messages.append({"role": "user", "content": f"我的基本信息：{user_info}"})
        
        messages.append({"role": "user", "content": request.message})
        
        return messages
    
    def _build_summary_messages(self, request: AIRequest) -> List[Dict[str, str]]:
        """构建总结消息"""
        messages = [
            {"role": "system", "content": self.system_prompts[AIScenario.CONSULTATION_SUMMARY]},
            {"role": "system", "content": """
请按以下格式输出咨询总结：

## 客户信息
- 基本情况
- 主要需求

## 咨询要点
- 关键问题
- 客户关注点
- 预算情况

## 推荐方案
- 建议项目
- 预期效果

## 客户反馈
- 意向程度
- 主要顾虑
- 决策倾向

## 跟进建议
- 下次联系时间
- 需要准备的资料
- 重点说明事项
"""}
        ]
        
        messages.append({"role": "user", "content": f"请总结以下咨询对话：\n\n{request.message}"})
        
        return messages
    
    def _build_sentiment_messages(self, request: AIRequest) -> List[Dict[str, str]]:
        """构建情感分析消息"""
        messages = [
            {"role": "system", "content": self.system_prompts[AIScenario.SENTIMENT_ANALYSIS]},
            {"role": "system", "content": """
请按以下JSON格式输出情感分析结果：

{
    "sentiment_score": 0.0,  // -1.0到1.0之间，负数表示负面情感
    "confidence": 0.0,       // 0.0到1.0之间，表示分析置信度
    "emotions": {            // 具体情感分类及强度
        "satisfaction": 0.0,
        "worry": 0.0,
        "excitement": 0.0,
        "hesitation": 0.0
    },
    "analysis": "详细分析说明"
}
"""}
        ]
        
        messages.append({"role": "user", "content": f"请分析以下文本的情感：\n\n{request.message}"})
        
        return messages
    
    def _build_context_info(self, user_profile: Dict[str, Any]) -> str:
        """构建用户上下文信息"""
        info_parts = []
        
        if user_profile.get("age"):
            info_parts.append(f"年龄：{user_profile['age']}岁")
        if user_profile.get("gender"):
            info_parts.append(f"性别：{user_profile['gender']}")
        if user_profile.get("skin_type"):
            info_parts.append(f"肤质：{user_profile['skin_type']}")
        if user_profile.get("budget"):
            info_parts.append(f"预算：{user_profile['budget']}")
        if user_profile.get("concerns"):
            info_parts.append(f"关注问题：{user_profile['concerns']}")
        
        return "，".join(info_parts) if info_parts else "暂无详细信息"
    
    def _format_user_profile(self, user_profile: Dict[str, Any]) -> str:
        """格式化用户档案"""
        return json.dumps(user_profile, ensure_ascii=False, indent=2)
    
    def _transform_to_ai_response(self, response_data: Dict[str, Any], request: AIRequest) -> AIResponse:
        """转换OpenAI响应为统一AI响应"""
        choice = response_data["choices"][0]
        content = choice["message"]["content"]
        
        usage = response_data.get("usage", {})
        
        return AIResponse(
            request_id=request.request_id,
            content=content,
            provider=AIProvider.OPENAI,
            scenario=request.scenario,
            success=True,
            metadata={
                "model": response_data.get("model"),
                "finish_reason": choice.get("finish_reason")
            },
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        )
    
    def _parse_beauty_plan(self, content: str) -> Dict[str, Any]:
        """解析医美方案内容"""
        # 简单的文本解析，实际项目中可以使用更复杂的NLP技术
        plan_data = {
            "sections": [],
            "cost": {},
            "timeline": {},
            "risks": []
        }
        
        # 解析费用信息
        import re
        cost_patterns = re.findall(r'(\d+(?:,\d+)*)\s*元', content)
        if cost_patterns:
            try:
                total_cost = sum(int(cost.replace(',', '')) for cost in cost_patterns)
                plan_data["cost"] = {"total": total_cost, "currency": "CNY"}
            except ValueError:
                pass
        
        # 解析时间信息
        timeline_patterns = re.findall(r'(\d+)\s*(?:周|天|月)', content)
        if timeline_patterns:
            plan_data["timeline"] = {"duration": timeline_patterns[0]}
        
        return plan_data
    
    def _parse_consultation_summary(self, content: str) -> Dict[str, Any]:
        """解析咨询总结"""
        return {
            "key_points": [],
            "action_items": [],
            "sentiment_score": 0.5,
            "categories": ["medical_beauty", "consultation"]
        }
    
    def _parse_sentiment_analysis(self, content: str) -> Dict[str, Any]:
        """解析情感分析结果"""
        try:
            # 尝试解析JSON格式的响应
            import json
            if content.strip().startswith('{'):
                return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 默认返回中性情感
        return {
            "score": 0.0,
            "confidence": 0.5,
            "emotions": {
                "satisfaction": 0.0,
                "worry": 0.0,
                "excitement": 0.0,
                "hesitation": 0.0
            }
        }
    
    def _create_error_response(self, request: AIRequest, error_message: str) -> AIResponse:
        """创建错误响应"""
        return AIResponse(
            request_id=request.request_id,
            content=f"抱歉，处理您的请求时发生错误：{error_message}",
            provider=AIProvider.OPENAI,
            scenario=request.scenario,
            success=False,
            error_message=error_message
        )
    
    def _create_error_plan_response(self, request: AIRequest, error_message: str) -> PlanResponse:
        """创建错误方案响应"""
        return PlanResponse(
            request_id=request.request_id,
            content=f"抱歉，生成医美方案时发生错误：{error_message}",
            provider=AIProvider.OPENAI,
            scenario=request.scenario,
            success=False,
            error_message=error_message
        )
    
    def _create_error_summary_response(self, request: AIRequest, error_message: str) -> SummaryResponse:
        """创建错误总结响应"""
        return SummaryResponse(
            request_id=request.request_id,
            content=f"抱歉，总结咨询内容时发生错误：{error_message}",
            provider=AIProvider.OPENAI,
            scenario=request.scenario,
            success=False,
            error_message=error_message
        )
    
    def _create_error_sentiment_response(self, request: AIRequest, error_message: str) -> SentimentResponse:
        """创建错误情感分析响应"""
        return SentimentResponse(
            request_id=request.request_id,
            content=f"抱歉，分析情感时发生错误：{error_message}",
            provider=AIProvider.OPENAI,
            scenario=request.scenario,
            success=False,
            error_message=error_message,
            sentiment_score=0.0,
            confidence=0.0
        ) 