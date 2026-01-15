"""
渠道 Webhook 接收端点
"""
import logging
from typing import Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse

from app.channels.services.channel_service import ChannelService
from app.channels.adapters.wechat_work.adapter import WeChatWorkAdapter
from app.channels.adapters.wechat_work.kf_adapter import WeChatWorkKfAdapter
from app.channels.interfaces import ChannelMessage
from app.channels.services.wechat_work_archive_service import WeChatWorkArchiveService
from app.channels.services.wechat_work_archive_ingest import ingest_decrypted_messages
from app.channels.deps.channel_deps import get_channel_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channels", tags=["channels"])


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
        logger.info(f"收到企业微信验证请求: msg_signature={msg_signature[:20]}..., timestamp={timestamp}, nonce={nonce}, echostr={echostr[:30]}...")
        
        # 获取适配器
        adapter = channel_service.get_adapter("wechat_work")
        if not adapter:
            logger.error("企业微信适配器未注册")
            raise HTTPException(status_code=500, detail="渠道适配器未配置")
        
        # 验证请求（包括签名验证）
        is_valid = await adapter.validate_webhook(request)
        if not is_valid:
            logger.error("Webhook验证失败（签名验证未通过）")
            raise HTTPException(status_code=403, detail="验证失败")
        
        logger.info("签名验证通过，开始处理echostr")
        
        # 如果配置了EncodingAESKey，需要解密echostr
        if isinstance(adapter, WeChatWorkAdapter):
            decrypted_echostr = adapter.decrypt_echostr(echostr)
            if decrypted_echostr:
                logger.info(f"成功解密echostr，返回明文: {decrypted_echostr[:30]}...")
                return PlainTextResponse(decrypted_echostr)
            else:
                # 如果解密失败，可能是未配置EncodingAESKey或配置错误
                logger.warning("解密echostr失败，尝试返回原始值（可能未配置EncodingAESKey）")
                # 注意：如果配置了EncodingAESKey但解密失败，返回原始值会导致验证失败
                # 这里返回原始值是为了兼容未配置EncodingAESKey的情况
                return PlainTextResponse(echostr)
        else:
            # 非WeChatWorkAdapter，直接返回原始值
            logger.warning("适配器类型不是WeChatWorkAdapter，返回原始echostr")
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
    """
    # 打印最原始的请求信息，用于确认请求是否到达
    logger.info(f"--- [Webhook Entry] 收到企业微信 POST 请求: signature={msg_signature}, timestamp={timestamp} ---")
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
        
        # 读取请求体（XML格式，可能包含 Encrypt）
        body = await request.body()
        xml_content = body.decode("utf-8")
        
        logger.info(f"收到企业微信消息: {xml_content}...")

        # 加密回调：解密 Encrypt 字段
        if isinstance(adapter, WeChatWorkAdapter):
            encrypt = adapter.parse_xml_message(xml_content).get("Encrypt")
            if encrypt:
                # 如果消息是加密的但没有配置加解密工具，记录警告并返回success
                if not getattr(adapter, "crypto", None):
                    logger.warning("收到加密消息但未配置加解密工具（EncodingAESKey配置错误），无法处理消息")
                    # 返回success避免企业微信重复推送
                    return PlainTextResponse("success")
                
                # POST 回调验签：value 用 Encrypt
                if not adapter.crypto.verify_signature(msg_signature, timestamp, nonce, encrypt):
                    raise HTTPException(status_code=403, detail="验证失败")
                decrypted = adapter.crypto.decrypt_encrypt_field(encrypt)
                if decrypted:
                    xml_content = decrypted
                    logger.info(f"企业微信消息解密成功: {xml_content}...")
                else:
                    logger.error("企业微信消息解密失败")
                    raise HTTPException(status_code=400, detail="消息解密失败")

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


@router.get("/webhook/wechat-work-kf")
async def wechat_work_kf_webhook_verify(
    request: Request,
    msg_signature: str = Query(..., description="签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    echostr: str = Query(..., description="随机字符串"),
    channel_service: ChannelService = Depends(get_channel_service),
):
    """微信客服回调验证（GET）"""
    adapter = channel_service.get_adapter("wechat_work_kf")
    if not adapter or not isinstance(adapter, WeChatWorkKfAdapter):
        raise HTTPException(status_code=500, detail="渠道适配器未配置")

    if not await adapter.validate_webhook(request):
        raise HTTPException(status_code=403, detail="验证失败")

    decrypted = adapter.decrypt_echostr(echostr)
    return PlainTextResponse(decrypted or echostr)


@router.post("/webhook/wechat-work-kf")
async def wechat_work_kf_webhook(
    request: Request,
    msg_signature: str = Query(..., description="签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    channel_service: ChannelService = Depends(get_channel_service),
):
    """接收微信客服回调消息（POST）"""
    logger.info(f"--- [Webhook Entry] 收到微信客服 POST 请求: signature={msg_signature}, timestamp={timestamp} ---")
    adapter = channel_service.get_adapter("wechat_work_kf")
    if not adapter or not isinstance(adapter, WeChatWorkKfAdapter):
        raise HTTPException(status_code=500, detail="渠道适配器未配置")

    if not await adapter.validate_webhook(request):
        raise HTTPException(status_code=403, detail="验证失败")

    body = await request.body()
    raw = body.decode("utf-8")

    # 兼容加密回调：先取 Encrypt，验签后解密
    decrypt_body = raw
    encrypt = adapter._extract_encrypt_from_xml(raw)
    if encrypt and adapter.crypto:
        if not adapter.crypto.verify_signature(msg_signature, timestamp, nonce, encrypt):
            raise HTTPException(status_code=403, detail="验证失败")
        decrypted = adapter.decrypt_encrypt_field(encrypt)
        if decrypted:
            decrypt_body = decrypted
        else:
            logger.error("微信客服消息解密失败")
            raise HTTPException(status_code=400, detail="消息解密失败")

    payload = adapter.parse_incoming_payload(decrypt_body)
    channel_message = await adapter.receive_message(payload)
    await channel_service.process_incoming_message(channel_message)
    return PlainTextResponse("success")




@router.post("/webhook/wechat-work-archive")
async def wechat_work_archive_webhook(
    request: Request,
    msg_signature: str = Query(None, description="签名"),
    timestamp: str = Query(None, description="时间戳"),
    nonce: str = Query(None, description="随机数"),
    channel_service: ChannelService = Depends(get_channel_service),
):
    """
    企业微信「会话内容存档」入站接收（已解密的 JSON）。

    说明：
    - 本端点接收已解密后的 chatdata 列表。
    - 目前仅落库文本消息，媒体消息后续再完善。
    """
    try:
        payload = await request.json()
    except Exception:
        logger.warning("会话存档回调 JSON 解析失败，直接返回 success")
        return PlainTextResponse("success")

    # 兼容加密回调：payload 内存在 encrypt
    encrypt = payload.get("encrypt") or payload.get("Encrypt")
    if encrypt and msg_signature and timestamp and nonce:
        archive_service = WeChatWorkArchiveService(db=channel_service.db)
        decrypted = archive_service.decrypt_callback_payload(
            msg_signature=msg_signature,
            timestamp=timestamp,
            nonce=nonce,
            encrypted=str(encrypt),
        )
        if decrypted:
            payload = decrypted
        else:
            logger.warning("会话存档回调解密失败，已忽略")
            return PlainTextResponse("success")

    chatdata = payload.get("chatdata") or payload.get("data") or []
    if not isinstance(chatdata, list):
        logger.info("会话存档回调未包含 chatdata 列表，已忽略")
        return PlainTextResponse("success")

    await ingest_decrypted_messages(chatdata, channel_service=channel_service)

    return PlainTextResponse("success")

