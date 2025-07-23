"""
会话数据MCP工具（装饰器模式）

为Dify Agent提供用户会话历史和消息数据查询，
用于理解用户需求和提供上下文相关的服务。
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models.chat import Conversation, Message
from ..server import mcp_server

logger = logging.getLogger(__name__)


@mcp_server.tool()
async def get_conversation_data(user_id: str, limit: int = 10, include_messages: bool = True) -> Dict[str, Any]:
    """
    获取用户会话历史和消息数据，用于理解用户需求和提供上下文
    
    Args:
        user_id: 用户ID
        limit: 返回的会话数量限制（默认10）
        include_messages: 是否包含消息详情（默认True）
    
    Returns:
        Dict: 会话数据，包含会话列表、消息统计、最近活动等
    """
    db = next(get_db())
    
    try:
        logger.info(f"获取会话数据: user_id={user_id}, limit={limit}, include_messages={include_messages}")
        
        # 查询用户的会话
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()
        
        if not conversations:
            logger.info(f"用户无会话记录: {user_id}")
            return {
                "user_id": user_id,
                "total_conversations": 0,
                "conversations": [],
                "message_statistics": _get_empty_message_stats(),
                "activity_summary": "无会话活动",
                "source": "mcp_conversation_data_tool"
            }
        
        # 构建会话数据
        conversation_data = []
        total_messages = 0
        
        for conv in conversations:
            conv_info = {
                "conversation_id": conv.id,
                "title": conv.title or "未命名会话",
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "ai_enabled": conv.ai_enabled,
                "status": conv.status or "active"
            }
            
            # 如果需要包含消息
            if include_messages:
                messages = db.query(Message).filter(
                    Message.conversation_id == conv.id
                ).order_by(Message.created_at.desc()).limit(20).all()
                
                conv_info["message_count"] = len(messages)
                total_messages += len(messages)
                
                # 最近消息摘要
                if messages:
                    recent_messages = []
                    for msg in messages[:5]:  # 只取最近5条
                        msg_content = _extract_message_content(msg)
                        recent_messages.append({
                            "id": msg.id,
                            "type": msg.type,
                            "content_preview": msg_content[:100] + "..." if len(msg_content) > 100 else msg_content,
                            "created_at": msg.created_at.isoformat(),
                            "sender": _determine_message_sender(msg)
                        })
                    conv_info["recent_messages"] = recent_messages
                else:
                    conv_info["recent_messages"] = []
            
            conversation_data.append(conv_info)
        
        # 构建统计信息
        result = {
            "user_id": user_id,
            "total_conversations": len(conversations),
            "conversations": conversation_data,
            "message_statistics": _calculate_message_statistics(db, user_id, total_messages),
            "activity_summary": _generate_activity_summary(conversations),
            "insights": _generate_conversation_insights(conversations, db, user_id),
            "query_timestamp": datetime.now().isoformat(),
            "source": "mcp_conversation_data_tool"
        }
        
        logger.info(f"成功获取会话数据: user_id={user_id}, conversations={len(conversations)}")
        return result
        
    except Exception as e:
        logger.error(f"获取会话数据失败: user_id={user_id}, error={e}", exc_info=True)
        return {
            "error": f"Failed to get conversation data: {str(e)}",
            "error_code": "CONVERSATION_DATA_ERROR",
            "user_id": user_id
        }
    finally:
        db.close()


def _extract_message_content(message) -> str:
    """提取消息内容文本"""
    try:
        if hasattr(message, 'content') and message.content:
            if isinstance(message.content, dict):
                # 结构化内容
                if message.type == "text":
                    return message.content.get("text", "")
                elif message.type == "media":
                    media_type = message.content.get("media_type", "unknown")
                    text = message.content.get("text", "")
                    return f"[{media_type}]{text}" if text else f"[{media_type}消息]"
                else:
                    return str(message.content.get("text", "[系统消息]"))
            else:
                # 纯文本内容
                return str(message.content)
        return "[空消息]"
    except Exception:
        return "[消息解析失败]"


def _determine_message_sender(message) -> str:
    """确定消息发送者"""
    try:
        if hasattr(message, 'sender_type'):
            return message.sender_type
        elif hasattr(message, 'content') and isinstance(message.content, dict):
            return message.content.get("sender", "user")
        return "user"
    except Exception:
        return "unknown"


def _get_empty_message_stats() -> Dict[str, Any]:
    """获取空的消息统计"""
    return {
        "total_messages": 0,
        "user_messages": 0,
        "ai_messages": 0,
        "media_messages": 0,
        "average_message_length": 0
    }


def _calculate_message_statistics(db: Session, user_id: str, known_total: int = 0) -> Dict[str, Any]:
    """计算消息统计"""
    try:
        # 获取用户所有消息统计
        total_query = db.query(Message).join(
            Conversation, Message.conversation_id == Conversation.id
        ).filter(
            Conversation.customer_id == user_id
        )
        
        total_messages = total_query.count()
        
        # 按类型统计
        user_messages = total_query.filter(Message.type == "text").count()
        ai_messages = total_query.filter(Message.type == "system").count()
        media_messages = total_query.filter(Message.type == "media").count()
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "ai_messages": ai_messages,
            "media_messages": media_messages,
            "message_type_distribution": {
                "text": user_messages,
                "system": ai_messages,
                "media": media_messages
            }
        }
    except Exception as e:
        logger.warning(f"消息统计计算失败: {e}")
        return {
            "total_messages": known_total,
            "user_messages": 0,
            "ai_messages": 0,
            "media_messages": 0
        }


def _generate_activity_summary(conversations: List) -> str:
    """生成活动摘要"""
    if not conversations:
        return "无会话活动"
    
    total_conversations = len(conversations)
    latest_activity = conversations[0].updated_at if conversations else None
    
    if latest_activity:
        time_diff = datetime.now() - latest_activity
        if time_diff.days == 0:
            activity_time = "今天"
        elif time_diff.days == 1:
            activity_time = "昨天"
        elif time_diff.days <= 7:
            activity_time = f"{time_diff.days}天前"
        else:
            activity_time = latest_activity.strftime("%Y-%m-%d")
    else:
        activity_time = "未知时间"
    
    return f"共{total_conversations}个会话，最近活动：{activity_time}"


def _generate_conversation_insights(conversations: List, db: Session, user_id: str) -> Dict[str, Any]:
    """生成会话洞察"""
    insights = {
        "conversation_frequency": "low",
        "preferred_interaction_time": "unknown",
        "engagement_pattern": "unknown",
        "conversation_topics": []
    }
    
    if not conversations:
        return insights
    
    try:
        # 会话频率分析
        if len(conversations) >= 5:
            insights["conversation_frequency"] = "high"
        elif len(conversations) >= 2:
            insights["conversation_frequency"] = "medium"
        
        # AI使用偏好
        ai_enabled_count = sum(1 for conv in conversations if conv.ai_enabled)
        if ai_enabled_count > len(conversations) * 0.8:
            insights["ai_usage_preference"] = "high"
        elif ai_enabled_count > len(conversations) * 0.5:
            insights["ai_usage_preference"] = "medium"
        else:
            insights["ai_usage_preference"] = "low"
        
        # 参与模式
        recent_conversations = [conv for conv in conversations if 
                              (datetime.now() - conv.updated_at).days <= 7]
        
        if len(recent_conversations) >= 3:
            insights["engagement_pattern"] = "active"
        elif len(recent_conversations) >= 1:
            insights["engagement_pattern"] = "moderate"
        else:
            insights["engagement_pattern"] = "inactive"
        
        return insights
        
    except Exception as e:
        logger.warning(f"生成会话洞察失败: {e}")
        return insights 