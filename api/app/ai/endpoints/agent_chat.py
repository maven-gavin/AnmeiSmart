"""
Agent 对话 API 端点
提供 Agent 对话功能的 HTTP 接口
"""

import logging
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.deps import get_current_user
from app.identity_access.models.user import User
from app.ai.schemas.agent_chat import (
    AgentChatRequest,
    AgentConversationCreate,
    AgentConversationUpdate,
    AgentMessageResponse,
    AgentConversationResponse,
    MessageFeedbackRequest,
    MessageFeedbackResponse,
    SuggestedQuestionsResponse,
    StopMessageRequest,
    StopMessageResponse,
    AudioToTextResponse,
    TextToAudioRequest,
    FileUploadResponse,
    ApplicationParametersResponse,
    ApplicationMetaResponse
)
from app.ai.application.agent_chat_service import AgentChatApplicationService
from app.ai.deps import get_agent_chat_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{agent_config_id}/chat")
async def agent_chat(
    agent_config_id: str,
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service),
    db: Session = Depends(get_db)
):
    """
    Agent 流式对话
    
    支持流式响应，返回 SSE 格式数据
    """
    try:
        return StreamingResponse(
            service.stream_chat(
                agent_config_id=agent_config_id,
                user_id=str(current_user.id),
                message=request.message,
                conversation_id=request.conversation_id,
                inputs=request.inputs
            ),
            media_type="text/event-stream"
        )
    except ValueError as e:
        logger.error(f"Agent 对话参数错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Agent 对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="对话处理失败")


@router.get("/{agent_config_id}/conversations", response_model=List[AgentConversationResponse])
async def get_agent_conversations(
    agent_config_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """获取 Agent 会话列表"""
    try:
        return await service.get_conversations(
            agent_config_id=agent_config_id,
            user_id=str(current_user.id)
        )
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取会话列表失败")


@router.post("/{agent_config_id}/conversations", response_model=AgentConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_conversation(
    agent_config_id: str,
    request: AgentConversationCreate,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """创建新会话"""
    try:
        return await service.create_conversation(
            agent_config_id=agent_config_id,
            user_id=str(current_user.id),
            title=request.title
        )
    except Exception as e:
        logger.error(f"创建会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建会话失败")


@router.get("/conversations/{conversation_id}/messages", response_model=List[AgentMessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """获取会话消息历史"""
    try:
        return await service.get_messages(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            limit=limit
        )
    except ValueError as e:
        logger.error(f"会话不存在或无权访问: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取消息历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取消息历史失败")


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """删除会话"""
    try:
        await service.delete_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )
    except ValueError as e:
        logger.error(f"会话不存在或无权访问: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除会话失败")


@router.put("/conversations/{conversation_id}", response_model=AgentConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: AgentConversationUpdate,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """更新会话"""
    try:
        return await service.update_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            title=request.title
        )
    except ValueError as e:
        logger.error(f"会话不存在或无权访问: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"更新会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新会话失败")


# ========== 消息反馈相关端点 ==========

@router.post("/{agent_config_id}/feedback", response_model=MessageFeedbackResponse)
async def submit_message_feedback(
    agent_config_id: str,
    request: MessageFeedbackRequest,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """
    提交消息反馈
    
    支持对 AI 回复进行点赞或点踩
    """
    try:
        await service.message_feedback(
            agent_config_id=agent_config_id,
            message_id=request.message_id,
            rating=request.rating,
            user_id=str(current_user.id)
        )
        return MessageFeedbackResponse(success=True, message="反馈提交成功")
    except ValueError as e:
        logger.error(f"反馈参数错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"提交反馈失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交反馈失败")


# ========== 建议问题相关端点 ==========

@router.get("/{agent_config_id}/messages/{message_id}/suggested", response_model=SuggestedQuestionsResponse)
async def get_suggested_questions(
    agent_config_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """
    获取建议问题
    
    基于当前对话上下文，AI 建议的后续问题
    """
    try:
        questions = await service.get_suggested_questions(
            agent_config_id=agent_config_id,
            message_id=message_id,
            user_id=str(current_user.id)
        )
        return SuggestedQuestionsResponse(questions=questions)
    except ValueError as e:
        logger.error(f"获取建议问题参数错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"获取建议问题失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取建议问题失败")


# ========== 停止生成相关端点 ==========

@router.post("/{agent_config_id}/stop", response_model=StopMessageResponse)
async def stop_message_generation(
    agent_config_id: str,
    request: StopMessageRequest,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """
    停止消息生成
    
    中断正在进行的 AI 回复生成
    """
    try:
        await service.stop_message_generation(
            agent_config_id=agent_config_id,
            task_id=request.task_id,
            user_id=str(current_user.id)
        )
        return StopMessageResponse(success=True, message="已停止消息生成")
    except ValueError as e:
        logger.error(f"停止生成参数错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"停止生成失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="停止生成失败")


# ========== 语音处理相关端点 ==========

@router.post("/{agent_config_id}/audio-to-text", response_model=AudioToTextResponse)
async def audio_to_text(
    agent_config_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """
    语音转文字
    
    上传音频文件，转换为文本
    """
    try:
        # 读取音频文件
        audio_content = await file.read()
        audio_file = (file.filename, audio_content, file.content_type)
        
        # 调用服务
        text = await service.audio_to_text(
            agent_config_id=agent_config_id,
            audio_file=audio_file,
            user_id=str(current_user.id)
        )
        
        return AudioToTextResponse(text=text)
    except ValueError as e:
        logger.error(f"语音转文字参数错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"语音转文字失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="语音转文字失败")


@router.post("/{agent_config_id}/text-to-audio")
async def text_to_audio(
    agent_config_id: str,
    request: TextToAudioRequest,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """
    文字转语音
    
    将文本转换为语音
    """
    try:
        result = await service.text_to_audio(
            agent_config_id=agent_config_id,
            text=request.text,
            user_id=str(current_user.id),
            streaming=request.streaming
        )
        
        # 返回音频数据
        return JSONResponse(content=result)
    except ValueError as e:
        logger.error(f"文字转语音参数错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"文字转语音失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="文字转语音失败")


# ========== 文件上传相关端点 ==========

@router.post("/{agent_config_id}/upload", response_model=FileUploadResponse)
async def upload_file(
    agent_config_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """
    上传文件到 Dify
    
    上传文件用于后续对话中引用
    """
    try:
        # 读取文件
        file_content = await file.read()
        files_dict = {'file': (file.filename, file_content, file.content_type)}
        
        # 调用服务
        result = await service.upload_file(
            agent_config_id=agent_config_id,
            file=files_dict,
            user_id=str(current_user.id)
        )
        
        # 转换响应格式
        # Dify返回的created_at是Unix时间戳（整数），需要转换为ISO格式字符串
        created_at_value = result.get('created_at')
        if isinstance(created_at_value, int):
            # 将Unix时间戳转换为ISO格式字符串
            created_at_str = datetime.fromtimestamp(created_at_value).isoformat()
        else:
            # 如果已经是字符串或其他类型，保持原样
            created_at_str = str(created_at_value) if created_at_value else ''
        
        return FileUploadResponse(
            id=result.get('id', ''),
            name=result.get('name', file.filename),
            size=result.get('size', len(file_content)),
            mime_type=result.get('mime_type', file.content_type or ''),
            created_at=created_at_str
        )
    except ValueError as e:
        logger.error(f"文件上传参数错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="文件上传失败")


# ========== 应用配置相关端点 ==========

@router.get("/{agent_config_id}/parameters", response_model=ApplicationParametersResponse)
async def get_application_parameters(
    agent_config_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """
    获取应用参数配置
    
    返回应用的各项配置参数，包括：
    - 用户输入表单配置
    - 文件上传配置
    - 系统参数
    - 开场白
    - 建议问题
    - 语音配置等
    """
    try:
        result = await service.get_application_parameters(
            agent_config_id=agent_config_id,
            user_id=str(current_user.id)
        )
        
        # 转换为响应模型
        return ApplicationParametersResponse(**result)
    except ValueError as e:
        logger.error(f"获取应用参数错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"获取应用参数失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取应用参数失败")


@router.get("/{agent_config_id}/meta", response_model=ApplicationMetaResponse)
async def get_application_meta(
    agent_config_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """
    获取应用元数据
    
    返回应用的元数据信息，如工具图标等
    """
    try:
        result = await service.get_application_meta(
            agent_config_id=agent_config_id,
            user_id=str(current_user.id)
        )
        
        # 转换为响应模型
        return ApplicationMetaResponse(**result)
    except ValueError as e:
        logger.error(f"获取应用元数据错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"获取应用元数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取应用元数据失败")

