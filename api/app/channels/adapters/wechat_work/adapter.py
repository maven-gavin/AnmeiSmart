"""
企业微信渠道适配器
"""
import logging
from typing import Dict, Any, Optional
from fastapi import Request
import xml.etree.ElementTree as ET

from app.channels.interfaces import ChannelAdapter, ChannelMessage
from app.channels.adapters.wechat_work.client import WeChatWorkClient
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
        else:
            logger.warning(f"不支持的消息类型: {msg_type}")
            raise ValueError(f"不支持的消息类型: {msg_type}")
    
    async def send_message(self, message: Message, channel_user_id: str) -> bool:
        """发送消息到企业微信"""
        try:
            if message.type == "text":
                content = message.content.get("text", "")
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
        # TODO: 实现签名验证逻辑
        # 企业微信使用SHA1签名算法
        # 参考：https://developer.work.weixin.qq.com/document/path/90930
        
        # 临时实现：简单验证token是否存在
        query_params = request.query_params
        msg_signature = query_params.get("msg_signature")
        timestamp = query_params.get("timestamp")
        nonce = query_params.get("nonce")
        
        if not all([msg_signature, timestamp, nonce]):
            logger.warning("Webhook验证参数不完整")
            return False
        
        # TODO: 实现完整的签名验证
        # 这里暂时返回True，实际生产环境需要实现签名验证
        logger.info("Webhook验证通过（临时实现）")
        return True
    
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

