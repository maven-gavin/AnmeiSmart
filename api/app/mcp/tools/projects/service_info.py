"""
项目服务信息查询MCP工具
"""

from app.mcp.registry import mcp_tool


@mcp_tool(
    name="get_service_info",
    description="获取服务项目信息和价格",
    category="projects"
)
async def get_service_info(service_type: str = "all") -> dict:
    """获取服务信息"""
    services = {
        "face_care": {
            "name": "面部护理",
            "price_range": "500-2000元",
            "duration": "60-90分钟",
            "description": "深层清洁、补水保湿、紧致提升"
        },
        "anti_aging": {
            "name": "抗衰老",
            "price_range": "1000-5000元",
            "duration": "90-120分钟",
            "description": "射频紧肤、微针美塑、光子嫩肤"
        },
        "skin_treatment": {
            "name": "皮肤治疗",
            "price_range": "800-3000元",
            "duration": "45-75分钟",
            "description": "祛痘、淡斑、修复敏感肌"
        }
    }
    
    if service_type == "all":
        return {
            "services": services,
            "total_categories": len(services),
            "popular_services": ["face_care", "anti_aging"]
        }
    else:
        service = services.get(service_type)
        return {
            "service": service if service else "服务未找到",
            "alternatives": list(services.keys()) if not service else []
        } 