"""
咨询服务 - 处理客户发起咨询的业务逻辑
"""
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import logging

from app.db.models.chat import Conversation, ConversationParticipant, Message
from app.db.models.user import User
from app.db.models.digital_human import PendingTask
from app.db.uuid_utils import conversation_id, message_id, task_id
from app.schemas.chat import ConversationInfo

logger = logging.getLogger(__name__)


class ConsultationService:
    """咨询服务 - 处理咨询会话的创建和管理"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_consultation_session(self, customer_id: str) -> ConversationInfo:
        """
        客户发起新的咨询会话
        创建咨询类会话，等待顾问接待
        """
        try:
            # 验证客户用户
            customer = self.db.query(User).filter(User.id == customer_id).first()
            if not customer:
                raise ValueError("客户用户不存在")
            
            # 生成会话标题
            title = f"{customer.username} 的咨询会话"
            
            # 创建咨询会话
            consultation_conversation = Conversation(
                id=conversation_id(),
                title=title,
                chat_mode="single",
                tag="consultation",  # 咨询会话标签为consultation
                owner_id=customer_id,  # 客户为所有者
                first_participant_id=None,  # 第一个参与者ID为空，等待顾问接待
                is_pinned=False,
                is_active=True,
                is_archived=False,
                message_count=0,
                unread_count=0
            )
            
            self.db.add(consultation_conversation)
            self.db.flush()  # 获取ID
            
            # 创建客户参与者记录
            customer_participant = ConversationParticipant(
                id=message_id(),
                conversation_id=consultation_conversation.id,
                user_id=customer_id,
                role="owner",
                takeover_status="no_takeover",
                is_active=True,
                joined_at=datetime.now()
            )
            self.db.add(customer_participant)
            
            self.db.commit()
            
            logger.info(f"咨询会话创建成功: {consultation_conversation.id}, 客户: {customer_id}")
            
            # 使用Schema的from_model方法转换
            return ConversationInfo.from_model(consultation_conversation)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建咨询会话失败: {e}")
            raise
    
    async def create_consultation_task_on_first_message(
        self, 
        conversation_id: str, 
        customer_id: str
    ) -> Optional[str]:
        """
        客户发送第一条消息后创建咨询待办任务
        """
        try:
            # 验证是否为咨询会话
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.tag == "consultation",
                Conversation.owner_id == customer_id
            ).first()
            
            if not conversation:
                raise ValueError("咨询会话不存在或无权限")
            
            # 检查是否已经有待办任务
            existing_task = self.db.query(PendingTask).filter(
                PendingTask.related_object_type == "consultation",
                PendingTask.related_object_id == conversation_id,
                PendingTask.status.in_(["pending", "assigned"])
            ).first()
            
            if existing_task:
                logger.info(f"咨询任务已存在: {existing_task.id}")
                return existing_task.id
            
            # 获取客户信息
            customer = self.db.query(User).filter(User.id == customer_id).first()
            customer_name = customer.username if customer else "客户"
            
            # 创建咨询待办任务
            consultation_task = PendingTask(
                id=task_id(),
                title=f"新客户咨询接待：{customer_name}",
                description=f"客户 {customer_name} 发起了新的咨询，请及时接待和回复",
                task_type="customer_consultation",
                status="pending",
                priority="medium",
                created_by=customer_id,
                assigned_to=None,  # 暂未分配
                related_object_type="consultation",
                related_object_id=conversation_id,
                task_data={
                    "conversation_id": conversation_id,
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "conversation_title": conversation.title,
                    "created_reason": "first_message_sent"
                }
            )
            
            self.db.add(consultation_task)
            self.db.commit()
            
            logger.info(f"咨询待办任务创建成功: {consultation_task.id}")
            return consultation_task.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建咨询待办任务失败: {e}")
            raise
    
    async def assign_consultant_to_consultation(
        self, 
        conversation_id: str, 
        consultant_id: str,
        task_id: str
    ) -> bool:
        """
        顾问接待咨询，分配到咨询会话
        """
        try:
            # 验证咨询会话
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.tag == "consultation",
                Conversation.is_active == True
            ).first()
            
            if not conversation:
                raise ValueError("咨询会话不存在")
            
            # 验证顾问用户
            consultant = self.db.query(User).filter(User.id == consultant_id).first()
            if not consultant:
                raise ValueError("顾问用户不存在")
            
            # 更新会话的第一个参与者为该顾问
            conversation.first_participant_id = consultant_id
            conversation.updated_at = datetime.now()
            
            # 创建顾问参与者记录
            consultant_participant = ConversationParticipant(
                id=message_id(),
                conversation_id=conversation_id,
                user_id=consultant_id,
                role="member",
                takeover_status="full_takeover",  # 顾问全接管
                is_active=True,
                joined_at=datetime.now()
            )
            self.db.add(consultant_participant)
            
            # 更新待办任务状态
            task = self.db.query(PendingTask).filter(PendingTask.id == task_id).first()
            if task:
                task.status = "assigned"
                task.assigned_to = consultant_id
                task.assigned_at = datetime.now()
                task.notes = f"顾问 {consultant.username} 已接待该咨询"
            
            self.db.commit()
            
            logger.info(f"顾问 {consultant_id} 已接待咨询会话 {conversation_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"分配顾问到咨询失败: {e}")
            raise
    
    async def pin_conversation(
        self, 
        conversation_id: str, 
        user_id: str, 
        pin: bool = True
    ) -> bool:
        """
        置顶/取消置顶会话
        """
        try:
            # 验证用户对会话的访问权限
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.is_active == True
            ).first()
            
            if not conversation:
                raise ValueError("会话不存在")
            
            # 检查用户是否有权限（所有者或参与者）
            has_permission = (
                conversation.owner_id == user_id or
                self.db.query(ConversationParticipant).filter(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                    ConversationParticipant.is_active == True
                ).first() is not None
            )
            
            if not has_permission:
                raise ValueError("无权限操作该会话")
            
            # 更新置顶状态
            conversation.is_pinned = pin
            conversation.pinned_at = datetime.now() if pin else None
            conversation.updated_at = datetime.now()
            
            self.db.commit()
            
            action = "置顶" if pin else "取消置顶"
            logger.info(f"会话 {conversation_id} 已{action}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"{'置顶' if pin else '取消置顶'}会话失败: {e}")
            raise
    
    async def get_conversations_with_priority_sorting(
        self, 
        user_id: str, 
        include_consultation: bool = True,
        include_friend_chat: bool = True
    ) -> list[ConversationInfo]:
        """
        获取用户的会话列表，支持置顶排序
        置顶会话按置顶时间倒序，非置顶会话按最后消息时间倒序
        """
        try:
            query = self.db.query(Conversation).options(
                joinedload(Conversation.owner),
                joinedload(Conversation.first_participant)
            )
            
            # 构建查询条件
            conditions = []
            
            # 用户参与的会话（作为所有者或参与者）
            user_conversations = (
                (Conversation.owner_id == user_id) |
                (Conversation.id.in_(
                    self.db.query(ConversationParticipant.conversation_id).filter(
                        ConversationParticipant.user_id == user_id,
                        ConversationParticipant.is_active == True
                    )
                ))
            )
            conditions.append(user_conversations)
            
            # 会话类型筛选
            if include_consultation and include_friend_chat:
                # 包含所有类型
                pass
            elif include_consultation:
                conditions.append(Conversation.tag == "consultation")
            elif include_friend_chat:
                conditions.append(Conversation.tag == "chat")
            else:
                # 两种都不包含，返回空
                return []
            
            # 只查询活跃会话
            conditions.append(Conversation.is_active == True)
            
            # 应用筛选条件
            for condition in conditions:
                query = query.filter(condition)
            
            # 排序：置顶会话在前（按置顶时间倒序），非置顶会话在后（按最后消息时间倒序）
            query = query.order_by(
                Conversation.is_pinned.desc(),  # 置顶的在前
                Conversation.pinned_at.desc(),  # 置顶时间倒序
                Conversation.last_message_at.desc()  # 最后消息时间倒序
            )
            
            conversations = query.all()
            
            # 使用Schema的from_model方法转换
            result = []
            for conversation in conversations:
                conv_info = ConversationInfo.from_model(conversation)
                if conv_info:
                    result.append(conv_info)
            
            return result
            
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            raise
