"""
咨询业务API端点
整合咨询会话、总结、方案管理、方案生成等所有咨询相关功能
使用清晰的业务术语和路由结构，避免consultant和consultation的混淆
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.common.infrastructure.db.base import get_current_user
from app.consultation.deps.consultation_business import (
    get_consultation_session_app_service,
    get_consultation_summary_app_service,
    get_plan_management_app_service,
    get_plan_generation_app_service
)
from app.consultation.application import (
    ConsultationSessionApplicationService,
    ConsultationSummaryApplicationService,
    PlanManagementApplicationService,
    PlanGenerationApplicationService
)
from app.identity_access.infrastructure.db.user import User
from app.identity_access.schemas.user import UserResponse
from app.chat.schemas.chat import (
    ConversationInfo,
    ConsultationSummaryResponse,
    ConsultationSummaryInfo,
    CreateConsultationSummaryRequest,
    UpdateConsultationSummaryRequest,
    AIGenerateSummaryRequest
)
from app.consultation.schemas.consultation import (
    PersonalizedPlanResponse, PersonalizedPlanCreate, PersonalizedPlanUpdate,
    ProjectTypeResponse, ProjectTemplateResponse,
    RecommendationRequest, RecommendationResponse,
    PlanGenerationSessionCreate,
    PlanGenerationSessionInfo,
    PlanDraftInfo,
    GeneratePlanRequest,
    OptimizePlanRequest,
    AnalyzeInfoRequest,
    GenerateGuidanceRequest,
    PlanGenerationResponse,
    InfoAnalysisResponse,
    PlanVersionCompareResponse
)

router = APIRouter()


def get_user_role(user: User) -> str:
    """获取用户角色"""
    if hasattr(user, '_active_role') and user._active_role:
        return user._active_role
    elif user.roles:
        return user.roles[0].name
    return 'consultant'


# ==================== 咨询会话管理API ====================

@router.post("/sessions", response_model=ConversationInfo)
async def create_consultation_session(
    current_user: User = Depends(get_current_user),
    session_app_service: ConsultationSessionApplicationService = Depends(get_consultation_session_app_service)
):
    """客户发起新的咨询会话"""
    try:
        result = await session_app_service.create_consultation_session_use_case(str(current_user.id))
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建咨询会话失败")


@router.post("/sessions/{conversation_id}/first-message-task")
async def create_first_message_task(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session_app_service: ConsultationSessionApplicationService = Depends(get_consultation_session_app_service)
):
    """客户发送第一条消息后创建咨询待办任务"""
    try:
        task_id = await session_app_service.create_first_message_task_use_case(
            conversation_id, str(current_user.id)
        )
        return {"task_id": task_id, "message": "咨询任务创建成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建咨询任务失败")


@router.post("/sessions/{conversation_id}/assign")
async def assign_consultant_to_consultation(
    conversation_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    session_app_service: ConsultationSessionApplicationService = Depends(get_consultation_session_app_service)
):
    """顾问接待咨询会话"""
    try:
        success = await session_app_service.assign_consultant_use_case(
            conversation_id, str(current_user.id), task_id
        )
        
        if success:
            return {"message": "咨询接待成功"}
        else:
            raise HTTPException(status_code=400, detail="接待失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="接待咨询失败")


@router.put("/sessions/{conversation_id}/pin")
async def pin_conversation(
    conversation_id: str,
    pin: bool = True,
    current_user: User = Depends(get_current_user),
    session_app_service: ConsultationSessionApplicationService = Depends(get_consultation_session_app_service)
):
    """置顶/取消置顶会话"""
    try:
        success = await session_app_service.pin_conversation_use_case(
            conversation_id, str(current_user.id), pin
        )
        
        if success:
            action = "置顶" if pin else "取消置顶"
            return {"message": f"会话{action}成功"}
        else:
            raise HTTPException(status_code=400, detail="操作失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="会话置顶操作失败")


@router.get("/sessions", response_model=List[ConversationInfo])
async def get_conversations_with_priority(
    include_consultation: bool = True,
    include_friend_chat: bool = True,
    current_user: User = Depends(get_current_user),
    session_app_service: ConsultationSessionApplicationService = Depends(get_consultation_session_app_service)
):
    """获取用户的会话列表（支持置顶排序）"""
    try:
        result = await session_app_service.get_conversations_use_case(
            user_id=str(current_user.id),
            include_consultation=include_consultation,
            include_friend_chat=include_friend_chat
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取会话列表失败")


# ==================== 咨询总结管理API ====================

@router.get("/summaries/{conversation_id}", response_model=ConsultationSummaryResponse)
def get_consultation_summary(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    summary_app_service: ConsultationSummaryApplicationService = Depends(get_consultation_summary_app_service)
):
    """获取会话的咨询总结"""
    try:
        result = summary_app_service.get_consultation_summary_use_case(conversation_id, str(current_user.id))
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取咨询总结失败")


@router.post("/summaries/{conversation_id}", response_model=ConsultationSummaryResponse)
def create_consultation_summary(
    conversation_id: str,
    request: CreateConsultationSummaryRequest,
    current_user: User = Depends(get_current_user),
    summary_app_service: ConsultationSummaryApplicationService = Depends(get_consultation_summary_app_service)
):
    """创建咨询总结"""
    # 验证请求中的conversation_id与URL中的一致
    if request.conversation_id != conversation_id:
        raise HTTPException(status_code=400, detail="请求中的会话ID与URL不匹配")
    
    try:
        result = summary_app_service.create_consultation_summary_use_case(request, str(current_user.id))
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建咨询总结失败")


@router.put("/summaries/{conversation_id}", response_model=ConsultationSummaryResponse)
def update_consultation_summary(
    conversation_id: str,
    request: UpdateConsultationSummaryRequest,
    current_user: User = Depends(get_current_user),
    summary_app_service: ConsultationSummaryApplicationService = Depends(get_consultation_summary_app_service)
):
    """更新咨询总结"""
    try:
        result = summary_app_service.update_consultation_summary_use_case(
            conversation_id, request, str(current_user.id)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新咨询总结失败")


@router.delete("/summaries/{conversation_id}")
def delete_consultation_summary(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    summary_app_service: ConsultationSummaryApplicationService = Depends(get_consultation_summary_app_service)
):
    """删除咨询总结"""
    try:
        summary_app_service.delete_consultation_summary_use_case(conversation_id, str(current_user.id))
        return {"message": "咨询总结已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除咨询总结失败")


@router.post("/summaries/{conversation_id}/ai-generate")
async def ai_generate_summary(
    conversation_id: str,
    request: AIGenerateSummaryRequest,
    current_user: User = Depends(get_current_user),
    summary_app_service: ConsultationSummaryApplicationService = Depends(get_consultation_summary_app_service)
):
    """AI生成咨询总结"""
    # 验证请求中的conversation_id与URL中的一致
    if request.conversation_id != conversation_id:
        raise HTTPException(status_code=400, detail="请求中的会话ID与URL不匹配")
    
    try:
        result = await summary_app_service.ai_generate_summary_use_case(request, str(current_user.id))
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI生成咨询总结失败")


@router.post("/summaries/{conversation_id}/ai-save", response_model=ConsultationSummaryResponse)
def save_ai_generated_summary(
    conversation_id: str,
    ai_summary: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    summary_app_service: ConsultationSummaryApplicationService = Depends(get_consultation_summary_app_service)
):
    """保存AI生成的咨询总结"""
    try:
        result = summary_app_service.save_ai_generated_summary_use_case(
            conversation_id, ai_summary, str(current_user.id)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="保存AI生成的咨询总结失败")


@router.get("/customers/{customer_id}/history", response_model=List[ConsultationSummaryInfo])
def get_customer_consultation_history(
    customer_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    summary_app_service: ConsultationSummaryApplicationService = Depends(get_consultation_summary_app_service)
):
    """获取客户的咨询历史总结"""
    try:
        result = summary_app_service.get_customer_consultation_history_use_case(
            customer_id, str(current_user.id), limit
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取客户咨询历史失败")


# ==================== 方案管理API ====================

@router.get("/plans", response_model=List[PersonalizedPlanResponse])
async def get_all_plans(
    consultant_id: Optional[str] = Query(None, description="筛选特定顾问的方案"),
    plan_app_service: PlanManagementApplicationService = Depends(get_plan_management_app_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取所有个性化方案"""
    try:
        return plan_app_service.get_all_plans_use_case(consultant_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取方案列表失败: {str(e)}"
        )


@router.get("/plans/{plan_id}", response_model=PersonalizedPlanResponse)
async def get_plan(
    plan_id: str,
    plan_app_service: PlanManagementApplicationService = Depends(get_plan_management_app_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """根据ID获取个性化方案详情"""
    try:
        return plan_app_service.get_plan_by_id_use_case(plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取方案详情失败: {str(e)}"
        )


@router.get("/customers/{customer_id}/plans", response_model=List[PersonalizedPlanResponse])
async def get_customer_plans(
    customer_id: str,
    plan_app_service: PlanManagementApplicationService = Depends(get_plan_management_app_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取客户的所有方案"""
    try:
        return plan_app_service.get_customer_plans_use_case(customer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取客户方案失败: {str(e)}"
        )


@router.post("/plans", response_model=PersonalizedPlanResponse)
async def create_plan(
    plan_data: PersonalizedPlanCreate,
    plan_app_service: PlanManagementApplicationService = Depends(get_plan_management_app_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """创建个性化方案"""
    try:
        # 从当前用户信息获取顾问ID和姓名
        consultant_id = current_user.id
        consultant_name = current_user.username  # 或者从顾问扩展信息获取
        
        return plan_app_service.create_plan_use_case(plan_data, consultant_id, consultant_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建方案失败: {str(e)}"
        )


@router.put("/plans/{plan_id}", response_model=PersonalizedPlanResponse)
async def update_plan(
    plan_id: str,
    plan_data: PersonalizedPlanUpdate,
    plan_app_service: PlanManagementApplicationService = Depends(get_plan_management_app_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """更新个性化方案"""
    try:
        return plan_app_service.update_plan_use_case(plan_id, plan_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新方案失败: {str(e)}"
        )


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    plan_app_service: PlanManagementApplicationService = Depends(get_plan_management_app_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """删除个性化方案"""
    try:
        success = plan_app_service.delete_plan_use_case(plan_id)
        if success:
            return {"message": "方案删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除方案失败"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除方案失败: {str(e)}"
        )


# ==================== 项目类型和模板管理API ====================

@router.get("/project-types", response_model=List[ProjectTypeResponse])
async def get_project_types(
    active_only: bool = Query(True, description="是否只返回激活的项目类型"),
    plan_app_service: PlanManagementApplicationService = Depends(get_plan_management_app_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取所有项目类型"""
    try:
        return plan_app_service.get_all_project_types_use_case(active_only)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目类型失败: {str(e)}"
        )


@router.get("/project-templates", response_model=List[ProjectTemplateResponse])
async def get_project_templates(
    category: Optional[str] = Query(None, description="项目分类筛选"),
    active_only: bool = Query(True, description="是否只返回激活的模板"),
    plan_app_service: PlanManagementApplicationService = Depends(get_plan_management_app_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取所有项目模板"""
    try:
        return plan_app_service.get_all_project_templates_use_case(category, active_only)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目模板失败: {str(e)}"
        )


# ==================== 推荐生成API ====================

@router.post("/recommendations", response_model=RecommendationResponse)
async def generate_recommendations(
    request: RecommendationRequest,
    plan_app_service: PlanManagementApplicationService = Depends(get_plan_management_app_service),
    current_user: UserResponse = Depends(get_current_user)
):
    """生成个性化方案推荐"""
    try:
        return plan_app_service.generate_recommendations_use_case(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成推荐失败: {str(e)}"
        )


# ==================== 方案生成API ====================

@router.post("/plan-generation/sessions", response_model=PlanGenerationSessionInfo, status_code=status.HTTP_201_CREATED)
async def create_plan_generation_session(
    session_data: PlanGenerationSessionCreate,
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """创建方案生成会话"""
    try:
        # 验证用户权限（只有顾问可以创建会话）
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有顾问和管理员可以创建方案生成会话"
            )
        
        session = generation_app_service.create_plan_generation_session_use_case(
            session_data, str(current_user.id)
        )
        return session
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建方案生成会话失败")


@router.get("/plan-generation/sessions/{session_id}", response_model=PlanGenerationSessionInfo)
async def get_plan_generation_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """获取方案生成会话详情"""
    try:
        session = generation_app_service.get_plan_generation_session_use_case(session_id)
        
        # 权限检查：只有相关的顾问或客户可以查看
        user_role = get_user_role(current_user)
        if user_role not in ['admin'] and current_user.id not in [session.consultant_id, session.customer_id]:
            raise HTTPException(status_code=403, detail="无权限访问该会话")
        
        return session
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取方案生成会话失败")


@router.get("/plan-generation/sessions/conversation/{conversation_id}", response_model=Optional[PlanGenerationSessionInfo])
async def get_plan_generation_session_by_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """根据对话ID获取方案生成会话"""
    try:
        session = generation_app_service.get_plan_generation_session_by_conversation_use_case(conversation_id)
        
        if not session:
            return None
        
        # 权限检查
        user_role = get_user_role(current_user)
        if user_role not in ['admin'] and current_user.id not in [session.consultant_id, session.customer_id]:
            raise HTTPException(status_code=403, detail="无权限访问该会话")
        
        return session
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="根据对话ID获取会话失败")


@router.post("/plan-generation/analyze-info", response_model=InfoAnalysisResponse)
async def analyze_conversation_info(
    request: AnalyzeInfoRequest,
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """分析对话信息完整性"""
    try:
        analysis = await generation_app_service.analyze_conversation_info_use_case(
            request.conversation_id,
            force_analysis=request.force_analysis
        )
        return analysis
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="分析信息失败")


@router.post("/plan-generation/generate-guidance")
async def generate_guidance_questions(
    request: GenerateGuidanceRequest,
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """生成引导问题"""
    try:
        guidance = await generation_app_service.generate_guidance_questions_use_case(
            request.conversation_id or "",
            request.missing_categories if request.missing_categories is not None else [],
            request.context if request.context is not None else {}
        )
        return {"guidance_questions": guidance}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="生成引导问题失败")


@router.post("/plan-generation/generate", response_model=PlanGenerationResponse)
async def generate_plan(
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """生成方案"""
    try:
        # 验证用户权限（只有顾问可以生成方案）
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'admin']:
            raise HTTPException(status_code=403, detail="只有顾问和管理员可以生成方案")
        
        response = await generation_app_service.generate_plan_use_case(request, str(current_user.id))
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="生成方案失败")


@router.post("/plan-generation/optimize", response_model=PlanDraftInfo)
async def optimize_plan(
    request: OptimizePlanRequest,
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """优化方案"""
    try:
        # 验证用户权限
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'admin']:
            raise HTTPException(status_code=403, detail="只有顾问和管理员可以优化方案")
        
        optimized_draft = await generation_app_service.optimize_plan_use_case(request, str(current_user.id))
        return optimized_draft
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="优化方案失败")


@router.get("/plan-generation/sessions/{session_id}/drafts", response_model=List[PlanDraftInfo])
async def get_session_drafts(
    session_id: str,
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """获取会话的所有草稿"""
    try:
        drafts = generation_app_service.get_session_drafts_use_case(session_id)
        return drafts
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取草稿失败")


@router.get("/plan-generation/drafts/{draft_id}", response_model=PlanDraftInfo)
async def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """获取草稿详情"""
    try:
        draft = generation_app_service.get_draft_use_case(draft_id)
        return draft
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取草稿失败")


@router.get("/plan-generation/sessions/{session_id}/versions", response_model=List[PlanDraftInfo])
async def get_session_versions(
    session_id: str,
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """获取会话的所有版本"""
    try:
        versions = generation_app_service.get_session_versions_use_case(session_id)
        return versions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取版本失败")


@router.post("/plan-generation/sessions/{session_id}/compare", response_model=PlanVersionCompareResponse)
async def compare_session_versions(
    session_id: str,
    version_numbers: List[int],
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """比较会话版本"""
    try:
        if len(version_numbers) != 2:
            raise HTTPException(status_code=400, detail="版本比较需要提供两个版本号")
        
        comparison = generation_app_service.compare_session_versions_use_case(
            session_id, version_numbers[0], version_numbers[1]
        )
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="版本比较失败")


@router.get("/plan-generation/stats")
async def get_generation_stats(
    current_user: User = Depends(get_current_user),
    generation_app_service: PlanGenerationApplicationService = Depends(get_plan_generation_app_service)
):
    """获取方案生成统计信息"""
    try:
        # 只有管理员可以查看统计信息
        user_role = get_user_role(current_user)
        if user_role != 'admin':
            raise HTTPException(status_code=403, detail="只有管理员可以查看统计信息")
        
        stats = generation_app_service.get_generation_stats_use_case()
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取统计信息失败")
