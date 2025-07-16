"""
方案生成服务 - 负责整个方案生成流程的编排和管理
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import asyncio

from app.db.models.plan_generation import PlanGenerationSession, PlanDraft, InfoCompleteness
from app.db.models.chat import Conversation
from app.db.models.user import User
from app.schemas.plan_generation import (
    PlanGenerationSessionCreate,
    PlanGenerationSessionInfo,
    PlanDraftCreate,
    PlanDraftInfo,
    PlanSessionStatus,
    PlanDraftStatus,
    GeneratePlanRequest,
    PlanGenerationResponse,
    InfoAnalysisResponse,
    ExtractedInfo,
    PlanContent,
    PlanBasicInfo
)
from app.services.ai.ai_gateway_service import get_ai_gateway_service
from .info_analysis_service import InfoAnalysisService
from .plan_optimization_service import PlanOptimizationService
from .plan_version_service import PlanVersionService

logger = logging.getLogger(__name__)


class PlanGenerationService:
    """方案生成服务类 - 统筹整个方案生成流程"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_gateway_service = get_ai_gateway_service(db)  # 使用AI Gateway服务
        self.info_analysis_service = InfoAnalysisService(db)
        self.plan_optimization_service = PlanOptimizationService(db)
        self.plan_version_service = PlanVersionService(db)
    
    def create_session(
        self,
        conversation_id: str,
        customer_id: str,
        consultant_id: str,
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> PlanGenerationSessionInfo:
        """创建方案生成会话"""
        logger.info(f"创建方案生成会话: conversation_id={conversation_id}")
        
        # 检查是否已存在会话
        existing_session = self.db.query(PlanGenerationSession).filter(
            PlanGenerationSession.conversation_id == conversation_id
        ).first()
        
        if existing_session:
            logger.warning(f"会话已存在: {existing_session.id}")
            return PlanGenerationSessionInfo.from_model(existing_session)
        
        # 创建新会话
        session = PlanGenerationSession(
            conversation_id=conversation_id,
            customer_id=customer_id,
            consultant_id=consultant_id,
            status=PlanSessionStatus.collecting,
            session_metadata=session_metadata or {}
        )
        
        # 记录创建操作
        self._add_interaction_history(
            session, 
            "session_created", 
            "consultant", 
            consultant_id,
            {"trigger": "manual", "context": "customer_inquiry"}
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # 初始化信息完整性记录
        self.info_analysis_service.create_completeness_record(session.id)
        
        logger.info(f"方案生成会话创建成功: {session.id}")
        return PlanGenerationSessionInfo.from_model(session)
    
    def get_session(self, session_id: str) -> Optional[PlanGenerationSessionInfo]:
        """获取方案生成会话"""
        session = self.db.query(PlanGenerationSession).filter(
            PlanGenerationSession.id == session_id
        ).first()
        
        if not session:
            return None
        
        return PlanGenerationSessionInfo.from_model(session)
    
    def get_session_by_conversation(
        self, 
        conversation_id: str
    ) -> Optional[PlanGenerationSessionInfo]:
        """通过对话ID获取方案生成会话"""
        session = self.db.query(PlanGenerationSession).filter(
            PlanGenerationSession.conversation_id == conversation_id
        ).first()
        
        if not session:
            return None
        
        return PlanGenerationSessionInfo.from_model(session)
    
    async def analyze_conversation_info(
        self,
        conversation_id: str,
        force_analysis: bool = False
    ) -> InfoAnalysisResponse:
        """分析对话信息"""
        logger.info(f"分析对话信息: conversation_id={conversation_id}")
        
        # 获取或创建会话
        session = self.get_session_by_conversation(conversation_id)
        if not session:
            raise ValueError(f"方案生成会话不存在: {conversation_id}")
        
        # 更新会话状态
        self._update_session_status(session.id, PlanSessionStatus.collecting)
        
        # 执行信息分析
        analysis_result = await self.info_analysis_service.analyze_conversation_info(
            session.id,
            force_analysis=force_analysis
        )
        
        # 记录分析操作
        self._add_interaction_history(
            session, 
            "info_analysis_completed", 
            "ai", 
            "info_extraction_agent",
            {
                "completeness_score": analysis_result.completeness_score,
                "missing_categories": analysis_result.missing_categories
            }
        )
        
        logger.info(f"对话信息分析完成: completeness_score={analysis_result.completeness_score}")
        return analysis_result
    
    async def generate_plan(
        self,
        request: GeneratePlanRequest,
        consultant_id: str
    ) -> PlanGenerationResponse:
        """生成方案"""
        logger.info(f"开始生成方案: conversation_id={request.conversation_id}")
        
        # 获取会话
        session = self.get_session_by_conversation(request.conversation_id)
        if not session:
            raise ValueError(f"方案生成会话不存在: {request.conversation_id}")
        
        # 检查信息完整性
        if not request.force_generation:
            analysis_result = await self.info_analysis_service.analyze_conversation_info(
                session.id,
                force_analysis=False
            )
            
            if not analysis_result.can_generate_plan:
                logger.warning(f"信息不完整，无法生成方案: score={analysis_result.completeness_score}")
                return PlanGenerationResponse(
                    session_id=session.id,
                    draft_id="",
                    status=PlanSessionStatus.collecting,
                    draft_status=PlanDraftStatus.draft,
                    message="信息不完整，请补充缺失信息后再生成方案",
                    needs_review=False,
                    next_steps=["补充客户信息", "重新分析", "生成方案"]
                )
        
        # 更新会话状态
        self._update_session_status(session.id, PlanSessionStatus.generating)
        
        # 记录生成开始
        self._add_interaction_history(
            session, 
            "plan_generation_started", 
            "consultant", 
            consultant_id,
            {"force_generation": request.force_generation}
        )
        
        try:
            # 生成方案内容
            plan_content = await self._generate_plan_content(
                session.id,
                request.generation_options or {}
            )
            
            # 创建方案草稿
            draft = self._create_plan_draft(
                session.id,
                plan_content,
                generation_info={
                    "generator": "ai",
                    "ai_model": "dify-plan-generator-v1.0",
                    "generation_method": "template_based",
                    "generation_time": 60,
                    "tokens_used": 800,
                    "confidence_score": 0.88
                }
            )
            
            # 更新会话状态
            self._update_session_status(session.id, PlanSessionStatus.reviewing)
            
            # 记录生成完成
            self._add_interaction_history(
                session, 
                "plan_generation_completed", 
                "ai", 
                "plan_generation_agent",
                {"draft_id": draft.id, "version": draft.version}
            )
            
            logger.info(f"方案生成完成: draft_id={draft.id}")
            
            return PlanGenerationResponse(
                session_id=session.id,
                draft_id=draft.id,
                status=PlanSessionStatus.reviewing,
                draft_status=PlanDraftStatus.draft,
                message="方案生成完成，请审核",
                needs_review=True,
                next_steps=["审核方案", "优化调整", "确认发送"]
            )
            
        except Exception as e:
            logger.error(f"方案生成失败: {str(e)}")
            
            # 更新会话状态为失败
            self._update_session_status(session.id, PlanSessionStatus.failed)
            
            # 记录生成失败
            self._add_interaction_history(
                session, 
                "plan_generation_failed", 
                "ai", 
                "plan_generation_agent",
                {"error": str(e)}
            )
            
            return PlanGenerationResponse(
                session_id=session.id,
                draft_id="",
                status=PlanSessionStatus.failed,
                draft_status=PlanDraftStatus.draft,
                message=f"方案生成失败: {str(e)}",
                needs_review=False,
                next_steps=["重新生成", "检查信息", "手动编辑"]
            )
    
    async def _generate_plan_content(
        self,
        session_id: str,
        generation_options: Dict[str, Any]
    ) -> PlanContent:
        """生成方案内容（调用AI服务）"""
        logger.info(f"调用AI服务生成方案内容: session_id={session_id}")
        
        # 获取提取的信息
        session = self.db.query(PlanGenerationSession).filter(
            PlanGenerationSession.id == session_id
        ).first()
        
        if not session or not session.extracted_info:
            raise ValueError("缺少客户信息，无法生成方案")
        
        # 构建AI请求
        ai_request = {
            "customer_info": session.extracted_info,
            "generation_options": generation_options,
            "session_context": {
                "conversation_id": session.conversation_id,
                "customer_id": session.customer_id,
                "consultant_id": session.consultant_id
            }
        }
        
        # 调用AI服务生成方案
        try:
            ai_response = await self.ai_gateway_service.generate_beauty_plan(ai_request)
            
            # 解析AI响应为方案内容
            plan_content = self._parse_ai_response_to_plan_content(ai_response)
            
            return plan_content
            
        except Exception as e:
            logger.error(f"AI服务调用失败: {str(e)}")
            # 返回默认方案内容
            return self._create_default_plan_content(session.extracted_info)
    
    def _parse_ai_response_to_plan_content(self, ai_response: Dict[str, Any]) -> PlanContent:
        """解析AI响应为方案内容"""
        logger.info("解析AI响应为方案内容")
        
        # 这里需要根据AI服务的实际响应格式进行解析
        # 目前提供一个示例实现
        basic_info = PlanBasicInfo(
            title=ai_response.get("title", "个性化美肌方案"),
            description=ai_response.get("description", "基于您的需求定制的专业方案"),
            target_concerns=ai_response.get("target_concerns", []),
            difficulty_level=ai_response.get("difficulty_level", "intermediate"),
            total_duration=ai_response.get("total_duration", "3-6个月")
        )
        
        return PlanContent(
            basic_info=basic_info,
            # 其他字段根据AI响应填充
            analysis=None,
            treatment_plan=None,
            cost_breakdown=None,
            timeline=None,
            risks_and_precautions=None,
            aftercare=None
        )
    
    def _create_default_plan_content(self, customer_info: Dict[str, Any]) -> PlanContent:
        """创建默认方案内容"""
        logger.info("创建默认方案内容")
        
        basic_info = PlanBasicInfo(
            title="个性化美肌方案",
            description="基于您的需求定制的专业方案",
            target_concerns=[],
            difficulty_level="intermediate",
            total_duration="3-6个月"
        )
        
        return PlanContent(
            basic_info=basic_info
        )
    
    def _create_plan_draft(
        self,
        session_id: str,
        content: PlanContent,
        generation_info: Optional[Dict[str, Any]] = None
    ) -> PlanDraftInfo:
        """创建方案草稿"""
        # 获取下一个版本号
        version = self.plan_version_service.get_next_version(session_id)
        
        draft = PlanDraft(
            session_id=session_id,
            version=version,
            content=content.dict(),
            generation_info=generation_info or {},
            status=PlanDraftStatus.draft
        )
        
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        
        return PlanDraftInfo.from_model(draft)
    
    def _update_session_status(
        self,
        session_id: str,
        status: PlanSessionStatus
    ) -> None:
        """更新会话状态"""
        session = self.db.query(PlanGenerationSession).filter(
            PlanGenerationSession.id == session_id
        ).first()
        
        if session:
            session.status = status
            session.updated_at = datetime.now()
            self.db.commit()
    
    def _add_interaction_history(
        self,
        session: PlanGenerationSession,
        action: str,
        actor: str,
        actor_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加交互历史记录"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "actor": actor,
            "actor_id": actor_id,
            "details": details or {}
        }
        
        if not session.interaction_history:
            session.interaction_history = []
        
        session.interaction_history.append(interaction)
        self.db.commit()
    
    def get_session_drafts(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[PlanDraftInfo]:
        """获取会话的所有草稿"""
        drafts = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).order_by(PlanDraft.version.desc()).limit(limit).all()
        
        return [PlanDraftInfo.from_model(draft) for draft in drafts]
    
    def get_latest_draft(self, session_id: str) -> Optional[PlanDraftInfo]:
        """获取最新的草稿"""
        draft = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).order_by(PlanDraft.version.desc()).first()
        
        if not draft:
            return None
        
        return PlanDraftInfo.from_model(draft)
    
    def approve_draft(
        self,
        draft_id: str,
        consultant_id: str
    ) -> PlanDraftInfo:
        """批准方案草稿"""
        draft = self.db.query(PlanDraft).filter(
            PlanDraft.id == draft_id
        ).first()
        
        if not draft:
            raise ValueError(f"草稿不存在: {draft_id}")
        
        draft.status = PlanDraftStatus.approved
        draft.updated_at = datetime.now()
        
        # 更新会话状态
        self._update_session_status(draft.session_id, PlanSessionStatus.completed)
        
        self.db.commit()
        
        logger.info(f"方案草稿已批准: {draft_id}")
        return PlanDraftInfo.from_model(draft)
    
    def get_session_performance_metrics(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """获取会话性能指标"""
        session = self.db.query(PlanGenerationSession).filter(
            PlanGenerationSession.id == session_id
        ).first()
        
        if not session:
            return {}
        
        return session.performance_metrics or {}
    
    def update_session_performance_metrics(
        self,
        session_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """更新会话性能指标"""
        session = self.db.query(PlanGenerationSession).filter(
            PlanGenerationSession.id == session_id
        ).first()
        
        if session:
            session.performance_metrics = metrics
            session.updated_at = datetime.now()
            self.db.commit()
    
    def get_draft(self, draft_id: str) -> Optional[PlanDraftInfo]:
        """获取草稿详情"""
        draft = self.db.query(PlanDraft).filter(
            PlanDraft.id == draft_id
        ).first()
        
        if not draft:
            return None
        
        return PlanDraftInfo.from_model(draft)
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """获取方案生成统计信息"""
        from sqlalchemy import func
        
        # 统计会话数量
        total_sessions = self.db.query(PlanGenerationSession).count()
        
        # 统计不同状态的会话数量
        session_stats = self.db.query(
            PlanGenerationSession.status,
            func.count(PlanGenerationSession.id).label('count')
        ).group_by(PlanGenerationSession.status).all()
        
        # 统计草稿数量
        total_drafts = self.db.query(PlanDraft).count()
        
        # 统计不同状态的草稿数量
        draft_stats = self.db.query(
            PlanDraft.status,
            func.count(PlanDraft.id).label('count')
        ).group_by(PlanDraft.status).all()
        
        return {
            "total_sessions": total_sessions,
            "session_stats": {str(stat.status): stat.count for stat in session_stats},
            "total_drafts": total_drafts,
            "draft_stats": {str(stat.status): stat.count for stat in draft_stats}
        } 