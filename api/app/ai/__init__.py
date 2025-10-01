"""
AI模块 - 新架构

本模块采用AI Gateway架构，提供统一的AI服务调用接口。

主要组件：
- AIGatewayService: 统一AI服务入口
- AIServiceInterface: AI服务抽象接口
- 多种AI适配器：Agent、Dify等

使用方式：
    from app.ai.ai_gateway_service import get_ai_gateway_service
    
    ai_gateway = get_ai_gateway_service(db)
    response = await ai_gateway.chat(message, user_id, session_id)
"""

# 导出依赖注入配置
try:
    from .deps import get_agent_config_service
    __all__ = ["get_agent_config_service"]
except ImportError:
    __all__ = [] 