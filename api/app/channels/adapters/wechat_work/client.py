"""
企业微信 API 客户端
"""
import time
import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class WeChatWorkClient:
    """企业微信 API 客户端"""
    
    BASE_URL = "https://qyapi.weixin.qq.com"
    
    def __init__(self, corp_id: str, agent_id: str, secret: str):
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.secret = secret
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[int] = None
    
    async def get_access_token(self) -> str:
        """获取 access_token"""
        if self.access_token and self.token_expires_at and time.time() < self.token_expires_at:
            return self.access_token
        
        url = f"{self.BASE_URL}/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.secret
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("errcode") != 0:
                    raise Exception(f"获取 access_token 失败: {data.get('errmsg')}")
                
                self.access_token = data["access_token"]
                # 提前5分钟刷新
                self.token_expires_at = time.time() + data["expires_in"] - 300
                logger.info(f"成功获取 access_token，过期时间: {self.token_expires_at}")
                return self.access_token
            except httpx.HTTPError as e:
                logger.error(f"获取 access_token HTTP错误: {e}")
                raise
            except Exception as e:
                logger.error(f"获取 access_token 失败: {e}")
                raise
    
    async def send_text_message(self, user_id: str, content: str) -> bool:
        """发送文本消息"""
        token = await self.get_access_token()
        url = f"{self.BASE_URL}/cgi-bin/message/send"
        params = {"access_token": token}
        
        payload = {
            "touser": user_id,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {
                "content": content
            }
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, params=params, json=payload)
                response.raise_for_status()
                data = response.json()
                
                if data.get("errcode") != 0:
                    logger.error(f"发送消息失败: {data.get('errmsg')}, errcode: {data.get('errcode')}")
                    return False
                
                logger.info(f"成功发送文本消息到用户: {user_id}")
                return True
            except httpx.HTTPError as e:
                logger.error(f"发送消息 HTTP错误: {e}")
                return False
            except Exception as e:
                logger.error(f"发送消息异常: {e}")
                return False
    
    async def send_image_message(self, user_id: str, media_id: str) -> bool:
        """发送图片消息"""
        token = await self.get_access_token()
        url = f"{self.BASE_URL}/cgi-bin/message/send"
        params = {"access_token": token}
        
        payload = {
            "touser": user_id,
            "msgtype": "image",
            "agentid": self.agent_id,
            "image": {
                "media_id": media_id
            }
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, params=params, json=payload)
                response.raise_for_status()
                data = response.json()
                
                if data.get("errcode") != 0:
                    logger.error(f"发送图片失败: {data.get('errmsg')}, errcode: {data.get('errcode')}")
                    return False
                
                logger.info(f"成功发送图片消息到用户: {user_id}")
                return True
            except httpx.HTTPError as e:
                logger.error(f"发送图片 HTTP错误: {e}")
                return False
            except Exception as e:
                logger.error(f"发送图片异常: {e}")
                return False
    
    async def upload_media(self, file_path: str, media_type: str = "image") -> Optional[str]:
        """
        上传媒体文件，返回 media_id
        
        Args:
            file_path: 文件路径
            media_type: 媒体类型：image, voice, video, file
            
        Returns:
            media_id 或 None
        """
        token = await self.get_access_token()
        url = f"{self.BASE_URL}/cgi-bin/media/upload"
        params = {
            "access_token": token,
            "type": media_type
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                with open(file_path, "rb") as f:
                    files = {"media": f}
                    response = await client.post(url, params=params, files=files)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get("errcode") != 0:
                        logger.error(f"上传媒体失败: {data.get('errmsg')}, errcode: {data.get('errcode')}")
                        return None
                    
                    media_id = data.get("media_id")
                    logger.info(f"成功上传媒体文件: {media_id}")
                    return media_id
            except FileNotFoundError:
                logger.error(f"文件不存在: {file_path}")
                return None
            except httpx.HTTPError as e:
                logger.error(f"上传媒体 HTTP错误: {e}")
                return None
            except Exception as e:
                logger.error(f"上传媒体异常: {e}")
                return None

    async def download_media(self, media_id: str) -> Optional[bytes]:
        """
        从企业微信下载媒体文件
        
        Args:
            media_id: 媒体文件ID
            
        Returns:
            文件二进制数据 或 None
        """
        token = await self.get_access_token()
        url = f"{self.BASE_URL}/cgi-bin/media/get"
        params = {
            "access_token": token,
            "media_id": media_id
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                # 检查响应头，如果不是文件流可能是错误信息
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    data = response.json()
                    if data.get("errcode") != 0:
                        logger.error(f"下载媒体失败: {data.get('errmsg')}, errcode: {data.get('errcode')}")
                        return None
                
                return response.content
            except httpx.HTTPError as e:
                logger.error(f"下载媒体 HTTP错误: {e}")
                return None
            except Exception as e:
                logger.error(f"下载媒体异常: {e}")
                return None

