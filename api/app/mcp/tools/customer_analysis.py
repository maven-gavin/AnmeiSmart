"""
客户分析MCP工具（装饰器模式）

为Dify Agent提供客户画像分析和行为模式预测，
用于生成个性化的服务建议和营销策略。
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from ..server import mcp_server
from .user_profile import get_user_profile

logger = logging.getLogger(__name__)


@mcp_server.tool()
async def analyze_customer(user_id: str, analysis_type: str = "basic") -> Dict[str, Any]:
    """
    分析客户画像和行为模式，提供个性化服务建议
    
    Args:
        user_id: 用户ID
        analysis_type: 分析类型 (basic/detailed/predictive)
    
    Returns:
        Dict: 客户分析结果，包含客户细分、行为模式、推荐策略等
    """
    try:
        logger.info(f"开始客户分析: user_id={user_id}, analysis_type={analysis_type}")
        
        # 获取用户基础信息
        user_profile = await get_user_profile(user_id, include_details=True)
        
        if "error" in user_profile:
            return user_profile
        
        # 基础分析
        analysis_result = {
            "customer_segment": _determine_customer_segment(user_profile),
            "behavior_pattern": _analyze_behavior_pattern(user_profile),
            "engagement_level": _calculate_engagement_level(user_profile),
            "recommendations": _generate_recommendations(user_profile, analysis_type),
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_type": analysis_type
        }
        
        # 详细分析
        if analysis_type in ["detailed", "predictive"]:
            analysis_result.update({
                "risk_profile": _assess_risk_profile(user_profile),
                "lifetime_value_prediction": _predict_lifetime_value(user_profile),
                "churn_probability": _calculate_churn_probability(user_profile),
                "preferred_services": _analyze_preferred_services(user_profile)
            })
        
        # 预测性分析
        if analysis_type == "predictive":
            analysis_result.update({
                "next_best_action": _predict_next_best_action(user_profile),
                "optimal_contact_time": _predict_optimal_contact_time(user_profile),
                "personalization_strategy": _generate_personalization_strategy(user_profile),
                "conversion_probability": _calculate_conversion_probability(user_profile)
            })
        
        logger.info(f"客户分析完成: user_id={user_id}, segment={analysis_result['customer_segment']}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"客户分析失败: user_id={user_id}, error={e}", exc_info=True)
        return {
            "error": f"Customer analysis failed: {str(e)}",
            "error_code": "ANALYSIS_ERROR",
            "user_id": user_id
        }


def _determine_customer_segment(user_profile: Dict[str, Any]) -> str:
    """确定客户细分"""
    primary_role = user_profile.get("primary_role", "unknown")
    is_new_user = user_profile.get("is_new_user", False)
    is_active = user_profile.get("is_active", False)
    
    if not is_active:
        return "inactive_user"
    elif is_new_user:
        return "new_customer"
    elif primary_role == "customer":
        return "regular_customer"
    elif primary_role in ["consultant", "doctor"]:
        return "professional_user"
    elif primary_role == "admin":
        return "system_administrator"
    else:
        return "unknown_segment"


def _analyze_behavior_pattern(user_profile: Dict[str, Any]) -> str:
    """分析行为模式"""
    is_new_user = user_profile.get("is_new_user", False)
    primary_role = user_profile.get("primary_role", "unknown")
    
    if is_new_user:
        return "exploration_phase"
    elif primary_role == "customer":
        return "consultation_seeking"
    elif primary_role in ["consultant", "doctor"]:
        return "service_providing"
    else:
        return "administrative_usage"


def _calculate_engagement_level(user_profile: Dict[str, Any]) -> str:
    """计算参与度水平"""
    is_active = user_profile.get("is_active", False)
    is_new_user = user_profile.get("is_new_user", False)
    
    if not is_active:
        return "low"
    elif is_new_user:
        return "high"  # 新用户通常参与度较高
    else:
        return "medium"


def _generate_recommendations(user_profile: Dict[str, Any], analysis_type: str) -> list:
    """生成推荐策略"""
    recommendations = []
    
    primary_role = user_profile.get("primary_role", "unknown")
    is_new_user = user_profile.get("is_new_user", False)
    
    if is_new_user:
        recommendations.extend([
            "发送个性化欢迎消息",
            "提供新用户引导流程",
            "推荐基础咨询服务",
            "建立初始信任关系"
        ])
    
    if primary_role == "customer":
        recommendations.extend([
            "提供个性化美容建议",
            "推荐合适的医美项目",
            "安排专业顾问咨询",
            "定期跟进服务效果"
        ])
    
    if analysis_type in ["detailed", "predictive"]:
        recommendations.extend([
            "定制长期服务计划",
            "建立客户关系管理",
            "实施精准营销策略"
        ])
    
    return recommendations


def _assess_risk_profile(user_profile: Dict[str, Any]) -> str:
    """评估风险画像"""
    is_active = user_profile.get("is_active", False)
    is_new_user = user_profile.get("is_new_user", False)
    
    if not is_active:
        return "high_risk"
    elif is_new_user:
        return "medium_risk"  # 新用户流失风险中等
    else:
        return "low_risk"


def _predict_lifetime_value(user_profile: Dict[str, Any]) -> str:
    """预测客户终身价值"""
    primary_role = user_profile.get("primary_role", "unknown")
    is_active = user_profile.get("is_active", False)
    
    if not is_active:
        return "low"
    elif primary_role == "customer":
        return "high"  # 付费客户价值较高
    elif primary_role in ["consultant", "doctor"]:
        return "medium"  # 专业用户有间接价值
    else:
        return "low"


def _calculate_churn_probability(user_profile: Dict[str, Any]) -> float:
    """计算流失概率"""
    is_active = user_profile.get("is_active", False)
    is_new_user = user_profile.get("is_new_user", False)
    
    if not is_active:
        return 0.9  # 已经不活跃，流失概率很高
    elif is_new_user:
        return 0.3  # 新用户流失概率中等
    else:
        return 0.1  # 老用户流失概率较低


def _analyze_preferred_services(user_profile: Dict[str, Any]) -> list:
    """分析偏好服务"""
    primary_role = user_profile.get("primary_role", "unknown")
    
    if primary_role == "customer":
        return [
            "美容咨询",
            "项目推荐", 
            "价格查询",
            "预约服务"
        ]
    elif primary_role == "consultant":
        return [
            "客户管理",
            "方案制定",
            "业绩统计"
        ]
    elif primary_role == "doctor":
        return [
            "病例管理", 
            "专业咨询",
            "技术分享"
        ]
    else:
        return ["基础服务"]


def _predict_next_best_action(user_profile: Dict[str, Any]) -> str:
    """预测下一步最佳行动"""
    is_new_user = user_profile.get("is_new_user", False)
    primary_role = user_profile.get("primary_role", "unknown")
    
    if is_new_user:
        return "主动欢迎并提供引导"
    elif primary_role == "customer":
        return "推荐个性化美容方案"
    else:
        return "提供角色相关功能介绍"


def _predict_optimal_contact_time(user_profile: Dict[str, Any]) -> str:
    """预测最佳联系时间"""
    primary_role = user_profile.get("primary_role", "unknown")
    
    if primary_role == "customer":
        return "工作日晚上或周末下午"
    elif primary_role in ["consultant", "doctor"]:
        return "工作日上午或下午"
    else:
        return "工作时间"


def _generate_personalization_strategy(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """生成个性化策略"""
    primary_role = user_profile.get("primary_role", "unknown")
    is_new_user = user_profile.get("is_new_user", False)
    
    strategy = {
        "communication_style": "professional" if primary_role in ["consultant", "doctor"] else "friendly",
        "content_focus": "educational" if is_new_user else "service_oriented",
        "interaction_frequency": "high" if is_new_user else "medium",
        "preferred_channels": ["chat", "email"] if primary_role == "customer" else ["system_notification"]
    }
    
    return strategy


def _calculate_conversion_probability(user_profile: Dict[str, Any]) -> float:
    """计算转化概率"""
    primary_role = user_profile.get("primary_role", "unknown")
    is_new_user = user_profile.get("is_new_user", False)
    is_active = user_profile.get("is_active", False)
    
    if not is_active:
        return 0.1
    elif is_new_user and primary_role == "customer":
        return 0.7  # 新客户转化概率较高
    elif primary_role == "customer":
        return 0.5
    else:
        return 0.2 