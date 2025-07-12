"""
信息分析服务 - 负责从对话中提取和分析客户信息
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.models.plan_generation import PlanGenerationSession, InfoCompleteness
from app.db.models.chat import Message
from app.schemas.plan_generation import (
    InfoAnalysisResponse,
    InfoCompletenessInfo,
    GuidanceQuestions,
    GuidanceQuestion,
    InfoStatus,
    ExtractedInfo,
    BasicInfo,
    ConcernsInfo,
    BudgetInfo,
    TimelineInfo,
    ExpectationsInfo
)
from app.services.ai.ai_service import AIService

logger = logging.getLogger(__name__)


class InfoAnalysisService:
    """信息分析服务类 - 从对话中提取和分析客户信息"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    def create_completeness_record(self, session_id: str) -> InfoCompletenessInfo:
        """创建信息完整性记录"""
        logger.info(f"创建信息完整性记录: session_id={session_id}")
        
        # 检查是否已存在记录
        existing_record = self.db.query(InfoCompleteness).filter(
            InfoCompleteness.session_id == session_id
        ).first()
        
        if existing_record:
            logger.warning(f"信息完整性记录已存在: {existing_record.id}")
            return InfoCompletenessInfo.from_model(existing_record)
        
        # 创建新记录
        record = InfoCompleteness(
            session_id=session_id,
            basic_info_status=InfoStatus.missing,
            concerns_status=InfoStatus.missing,
            budget_status=InfoStatus.missing,
            timeline_status=InfoStatus.missing,
            medical_history_status=InfoStatus.missing,
            expectations_status=InfoStatus.missing,
            completeness_score=0.0,
            analysis_version=1
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(f"信息完整性记录创建成功: {record.id}")
        return InfoCompletenessInfo.from_model(record)
    
    async def analyze_conversation_info(
        self,
        session_id: str,
        force_analysis: bool = False
    ) -> InfoAnalysisResponse:
        """分析对话信息"""
        logger.info(f"分析对话信息: session_id={session_id}")
        
        # 获取会话信息
        session = self.db.query(PlanGenerationSession).filter(
            PlanGenerationSession.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"方案生成会话不存在: {session_id}")
        
        # 获取对话消息
        messages = self._get_conversation_messages(session.conversation_id)
        
        # 检查是否需要重新分析
        if not force_analysis and session.extracted_info:
            logger.info("使用缓存的分析结果")
            return await self._create_analysis_response(session_id, session.extracted_info)
        
        # 执行AI信息提取
        extracted_info = await self._extract_info_from_messages(messages)
        
        # 更新会话的提取信息
        session.extracted_info = extracted_info.dict() if extracted_info else {}
        session.updated_at = datetime.now()
        self.db.commit()
        
        # 分析信息完整性
        completeness_info = await self._analyze_info_completeness(session_id, extracted_info)
        
        # 生成引导问题
        guidance_questions = await self._generate_guidance_questions(
            session_id, 
            extracted_info,
            completeness_info
        )
        
        # 创建分析响应
        return InfoAnalysisResponse(
            session_id=session_id,
            completeness_score=completeness_info.completeness_score,
            missing_categories=self._get_missing_categories(completeness_info),
            suggestions=self._generate_suggestions(completeness_info),
            can_generate_plan=completeness_info.completeness_score >= 0.7,
            guidance_questions=guidance_questions
        )
    
    def _get_conversation_messages(self, conversation_id: str) -> List[Message]:
        """获取对话消息"""
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender_type.in_(["customer", "consultant"])
        ).order_by(Message.timestamp.asc()).all()
        
        logger.info(f"获取到 {len(messages)} 条对话消息")
        return messages
    
    async def _extract_info_from_messages(self, messages: List[Message]) -> Optional[ExtractedInfo]:
        """从消息中提取信息"""
        logger.info("开始AI信息提取")
        
        if not messages:
            logger.warning("没有可分析的消息")
            return None
        
        # 构建消息文本
        message_texts = []
        for message in messages:
            content = message.content
            if isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = str(content)
            
            if text:
                message_texts.append(f"{message.sender_type}: {text}")
        
        conversation_text = "\n".join(message_texts)
        
        try:
            # 调用AI服务提取信息
            ai_response = await self.ai_service.extract_customer_info(conversation_text)
            
            # 解析AI响应
            extracted_info = self._parse_ai_extraction_response(ai_response)
            
            logger.info(f"AI信息提取完成: confidence={extracted_info.extraction_confidence}")
            return extracted_info
            
        except Exception as e:
            logger.error(f"AI信息提取失败: {str(e)}")
            # 返回基础的信息提取结果
            return self._create_basic_extracted_info(conversation_text)
    
    def _parse_ai_extraction_response(self, ai_response: Dict[str, Any]) -> ExtractedInfo:
        """解析AI提取响应"""
        logger.info("解析AI提取响应")
        
        # 解析基础信息
        basic_info = None
        if "basic_info" in ai_response:
            basic_info = BasicInfo(**ai_response["basic_info"])
        
        # 解析关注点信息
        concerns = None
        if "concerns" in ai_response:
            concerns = ConcernsInfo(**ai_response["concerns"])
        
        # 解析预算信息
        budget = None
        if "budget" in ai_response:
            budget = BudgetInfo(**ai_response["budget"])
        
        # 解析时间安排信息
        timeline = None
        if "timeline" in ai_response:
            timeline = TimelineInfo(**ai_response["timeline"])
        
        # 解析期望信息
        expectations = None
        if "expectations" in ai_response:
            expectations = ExpectationsInfo(**ai_response["expectations"])
        
        return ExtractedInfo(
            basic_info=basic_info,
            concerns=concerns,
            budget=budget,
            timeline=timeline,
            expectations=expectations,
            additional_notes=ai_response.get("additional_notes"),
            extraction_confidence=ai_response.get("extraction_confidence", 0.8),
            last_updated=datetime.now().isoformat()
        )
    
    def _create_basic_extracted_info(self, conversation_text: str) -> ExtractedInfo:
        """创建基础的信息提取结果"""
        logger.info("创建基础信息提取结果")
        
        # 简单的关键词匹配
        concerns_keywords = ["痘痘", "痤疮", "细纹", "色斑", "毛孔", "暗沉", "敏感"]
        found_concerns = []
        
        for keyword in concerns_keywords:
            if keyword in conversation_text:
                found_concerns.append(keyword)
        
        concerns = ConcernsInfo(
            primary_concern=found_concerns[0] if found_concerns else None,
            secondary_concerns=found_concerns[1:] if len(found_concerns) > 1 else []
        ) if found_concerns else None
        
        return ExtractedInfo(
            basic_info=None,
            concerns=concerns,
            budget=None,
            timeline=None,
            expectations=None,
            additional_notes="基于关键词匹配的基础信息提取",
            extraction_confidence=0.3,
            last_updated=datetime.now().isoformat()
        )
    
    async def _analyze_info_completeness(
        self,
        session_id: str,
        extracted_info: Optional[ExtractedInfo]
    ) -> InfoCompletenessInfo:
        """分析信息完整性"""
        logger.info(f"分析信息完整性: session_id={session_id}")
        
        # 获取完整性记录
        record = self.db.query(InfoCompleteness).filter(
            InfoCompleteness.session_id == session_id
        ).first()
        
        if not record:
            record = InfoCompleteness(
                session_id=session_id,
                analysis_version=1
            )
            self.db.add(record)
        
        # 分析各类信息的完整性
        if extracted_info:
            # 基础信息
            basic_info_score, basic_info_status = self._evaluate_basic_info(extracted_info.basic_info)
            record.basic_info_score = basic_info_score
            record.basic_info_status = basic_info_status
            
            # 关注点信息
            concerns_score, concerns_status = self._evaluate_concerns_info(extracted_info.concerns)
            record.concerns_score = concerns_score
            record.concerns_status = concerns_status
            
            # 预算信息
            budget_score, budget_status = self._evaluate_budget_info(extracted_info.budget)
            record.budget_score = budget_score
            record.budget_status = budget_status
            
            # 时间安排信息
            timeline_score, timeline_status = self._evaluate_timeline_info(extracted_info.timeline)
            record.timeline_score = timeline_score
            record.timeline_status = timeline_status
            
            # 期望信息
            expectations_score, expectations_status = self._evaluate_expectations_info(extracted_info.expectations)
            record.expectations_score = expectations_score
            record.expectations_status = expectations_status
            
            # 病史信息（从基础信息中提取）
            medical_history_score, medical_history_status = self._evaluate_medical_history(extracted_info.basic_info)
            record.medical_history_score = medical_history_score
            record.medical_history_status = medical_history_status
        else:
            # 没有提取到信息
            record.basic_info_score = 0.0
            record.basic_info_status = InfoStatus.missing
            record.concerns_score = 0.0
            record.concerns_status = InfoStatus.missing
            record.budget_score = 0.0
            record.budget_status = InfoStatus.missing
            record.timeline_score = 0.0
            record.timeline_status = InfoStatus.missing
            record.expectations_score = 0.0
            record.expectations_status = InfoStatus.missing
            record.medical_history_score = 0.0
            record.medical_history_status = InfoStatus.missing
        
        # 计算总体完整性评分
        total_score = (
            record.basic_info_score +
            record.concerns_score +
            record.budget_score +
            record.timeline_score +
            record.expectations_score +
            record.medical_history_score
        ) / 6
        
        record.completeness_score = total_score
        record.last_analysis_at = datetime.now()
        record.analysis_version += 1
        
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(f"信息完整性分析完成: score={total_score:.2f}")
        return InfoCompletenessInfo.from_model(record)
    
    def _evaluate_basic_info(self, basic_info: Optional[BasicInfo]) -> tuple[float, InfoStatus]:
        """评估基础信息完整性"""
        if not basic_info:
            return 0.0, InfoStatus.missing
        
        score = 0.0
        total_fields = 4
        
        if basic_info.age:
            score += 0.25
        if basic_info.gender:
            score += 0.25
        if basic_info.skin_type:
            score += 0.25
        if basic_info.medical_history:
            score += 0.25
        
        if score == 0:
            return 0.0, InfoStatus.missing
        elif score < 1.0:
            return score, InfoStatus.partial
        else:
            return score, InfoStatus.complete
    
    def _evaluate_concerns_info(self, concerns: Optional[ConcernsInfo]) -> tuple[float, InfoStatus]:
        """评估关注点信息完整性"""
        if not concerns:
            return 0.0, InfoStatus.missing
        
        score = 0.0
        
        if concerns.primary_concern:
            score += 0.5
        if concerns.secondary_concerns:
            score += 0.25
        if concerns.severity_level:
            score += 0.25
        
        if score == 0:
            return 0.0, InfoStatus.missing
        elif score < 1.0:
            return score, InfoStatus.partial
        else:
            return score, InfoStatus.complete
    
    def _evaluate_budget_info(self, budget: Optional[BudgetInfo]) -> tuple[float, InfoStatus]:
        """评估预算信息完整性"""
        if not budget:
            return 0.0, InfoStatus.missing
        
        score = 0.0
        
        if budget.budget_range:
            score += 0.6
        if budget.payment_preference:
            score += 0.4
        
        if score == 0:
            return 0.0, InfoStatus.missing
        elif score < 1.0:
            return score, InfoStatus.partial
        else:
            return score, InfoStatus.complete
    
    def _evaluate_timeline_info(self, timeline: Optional[TimelineInfo]) -> tuple[float, InfoStatus]:
        """评估时间安排信息完整性"""
        if not timeline:
            return 0.0, InfoStatus.missing
        
        score = 0.0
        
        if timeline.preferred_start_date:
            score += 0.4
        if timeline.availability:
            score += 0.4
        if timeline.urgency_level:
            score += 0.2
        
        if score == 0:
            return 0.0, InfoStatus.missing
        elif score < 1.0:
            return score, InfoStatus.partial
        else:
            return score, InfoStatus.complete
    
    def _evaluate_expectations_info(self, expectations: Optional[ExpectationsInfo]) -> tuple[float, InfoStatus]:
        """评估期望信息完整性"""
        if not expectations:
            return 0.0, InfoStatus.missing
        
        score = 0.0
        
        if expectations.desired_outcome:
            score += 0.4
        if expectations.previous_experience:
            score += 0.3
        if expectations.risk_tolerance:
            score += 0.3
        
        if score == 0:
            return 0.0, InfoStatus.missing
        elif score < 1.0:
            return score, InfoStatus.partial
        else:
            return score, InfoStatus.complete
    
    def _evaluate_medical_history(self, basic_info: Optional[BasicInfo]) -> tuple[float, InfoStatus]:
        """评估病史信息完整性"""
        if not basic_info or not basic_info.medical_history:
            return 0.0, InfoStatus.missing
        
        if basic_info.medical_history:
            return 1.0, InfoStatus.complete
        else:
            return 0.0, InfoStatus.missing
    
    async def _generate_guidance_questions(
        self,
        session_id: str,
        extracted_info: Optional[ExtractedInfo],
        completeness_info: InfoCompletenessInfo
    ) -> Optional[GuidanceQuestions]:
        """生成引导问题"""
        logger.info(f"生成引导问题: session_id={session_id}")
        
        questions = GuidanceQuestions(
            generated_at=datetime.now().isoformat(),
            total_questions=0
        )
        
        # 根据缺失信息生成问题
        if completeness_info.basic_info_status != InfoStatus.complete:
            basic_questions = self._generate_basic_info_questions(extracted_info)
            questions.basic_info.extend(basic_questions)
        
        if completeness_info.concerns_status != InfoStatus.complete:
            concern_questions = self._generate_concern_questions(extracted_info)
            questions.concerns.extend(concern_questions)
        
        if completeness_info.budget_status != InfoStatus.complete:
            budget_questions = self._generate_budget_questions(extracted_info)
            questions.budget.extend(budget_questions)
        
        if completeness_info.timeline_status != InfoStatus.complete:
            timeline_questions = self._generate_timeline_questions(extracted_info)
            questions.timeline.extend(timeline_questions)
        
        if completeness_info.expectations_status != InfoStatus.complete:
            expectation_questions = self._generate_expectation_questions(extracted_info)
            questions.expectations.extend(expectation_questions)
        
        # 更新总问题数
        questions.total_questions = (
            len(questions.basic_info) +
            len(questions.concerns) +
            len(questions.budget) +
            len(questions.timeline) +
            len(questions.expectations)
        )
        
        logger.info(f"生成了 {questions.total_questions} 个引导问题")
        return questions if questions.total_questions > 0 else None
    
    def _generate_basic_info_questions(self, extracted_info: Optional[ExtractedInfo]) -> List[GuidanceQuestion]:
        """生成基础信息问题"""
        questions = []
        
        if not extracted_info or not extracted_info.basic_info:
            questions.extend([
                GuidanceQuestion(
                    field="age",
                    question="请问您的年龄是多少？",
                    priority="high",
                    category="basic_info"
                ),
                GuidanceQuestion(
                    field="gender",
                    question="请问您的性别是？",
                    priority="high",
                    category="basic_info"
                ),
                GuidanceQuestion(
                    field="skin_type",
                    question="请问您的肌肤类型是？（干性/油性/混合性/敏感性）",
                    priority="medium",
                    category="basic_info"
                )
            ])
        else:
            basic_info = extracted_info.basic_info
            if not basic_info.age:
                questions.append(GuidanceQuestion(
                    field="age",
                    question="请问您的年龄是多少？",
                    priority="high",
                    category="basic_info"
                ))
            if not basic_info.skin_type:
                questions.append(GuidanceQuestion(
                    field="skin_type",
                    question="请问您的肌肤类型是？（干性/油性/混合性/敏感性）",
                    priority="medium",
                    category="basic_info"
                ))
        
        return questions
    
    def _generate_concern_questions(self, extracted_info: Optional[ExtractedInfo]) -> List[GuidanceQuestion]:
        """生成关注点问题"""
        questions = []
        
        if not extracted_info or not extracted_info.concerns:
            questions.append(GuidanceQuestion(
                field="primary_concern",
                question="请问您最主要的肌肤困扰是什么？",
                priority="high",
                category="concerns"
            ))
        else:
            concerns = extracted_info.concerns
            if not concerns.severity_level:
                questions.append(GuidanceQuestion(
                    field="severity_level",
                    question="您觉得这个问题的严重程度如何？（轻微/中等/严重）",
                    priority="medium",
                    category="concerns"
                ))
        
        return questions
    
    def _generate_budget_questions(self, extracted_info: Optional[ExtractedInfo]) -> List[GuidanceQuestion]:
        """生成预算问题"""
        questions = []
        
        if not extracted_info or not extracted_info.budget:
            questions.append(GuidanceQuestion(
                field="budget_range",
                question="请问您的预算范围大概是多少？",
                priority="medium",
                category="budget"
            ))
        
        return questions
    
    def _generate_timeline_questions(self, extracted_info: Optional[ExtractedInfo]) -> List[GuidanceQuestion]:
        """生成时间安排问题"""
        questions = []
        
        if not extracted_info or not extracted_info.timeline:
            questions.append(GuidanceQuestion(
                field="preferred_start_date",
                question="您希望什么时候开始治疗？",
                priority="medium",
                category="timeline"
            ))
        
        return questions
    
    def _generate_expectation_questions(self, extracted_info: Optional[ExtractedInfo]) -> List[GuidanceQuestion]:
        """生成期望问题"""
        questions = []
        
        if not extracted_info or not extracted_info.expectations:
            questions.append(GuidanceQuestion(
                field="desired_outcome",
                question="您希望达到什么样的效果？",
                priority="medium",
                category="expectations"
            ))
        
        return questions
    
    def _get_missing_categories(self, completeness_info: InfoCompletenessInfo) -> List[str]:
        """获取缺失的信息类别"""
        missing_categories = []
        
        if completeness_info.basic_info_status == InfoStatus.missing:
            missing_categories.append("基础信息")
        if completeness_info.concerns_status == InfoStatus.missing:
            missing_categories.append("关注点")
        if completeness_info.budget_status == InfoStatus.missing:
            missing_categories.append("预算")
        if completeness_info.timeline_status == InfoStatus.missing:
            missing_categories.append("时间安排")
        if completeness_info.expectations_status == InfoStatus.missing:
            missing_categories.append("期望")
        if completeness_info.medical_history_status == InfoStatus.missing:
            missing_categories.append("病史")
        
        return missing_categories
    
    def _generate_suggestions(self, completeness_info: InfoCompletenessInfo) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if completeness_info.completeness_score < 0.3:
            suggestions.append("建议与客户进行更详细的沟通，收集基本信息")
        elif completeness_info.completeness_score < 0.7:
            suggestions.append("信息基本完整，可以补充一些细节信息")
        else:
            suggestions.append("信息较为完整，可以开始生成方案")
        
        # 根据具体缺失类别提供建议
        if completeness_info.concerns_status == InfoStatus.missing:
            suggestions.append("重点了解客户的主要肌肤困扰")
        if completeness_info.budget_status == InfoStatus.missing:
            suggestions.append("了解客户的预算范围有助于制定合适的方案")
        
        return suggestions
    
    async def _create_analysis_response(
        self,
        session_id: str,
        extracted_info: Dict[str, Any]
    ) -> InfoAnalysisResponse:
        """基于缓存信息创建分析响应"""
        logger.info("基于缓存信息创建分析响应")
        
        # 获取完整性信息
        completeness_record = self.db.query(InfoCompleteness).filter(
            InfoCompleteness.session_id == session_id
        ).first()
        
        if not completeness_record:
            # 如果没有完整性记录，创建一个
            completeness_record = InfoCompleteness(
                session_id=session_id,
                completeness_score=0.5,  # 默认分数
                analysis_version=1
            )
            self.db.add(completeness_record)
            self.db.commit()
            self.db.refresh(completeness_record)
        
        completeness_info = InfoCompletenessInfo.from_model(completeness_record)
        
        return InfoAnalysisResponse(
            session_id=session_id,
            completeness_score=completeness_info.completeness_score,
            missing_categories=self._get_missing_categories(completeness_info),
            suggestions=self._generate_suggestions(completeness_info),
            can_generate_plan=completeness_info.completeness_score >= 0.7,
            guidance_questions=completeness_info.guidance_questions
        )
    
    async def generate_guidance_questions(
        self,
        session_id: str,
        missing_categories: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[GuidanceQuestions]:
        """生成引导问题"""
        logger.info(f"生成引导问题: session_id={session_id}")
        
        # 获取会话信息
        session = self.db.query(PlanGenerationSession).filter(
            PlanGenerationSession.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"方案生成会话不存在: {session_id}")
        
        # 获取已提取的信息
        extracted_info = None
        if session.extracted_info:
            try:
                extracted_info = ExtractedInfo(**session.extracted_info)
            except Exception as e:
                logger.warning(f"解析提取信息失败: {e}")
        
        # 获取完整性信息
        completeness_record = self.db.query(InfoCompleteness).filter(
            InfoCompleteness.session_id == session_id
        ).first()
        
        if not completeness_record:
            # 如果没有完整性记录，创建一个
            completeness_record = InfoCompleteness(
                session_id=session_id,
                completeness_score=0.5,  # 默认分数
                analysis_version=1
            )
            self.db.add(completeness_record)
            self.db.commit()
            self.db.refresh(completeness_record)
        
        completeness_info = InfoCompletenessInfo.from_model(completeness_record)
        
        # 生成引导问题
        guidance_questions = await self._generate_guidance_questions(
            session_id,
            extracted_info,
            completeness_info
        )
        
        return guidance_questions 