# Schema架构重构 - 领域分离

## 重构背景

之前的 `chat.py` Schema文件违反了DDD（领域驱动设计）原则，将聊天、文件、WebSocket等不同领域的数据模型混合在一起，导致：

1. **职责不清**: 一个文件包含多个领域的模型
2. **耦合度高**: 不同功能的Schema混在一起
3. **维护困难**: 修改某个领域的模型可能影响其他领域
4. **扩展性差**: 难以独立扩展某个特定领域

## 重构目标

遵循DDD原则，按照业务领域对Schema进行分离：

- **chat.py**: 纯粹的聊天领域（消息、会话）
- **file.py**: 文件领域（上传、管理、断点续传）
- **websocket.py**: WebSocket领域（连接、消息传输）

## 重构内容

### 1. 创建文件领域Schema (`app/schemas/file.py`)

包含所有文件相关的数据模型：

```python
# 基础文件模型
- FileInfo: 文件基本信息
- FileUploadResponse: 文件上传响应
- FileUploadRequest: 文件上传请求

# 断点续传相关
- ChunkUploadRequest: 分片上传请求
- UploadStatusResponse: 上传状态响应  
- CompleteUploadRequest: 完成上传请求
- ResumableUploadInfo: 断点续传信息
- StartResumableUploadRequest: 开始断点续传请求
- StartResumableUploadResponse: 开始断点续传响应
- CancelUploadResponse: 取消上传响应
```

### 2. 创建WebSocket领域Schema (`app/schemas/websocket.py`)

包含WebSocket相关的数据模型：

```python
- WebSocketMessage: WebSocket消息模型
- WebSocketConnectionInfo: 连接信息模型
- WebSocketError: 错误模型
- WebSocketStats: 统计信息模型
```

**注意**: 当前项目主要使用前端WebSocket客户端，后端Schema暂时保留供将来扩展使用。

### 3. 精简聊天领域Schema (`app/schemas/chat.py`)

只保留纯粹的聊天相关模型：

```python
# 消息相关
- MessageSender: 消息发送者信息
- MessageBase: 消息基础模型
- MessageCreate: 创建消息请求
- MessageCreateRequest: HTTP API创建消息请求
- AIChatRequest: AI聊天请求
- MessageInfo: 消息完整模型

# 会话相关  
- ConversationBase: 会话基础模型
- ConversationCreate: 创建会话请求
- ConversationInfo: 会话完整模型
```

### 4. 统一Schema导入管理 (`app/schemas/__init__.py`)

创建统一的Schema包初始化文件，按领域组织导入：

```python
# 聊天领域
from .chat import (MessageSender, MessageInfo, ...)

# 文件领域
from .file import (FileInfo, FileUploadResponse, ...)

# WebSocket领域
from .websocket import (WebSocketMessage, ...)
```

## 文件变更清单

### 新增文件
- `api/app/schemas/file.py` - 文件领域Schema
- `api/app/schemas/websocket.py` - WebSocket领域Schema
- `api/app/schemas/__init__.py` - Schema包初始化

### 修改文件
- `api/app/schemas/chat.py` - 移除文件和WebSocket相关Schema
- `api/app/api/v1/endpoints/files.py` - 更新导入引用

### 导入变更

**修改前**:
```python
from app.schemas.chat import FileUploadResponse, ChunkUploadRequest
```

**修改后**:
```python
from app.schemas.file import FileUploadResponse, ChunkUploadRequest
from app.schemas.chat import MessageInfo
```

## 兼容性保证

通过 `app/schemas/__init__.py` 文件，保证现有代码可以通过以下方式导入：

```python
# 方式1: 直接从对应领域导入
from app.schemas.file import FileUploadResponse
from app.schemas.chat import MessageInfo

# 方式2: 从schemas包导入（推荐）
from app.schemas import FileUploadResponse, MessageInfo
```

## 设计原则

### 1. 单一职责原则 (SRP)
每个Schema文件只负责一个业务领域的数据模型定义。

### 2. 开闭原则 (OCP)
- 对扩展开放：可以在任何领域添加新的Schema
- 对修改封闭：修改某个领域不影响其他领域

### 3. 依赖倒置原则 (DIP)
- 聊天领域可以依赖文件领域（文件消息需要FileInfo）
- 文件领域不依赖聊天领域
- WebSocket领域独立，不依赖其他领域

### 4. 接口隔离原则 (ISP)
每个API端点只导入它需要的Schema，不导入不相关的模型。

## 未来扩展建议

### 1. 用户领域Schema
当用户相关功能复杂化时，可以创建独立的 `user.py` Schema文件。

### 2. 支付领域Schema
如果需要支付功能，可以创建独立的 `payment.py` Schema文件。

### 3. 通知领域Schema
如果需要复杂的通知功能，可以创建独立的 `notification.py` Schema文件。

## 测试验证

### 1. 导入测试
```bash
cd api
source venv/bin/activate
python -c "from app.schemas import FileUploadResponse, MessageInfo; print('导入成功')"
```

### 2. 服务启动测试
```bash
source venv/bin/activate
python -c "from app.api.v1.endpoints.files import router; print('文件端点正常')"
```

### 3. 功能测试
按照 [文件上传功能测试指南](./文件上传功能测试指南.md) 进行完整的功能测试。

## 总结

这次重构实现了：

1. ✅ **领域分离**: 按业务领域组织Schema文件
2. ✅ **职责明确**: 每个文件只负责一个领域
3. ✅ **依赖清晰**: 明确的依赖关系和导入规则
4. ✅ **扩展性强**: 易于添加新领域和新功能
5. ✅ **向后兼容**: 现有代码无需修改即可正常工作

重构后的架构更加符合DDD原则，为系统的长期维护和扩展奠定了良好的基础。 