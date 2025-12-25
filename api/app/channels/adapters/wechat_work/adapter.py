"""
企业微信渠道适配器
"""
import logging
from typing import Dict, Any, Optional
from fastapi import Request
import xml.etree.ElementTree as ET

from app.channels.interfaces import ChannelAdapter, ChannelMessage
from app.channels.adapters.wechat_work.client import WeChatWorkClient
from app.channels.adapters.wechat_work.crypto import WeChatWorkCrypto
from app.chat.models.chat import Message

logger = logging.getLogger(__name__)


class WeChatWorkAdapter(ChannelAdapter):
    """企业微信渠道适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = WeChatWorkClient(
            corp_id=config["corp_id"],
            agent_id=config["agent_id"],
            secret=config["secret"]
        )
        self.token = config.get("token", "")  # Webhook验证token
        self.encoding_aes_key = config.get("encoding_aes_key", "")  # 消息加解密key
        self.corp_id = config.get("corp_id", "")
        
        # 初始化加解密工具（如果配置了EncodingAESKey）
        self.crypto = None
        if self.token and self.encoding_aes_key and self.corp_id:
            try:
                self.crypto = WeChatWorkCrypto(
                    token=self.token,
                    encoding_aes_key=self.encoding_aes_key,
                    corp_id=self.corp_id
                )
            except Exception as e:
                logger.warning(f"初始化企业微信加解密工具失败: {e}")
    
    def get_channel_type(self) -> str:
        """获取渠道类型"""
        return "wechat_work"
    
    async def receive_message(self, raw_message: Dict[str, Any]) -> ChannelMessage:
        """
        接收企业微信消息，转换为系统标准格式
        
        企业微信消息格式（XML）：
        <xml>
            <ToUserName><![CDATA[toUser]]></ToUserName>
            <FromUserName><![CDATA[fromUser]]></FromUserName>
            <CreateTime>1348831860</CreateTime>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA[this is a test]]></Content>
            <MsgId>1234567890123456</MsgId>
            <AgentID>1</AgentID>
        </xml>
        """
        msg_type = raw_message.get("MsgType", "")
        from_user = raw_message.get("FromUserName", "")
        msg_id = raw_message.get("MsgId", "")
        create_time = raw_message.get("CreateTime", 0)
        
        # 如果MsgType为空，可能是消息未正确解密或格式异常
        if not msg_type:
            logger.error(f"消息类型为空，可能是解密失败或消息格式异常。原始消息字段: {list(raw_message.keys())}")
            logger.debug(f"原始消息内容: {raw_message}")
            raise ValueError(f"消息类型为空，无法处理消息。请检查EncodingAESKey配置是否正确。消息字段: {list(raw_message.keys())}")
        
        if msg_type == "text":
            content = raw_message.get("Content", "")
            return ChannelMessage(
                channel_type="wechat_work",
                channel_message_id=msg_id,
                channel_user_id=from_user,
                content={"text": content},
                message_type="text",
                timestamp=create_time
            )
        elif msg_type == "image":
            media_id = raw_message.get("MediaId", "")
            pic_url = raw_message.get("PicUrl", "")
            return ChannelMessage(
                channel_type="wechat_work",
                channel_message_id=msg_id,
                channel_user_id=from_user,
                content={
                    "media_info": {
                        "url": pic_url,
                        "media_id": media_id,
                        "mime_type": "image/jpeg"
                    }
                },
                message_type="media",
                timestamp=create_time,
                extra_data={"media_id": media_id}
            )
        elif msg_type == "file":
            media_id = raw_message.get("MediaId", "")
            file_name = raw_message.get("FileName", "unknown")
            file_ext = raw_message.get("FileExt", "")
            file_size = raw_message.get("FileSize", 0)
            return ChannelMessage(
                channel_type="wechat_work",
                channel_message_id=msg_id,
                channel_user_id=from_user,
                content={
                    "media_info": {
                        "url": "",  # file 类型没有 PicUrl，需要通过 MediaId 下载
                        "media_id": media_id,
                        "name": file_name,
                        "size_bytes": int(file_size),
                        "mime_type": "application/octet-stream"
                    }
                },
                message_type="media",
                timestamp=create_time,
                extra_data={
                    "media_id": media_id,
                    "file_name": file_name,
                    "file_ext": file_ext
                }
            )
        elif msg_type == "event":
            event = raw_message.get("Event", "")
            logger.info(f"收到企业微信事件: event={event}, from={from_user}")
            # 返回一个特殊的系统消息或空，取决于业务需求
            return ChannelMessage(
                channel_type="wechat_work",
                channel_message_id=msg_id or f"evt_{create_time}",
                channel_user_id=from_user,
                content={"text": f"[系统事件: {event}]"},
                message_type="text",
                timestamp=create_time,
                extra_data={"event": event}
            )
        else:
            logger.warning(f"不支持的消息类型: {msg_type}")
            logger.debug(f"原始消息内容: {raw_message}")
            raise ValueError(f"不支持的消息类型: {msg_type}")
    
    async def send_message(self, message: Message, channel_user_id: str) -> bool:
        """发送消息到企业微信"""
        try:
            if message.type == "text":
                content = message.content.get("text", "")
                # 渠道转发：外部看到的是应用身份，这里用前缀补充 A 的名字
                extra = message.extra_metadata or {}
                channel_meta = extra.get("channel") if isinstance(extra, dict) else None
                from_user_name = None
                if isinstance(channel_meta, dict):
                    from_user_name = channel_meta.get("from_user_name")
                if from_user_name:
                    content = f"【{from_user_name}】{content}"
                return await self.client.send_text_message(channel_user_id, content)
            elif message.type == "media":
                media_info = message.content.get("media_info", {})
                media_url = media_info.get("url")
                
                if not media_url:
                    logger.error("媒体消息缺少URL")
                    return False
                
                # 下载文件并上传到企业微信
                media_id = await self._upload_media_to_wechat(media_url)
                if media_id:
                    return await self.client.send_image_message(channel_user_id, media_id)
                return False
            else:
                logger.warning(f"不支持的消息类型: {message.type}")
                return False
        except Exception as e:
            logger.error(f"发送消息到企业微信失败: {e}", exc_info=True)
            return False
    
    async def validate_webhook(self, request: Request) -> bool:
        """
        验证企业微信 Webhook 请求
        
        企业微信使用URL参数验证：
        - msg_signature: 签名
        - timestamp: 时间戳
        - nonce: 随机数
        - echostr: 随机字符串（仅验证时使用）
        """
        query_params = request.query_params
        msg_signature = query_params.get("msg_signature")
        timestamp = query_params.get("timestamp")
        nonce = query_params.get("nonce")
        echostr = query_params.get("echostr")
        
        if not all([msg_signature, timestamp, nonce]):
            logger.warning("Webhook验证参数不完整")
            return False
        
        # 如果没有配置加解密工具，使用简单验证
        if not self.crypto:
            logger.warning("未配置加解密工具，使用简单验证")
            return True
        
        # 如果有echostr，进行签名验证
        if echostr:
            is_valid = self.crypto.verify_signature(
                msg_signature=msg_signature,
                timestamp=timestamp,
                nonce=nonce,
                echostr=echostr
            )
            if is_valid:
                logger.info("Webhook签名验证通过")
            return is_valid
        
        # 没有echostr的情况（POST请求），只验证签名参数存在
        logger.info("Webhook验证通过（POST请求）")
        return True
    
    def decrypt_echostr(self, encrypted_echostr: str) -> Optional[str]:
        """
        解密企业微信的echostr
        
        Args:
            encrypted_echostr: Base64编码的加密字符串
            
        Returns:
            解密后的明文，失败返回None
        """
        if not self.crypto:
            logger.error("未配置加解密工具，无法解密echostr")
            return None
        
        return self.crypto.decrypt_echostr(encrypted_echostr)
    
    async def _upload_media_to_wechat(self, media_url: str) -> Optional[str]:
        """
        下载媒体文件并上传到企业微信
        
        Args:
            media_url: 媒体文件URL（MinIO URL）
            
        Returns:
            media_id 或 None
        """
        import tempfile
        import httpx
        import os
        
        try:
            # 1. 从MinIO下载文件
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(media_url)
                response.raise_for_status()
                
                # 2. 保存到临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                try:
                    # 3. 上传到企业微信
                    media_id = await self.client.upload_media(tmp_path, media_type="image")
                    return media_id
                finally:
                    # 4. 清理临时文件
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
        except Exception as e:
            logger.error(f"上传媒体到企业微信失败: {e}", exc_info=True)
            return None
    
    @staticmethod
    def parse_xml_message(xml_content: str) -> Dict[str, Any]:
        """解析企业微信XML消息"""
        try:
            root = ET.fromstring(xml_content)
            result = {}
            for child in root:
                result[child.tag] = child.text
            return result
        except ET.ParseError as e:
            logger.error(f"解析XML消息失败: {e}")
            raise ValueError(f"无效的XML格式: {e}")

