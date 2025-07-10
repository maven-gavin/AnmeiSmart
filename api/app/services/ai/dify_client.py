"""
Dify API客户端，用于获取应用列表等管理功能
"""
import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DifyAPIClient:
    """Dify API客户端，用于获取应用列表等管理功能"""
    
    def __init__(self, api_base_url: str, api_key: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接是否有效"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 尝试获取应用列表来验证连接
                response = await client.get(
                    f"{self.api_base_url}/apps",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return {"success": True, "message": "连接成功"}
                else:
                    return {"success": False, "message": f"连接失败: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Dify连接测试失败: {e}")
            return {"success": False, "message": f"连接错误: {str(e)}"}
    
    async def get_apps(self) -> List[Dict[str, Any]]:
        """获取Dify应用列表"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_base_url}/apps",
                    headers=self.headers,
                    params={"page": 1, "limit": 100}  # 根据Dify API调整参数
                )
                
                if response.status_code != 200:
                    logger.error(f"获取Dify应用列表失败: {response.status_code} {response.text}")
                    return []
                
                data = response.json()
                
                # 根据Dify API响应格式调整
                apps = data.get("data", []) if isinstance(data, dict) else data
                
                formatted_apps = []
                for app in apps:
                    formatted_apps.append({
                        "id": app.get("id"),
                        "name": app.get("name", "未知应用"),
                        "description": app.get("description", ""),
                        "mode": app.get("mode", "unknown"),  # agent, workflow, chat, etc.
                        "status": app.get("status", "normal"),
                        "created_at": app.get("created_at"),
                        "icon": app.get("icon", ""),
                        "icon_background": app.get("icon_background", ""),
                        "model_config": app.get("model_config", {}),
                        "tags": app.get("tags", [])
                    })
                
                logger.info(f"获取到 {len(formatted_apps)} 个Dify应用")
                return formatted_apps
                
        except Exception as e:
            logger.error(f"获取Dify应用列表异常: {e}")
            return []
    
    async def get_app_detail(self, app_id: str) -> Optional[Dict[str, Any]]:
        """获取应用详细信息"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_base_url}/apps/{app_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"获取应用详情失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取应用详情异常: {e}")
            return None 