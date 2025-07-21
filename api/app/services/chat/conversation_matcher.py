"""
会话匹配服务 - 实现客户与顾问的智能匹配
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.db.models.user import User
from app.db.models.chat import Conversation, Message

logger = logging.getLogger(__name__)


class ConversationMatcher:
    """会话匹配器 - 负责将客户会话分配给合适的顾问"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_best_consultant(
        self, 
        customer_id: str, 
        conversation_content: str = "",
        customer_tags: List[str] = None
    ) -> Optional[str]:
        """
        为客户找到最佳匹配的顾问
        
        匹配规则优先级：
        1. 历史服务过该客户的顾问（优先选择最近服务的）
        2. 专业标签匹配度最高的顾问
        3. 当前工作负载最轻的顾问
        4. 在线状态优先
        """
        try:
            # 获取所有可用的顾问
            available_consultants = self.db.query(User).join(User.roles).filter(
                User.roles.any(name='consultant'),
                User.is_active == True
            ).all()
            
            if not available_consultants:
                logger.warning("没有可用的顾问")
                return None
            
            # 1. 查找历史服务过该客户的顾问
            historical_consultant = self._find_historical_consultant(customer_id)
            if historical_consultant and historical_consultant in [c.id for c in available_consultants]:
                logger.info(f"选择历史顾问: {historical_consultant}")
                return historical_consultant
            
            # 2. 根据专业标签匹配
            if customer_tags:
                tag_matched_consultant = self._find_tag_matched_consultant(
                    available_consultants, customer_tags
                )
                if tag_matched_consultant:
                    logger.info(f"选择标签匹配顾问: {tag_matched_consultant}")
                    return tag_matched_consultant
            
            # 3. 根据内容关键词匹配
            if conversation_content:
                content_matched_consultant = self._find_content_matched_consultant(
                    available_consultants, conversation_content
                )
                if content_matched_consultant:
                    logger.info(f"选择内容匹配顾问: {content_matched_consultant}")
                    return content_matched_consultant
            
            # 4. 选择工作负载最轻的在线顾问
            load_balanced_consultant = self._find_load_balanced_consultant(available_consultants)
            if load_balanced_consultant:
                logger.info(f"选择负载均衡顾问: {load_balanced_consultant}")
                return load_balanced_consultant
            
            # 5. 如果都没有，随机选择第一个可用顾问
            fallback_consultant = available_consultants[0].id
            logger.info(f"选择备用顾问: {fallback_consultant}")
            return fallback_consultant
            
        except Exception as e:
            logger.error(f"匹配顾问失败: {e}")
            return None
    
    def _find_historical_consultant(self, customer_id: str) -> Optional[str]:
        """查找历史服务过该客户的顾问"""
        try:
            # 查找该客户最近的会话中的顾问消息
            recent_consultant_message = self.db.query(Message).join(Conversation).filter(
                Conversation.customer_id == customer_id,
                Message.sender_type == 'consultant'
            ).order_by(Message.timestamp.desc()).first()
            
            if recent_consultant_message:
                # 验证该顾问是否仍然可用
                consultant = self.db.query(User).join(User.roles).filter(
                    User.id == recent_consultant_message.sender_id,
                    User.roles.any(name='consultant'),
                    User.is_active == True
                ).first()
                
                if consultant:
                    return consultant.id
            
            return None
            
        except Exception as e:
            logger.error(f"查找历史顾问失败: {e}")
            return None
    
    def _find_tag_matched_consultant(
        self, 
        consultants: List[User], 
        customer_tags: List[str]
    ) -> Optional[str]:
        """根据标签匹配顾问"""
        try:
            best_match = None
            best_score = 0
            
            for consultant in consultants:
                consultant_tags = getattr(consultant, 'specialties', []) or []
                
                # 计算标签匹配分数
                match_score = len(set(customer_tags) & set(consultant_tags))
                
                # 在线顾问加分
                if getattr(consultant, 'is_online', False):
                    match_score += 0.5
                
                if match_score > best_score:
                    best_score = match_score
                    best_match = consultant.id
            
            return best_match if best_score > 0 else None
            
        except Exception as e:
            logger.error(f"标签匹配失败: {e}")
            return None
    
    def _find_content_matched_consultant(
        self, 
        consultants: List[User], 
        content: str
    ) -> Optional[str]:
        """根据内容关键词匹配顾问"""
        try:
            # 定义关键词到专业领域的映射
            keyword_mapping = {
                '整形': ['plastic_surgery', 'facial'],
                '美容': ['beauty', 'skincare'],
                '减肥': ['weight_loss', 'body_shaping'],
                '护肤': ['skincare', 'beauty'],
                '注射': ['injection', 'botox'],
                '激光': ['laser', 'treatment'],
                '面部': ['facial', 'plastic_surgery'],
                '身体': ['body_shaping', 'weight_loss']
            }
            
            # 提取内容中的关键词
            detected_specialties = []
            content_lower = content.lower()
            
            for keyword, specialties in keyword_mapping.items():
                if keyword in content_lower:
                    detected_specialties.extend(specialties)
            
            if not detected_specialties:
                return None
            
            # 找到专业匹配的顾问
            for consultant in consultants:
                consultant_specialties = getattr(consultant, 'specialties', []) or []
                
                if any(spec in consultant_specialties for spec in detected_specialties):
                    # 优先选择在线的专业匹配顾问
                    if getattr(consultant, 'is_online', False):
                        return consultant.id
            
            # 如果没有在线的专业匹配顾问，选择第一个专业匹配的
            for consultant in consultants:
                consultant_specialties = getattr(consultant, 'specialties', []) or []
                
                if any(spec in consultant_specialties for spec in detected_specialties):
                    return consultant.id
            
            return None
            
        except Exception as e:
            logger.error(f"内容匹配失败: {e}")
            return None
    
    def _find_load_balanced_consultant(self, consultants: List[User]) -> Optional[str]:
        """选择工作负载最轻的顾问"""
        try:
            consultant_loads = []
            
            for consultant in consultants:
                # 计算当前活跃会话数
                active_conversations = self.db.query(Conversation).join(Message).filter(
                    Message.sender_id == consultant.id,
                    Message.sender_type == 'consultant',
                    Conversation.is_active == True,
                    Message.timestamp >= datetime.now() - timedelta(hours=24)  # 24小时内有活动
                ).distinct().count()
                
                # 计算今日消息数
                today_messages = self.db.query(Message).filter(
                    Message.sender_id == consultant.id,
                    Message.sender_type == 'consultant',
                    Message.timestamp >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                ).count()
                
                # 计算负载分数（越低越好）
                load_score = active_conversations * 2 + today_messages * 0.1
                
                # 在线顾问优先
                if getattr(consultant, 'is_online', False):
                    load_score -= 10
                
                consultant_loads.append({
                    'id': consultant.id,
                    'load_score': load_score,
                    'is_online': getattr(consultant, 'is_online', False)
                })
            
            # 按负载分数排序
            consultant_loads.sort(key=lambda x: x['load_score'])
            
            if consultant_loads:
                return consultant_loads[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"负载均衡匹配失败: {e}")
            return None
    
    async def assign_conversation_to_consultant(
        self, 
        conversation_id: str, 
        consultant_id: str
    ) -> bool:
        """将会话分配给指定顾问"""
        try:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                logger.error(f"会话不存在: {conversation_id}")
                return False
            
            # 更新会话的分配顾问
            conversation.assigned_consultant_id = consultant_id
            conversation.updated_at = datetime.now()
            
            # 创建系统消息通知分配
            from app.services.chat.message_service import MessageService
            message_service = MessageService(self.db)
            
            consultant = self.db.query(User).filter(User.id == consultant_id).first()
            consultant_name = consultant.username if consultant else "顾问"
            
            message_service.create_system_event_message(
                conversation_id=conversation_id,
                event_type="consultant_assigned",
                status="assigned",
                event_data={
                    "consultant_id": consultant_id,
                    "consultant_name": consultant_name,
                    "message": f"您的咨询已分配给{consultant_name}，稍后将为您服务"
                }
            )
            
            self.db.commit()
            logger.info(f"会话 {conversation_id} 已分配给顾问 {consultant_id}")
            return True
            
        except Exception as e:
            logger.error(f"分配会话失败: {e}")
            self.db.rollback()
            return False
    
    def get_consultant_workload(self, consultant_id: str) -> Dict[str, Any]:
        """获取顾问的工作负载信息"""
        try:
            # 活跃会话数
            active_conversations = self.db.query(Conversation).join(Message).filter(
                Message.sender_id == consultant_id,
                Message.sender_type == 'consultant',
                Conversation.is_active == True,
                Message.timestamp >= datetime.now() - timedelta(hours=24)
            ).distinct().count()
            
            # 今日消息数
            today_messages = self.db.query(Message).filter(
                Message.sender_id == consultant_id,
                Message.sender_type == 'consultant',
                Message.timestamp >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            # 本周消息数
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            week_messages = self.db.query(Message).filter(
                Message.sender_id == consultant_id,
                Message.sender_type == 'consultant',
                Message.timestamp >= week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            return {
                "consultant_id": consultant_id,
                "active_conversations": active_conversations,
                "today_messages": today_messages,
                "week_messages": week_messages,
                "load_level": self._calculate_load_level(active_conversations, today_messages)
            }
            
        except Exception as e:
            logger.error(f"获取顾问工作负载失败: {e}")
            return {}
    
    def _calculate_load_level(self, active_conversations: int, today_messages: int) -> str:
        """计算负载等级"""
        if active_conversations >= 10 or today_messages >= 100:
            return "high"
        elif active_conversations >= 5 or today_messages >= 50:
            return "medium"
        else:
            return "low" 