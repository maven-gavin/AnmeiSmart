"""
Agent管理器，负责管理多个Dify Agent
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models.system import AIModelConfig, AgentType
from app.services.ai.dify_factory import DifyServiceFactory
from app.services.ai.dify_service import DifyService

logger = logging.getLogger(__name__)

class AgentManager:
    """Agent管理器，负责管理多个Dify Agent"""
    
    def __init__(self, db: Session):
        self.db = db
        self._agent_cache: Dict[str, DifyService] = {}
    
    def get_agent_by_type(self, agent_type: AgentType) -> Optional[DifyService]:
        """根据类型获取Agent"""
        try:
            # 查找该类型的默认Agent
            config = self.db.query(AIModelConfig).filter(
                and_(
                    AIModelConfig.provider == "dify",
                    AIModelConfig.agent_type == agent_type,
                    AIModelConfig.enabled == True,
                    AIModelConfig.is_default_for_type == True
                )
            ).first()
            
            if not config:
                # 如果没有默认的，获取该类型的第一个可用Agent
                config = self.db.query(AIModelConfig).filter(
                    and_(
                        AIModelConfig.provider == "dify",
                        AIModelConfig.agent_type == agent_type,
                        AIModelConfig.enabled == True
                    )
                ).first()
            
            if not config:
                logger.warning(f"未找到类型为 {agent_type} 的可用Agent")
                return None
            
            return self._get_or_create_agent(config)
            
        except Exception as e:
            logger.error(f"获取Agent失败: {e}")
            return None
    
    def get_agent_by_name(self, model_name: str) -> Optional[DifyService]:
        """根据模型名称获取Agent"""
        try:
            config = self.db.query(AIModelConfig).filter(
                and_(
                    AIModelConfig.model_name == model_name,
                    AIModelConfig.provider == "dify",
                    AIModelConfig.enabled == True
                )
            ).first()
            
            if not config:
                logger.warning(f"未找到名称为 {model_name} 的Agent")
                return None
            
            return self._get_or_create_agent(config)
            
        except Exception as e:
            logger.error(f"获取Agent失败: {e}")
            return None
    
    def _get_or_create_agent(self, config: AIModelConfig) -> DifyService:
        """获取或创建Agent实例"""
        cache_key = f"{config.model_name}_{config.id}"
        
        if cache_key not in self._agent_cache:
            # 使用工厂创建实例
            self._agent_cache[cache_key] = DifyServiceFactory.create_from_ai_model_config(config)
            logger.info(f"创建Agent实例: {config.model_name} ({config.agent_type})")
        
        return self._agent_cache[cache_key]
    
    def list_agents_by_type(self, agent_type: AgentType) -> List[Dict[str, Any]]:
        """列出指定类型的所有Agent"""
        configs = self.db.query(AIModelConfig).filter(
            and_(
                AIModelConfig.provider == "dify",
                AIModelConfig.agent_type == agent_type,
                AIModelConfig.enabled == True
            )
        ).all()
        
        return [
            {
                "id": config.id,
                "name": config.model_name,
                "app_id": config.dify_app_id,
                "description": config.description,
                "is_default": config.is_default_for_type,
                "connection_name": config.dify_connection.name if config.dify_connection else "未知连接"
            }
            for config in configs
        ]
    
    def clear_cache(self):
        """清空Agent缓存"""
        self._agent_cache.clear()
        logger.info("Agent缓存已清空")

# 全局Agent管理器实例
_agent_manager: Optional[AgentManager] = None

def get_agent_manager(db: Session) -> AgentManager:
    """获取Agent管理器实例"""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager(db)
    return _agent_manager 