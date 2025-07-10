"""
Dify服务工厂，统一创建和管理DifyService实例
避免重复的实例化逻辑
"""
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

from app.services.ai.dify_service import DifyService
from app.db.models.system import AIModelConfig, DifyConnection

logger = logging.getLogger(__name__)

class DifyServiceFactory:
    """Dify服务工厂类"""
    
    _instance_cache: Dict[str, DifyService] = {}
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> DifyService:
        """
        从配置字典创建DifyService实例
        
        Args:
            config: 包含api_key, api_base_url, app_id等的配置字典
        """
        cache_key = f"{config.get('api_base_url')}_{config.get('app_id')}"
        
        if cache_key not in cls._instance_cache:
            cls._instance_cache[cache_key] = DifyService(config)
            logger.debug(f"创建DifyService实例: {cache_key}")
        
        return cls._instance_cache[cache_key]
    
    @classmethod
    def create_from_ai_model_config(cls, ai_config: AIModelConfig) -> DifyService:
        """
        从AIModelConfig创建DifyService实例
        
        Args:
            ai_config: AI模型配置ORM对象
        """
        if not ai_config.dify_connection:
            raise ValueError(f"AI配置 {ai_config.model_name} 没有关联的Dify连接")
        
        connection = ai_config.dify_connection
        service_config = {
            "api_key": connection.api_key,
            "api_base_url": connection.api_base_url,
            "app_id": ai_config.dify_app_id,
            "model_name": ai_config.model_name,
            "agent_type": ai_config.agent_type.value if ai_config.agent_type else "general"
        }
        
        return cls.create_from_config(service_config)
    
    @classmethod
    def create_from_connection(cls, connection: DifyConnection, app_id: str) -> DifyService:
        """
        从DifyConnection创建DifyService实例
        
        Args:
            connection: Dify连接配置
            app_id: 应用ID
        """
        service_config = {
            "api_key": connection.api_key,
            "api_base_url": connection.api_base_url,
            "app_id": app_id
        }
        
        return cls.create_from_config(service_config)
    
    @classmethod
    def create_from_env_config(cls, env_config: Dict[str, Any]) -> DifyService:
        """
        从环境变量配置创建DifyService实例（兼容原有AIService逻辑）
        
        Args:
            env_config: 包含环境变量配置的字典
        """
        service_config = {
            "api_key": env_config.get("api_key", ""),
            "api_base_url": env_config.get("api_base_url", ""),
            "app_id": env_config.get("app_id", "")
        }
        
        return cls.create_from_config(service_config)
    
    @classmethod
    def clear_cache(cls):
        """清理缓存的实例"""
        cls._instance_cache.clear()
        logger.info("DifyService实例缓存已清理")
    
    @classmethod
    def get_cached_instance_count(cls) -> int:
        """获取缓存的实例数量"""
        return len(cls._instance_cache) 