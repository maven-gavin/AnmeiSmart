"""
AI服务主类
负责处理医美领域的智能问答
支持从system模块动态读取AI配置
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List, Type
from uuid import uuid4
from datetime import datetime
from functools import lru_cache
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.ai import StandardAIResponse, StandardConversationHistory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


class AIServiceException(Exception):
    """AI服务异常基类"""
    def __init__(self, message: str, error_code: str, provider: str = None):
        self.message = message
        self.error_code = error_code
        self.provider = provider
        super().__init__(self.message)


class AIService:
    """AI服务类，提供医美智能问答能力"""
    
    def __init__(self, db: Session = None):
        """初始化AI服务"""
        self.db = db
        self._service_instances = {}  # 缓存服务实例
        self._active_configs = []
        self._default_config = None
        
        # 加载配置
        self._load_configurations()
        
        # 加载医美领域知识库
        self.medical_beauty_knowledge = self._load_medical_beauty_knowledge()
        
        logger.info(f"AI服务初始化完成，可用提供商: {self.get_available_providers()}")
    
    def _load_configurations(self) -> None:
        """从system模块或环境变量加载AI配置"""
        if self.db:
            try:
                # 从数据库加载配置
                from app.services.system_service import get_active_ai_configs, get_default_ai_config
                self._active_configs = get_active_ai_configs(self.db)
                self._default_config = get_default_ai_config(self.db)
                
                if self._active_configs:
                    logger.info(f"从数据库加载了 {len(self._active_configs)} 个AI配置")
                else:
                    logger.warning("数据库中没有可用的AI配置，将使用环境变量或模拟服务")
                    
            except Exception as e:
                logger.error(f"从数据库加载AI配置失败: {e}")
        
        # 如果数据库配置不可用，使用环境变量配置
        if not self._active_configs:
            self._load_env_configurations()
    
    def _load_env_configurations(self) -> None:
        """从环境变量加载配置（兼容原有逻辑）"""
        provider = os.environ.get("AI_PROVIDER", "simulated").lower()
        api_key = os.environ.get("AI_API_KEY", "")
        model = os.environ.get("AI_MODEL", "default")
        api_base_url = os.environ.get("AI_API_BASE_URL", "")
        
        if provider != "simulated" and api_key:
            config = {
                "name": f"env_{provider}",
                "provider": provider,
                "api_key": api_key,
                "api_base_url": api_base_url or self._get_default_url(provider),
                "model": model,
                "temperature": 0.7,
                "max_tokens": 2000,
                "is_enabled": True
            }
            self._active_configs = [config]
            self._default_config = config
            logger.info(f"从环境变量加载配置: {provider}")
        else:
            logger.info("使用模拟AI服务")
    
    def _get_default_url(self, provider: str) -> str:
        """获取提供商默认URL"""
        default_urls = {
            "openai": "https://api.openai.com/v1",
            "dify": "http://localhost/v1"
        }
        return default_urls.get(provider, "")
    
    def get_available_providers(self) -> List[str]:
        """获取当前可用的AI提供商列表"""
        if not self._active_configs:
            return ["simulated"]
        return [config["provider"] for config in self._active_configs]
    
    def get_default_provider(self) -> str:
        """获取默认AI提供商"""
        if self._default_config:
            return self._default_config["provider"]
        elif self._active_configs:
            return self._active_configs[0]["provider"]
        return "simulated"
    
    def get_available_models(self) -> List[str]:
        """获取当前可用的AI模型列表"""
        if not self._active_configs:
            return ["simulated"]
        return [config["name"] for config in self._active_configs]
    
    async def check_providers_health(self) -> Dict[str, bool]:
        """检查各个提供商的健康状态"""
        health_status = {}
        
        for config in self._active_configs:
            provider = config["provider"]
            try:
                # 获取服务实例
                service = self._get_service_instance(config)
                if service and hasattr(service, 'health_check'):
                    is_healthy = await service.health_check()
                    health_status[provider] = is_healthy
                else:
                    health_status[provider] = True  # 假设可用
            except Exception as e:
                logger.error(f"检查提供商 {provider} 健康状态失败: {e}")
                health_status[provider] = False
        
        # 如果没有配置，模拟服务总是可用的
        if not health_status:
            health_status["simulated"] = True
        
        return health_status
    
    async def get_response(self, query: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        获取AI回复
        
        Args:
            query: 用户问题
            conversation_history: 对话历史记录
            
        Returns:
            包含AI回复内容的字典
        """
        # 如果没有可用配置，使用模拟回复
        if not self._active_configs:
            return self._get_simulated_response(query, conversation_history)
        
        # 选择配置（优先使用默认配置）
        config = self._default_config or self._active_configs[0]
        
        try:
            # 获取服务实例
            service = self._get_service_instance(config)
            
            if not service:
                logger.warning(f"无法获取{config['provider']}服务实例，使用模拟回复")
                return self._get_simulated_response(query, conversation_history)
            
            # 标准化历史记录格式
            standardized_history = self._standardize_conversation_history(conversation_history)
            
            # 调用实际AI服务
            response = await service.generate_response(query, standardized_history)
            
            # 标准化响应格式
            return self._standardize_response(response, config["provider"])
            
        except Exception as e:
            logger.error(f"AI服务调用失败: {str(e)}")
            return self._create_error_response(str(e))
    
    def _get_service_instance(self, config: Dict[str, Any]):
        """获取具体AI服务实例"""
        provider = config["provider"]
        
        # 检查缓存
        cache_key = f"{provider}_{config.get('name', 'default')}"
        if cache_key in self._service_instances:
            return self._service_instances[cache_key]
        
        try:
            if provider == "openai":
                from .openai_service import OpenAIService
                service = OpenAIService()
                # 设置配置
                service.api_key = config["api_key"]
                service.api_base_url = config["api_base_url"]
                service.model = config.get("model", "gpt-3.5-turbo")
                
            elif provider == "dify":
                from .dify_service import DifyService
                service_config = {
                    "api_key": config["api_key"],
                    "api_base_url": config["api_base_url"],
                    "app_id": config.get("app_id", "")
                }
                service = DifyService(service_config)
                
            else:
                logger.warning(f"未知的AI提供商: {provider}")
                return None
            
            # 缓存服务实例
            self._service_instances[cache_key] = service
            return service
            
        except Exception as e:
            logger.error(f"创建{provider}服务实例失败: {str(e)}")
            return None
    
    def _standardize_conversation_history(self, history: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """标准化对话历史格式"""
        if not history:
            return None
        
        standardized = []
        for message in history:
            standardized.append({
                "content": message.get("content", ""),
                "sender_type": message.get("sender_type", "user"),
                "timestamp": message.get("timestamp", datetime.now().isoformat())
            })
        
        return standardized
    
    def _standardize_response(self, response: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """标准化AI响应格式"""
        return {
            "id": response.get("id", f"ai_msg_{uuid4().hex}"),
            "content": response.get("content", ""),
            "timestamp": response.get("timestamp", datetime.now().isoformat()),
            "provider": provider,
            "metadata": response.get("metadata", {})
        }
    
    def _create_error_response(self, error_msg: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "id": f"ai_msg_{uuid4().hex}",
            "content": "抱歉，我暂时无法回答您的问题，请稍后再试。",
            "timestamp": datetime.now().isoformat(),
            "provider": "error",
            "metadata": {"error": error_msg}
        }
    
    def _load_medical_beauty_knowledge(self) -> Dict[str, List[str]]:
        """加载医美领域知识库，用于模拟回复或增强AI回复"""
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
            "timestamp": datetime.now().isoformat(),
            "provider": "simulated",
            "metadata": {}
        }
    
    def reload_configurations(self) -> None:
        """重新加载配置（用于配置变更时的动态更新）"""
        self._service_instances.clear()  # 清除缓存
        self._load_configurations()
        logger.info("AI服务配置已重新加载")


# 全局AI服务实例
_ai_service_instance = None


def get_ai_service(db: Session = None) -> AIService:
    """
    获取AI服务实例
    如果传入db session，则创建支持数据库配置的实例
    否则返回全局单例实例
    """
    global _ai_service_instance
    
    if db:
        # 如果传入了数据库session，创建新实例支持数据库配置
        return AIService(db)
    else:
        # 使用全局单例
        if _ai_service_instance is None:
            _ai_service_instance = AIService()
        return _ai_service_instance 