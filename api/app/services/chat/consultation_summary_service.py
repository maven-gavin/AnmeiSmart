"""
咨询总结服务
处理咨询总结的创建、更新、查询等业务逻辑
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models.chat import Conversation, Message
from app.db.models.user import User
from app.schemas.chat import (
    ConsultationSummaryResponse,
    ConsultationSummaryInfo,
    CreateConsultationSummaryRequest,
    UpdateConsultationSummaryRequest,
    AIGenerateSummaryRequest,
    AIGeneratedSummaryResponse,  # 新增AI生成总结的响应schema
    ConsultationSummary,
    ConsultationSummaryBasicInfo,
    ConsultationType
)
from app.services.ai.ai_gateway_service import get_ai_gateway_service


class ConsultationSummaryService:
    """咨询总结服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = get_ai_gateway_service(db)
    
    def get_conversation_summary(self, conversation_id: str, user_id: str) -> Optional[ConsultationSummaryResponse]:
        """获取会话的咨询总结"""
        conversation = self._get_conversation_with_permission(conversation_id, user_id)
        if not conversation:
            return None
            
        return ConsultationSummaryResponse.from_model(conversation)
    
    def create_consultation_summary(self, request: CreateConsultationSummaryRequest, user_id: str) -> ConsultationSummaryResponse:
        """创建咨询总结"""
        conversation = self._get_conversation_with_permission(request.conversation_id, user_id)
        if not conversation:
            raise ValueError("会话不存在或无权限访问")
        
        if conversation.consultation_summary:
            raise ValueError("该会话已有咨询总结，请使用更新功能")
        
        # 获取会话消息用于计算基础信息
        messages = self._get_conversation_messages(conversation.id)
        
        # 计算基础信息
        basic_info = self._calculate_basic_info(conversation, messages, user_id)
        
        # 使用简化的工厂方法创建咨询总结
        consultation_summary = ConsultationSummary.create_summary(
            basic_info=basic_info,
            main_issues=request.main_issues,
            solutions=request.solutions,
            follow_up_plan=request.follow_up_plan,
            satisfaction_rating=request.satisfaction_rating,
            additional_notes=request.additional_notes,
            tags=request.tags,
            ai_generated=False
        )
        
        # 更新会话
        conversation.consultation_summary = consultation_summary.model_dump(mode='json')
        conversation.consultation_type = consultation_summary.basic_info.type.value
        conversation.summary = self._generate_short_summary(consultation_summary)
        
        self.db.commit()
        self.db.refresh(conversation)
        
        return ConsultationSummaryResponse.from_model(conversation)
    
    def update_consultation_summary(self, conversation_id: str, request: UpdateConsultationSummaryRequest, user_id: str) -> ConsultationSummaryResponse:
        """更新咨询总结"""
        conversation = self._get_conversation_with_permission(conversation_id, user_id)
        if not conversation:
            raise ValueError("会话不存在或无权限访问")
        
        if not conversation.consultation_summary:
            raise ValueError("该会话尚未创建咨询总结")
        
        # 使用schema的更新方法
        current_summary = ConsultationSummary.from_dict(conversation.consultation_summary)
        updated_summary = current_summary.update_from_request(request)
        
        # 保存更新
        conversation.consultation_summary = updated_summary.model_dump(mode='json')
        conversation.summary = self._generate_short_summary(updated_summary)
        
        self.db.commit()
        self.db.refresh(conversation)
        
        return ConsultationSummaryResponse.from_model(conversation)
    
    async def ai_generate_summary(self, request: AIGenerateSummaryRequest, user_id: str) -> AIGeneratedSummaryResponse:
        """AI生成咨询总结"""
        conversation = self._get_conversation_with_permission(request.conversation_id, user_id)
        if not conversation:
            raise ValueError("会话不存在或无权限访问")
        
        # 获取会话消息
        messages = self._get_conversation_messages(request.conversation_id)
        
        if not messages:
            raise ValueError("会话中没有消息，无法生成总结")
        
        # 构建AI查询
        conversation_text = self._build_conversation_text(messages)
        ai_prompt = self._build_summary_prompt(conversation_text, request.include_suggestions, request.focus_areas)
        
        # 调用AI Gateway生成总结
        ai_response = await self.ai_service.summarize_consultation(conversation_text, "consultant")
        
        # 使用schema处理AI响应
        return AIGeneratedSummaryResponse.from_ai_response(ai_response, request.conversation_id)
    
    def save_ai_generated_summary(self, conversation_id: str, ai_summary_data: Dict[str, Any], user_id: str) -> ConsultationSummaryResponse:
        """保存AI生成的咨询总结"""
        conversation = self._get_conversation_with_permission(conversation_id, user_id)
        if not conversation:
            raise ValueError("会话不存在或无权限访问")
        
        # 获取会话消息用于计算基础信息
        messages = self._get_conversation_messages(conversation.id)
        
        # 计算基础信息
        basic_info = self._calculate_basic_info(conversation, messages, user_id)
        
        # 使用简化的工厂方法创建AI生成的咨询总结
        consultation_summary = ConsultationSummary.create_summary(
            basic_info=basic_info,
            main_issues=ai_summary_data.get('main_issues', []),
            solutions=ai_summary_data.get('solutions', []),
            follow_up_plan=ai_summary_data.get('follow_up_plan', []),
            satisfaction_rating=ai_summary_data.get('satisfaction_rating'),
            additional_notes=ai_summary_data.get('additional_notes'),
            tags=ai_summary_data.get('tags', []),
            ai_generated=True
        )
        
        # 保存到数据库
        conversation.consultation_summary = consultation_summary.model_dump(mode='json')
        conversation.consultation_type = consultation_summary.basic_info.type.value
        conversation.summary = self._generate_short_summary(consultation_summary)
        
        self.db.commit()
        self.db.refresh(conversation)
        
        return ConsultationSummaryResponse.from_model(conversation)
    
    def get_customer_consultation_history(self, customer_id: str, user_id: str, limit: int = 10) -> List[ConsultationSummaryInfo]:
        """获取客户的咨询历史总结"""
        # 验证权限（只有顾问可以查看客户的咨询历史）
        self._validate_consultant_permission(user_id)
        
        conversations = self.db.query(Conversation).filter(
            and_(
                Conversation.owner_id == customer_id,
                Conversation.consultation_summary.isnot(None)
            )
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()
        
        return [ConsultationSummaryInfo.from_model(conv) for conv in conversations]
    
    def delete_consultation_summary(self, conversation_id: str, user_id: str) -> bool:
        """删除咨询总结"""
        conversation = self._get_conversation_with_permission(conversation_id, user_id)
        if not conversation:
            raise ValueError("会话不存在或无权限访问")
        
        if not conversation.consultation_summary:
            raise ValueError("该会话没有咨询总结")
        
        conversation.consultation_summary = None
        conversation.consultation_type = None
        conversation.summary = None
        
        self.db.commit()
        return True
    
    def _get_conversation_with_permission(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """获取会话并验证权限"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return None
        
        # 验证权限：顾问或客户本人可以访问
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        user_role_names = [role.name for role in user.roles] if user.roles else []
        is_consultant = 'consultant' in user_role_names or getattr(user, 'active_role', None) == 'consultant'
        if is_consultant or conversation.owner_id == user_id:
            return conversation
        
        return None
    
    def _validate_consultant_permission(self, user_id: str):
        """验证顾问权限"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        
        user_role_names = [role.name for role in user.roles] if user.roles else []
        is_consultant = 'consultant' in user_role_names or getattr(user, 'active_role', None) == 'consultant'
        if not is_consultant:
            raise ValueError("无权限访问客户咨询历史")
    
    def _get_conversation_messages(self, conversation_id: str) -> List[Message]:
        """获取会话消息"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp).all()

    def _build_conversation_text(self, messages: List[Message]) -> str:
        """构建对话文本用于AI分析"""
        conversation_lines = []
        for msg in messages:
            sender = "顾问" if msg.sender_type == "consultant" else "客户"
            if msg.type == "text" and isinstance(msg.content, dict):
                text = msg.content.get("text", "")
                conversation_lines.append(f"{sender}: {text}")
            elif msg.type == "text" and isinstance(msg.content, str):
                conversation_lines.append(f"{sender}: {msg.content}")
        
        return "\n".join(conversation_lines)

    def _build_summary_prompt(self, conversation_text: str, include_suggestions: bool = False, focus_areas: List[str] = None) -> str:
        """构建AI总结提示"""
        prompt = f"""
请分析以下医美咨询对话，并生成结构化的咨询总结：

对话内容：
{conversation_text}

请提供JSON格式的总结，包含以下字段：
- main_issues: 主要问题列表（数组）
- solutions: 解决方案列表（数组）
- follow_up_plan: 后续跟进计划列表（数组）
- satisfaction_rating: 客户满意度评分（1-5分，可选）
- additional_notes: 补充备注（字符串，可选）
- tags: 相关标签列表（数组，可选）

"""
        
        if focus_areas:
            prompt += f"\n特别关注以下方面：{', '.join(focus_areas)}\n"
        
        if include_suggestions:
            prompt += "\n请包含改进建议和专业意见。\n"
        
        prompt += "\n请确保回复是有效的JSON格式。"
        
        return prompt
    
    def _calculate_basic_info(self, conversation, messages, user_id: str) -> ConsultationSummaryBasicInfo:
        """计算会话基础信息"""
        if messages:
            start_time = messages[0].timestamp
            end_time = messages[-1].timestamp
        else:
            # 如果没有消息，使用会话创建时间
            start_time = conversation.created_at
            end_time = conversation.updated_at or datetime.utcnow()
        
        # 计算时长
        duration = end_time - start_time
        duration_minutes = int(duration.total_seconds() / 60)
        
        # 确定咨询类型
        consultation_type = self._determine_consultation_type(conversation)
        
        return ConsultationSummaryBasicInfo(
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            type=consultation_type,
            consultant_id=conversation.assigned_consultant_id or user_id,
            customer_id=conversation.owner_id
        )
    
    def _determine_consultation_type(self, conversation) -> ConsultationType:
        """确定咨询类型（需要数据库查询）"""
        if conversation.consultation_type:
            return ConsultationType(conversation.consultation_type)
        
        # 检查该客户是否有历史会话
        previous_conversations = self.db.query(Conversation).filter(
            and_(
                Conversation.owner_id == conversation.owner_id,
                Conversation.id != conversation.id,
                Conversation.created_at < conversation.created_at
            )
        ).count()
        
        if previous_conversations == 0:
            return ConsultationType.initial
        else:
            return ConsultationType.follow_up
    
    def _generate_short_summary(self, consultation_summary: ConsultationSummary) -> str:
        """生成简短摘要"""
        parts = []
        
        if consultation_summary.main_issues:
            parts.append(f"主要问题: {', '.join(consultation_summary.main_issues[:2])}")
        
        if consultation_summary.solutions:
            parts.append(f"解决方案: {', '.join(consultation_summary.solutions[:2])}")
        
        if consultation_summary.satisfaction_rating:
            parts.append(f"满意度: {consultation_summary.satisfaction_rating}/5")
        
        return "; ".join(parts) 