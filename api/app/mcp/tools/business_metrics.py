"""
业务指标MCP工具（装饰器模式）

为Dify Agent提供业务指标和统计数据，
用于生成数据驱动的洞察和建议。
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.base import get_db
from app.db.models.user import User
from app.db.models.chat import Conversation, Message
from ..server import mcp_server

logger = logging.getLogger(__name__)


@mcp_server.tool()
async def get_business_metrics(metric_type: str = "overview", time_range: str = "30d") -> Dict[str, Any]:
    """
    获取业务指标和统计数据，包括用户增长、活跃度、会话等指标
    
    Args:
        metric_type: 指标类型 (overview/user_growth/engagement/conversation)
        time_range: 时间范围 (7d/30d/90d/1y)
    
    Returns:
        Dict: 业务指标数据，包含各项统计和趋势分析
    """
    db = next(get_db())
    
    try:
        logger.info(f"获取业务指标: metric_type={metric_type}, time_range={time_range}")
        
        # 解析时间范围
        end_date = datetime.now()
        start_date = _parse_time_range(time_range)
        
        if metric_type == "overview":
            result = _get_overview_metrics(db, start_date, end_date)
        elif metric_type == "user_growth":
            result = _get_user_growth_metrics(db, start_date, end_date)
        elif metric_type == "engagement":
            result = _get_engagement_metrics(db, start_date, end_date)
        elif metric_type == "conversation":
            result = _get_conversation_metrics(db, start_date, end_date)
        else:
            return {
                "error": f"Unsupported metric type: {metric_type}",
                "error_code": "INVALID_METRIC_TYPE",
                "supported_types": ["overview", "user_growth", "engagement", "conversation"]
            }
        
        # 添加元数据
        result.update({
            "metric_type": metric_type,
            "time_range": time_range,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "generated_at": datetime.now().isoformat(),
            "source": "mcp_business_metrics_tool"
        })
        
        logger.info(f"成功获取业务指标: metric_type={metric_type}")
        return result
        
    except Exception as e:
        logger.error(f"获取业务指标失败: metric_type={metric_type}, error={e}", exc_info=True)
        return {
            "error": f"Failed to get business metrics: {str(e)}",
            "error_code": "METRICS_ERROR",
            "metric_type": metric_type
        }
    finally:
        db.close()


def _parse_time_range(time_range: str) -> datetime:
    """解析时间范围"""
    now = datetime.now()
    
    if time_range == "7d":
        return now - timedelta(days=7)
    elif time_range == "30d":
        return now - timedelta(days=30)
    elif time_range == "90d":
        return now - timedelta(days=90)
    elif time_range == "1y":
        return now - timedelta(days=365)
    else:
        # 默认30天
        return now - timedelta(days=30)


def _get_overview_metrics(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """获取概览指标"""
    try:
        # 总用户数
        total_users = db.query(User).count()
        
        # 新增用户数
        new_users = db.query(User).filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).count()
        
        # 活跃用户数（有会话活动的用户）
        active_users = db.query(User.id).join(
            Conversation, User.id == Conversation.customer_id
        ).filter(
            Conversation.updated_at >= start_date,
            Conversation.updated_at <= end_date
        ).distinct().count()
        
        # 总会话数
        total_conversations = db.query(Conversation).count()
        
        # 新增会话数
        new_conversations = db.query(Conversation).filter(
            Conversation.created_at >= start_date,
            Conversation.created_at <= end_date
        ).count()
        
        # 总消息数
        total_messages = db.query(Message).count()
        
        # 新增消息数
        new_messages = db.query(Message).filter(
            Message.created_at >= start_date,
            Message.created_at <= end_date
        ).count()
        
        # 角色分布
        role_distribution = _get_role_distribution(db)
        
        return {
            "summary": {
                "total_users": total_users,
                "new_users": new_users,
                "active_users": active_users,
                "total_conversations": total_conversations,
                "new_conversations": new_conversations,
                "total_messages": total_messages,
                "new_messages": new_messages
            },
            "user_stats": {
                "user_growth_rate": _calculate_growth_rate(total_users, new_users),
                "user_activation_rate": round(active_users / max(total_users, 1) * 100, 2),
                "role_distribution": role_distribution
            },
            "engagement_stats": {
                "avg_conversations_per_user": round(total_conversations / max(total_users, 1), 2),
                "avg_messages_per_conversation": round(total_messages / max(total_conversations, 1), 2),
                "avg_messages_per_user": round(total_messages / max(total_users, 1), 2)
            }
        }
        
    except Exception as e:
        logger.error(f"获取概览指标失败: {e}")
        return {"error": "Failed to calculate overview metrics"}


def _get_user_growth_metrics(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """获取用户增长指标"""
    try:
        # 按天统计用户注册
        daily_registrations = db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).group_by(func.date(User.created_at)).all()
        
        # 按角色统计用户增长
        role_growth = db.query(
            User.roles,
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).group_by(User.roles).all()
        
        # 用户留存分析
        retention_stats = _calculate_user_retention(db, start_date, end_date)
        
        return {
            "growth_trend": [
                {
                    "date": reg.date.isoformat(),
                    "new_users": reg.count
                }
                for reg in daily_registrations
            ],
            "role_based_growth": [
                {
                    "role": role.roles[0] if role.roles else "unknown",
                    "new_users": role.count
                }
                for role in role_growth
            ],
            "retention_metrics": retention_stats
        }
        
    except Exception as e:
        logger.error(f"获取用户增长指标失败: {e}")
        return {"error": "Failed to calculate user growth metrics"}


def _get_engagement_metrics(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """获取用户参与度指标"""
    try:
        # 活跃用户统计
        daily_active_users = db.query(
            func.date(Conversation.updated_at).label('date'),
            func.count(func.distinct(Conversation.user_id)).label('dau')
        ).filter(
            Conversation.updated_at >= start_date,
            Conversation.updated_at <= end_date
        ).group_by(func.date(Conversation.updated_at)).all()
        
        # 会话参与度
        conversation_engagement = db.query(
            func.count(Message.id).label('message_count'),
            Conversation.id.label('conversation_id')
        ).join(Conversation, Message.conversation_id == Conversation.id).filter(
            Conversation.updated_at >= start_date,
            Conversation.updated_at <= end_date
        ).group_by(Conversation.id).all()
        
        # AI功能使用率
        ai_usage = db.query(
            func.count(Conversation.id).label('total'),
            func.sum(func.case([(Conversation.ai_enabled == True, 1)], else_=0)).label('ai_enabled')
        ).filter(
            Conversation.created_at >= start_date,
            Conversation.created_at <= end_date
        ).first()
        
        return {
            "daily_active_users": [
                {
                    "date": dau.date.isoformat(),
                    "active_users": dau.dau
                }
                for dau in daily_active_users
            ],
            "conversation_engagement": {
                "avg_messages_per_conversation": round(
                    sum(eng.message_count for eng in conversation_engagement) / 
                    max(len(conversation_engagement), 1), 2
                ),
                "total_engaged_conversations": len(conversation_engagement)
            },
            "ai_feature_usage": {
                "total_conversations": ai_usage.total or 0,
                "ai_enabled_conversations": ai_usage.ai_enabled or 0,
                "ai_adoption_rate": round(
                    (ai_usage.ai_enabled or 0) / max(ai_usage.total or 1, 1) * 100, 2
                )
            }
        }
        
    except Exception as e:
        logger.error(f"获取参与度指标失败: {e}")
        return {"error": "Failed to calculate engagement metrics"}


def _get_conversation_metrics(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """获取会话相关指标"""
    try:
        # 会话统计
        conversation_stats = db.query(
            func.count(Conversation.id).label('total_conversations'),
            func.avg(func.datediff(Conversation.updated_at, Conversation.created_at)).label('avg_duration_days')
        ).filter(
            Conversation.created_at >= start_date,
            Conversation.created_at <= end_date
        ).first()
        
        # 消息类型分布
        message_type_dist = db.query(
            Message.type,
            func.count(Message.id).label('count')
        ).join(Conversation, Message.conversation_id == Conversation.id).filter(
            Message.created_at >= start_date,
            Message.created_at <= end_date
        ).group_by(Message.type).all()
        
        # 会话长度分布
        conversation_lengths = db.query(
            func.count(Message.id).label('message_count'),
            Conversation.id
        ).join(Message, Conversation.id == Message.conversation_id).filter(
            Conversation.created_at >= start_date,
            Conversation.created_at <= end_date
        ).group_by(Conversation.id).all()
        
        # 分析会话长度分布
        length_distribution = _analyze_conversation_length_distribution(conversation_lengths)
        
        return {
            "conversation_statistics": {
                "total_conversations": conversation_stats.total_conversations or 0,
                "avg_duration_days": round(conversation_stats.avg_duration_days or 0, 2)
            },
            "message_type_distribution": [
                {
                    "type": msg_type.type,
                    "count": msg_type.count,
                    "percentage": round(msg_type.count / sum(m.count for m in message_type_dist) * 100, 2)
                }
                for msg_type in message_type_dist
            ],
            "conversation_length_analysis": length_distribution
        }
        
    except Exception as e:
        logger.error(f"获取会话指标失败: {e}")
        return {"error": "Failed to calculate conversation metrics"}


def _get_role_distribution(db: Session) -> Dict[str, Any]:
    """获取角色分布"""
    try:
        total_users = db.query(User).count()
        
        # 统计各角色用户数（处理多角色用户）
        role_counts = {"customer": 0, "consultant": 0, "doctor": 0, "admin": 0, "operator": 0}
        
        users = db.query(User.roles).all()
        for user in users:
            if user.roles:
                for role in user.roles:
                    if role in role_counts:
                        role_counts[role] += 1
        
        return {
            "role_counts": role_counts,
            "role_percentages": {
                role: round(count / max(total_users, 1) * 100, 2)
                for role, count in role_counts.items()
            }
        }
    except Exception as e:
        logger.error(f"获取角色分布失败: {e}")
        return {"role_counts": {}, "role_percentages": {}}


def _calculate_growth_rate(total: int, new: int) -> float:
    """计算增长率"""
    if total == 0:
        return 0.0
    return round(new / total * 100, 2)


def _calculate_user_retention(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """计算用户留存率"""
    try:
        # 获取期间内注册的用户
        new_users = db.query(User.id).filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).all()
        
        if not new_users:
            return {"retention_rate": 0, "analysis": "No new users in period"}
        
        new_user_ids = [user.id for user in new_users]
        
        # 计算这些用户在注册后的活跃情况
        retained_users = db.query(User.id).join(
            Conversation, User.id == Conversation.customer_id
        ).filter(
            User.id.in_(new_user_ids),
            Conversation.created_at > User.created_at,
            Conversation.created_at <= end_date
        ).distinct().count()
        
        retention_rate = round(retained_users / len(new_user_ids) * 100, 2)
        
        return {
            "new_users_count": len(new_user_ids),
            "retained_users_count": retained_users,
            "retention_rate": retention_rate,
            "analysis": f"{retention_rate}% of new users remained active"
        }
        
    except Exception as e:
        logger.error(f"计算用户留存率失败: {e}")
        return {"retention_rate": 0, "analysis": "Failed to calculate retention"}


def _analyze_conversation_length_distribution(conversation_lengths) -> Dict[str, Any]:
    """分析会话长度分布"""
    if not conversation_lengths:
        return {"distribution": {}, "analysis": "No conversations found"}
    
    lengths = [conv.message_count for conv in conversation_lengths]
    
    # 分布统计
    short_convs = len([l for l in lengths if l <= 5])
    medium_convs = len([l for l in lengths if 6 <= l <= 20])
    long_convs = len([l for l in lengths if l > 20])
    
    total_convs = len(lengths)
    avg_length = round(sum(lengths) / total_convs, 2)
    
    return {
        "distribution": {
            "short_conversations": {"count": short_convs, "percentage": round(short_convs/total_convs*100, 2)},
            "medium_conversations": {"count": medium_convs, "percentage": round(medium_convs/total_convs*100, 2)},
            "long_conversations": {"count": long_convs, "percentage": round(long_convs/total_convs*100, 2)}
        },
        "statistics": {
            "average_length": avg_length,
            "total_conversations": total_convs,
            "min_length": min(lengths),
            "max_length": max(lengths)
        }
    } 