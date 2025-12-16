"""
渠道适配器接口定义
采用适配器模式，为不同渠道提供统一接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from fastapi import Request


@dataclass
class ChannelMessage:
    """渠道消息标准格式"""
    channel_type: str  # 渠道类型：wechat_work, wechat, whatsapp等
    channel_message_id: str  # 渠道消息ID（用于去重）
    channel_user_id: str  # 渠道用户ID
    content: Dict[str, Any]  # 消息内容（标准格式）
    message_type: str  # 消息类型：text, media, system等
    timestamp: Optional[int] = None  # 时间戳
    extra_data: Optional[Dict[str, Any]] = None  # 额外数据


class ChannelAdapter(ABC):
    """渠道适配器抽象基类"""
    
    @abstractmethod
    async def receive_message(self, raw_message: Dict[str, Any]) -> ChannelMessage:
        """
        接收外部渠道消息，转换为系统标准格式
        
        Args:
            raw_message: 原始渠道消息
            
        Returns:
            标准格式的渠道消息
        """
        pass
    
    @abstractmethod
    async def send_message(
        self, 
        message: Any,  # Message模型对象
        channel_user_id: str
    ) -> bool:
        """
        发送消息到外部渠道
        
        Args:
            message: 系统消息对象
            channel_user_id: 渠道用户ID
            
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def validate_webhook(self, request: Request) -> bool:
        """
        验证 Webhook 请求合法性
        
        Args:
            request: FastAPI Request对象
            
        Returns:
            是否验证通过
        """
        pass
    
    @abstractmethod
    def get_channel_type(self) -> str:
        """获取渠道类型"""
        pass

