"""
治疗方案优化MCP工具
"""

from datetime import datetime
from app.mcp.registry import mcp_tool


@mcp_tool(
    name="optimize_plan",
    description="根据反馈优化现有治疗方案",
    category="treatment"
)
async def optimize_plan(plan_id: str, feedback: dict) -> dict:
    """优化方案"""
    # TODO: 实现基于反馈的方案优化逻辑
    return {
        "optimized_plan_id": f"opt_{plan_id}",
        "changes": [
            "调整治疗频率从每周2次改为每周1次",
            "增加保湿护理项目",
            "延长疗程至8周"
        ],
        "reason": "根据客户反馈调整节奏和强度",
        "optimized_at": datetime.now().isoformat(),
        "feedback_summary": feedback.get("summary", "客户希望调整治疗强度"),
        "improvement_areas": ["舒适度", "效果持久性", "时间安排"]
    } 