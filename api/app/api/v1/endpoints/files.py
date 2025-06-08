"""
文件上传API端点
遵循DDD架构：Controller层只做参数校验和调用Service层
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models.user import User
from app.services.file_service import FileService
from app.services.chat.message_service import MessageService
from app.schemas.chat import FileUploadResponse, MessageInfo

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: str = Form(...),
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
        file_service = FileService()
        message_service = MessageService(db)
        
        # 验证用户对会话的访问权限
        if not await message_service.can_access_conversation(conversation_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此会话")
        
        # 上传文件到Minio
        file_info_dict = await file_service.upload_file(
            file=file,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        # 创建文件消息
        message_info = await message_service.create_message(
            conversation_id=conversation_id,
            content=json.dumps(file_info_dict),  # 将文件信息存储为JSON
            message_type="file",
            sender_id=current_user.id,
            sender_type=current_user.role,
            is_important=False
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


@router.get("/download/{object_name:path}")
async def download_file(
    object_name: str,
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
        file_service = FileService()
        
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
    current_user: User = Depends(get_current_user)
):
    """
    文件预览端点（用于图片、PDF等）
    
    Args:
        object_name: Minio中的对象名称
        current_user: 当前用户
        
    Returns:
        文件流响应
    """
    try:
        file_service = FileService()
        
        # 验证权限
        if not file_service.can_access_file(object_name, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此文件")
        
        # 获取文件流
        file_stream = file_service.get_file_stream(object_name)
        if not file_stream:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取文件信息
        file_info = file_service.get_file_metadata(object_name)
        content_type = file_info.get('content_type', 'application/octet-stream')
        
        # 只允许安全的预览类型
        safe_preview_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain'
        ]
        
        if content_type not in safe_preview_types:
            raise HTTPException(status_code=400, detail="此文件类型不支持预览")
        
        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={
                "Cache-Control": "private, max-age=3600",
                "X-Content-Type-Options": "nosniff"
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
        file_service = FileService()
        
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
        file_service = FileService()
        
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
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="只有管理员可以执行此操作")
        
        file_service = FileService()
        cleaned_count = file_service.cleanup_orphaned_files()
        
        return {
            "success": True,
            "message": f"清理完成，删除了 {cleaned_count} 个孤立文件"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件清理失败: {str(e)}") 