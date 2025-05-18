"""
AI服务主类
负责处理医美领域的智能问答
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List
from uuid import uuid4
from datetime import datetime
from functools import lru_cache

from app.core.config import get_settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

class AIService:
    """AI服务类，提供医美智能问答能力"""
    
    def __init__(self):
        """初始化AI服务"""
        self.api_key = os.environ.get("AI_API_KEY", "")
        self.ai_model = os.environ.get("AI_MODEL", "default")
        self.api_base_url = os.environ.get("AI_API_BASE_URL", "")
        # 检查环境变量是否配置
        self._check_config()
        logger.info(f"AI服务初始化完成，使用模型: {self.ai_model}")
        
        # 加载医美领域知识库
        self.medical_beauty_knowledge = self._load_medical_beauty_knowledge()
    
    def _check_config(self) -> None:
        """检查配置是否正确"""
        if not self.api_key:
            logger.warning("AI_API_KEY环境变量未设置，将使用模拟回复")
        if not self.api_base_url and self.api_key:
            logger.warning("AI_API_BASE_URL环境变量未设置，将使用默认API地址")
            self.api_base_url = "https://api.openai.com/v1"
    
    def _load_medical_beauty_knowledge(self) -> Dict[str, List[str]]:
        """加载医美领域知识库，用于模拟回复或增强AI回复"""
        # 这里使用简单的字典来模拟知识库，实际项目中可能连接到向量数据库
        return {
            "双眼皮": [
                "双眼皮手术一般术后1-2周即可基本恢复，但完全恢复需要1-3个月。",
                "拆线通常在术后5-7天进行，之后可以化淡妆。",
                "建议术后1个月内避免剧烈运动，3个月内防晒。",
                "双眼皮手术类型包括切开法、埋线法、三点法等，需根据个人眼部条件选择。"
            ],
            "玻尿酸": [
                "玻尿酸是一种天然存在于人体的物质，用于注射填充可以改善面部轮廓和减少皱纹。",
                "效果通常持续6-18个月，具体取决于注射部位和产品种类。",
                "注射玻尿酸的风险包括红肿、瘀青、疼痛、感染等，但大多数副作用是暂时性的。",
                "玻尿酸不适用于孕妇和有自身免疫性疾病的患者。"
            ],
            "肉毒素": [
                "肉毒素注射主要用于减少动态皱纹，如鱼尾纹、抬头纹等。",
                "效果通常持续3-6个月，需要定期注射维持效果。",
                "注射后24小时内应避免按摩注射区域、剧烈运动和饮酒。",
                "肉毒素不适用于孕妇、哺乳期妇女和特定神经肌肉疾病患者。"
            ],
            "光子嫩肤": [
                "光子嫩肤可以改善肤色不均、淡化色斑和减少细小皱纹。",
                "一般需要3-5次治疗，每次间隔3-4周。",
                "治疗后需要加强防晒，避免阳光直射。",
                "可能出现的副作用包括轻微红肿和色素沉着，通常会在几天内消退。"
            ],
            "隆鼻": [
                "隆鼻手术类型包括假体隆鼻、自体软骨隆鼻和注射隆鼻等。",
                "假体隆鼻恢复期约1-2周，完全消肿可能需要3-6个月。",
                "术后1个月内应避免剧烈运动和面部碰撞。",
                "自体软骨隆鼻效果更自然，但手术创伤较大，恢复期更长。"
            ]
        }
    
    async def get_response(self, query: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        获取AI回复
        
        Args:
            query: 用户问题
            conversation_history: 对话历史记录
            
        Returns:
            包含AI回复内容的字典
        """
        # 如果未配置API密钥，使用模拟回复
        if not self.api_key:
            return self._get_simulated_response(query, conversation_history)
        
        try:
            # 实际项目中，这里应调用AI服务API
            # 例如：OpenAI、Dify、DeepSeek等
            # 暂时使用模拟回复
            logger.warning("API调用尚未实现，使用模拟回复")
            return self._get_simulated_response(query, conversation_history)
        except Exception as e:
            logger.error(f"AI服务调用失败: {str(e)}")
            return {
                "id": f"ai_msg_{uuid4().hex}",
                "content": "抱歉，我暂时无法回答您的问题，请稍后再试。",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_simulated_response(self, query: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """生成模拟AI回复"""
        response_content = ""
        
        # 根据关键词匹配医美知识库
        query_lower = query.lower()
        
        # 检查关键词匹配
        for topic, knowledge_list in self.medical_beauty_knowledge.items():
            if topic in query_lower:
                # 从知识库中选择相关回复
                response_content = "。".join(knowledge_list[:2])
                break
        
        # 如果没有匹配到特定主题
        if not response_content:
            if "价格" in query_lower or "费用" in query_lower:
                response_content = "我们的医美项目价格根据具体操作和材料有所不同。基础项目从数千元起，精细项目可能达到数万元。我们提供免费咨询和评估服务，可以根据您的需求提供详细报价。"
            elif "风险" in query_lower or "副作用" in query_lower:
                response_content = "任何医疗美容项目都存在一定风险。常见的副作用包括暂时性红肿、瘀斑等。严重但罕见的风险包括感染、过敏反应等。我们的专业医生会在术前详细告知您相关风险并制定个性化方案降低风险。"
            elif "恢复" in query_lower or "术后" in query_lower:
                response_content = "术后恢复时间因人而异和手术类型而异。一般需要1-2周的恢复期。建议术后遵循医生的指导，保持伤口清洁，避免剧烈运动，按时服用药物。"
            else:
                response_content = "感谢您的咨询。作为安美智享的AI顾问，我可以为您提供医美相关的专业建议。您有任何关于医美项目、术前准备、术后恢复等方面的问题，都可以随时向我咨询。"
        
        return {
            "id": f"ai_msg_{uuid4().hex}",
            "content": response_content,
            "timestamp": datetime.now().isoformat()
        }


@lru_cache()
def get_ai_service() -> AIService:
    """获取AI服务单例"""
    return AIService() 