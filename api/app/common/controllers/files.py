"""
文件上传API端点
遵循扁平化架构：Controller层只做参数校验和调用Service层
"""
import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.identity_access.deps import get_current_user, get_user_primary_role
from app.common.deps import get_db
from app.identity_access.models.user import User
from app.common.services.file_service import FileService
from app.chat.services.chat_service import ChatService
from app.chat.deps.chat import get_chat_service
from app.common.schemas.file import (
    FileUploadResponse, 
    UploadStatusResponse, CompleteUploadRequest
)

logger = logging.getLogger(__name__)


# 移除本地定义的函数，使用公共方法 get_user_primary_role

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: str = Form(...),
    text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件并创建文件消息
    
    Args:
        file: 上传的文件
        conversation_id: 会话ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        文件上传响应
    """
    try:
        # 初始化服务
        file_service = FileService(db)
        chat_service = ChatService(db=db, broadcasting_service=None)
        
        # 验证用户对会话的访问权限
        logger.info(f"验证会话访问权限: conversation_id={conversation_id}, user_id={current_user.id}, user_email={current_user.email}")
        
        can_access = await chat_service.can_access_conversation(conversation_id, current_user.id)
        logger.info(f"权限验证结果: can_access={can_access}")
        
        if not can_access:
            raise HTTPException(status_code=403, detail="无权限访问此会话")
        
        # 上传文件到Minio（只上传文件，不创建消息）
        # 消息创建由前端调用专门的媒体消息API完成
        file_info_dict = await file_service.upload_file(
            file=file,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        return FileUploadResponse(
            success=True,
            message="文件上传成功",
            file_info=file_info_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/upload-avatar", response_model=FileUploadResponse)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传头像/配置类图片（不依赖会话）

    Returns:
        文件上传响应（file_info.file_url 可直接用于前端展示）
    """
    try:
        file_service = FileService(db)
        file_info_dict = await file_service.upload_avatar(file=file, user_id=current_user.id)

        # 返回浏览器可访问的公共URL（避免直接暴露/依赖 Minio 内网地址）
        object_name = file_info_dict.get("object_name")
        if object_name:
            file_info_dict["file_url"] = str(request.url_for("public_file", object_name=object_name))

        return FileUploadResponse(
            success=True,
            message="头像上传成功",
            file_info=file_info_dict,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"头像上传失败: {str(e)}")


@router.get("/public/{object_name:path}", name="public_file")
async def public_file(object_name: str, db: Session = Depends(get_db)):
    """
    公共文件访问端点（用于头像等无需鉴权展示的资源）

    安全策略：
    - 仅允许访问 avatars 目录下的对象，避免公开所有聊天文件
    """
    try:
        if "/avatars/" not in object_name:
            raise HTTPException(status_code=403, detail="禁止访问此资源")

        file_service = FileService(db)
        file_stream = file_service.get_file_stream(object_name)
        if not file_stream:
            raise HTTPException(status_code=404, detail="文件不存在")

        meta = file_service.get_file_metadata(object_name) or {}
        content_type = meta.get("content_type", "application/octet-stream")

        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={
                # 头像可缓存，URL 每次上传都会变化（uuid文件名）
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件访问失败: {str(e)}")


@router.get("/download/{object_name:path}")
async def download_file(
    object_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    安全的文件下载代理端点
    
    Args:
        object_name: Minio中的对象名称
        current_user: 当前用户
        
    Returns:
        文件流响应
    """
    try:
        file_service = FileService(db)
        
        # 验证用户是否有权限访问此文件
        if not file_service.can_access_file(object_name, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此文件")
        
        # 获取文件流
        file_stream = file_service.get_file_stream(object_name)
        if not file_stream:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取文件信息
        file_info = file_service.get_file_metadata(object_name)
        filename = file_info.get('filename', 'download')
        content_type = file_info.get('content_type', 'application/octet-stream')
        
        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "private, max-age=3600"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


@router.get("/preview/{object_name:path}")
async def preview_file(
    object_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    文件预览端点（用于图片、PDF等）
    根据文件大小和类型智能选择传输方式
    
    Args:
        object_name: Minio中的对象名称
        current_user: 当前用户
        
    Returns:
        文件流响应或完整文件响应
    """
    try:
        file_service = FileService(db)
        
        # 验证权限
        if not file_service.can_access_file(object_name, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此文件")
        
        # 获取文件信息
        file_info = file_service.get_file_metadata(object_name)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        content_type = file_info.get('content_type', 'application/octet-stream')
        file_size = file_info.get('size', 0)
        
        # 只允许安全的预览类型
        safe_preview_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain',
            # 音频文件类型
            'audio/webm', 'audio/webm;codecs=opus', 'audio/mpeg', 'audio/mp3',
            'audio/mp4', 'audio/wav', 'audio/ogg', 'audio/aac',
            # 视频文件类型
            'video/webm', 'video/mp4', 'video/avi', 'video/mov'
        ]
        
        if content_type not in safe_preview_types:
            raise HTTPException(status_code=400, detail="此文件类型不支持预览")
        
        # 根据文件大小和类型选择传输方式
        if file_service.should_use_streaming(object_name):
            # 大文件使用流式传输
            file_stream = file_service.get_file_stream(object_name)
            if not file_stream:
                raise HTTPException(status_code=404, detail="文件不存在")
            
            return StreamingResponse(
                file_stream,
                media_type=content_type,
                headers={
                    "Cache-Control": "private, max-age=3600",
                    "X-Content-Type-Options": "nosniff",
                    "Content-Length": str(file_size)
                }
            )
        else:
            # 小文件使用完整响应
            file_data = file_service.get_file_data(object_name)
            if not file_data:
                raise HTTPException(status_code=404, detail="文件不存在")
            
            from fastapi.responses import Response
            return Response(
                content=file_data,
                media_type=content_type,
                headers={
                    "Cache-Control": "private, max-age=3600",
                    "X-Content-Type-Options": "nosniff",
                    "Content-Length": str(len(file_data))
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件预览失败: {str(e)}")


@router.get("/supported-types")
async def get_supported_file_types():
    """
    获取支持的文件类型
    
    Returns:
        支持的文件类型列表
    """
    file_service = FileService()
    return file_service.get_supported_file_types()


@router.get("/conversation/{conversation_id}/files")
async def get_conversation_files(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    file_type: Optional[str] = Query(None, description="筛选文件类型：image, document, audio, video, archive")
):
    """
    获取会话中的文件列表
    
    Args:
        conversation_id: 会话ID
        current_user: 当前用户
        limit: 返回数量限制
        offset: 偏移量
        file_type: 文件类型筛选
        
    Returns:
        文件列表
    """
    try:
        file_service = FileService(db)
        
        # 验证用户对会话的访问权限
        if not file_service.can_access_conversation(conversation_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此会话")
        
        files = file_service.get_conversation_files(
            conversation_id=conversation_id,
            file_type=file_type,
            limit=limit,
            offset=offset
        )
        
        return {
            "files": files,
            "total": len(files),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.delete("/delete/{object_name:path}")
async def delete_file(
    object_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除文件（仅限文件所有者或管理员）
    
    Args:
        object_name: Minio中的对象名称
        current_user: 当前用户
        
    Returns:
        删除结果
    """
    try:
        file_service = FileService(db)
        
        # 验证删除权限
        if not file_service.can_delete_file(object_name, current_user.id):
            raise HTTPException(status_code=403, detail="无权限删除此文件")
        
        success = file_service.delete_file(object_name)
        
        if success:
            return {"success": True, "message": "文件删除成功"}
        else:
            raise HTTPException(status_code=404, detail="文件不存在或删除失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")


@router.get("/info")
async def get_file_info(
    file_url: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取文件信息
    
    Args:
        file_url: 文件URL
        current_user: 当前用户
        
    Returns:
        文件信息
    """
    try:
        file_service = FileService()
        file_info = file_service.get_file_info(file_url)
        
        if file_info:
            return file_info
        else:
            raise HTTPException(status_code=404, detail="文件不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")


@router.post("/cleanup")
async def cleanup_orphaned_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    清理孤立文件（仅管理员）
    
    Args:
        current_user: 当前用户
        
    Returns:
        清理结果
    """
    try:
        # 只有管理员可以执行清理操作
        user_role_names = [role.name for role in current_user.roles]
        if 'admin' not in user_role_names:
            raise HTTPException(status_code=403, detail="只有管理员可以执行此操作")
        
        file_service = FileService(db)
        cleaned_count = file_service.cleanup_orphaned_files()
        
        return {
            "success": True,
            "message": f"清理完成，删除了 {cleaned_count} 个孤立文件"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件清理失败: {str(e)}")


# ================== 断点续传相关端点 ==================

@router.get("/upload-status/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取上传状态
    
    Args:
        upload_id: 上传ID
        current_user: 当前用户
        
    Returns:
        上传状态信息
    """
    try:
        file_service = FileService(db)
        status_info = file_service.get_upload_status(upload_id)
        
        return UploadStatusResponse(**status_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上传状态失败: {str(e)}")


@router.post("/upload-chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    upload_id: str = Form(...),
    conversation_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件分片
    
    Args:
        chunk: 分片文件
        chunk_index: 分片索引
        total_chunks: 总分片数
        upload_id: 上传ID
        conversation_id: 会话ID
        current_user: 当前用户
        
    Returns:
        上传结果
    """
    try:
        file_service = FileService(db)
        
        # 读取分片数据
        chunk_data = await chunk.read()
        
        # 上传分片
        success = file_service.upload_chunk(
            upload_id=upload_id,
            chunk_index=chunk_index,
            chunk_data=chunk_data,
            user_id=current_user.id
        )
        
        if success:
            return {"success": True, "message": f"分片 {chunk_index} 上传成功"}
        else:
            raise HTTPException(status_code=500, detail=f"分片 {chunk_index} 上传失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分片上传失败: {str(e)}")


@router.post("/complete-upload", response_model=FileUploadResponse)
async def complete_upload(
    request: CompleteUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    完成文件上传，合并所有分片
    
    Args:
        request: 完成上传请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        文件上传响应
    """
    try:
        file_service = FileService()
        chat_service = ChatService(db=db, broadcasting_service=None)
        
        # 验证用户对会话的访问权限
        if not await chat_service.can_access_conversation(request.conversation_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此会话")
        
        # 完成上传并合并分片
        file_info_dict = file_service.complete_upload(
            upload_id=request.upload_id,
            conversation_id=request.conversation_id,
            user_id=current_user.id
        )
        
        # 创建媒体消息
        message_info = chat_service.create_media_message_with_details(
            conversation_id=request.conversation_id,
            sender_id=current_user.id,
            media_url=file_info_dict["file_url"],
            media_name=file_info_dict["file_name"],
            mime_type=file_info_dict["mime_type"],
            size_bytes=file_info_dict["file_size"],
            text=None,  # 分片上传没有附带文字
            metadata={"file_type": file_info_dict["file_type"]},
            is_important=False,
            upload_method="chunked_upload"
        )
        
        return FileUploadResponse(
            success=True,
            message="文件上传完成",
            file_info=file_info_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完成上传失败: {str(e)}")


@router.post("/start-resumable-upload")
async def start_resumable_upload(
    file_name: str = Form(...),
    file_size: int = Form(...),
    chunk_size: int = Form(...),
    conversation_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    开始断点续传上传
    
    Args:
        file_name: 文件名
        file_size: 文件大小
        chunk_size: 分片大小
        conversation_id: 会话ID
        current_user: 当前用户
        
    Returns:
        上传会话信息
    """
    try:
        file_service = FileService(db)
        
        # 生成上传ID
        import uuid
        upload_id = f"upload_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        # 创建上传会话
        file_service.create_upload_session(
            upload_id=upload_id,
            file_name=file_name,
            file_size=file_size,
            chunk_size=chunk_size,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        
        return {
            "success": True,
            "upload_id": upload_id,
            "total_chunks": total_chunks,
            "chunk_size": chunk_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"开始上传失败: {str(e)}")


@router.delete("/cancel-upload/{upload_id}")
async def cancel_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    取消上传
    
    Args:
        upload_id: 上传ID
        current_user: 当前用户
        
    Returns:
        取消结果
    """
    try:
        file_service = FileService(db)
        
        success = file_service.cancel_upload(upload_id, current_user.id)
        
        if success:
            return {"success": True, "message": "上传已取消"}
        else:
            raise HTTPException(status_code=404, detail="上传会话不存在或无权限")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消上传失败: {str(e)}")