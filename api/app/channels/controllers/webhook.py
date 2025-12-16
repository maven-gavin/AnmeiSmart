"""
渠道 Webhook 接收端点
"""
import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.common.deps.database import get_db
from app.channels.services.channel_service import ChannelService
from app.channels.adapters.wechat_work.adapter import WeChatWorkAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channels", tags=["channels"])


def get_channel_service(db: Session = Depends(get_db)) -> ChannelService:
    """获取渠道服务实例"""
    from app.websocket.broadcasting_service import BroadcastingService
    from app.websocket.broadcasting_factory import get_broadcasting_service
    
    # 获取 broadcasting_service
    broadcasting_service = get_broadcasting_service()
    
    service = ChannelService(db=db, broadcasting_service=broadcasting_service)
    
    # 注册企业微信适配器（临时实现，后续应从配置加载）
    # TODO: 从数据库加载渠道配置并注册适配器
    # 临时：使用环境变量或硬编码配置（仅用于MVP）
    import os
    corp_id = os.getenv("WECHAT_WORK_CORP_ID", "")
    agent_id = os.getenv("WECHAT_WORK_AGENT_ID", "")
    secret = os.getenv("WECHAT_WORK_SECRET", "")
    token = os.getenv("WECHAT_WORK_TOKEN", "")
    encoding_aes_key = os.getenv("WECHAT_WORK_ENCODING_AES_KEY", "")
    
    if corp_id and agent_id and secret:
        config = {
            "corp_id": corp_id,
            "agent_id": agent_id,
            "secret": secret,
            "token": token,
            "encoding_aes_key": encoding_aes_key
        }
        adapter = WeChatWorkAdapter(config)
        service.register_adapter("wechat_work", adapter)
    
    return service


@router.get("/webhook/wechat-work")
async def wechat_work_webhook_verify(
    request: Request,
    msg_signature: str = Query(..., description="签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    echostr: str = Query(..., description="随机字符串"),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    企业微信 Webhook 验证端点（GET请求）
    
    企业微信首次配置Webhook时会调用此端点进行验证
    """
    try:
        # 获取适配器
        adapter = channel_service.get_adapter("wechat_work")
        if not adapter:
            logger.error("企业微信适配器未注册")
            raise HTTPException(status_code=500, detail="渠道适配器未配置")
        
        # 验证请求
        is_valid = await adapter.validate_webhook(request)
        if not is_valid:
            raise HTTPException(status_code=403, detail="验证失败")
        
        # 返回 echostr 完成验证
        return PlainTextResponse(echostr)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook验证失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证异常: {str(e)}")


@router.post("/webhook/wechat-work")
async def wechat_work_webhook(
    request: Request,
    msg_signature: str = Query(..., description="签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    接收企业微信 Webhook 消息（POST请求）
    
    企业微信会向此端点推送消息
    """
    try:
        # 获取适配器
        adapter = channel_service.get_adapter("wechat_work")
        if not adapter:
            logger.error("企业微信适配器未注册")
            raise HTTPException(status_code=500, detail="渠道适配器未配置")
        
        # 验证请求
        is_valid = await adapter.validate_webhook(request)
        if not is_valid:
            raise HTTPException(status_code=403, detail="验证失败")
        
        # 读取请求体（XML格式）
        body = await request.body()
        xml_content = body.decode("utf-8")
        
        logger.info(f"收到企业微信消息: {xml_content[:200]}...")
        
        # 解析XML消息
        if isinstance(adapter, WeChatWorkAdapter):
            raw_message = adapter.parse_xml_message(xml_content)
        else:
            raise ValueError("适配器类型错误")
        
        # 转换为系统标准格式
        channel_message = await adapter.receive_message(raw_message)
        
        # 处理消息（创建会话、保存消息等）
        message = await channel_service.process_incoming_message(channel_message)
        
        if message:
            logger.info(f"成功处理企业微信消息: {channel_message.channel_message_id}")
            # 返回成功响应（企业微信要求返回特定格式）
            return PlainTextResponse("success")
        else:
            logger.warning(f"消息处理失败: {channel_message.channel_message_id}")
            return PlainTextResponse("failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理企业微信消息失败: {e}", exc_info=True)
        # 即使处理失败，也返回success，避免企业微信重复推送
        return PlainTextResponse("success")

