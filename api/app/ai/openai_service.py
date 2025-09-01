"""
OpenAI服务实现
提供与OpenAI API的集成能力
"""

import os
import logging
import httpx
from typing import Dict, Any, Optional, List
from uuid import uuid4
from datetime import datetime

from app.core.config import get_settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

class OpenAIService:
    """OpenAI服务客户端"""
    
    def __init__(self):
        """初始化OpenAI客户端"""
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.api_base_url = os.environ.get("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # 验证配置
        if not self.api_key:
            logger.warning("OPENAI_API_KEY环境变量未设置，OpenAI服务将不可用")
        else:
            logger.info(f"OpenAI服务初始化成功，使用模型: {self.model}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self.api_key:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenAI健康检查失败: {e}")
            return False
    
    async def generate_response(self, query: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        调用OpenAI API生成回复
        
        Args:
            query: 用户问题
            conversation_history: 对话历史记录
            
        Returns:
            包含AI回复内容的字典
        """
        if not self.api_key:
            return {
                "id": f"ai_msg_{uuid4().hex}",
                "content": "OpenAI服务未配置，无法生成回复。",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # 构建系统提示词
            system_prompt = "你是安美智享的AI医疗美容顾问，专门为用户提供医美咨询服务。提供准确、专业的医美知识，包括各类项目介绍、术前准备、术后护理、风险评估等。避免使用过于复杂的医学术语，以易于理解的方式回答问题。不要编造虚假信息，如果不确定，告知用户你需要查询更多信息。保持友好专业的沟通态度。"
            
            # 构建消息历史
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加对话历史
            if conversation_history:
                for message in conversation_history:
                    role = "assistant" if message.get("sender_type") == "ai" else "user"
                    messages.append({
                        "role": role,
                        "content": message.get("content", "")
                    })
            
            # 添加当前用户问题
            messages.append({"role": "user", "content": query})
            
            # 发送请求
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 800
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenAI API调用失败: {response.status_code} {response.text}")
                    return {
                        "id": f"ai_msg_{uuid4().hex}",
                        "content": "抱歉，AI服务暂时不可用，请稍后再试。",
                        "timestamp": datetime.now().isoformat()
                    }
                
                response_data = response.json()
                ai_response = response_data["choices"][0]["message"]["content"]
                
                return {
                    "id": f"ai_msg_{uuid4().hex}",
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"OpenAI API调用异常: {str(e)}")
            return {
                "id": f"ai_msg_{uuid4().hex}",
                "content": "抱歉，AI服务暂时不可用，请稍后再试。",
                "timestamp": datetime.now().isoformat()
            } 