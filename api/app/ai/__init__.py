"""
#### 主要职责

- **AI 业务能力的抽象与实现**  
  - 定义了 AI 服务的统一接口（`AIService`），屏蔽底层实现细节。
  - 提供了一个模拟实现（`MockAIService`），用于开发和测试。

- **对外提供 AI 能力调用入口**  
  - 通过 `get_ai_service()` 工厂函数，供业务层（如聊天、消息等服务）调用 AI 能力，无需关心 AI 服务的具体实现。

#### 在分层中的作用

- **服务层**：聚合和封装 AI 相关的业务逻辑，对上游（如聊天服务、控制器）提供统一的 AI 能力接口，对下游（如第三方 AI 平台）做适配和隔离。
- **可扩展性**：方便后续接入不同的 AI 服务实现，只需新增实现类并在工厂方法中切换即可。

---

**一句话总结**：  
该文件是服务层的“AI能力适配器”，负责对接和封装 AI 相关业务，为上层业务提供统一、可扩展的 AI 服务接口。

"""

import logging
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime
import random

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AI服务接口
class AIService:
    """AI服务通用接口"""
    
    async def get_response(self, query: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取AI回复
        
        参数:
            query: 用户查询文本
            history: 历史消息列表
            
        返回:
            包含回复内容的字典
        """
        raise NotImplementedError("子类必须实现get_response方法")
    
    async def stream_response(self, query: str, history: List[Dict[str, Any]]):
        """
        流式获取AI回复
        
        参数:
            query: 用户查询文本
            history: 历史消息列表
            
        返回:
            生成器，产生回复片段
        """
        raise NotImplementedError("子类必须实现stream_response方法")

# 模拟AI服务
class MockAIService(AIService):
    """模拟AI服务，用于开发和测试"""
    
    def __init__(self):
        self.responses = {
            "双眼皮": "双眼皮手术一般需要1-2周基本恢复，完全恢复需1-3个月。术后需要注意避免剧烈运动，保持切口清洁干燥，按医嘱服用消炎药和消肿药。",
            "价格": "我们提供多种医美套餐，价格从3000元起，根据具体项目和个人需求定制方案。建议您预约面诊，医生会为您提供详细报价。",
            "医美项目": "我们提供多种医美项目，包括注射类（肉毒素、玻尿酸）、激光类（祛斑、嫩肤）、手术类（双眼皮、隆鼻）等。您有什么特别感兴趣的项目吗？",
            "风险": "任何医疗美容项目都存在一定风险，常见的包括感染、出血、瘢痕等。我们的专业医师会在术前为您详细讲解风险控制措施。",
            "术后护理": "术后护理非常重要，一般需要注意以下几点：保持伤口清洁、避免剧烈运动、防晒、按时复诊、遵医嘱服药。具体护理方案会根据手术类型有所不同。",
            "效果": "医美项目效果因人而异，与个人体质、护理情况等因素有关。我们会在术前充分沟通预期效果，确保您对结果有合理预期。",
            "恢复时间": "不同项目恢复时间不同，一般注射类1-3天，激光类3-7天，手术类1-4周。具体恢复时间医生会在术前告知您。"
        }
    
    async def get_response(self, query: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取AI回复
        
        参数:
            query: 用户查询文本
            history: 历史消息列表
            
        返回:
            包含回复内容的字典
        """
        # 记录请求内容
        logger.info(f"收到AI请求: {query}")
        logger.debug(f"历史消息: {json.dumps(history, ensure_ascii=False)}")
        
        # 模拟处理延迟
        delay = random.uniform(0.5, 3.0)
        await asyncio.sleep(delay)
        
        # 根据关键词匹配回复
        response_text = None
        for keyword, response in self.responses.items():
            if keyword in query:
                response_text = response
                break
        
        # 如果没有匹配到关键词，返回默认回复
        if not response_text:
            response_text = "感谢您的咨询。对于您提到的问题，我建议您预约我们的专业医师进行面诊，以获取更精确的个性化方案。您有其他问题可以随时向我咨询。"
        
        # 模拟超时情况
        if "超时" in query or random.random() < 0.05:  # 5%概率模拟超时
            logger.warning("模拟AI响应超时")
            await asyncio.sleep(12)  # 超过通常的超时时间
        
        # 模拟错误情况
        if "错误" in query or random.random() < 0.02:  # 2%概率模拟错误
            logger.error("模拟AI响应错误")
            raise Exception("模拟的AI服务错误")
        
        # 返回结果
        return {
            "id": f"ai_response_{random.randint(10000, 99999)}",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        }
    
    async def stream_response(self, query: str, history: List[Dict[str, Any]]):
        """
        流式获取AI回复
        
        参数:
            query: 用户查询文本
            history: 历史消息列表
            
        返回:
            生成器，产生回复片段
        """
        # 获取完整回复
        full_response = await self.get_response(query, history)
        content = full_response["content"]
        
        # 分段返回
        chunk_size = max(len(content) // 5, 1)  # 将回复分成大约5段
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            await asyncio.sleep(0.3)  # 模拟网络延迟
            yield {
                "id": full_response["id"],
                "chunk": chunk,
                "is_final": i + chunk_size >= len(content)
            }

# 这里可以添加其他AI服务实现，如OpenAI、Dify等

# 获取配置的AI服务实例
def get_ai_service() -> AIService:
    """
    获取配置的AI服务实例
    
    当前使用模拟服务，实际项目中可以根据配置返回不同的服务实例
    """
    # TODO: 根据配置返回适当的AI服务实例
    return MockAIService()

__all__ = ["AIService", "get_ai_service"]

# 导出依赖注入配置
try:
    from .deps import get_ai_service as get_ai_service_di
    from .deps import get_agent_config_service
    __all__.extend(["get_ai_service_di", "get_agent_config_service"])
except ImportError:
    # 如果依赖注入配置不可用，使用默认实现
    pass 