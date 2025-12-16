# 截图功能与企业微信集成方案

## 1. 功能概述

### 1.1 目标
- **截图功能**：支持在 Web 界面中截取屏幕或指定区域，并作为媒体消息发送
- **企业微信集成（MVP）**：接入企业微信作为外部消息渠道，实现双向消息同步

### 1.2 核心价值
- 提升用户体验：快速截图并分享
- 多渠道统一管理：企业微信消息统一到平台管理
- 可扩展架构：为未来接入其他渠道（微信、WhatsApp等）打下基础

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端层        │    │   后端层        │    │   外部渠道      │
│                 │    │                 │    │                 │
│ • 截图组件      │───►│ • 文件服务      │    │ • 企业微信      │
│ • 消息输入      │    │ • 消息服务      │◄──►│ • Webhook接收   │
│ • 媒体预览      │    │ • 渠道适配器    │    │ • API发送       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │   数据层        │
                        │                 │
                        │ • 消息表        │
                        │ • 渠道配置表    │
                        │ • 文件存储      │
                        └─────────────────┘
```

### 2.2 渠道抽象层设计

采用**适配器模式（Adapter Pattern）**，为不同渠道提供统一接口：

```python
# 渠道接口定义
class ChannelAdapter(ABC):
    """渠道适配器抽象基类"""
    
    @abstractmethod
    async def receive_message(self, raw_message: dict) -> ChannelMessage:
        """接收外部渠道消息，转换为系统标准格式"""
        pass
    
    @abstractmethod
    async def send_message(self, message: Message, channel_user_id: str) -> bool:
        """发送消息到外部渠道"""
        pass
    
    @abstractmethod
    async def validate_webhook(self, request: Request) -> bool:
        """验证 Webhook 请求合法性"""
        pass
```

### 2.3 数据模型扩展

#### 2.3.1 渠道配置表（新增）

```python
class ChannelConfig(BaseModel):
    """渠道配置"""
    __tablename__ = "channel_configs"
    
    id = Column(String(36), primary_key=True)
    channel_type = Column(String(50), nullable=False)  # wechat_work, wechat, whatsapp等
    name = Column(String(100), nullable=False)  # 渠道名称
    config = Column(JSON, nullable=False)  # 渠道配置（API密钥、Webhook URL等）
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True))
```

#### 2.3.2 消息表扩展

在 `Message` 表的 `extra_metadata` 字段中存储渠道信息：

```json
{
  "channel": {
    "type": "wechat_work",
    "channel_message_id": "msg_xxx",
    "channel_user_id": "user_xxx"
  }
}
```

## 3. 截图功能实现

### 3.1 前端实现

#### 3.1.1 截图组件

使用 `html2canvas` 库实现截图功能：

```typescript
// web/src/components/chat/ScreenshotCapture.tsx
import html2canvas from 'html2canvas';

interface ScreenshotCaptureProps {
  onCapture: (blob: Blob) => void;
  targetElement?: HTMLElement;  // 可选：指定截图区域
}

export function ScreenshotCapture({ onCapture, targetElement }: ScreenshotCaptureProps) {
  const captureScreenshot = async () => {
    try {
      const element = targetElement || document.body;
      const canvas = await html2canvas(element, {
        useCORS: true,
        allowTaint: false,
        backgroundColor: '#ffffff',
        scale: 1,  // 可根据需要调整清晰度
      });
      
      canvas.toBlob((blob) => {
        if (blob) {
          onCapture(blob);
        }
      }, 'image/png');
    } catch (error) {
      console.error('截图失败:', error);
      toast.error('截图失败，请重试');
    }
  };
  
  return (
    <Button onClick={captureScreenshot}>
      <Camera className="h-4 w-4 mr-2" />
      截图
    </Button>
  );
}
```

#### 3.1.2 集成到消息输入组件

在 `MessageInput.tsx` 中添加截图功能：

```typescript
// 添加截图处理
const handleScreenshot = async (blob: Blob) => {
  const file = new File([blob], `screenshot_${Date.now()}.png`, {
    type: 'image/png'
  });
  
  const fileInfo: FileInfo = {
    file_url: URL.createObjectURL(blob),
    file_name: file.name,
    file_type: 'image',
    mime_type: 'image/png',
    file_size: blob.size,
  };
  
  // 添加到临时文件管理
  addTempFile(fileInfo.file_url, file);
  
  // 显示预览并准备发送
  setImagePreview(fileInfo);
};
```

### 3.2 后端实现

截图功能复用现有的文件上传和媒体消息机制，无需额外后端代码。

## 4. 企业微信集成实现

### 4.1 企业微信 API 集成

#### 4.1.1 企业微信客户端

```python
# api/app/channels/adapters/wechat_work/client.py
import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class WeChatWorkClient:
    """企业微信 API 客户端"""
    
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
        
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("errcode") != 0:
                raise Exception(f"获取 access_token 失败: {data.get('errmsg')}")
            
            self.access_token = data["access_token"]
            self.token_expires_at = time.time() + data["expires_in"] - 300  # 提前5分钟刷新
            return self.access_token
    
    async def send_text_message(self, user_id: str, content: str) -> bool:
        """发送文本消息"""
        token = await self.get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        
        payload = {
            "touser": user_id,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {
                "content": content
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            data = response.json()
            
            if data.get("errcode") != 0:
                logger.error(f"发送消息失败: {data.get('errmsg')}")
                return False
            
            return True
    
    async def send_image_message(self, user_id: str, media_id: str) -> bool:
        """发送图片消息"""
        token = await self.get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        
        payload = {
            "touser": user_id,
            "msgtype": "image",
            "agentid": self.agent_id,
            "image": {
                "media_id": media_id
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            data = response.json()
            
            if data.get("errcode") != 0:
                logger.error(f"发送图片失败: {data.get('errmsg')}")
                return False
            
            return True
    
    async def upload_media(self, file_path: str, media_type: str = "image") -> Optional[str]:
        """上传媒体文件，返回 media_id"""
        token = await self.get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={token}&type={media_type}"
        
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"media": f}
                response = await client.post(url, files=files)
                data = response.json()
                
                if data.get("errcode") != 0:
                    logger.error(f"上传媒体失败: {data.get('errmsg')}")
                    return None
                
                return data.get("media_id")
```

#### 4.1.2 企业微信适配器

```python
# api/app/channels/adapters/wechat_work/adapter.py
from app.channels.interfaces import ChannelAdapter, ChannelMessage
from app.channels.adapters.wechat_work.client import WeChatWorkClient
from app.chat.models.chat import Message
from typing import Dict, Any
import logging

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
    
    async def receive_message(self, raw_message: dict) -> ChannelMessage:
        """接收企业微信消息，转换为系统标准格式"""
        msg_type = raw_message.get("MsgType")
        from_user = raw_message.get("FromUserName")
        
        if msg_type == "text":
            content = raw_message.get("Content", "")
            return ChannelMessage(
                channel_type="wechat_work",
                channel_message_id=raw_message.get("MsgId"),
                channel_user_id=from_user,
                content={"text": content},
                message_type="text",
                timestamp=raw_message.get("CreateTime")
            )
        elif msg_type == "image":
            media_id = raw_message.get("MediaId")
            pic_url = raw_message.get("PicUrl", "")
            return ChannelMessage(
                channel_type="wechat_work",
                channel_message_id=raw_message.get("MsgId"),
                channel_user_id=from_user,
                content={
                    "media_info": {
                        "url": pic_url,
                        "media_id": media_id,
                        "mime_type": "image/jpeg"
                    }
                },
                message_type="media",
                timestamp=raw_message.get("CreateTime")
            )
        else:
            raise ValueError(f"不支持的消息类型: {msg_type}")
    
    async def send_message(self, message: Message, channel_user_id: str) -> bool:
        """发送消息到企业微信"""
        if message.type == "text":
            content = message.content.get("text", "")
            return await self.client.send_text_message(channel_user_id, content)
        elif message.type == "media":
            media_info = message.content.get("media_info", {})
            media_url = media_info.get("url")
            
            # 下载文件并上传到企业微信
            media_id = await self._upload_media_to_wechat(media_url)
            if media_id:
                return await self.client.send_image_message(channel_user_id, media_id)
            return False
        else:
            logger.warning(f"不支持的消息类型: {message.type}")
            return False
    
    async def validate_webhook(self, request: Request) -> bool:
        """验证企业微信 Webhook 请求"""
        # 企业微信使用 URL 参数验证
        msg_signature = request.query_params.get("msg_signature")
        timestamp = request.query_params.get("timestamp")
        nonce = request.query_params.get("nonce")
        echostr = request.query_params.get("echostr")
        
        # 实现签名验证逻辑
        # ...
        return True
    
    async def _upload_media_to_wechat(self, media_url: str) -> Optional[str]:
        """下载媒体文件并上传到企业微信"""
        # 1. 从 MinIO 下载文件
        # 2. 上传到企业微信
        # 3. 返回 media_id
        pass
```

### 4.2 Webhook 接收端点

```python
# api/app/channels/controllers/webhook.py
from fastapi import APIRouter, Request, HTTPException
from app.channels.services.channel_service import ChannelService

router = APIRouter()

@router.post("/webhook/wechat-work")
async def wechat_work_webhook(
    request: Request,
    channel_service: ChannelService = Depends(get_channel_service)
):
    """接收企业微信 Webhook 消息"""
    # 1. 验证请求
    adapter = channel_service.get_adapter("wechat_work")
    if not await adapter.validate_webhook(request):
        raise HTTPException(status_code=403, detail="验证失败")
    
    # 2. 解析消息
    body = await request.body()
    raw_message = parse_wechat_message(body)  # 解析 XML 或 JSON
    
    # 3. 转换为系统消息
    channel_message = await adapter.receive_message(raw_message)
    
    # 4. 创建或更新会话，保存消息
    await channel_service.process_incoming_message(channel_message)
    
    return {"errcode": 0, "errmsg": "ok"}
```

### 4.3 消息同步服务

```python
# api/app/channels/services/channel_service.py
from app.channels.interfaces import ChannelAdapter, ChannelMessage
from app.chat.services.chat_service import ChatService
from typing import Dict, Optional

class ChannelService:
    """渠道服务 - 统一管理所有渠道"""
    
    def __init__(self, db: Session):
        self.db = db
        self.adapters: Dict[str, ChannelAdapter] = {}
        self.chat_service = ChatService(db=db, broadcasting_service=None)
    
    def register_adapter(self, channel_type: str, adapter: ChannelAdapter):
        """注册渠道适配器"""
        self.adapters[channel_type] = adapter
    
    async def process_incoming_message(self, channel_message: ChannelMessage):
        """处理来自外部渠道的消息"""
        # 1. 查找或创建会话
        conversation = await self._get_or_create_conversation(channel_message)
        
        # 2. 创建消息
        message = self.chat_service.create_text_message(
            conversation_id=conversation.id,
            sender_id=channel_message.channel_user_id,  # 可能需要映射
            content=channel_message.content,
            sender_type="user"
        )
        
        # 3. 在 extra_metadata 中存储渠道信息
        message.extra_metadata = {
            "channel": {
                "type": channel_message.channel_type,
                "channel_message_id": channel_message.channel_message_id,
                "channel_user_id": channel_message.channel_user_id
            }
        }
        
        self.db.commit()
        
        # 4. 触发 WebSocket 广播
        # ...
    
    async def send_to_channel(
        self, 
        message: Message, 
        channel_type: str, 
        channel_user_id: str
    ) -> bool:
        """发送消息到外部渠道"""
        adapter = self.adapters.get(channel_type)
        if not adapter:
            raise ValueError(f"未找到渠道适配器: {channel_type}")
        
        return await adapter.send_message(message, channel_user_id)
```

## 5. 数据库迁移

创建渠道配置表的迁移文件：

```python
# api/alembic/versions/xxxx_add_channel_configs.py
def upgrade():
    op.create_table(
        'channel_configs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('channel_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('config', sa.JSON, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
```

## 6. 实施步骤

### Phase 1: 截图功能（1-2天）
1. ✅ 安装 `html2canvas` 依赖
2. ✅ 创建 `ScreenshotCapture` 组件
3. ✅ 集成到 `MessageInput` 组件
4. ✅ 测试截图和发送流程

### Phase 2: 渠道抽象层（2-3天）
1. ✅ 创建渠道接口定义
2. ✅ 创建 `ChannelService`
3. ✅ 创建数据库模型和迁移
4. ✅ 实现基础的消息路由

### Phase 3: 企业微信集成（3-5天）
1. ✅ 实现 `WeChatWorkClient`
2. ✅ 实现 `WeChatWorkAdapter`
3. ✅ 创建 Webhook 接收端点
4. ✅ 实现消息同步逻辑
5. ✅ 测试消息收发

### Phase 4: 优化和测试（2-3天）
1. ✅ 错误处理和重试机制
2. ✅ 日志和监控
3. ✅ 端到端测试
4. ✅ 性能优化

## 7. 技术选型

- **前端截图**：`html2canvas`（成熟稳定，支持复杂 DOM）
- **企业微信 SDK**：直接使用 HTTP API（更灵活，避免依赖）
- **异步处理**：FastAPI + httpx（原生异步支持）

## 8. 注意事项

1. **企业微信配置**：
   - 需要在企业微信管理后台配置可信域名
   - 配置 Webhook URL 和 Token
   - 获取 CorpID、AgentID、Secret

2. **消息去重**：
   - 使用 `channel_message_id` 防止重复处理

3. **用户映射**：
   - 需要建立企业微信用户ID与系统用户ID的映射关系

4. **媒体文件处理**：
   - 企业微信需要先上传媒体文件获取 `media_id`
   - 需要实现文件下载和上传的异步处理

5. **错误处理**：
   - 网络错误重试机制
   - 消息发送失败的回退策略

## 9. 未来扩展

- 支持更多消息类型（语音、视频、文件等）
- 接入其他渠道（微信、WhatsApp、Telegram等）
- 消息模板和自动化回复
- 渠道统计和分析

