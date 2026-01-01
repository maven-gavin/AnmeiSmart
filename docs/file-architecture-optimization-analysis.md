# 文件上传与访问架构优化分析

## 📋 优化目标

将文件存储方式从URL记录改为文件ID记录，通过API传递文件ID来访问所有文件和图片。

**当前架构**：

- 文件上传后返回URL（file_url），存储在数据库和消息中
- 前端直接使用URL访问文件
- 需要处理URL解析、权限验证等复杂逻辑

**目标架构**：

- 文件上传后返回文件ID（file_id）
- 数据库和消息中存储文件ID而非URL
- 前端通过文件ID调用API获取文件内容
- 统一的文件访问入口，便于权限控制和缓存管理

---

## 🔍 一、前端文件使用场景分析

### 1.1 数字人头像相关

#### 1.1.1 数字人头像上传

**文件位置**：`web/src/components/profile/DigitalHumanForm.tsx`

**当前实现**：

- 第170行：调用 `/files/upload-avatar` API上传头像
- 第175行：从响应中获取 `result?.file_info?.file_url`
- 第180行：将 `avatarUrl` 存储到 `submitData.avatar`

**需要改动**：

```typescript
// 当前
const avatarUrl = result?.file_info?.file_url as string | undefined;
submitData.avatar = avatarUrl;

// 改为
const fileId = result?.file_info?.file_id as string | undefined;
submitData.avatar = fileId; 
```

#### 1.1.2 数字人头像显示

**文件位置**：

- `web/src/components/admin/AdminDigitalHumanList.tsx`
- `web/src/components/profile/DigitalHumanList.tsx`
- `web/src/components/profile/DigitalHumanForm.tsx`
- `web/src/components/admin/AdminDigitalHumanDetail.tsx`
- `web/src/app/admin/digital-humans/page.tsx`

**当前实现**：

- 使用 `normalizeAvatarUrl(digitalHuman.avatar)` 处理头像URL
- 通过 `avatarUrl.ts` 工具函数归一化URL

**需要改动**：

```typescript
// 当前
<img src={normalizeAvatarUrl(digitalHuman.avatar)} />

// 改为
<img src={`/api/v1/files/${digitalHuman.avatar}/preview`} />
```

#### 1.1.3 数字人数据库模型

**文件位置**：`api/app/digital_humans/models/digital_human.py`

**需要改动**：

- `avatar` 字段从 `String(255)` 存储URL改为存储文件ID

---

### 1.2 用户头像相关

#### 1.2.1 用户头像上传

**文件位置**：`web/src/components/profile/BasicInfoPanel.tsx`

**当前实现**：

- 第140行：调用 `/files/upload-avatar` API上传头像
- 第145行：从响应中获取 `result?.file_info?.file_url`
- 第150行：将 `avatarUrl` 存储到 `updateData.avatar`

**需要改动**：同数字人头像上传

#### 1.2.2 用户头像显示

**文件位置**：

- `web/src/components/profile/BasicInfoPanel.tsx`
- `web/src/components/ui/AvatarCircle.tsx`
- `web/src/components/ui/avatar.tsx`
- 所有使用 `user.avatar` 的地方

**当前实现**：

- 使用 `normalizeAvatarUrl(user.avatar)` 处理头像URL

**需要改动**：同数字人头像显示

#### 1.2.3 用户数据库模型

**文件位置**：`api/app/identity_access/models/user.py`

**当前实现**：

- 第156行：`avatar = Column(String(255), nullable=True, comment="头像URL")`

**需要改动**：

- `avatar` 字段改为存储文件ID

---

### 1.3 智能沟通文件上传和显示

#### 1.3.1 图片上传发送

**文件位置**：`web/src/components/chat/MessageInput.tsx`

**当前实现**：

- 第228-343行：`sendImageMessage` 函数
- 上传文件后从响应获取 `file_info.file_url`
- 创建消息时使用 `media_info.url` 存储URL

**需要改动**：

```typescript
// 当前
const { data: result } = await apiClient.upload('/files/upload', formData);
const fileUrl = result.file_info.file_url;
media_info: {
  url: fileUrl,  // 存储URL
  ...
}

// 改为
const { data: result } = await apiClient.upload('/files/upload', formData);
const fileId = result.file_info.file_id;
media_info: {
  file_id: fileId,  // 存储文件ID
  ...
}
```

#### 1.3.2 文件上传发送

**文件位置**：`web/src/components/chat/MessageInput.tsx`

**当前实现**：

- 第346-462行：`sendFileMessage` 函数
- 使用 `file_info.file_url` 存储文件URL

**需要改动**：同图片上传

#### 1.3.3 录音上传发送

**文件位置**：`web/src/components/chat/MessageInput.tsx`

**当前实现**：

- 第465-579行：`sendAudioMessage` 函数
- 使用 `file_info.file_url` 存储文件URL

**需要改动**：同图片上传

#### 1.3.4 图片显示组件

**文件位置**：`web/src/components/chat/message/ImageMessage.tsx`

**当前实现**：

- 第44行：从 `mediaContent.media_info.url` 提取URL
- 第47-80行：解析URL获取object_name
- 第110行：使用 `FileService.getFilePreviewStream(objectName)` 获取文件流

**需要改动**：

```typescript
// 当前
const mediaUrl = mediaContent?.media_info?.url;
const objectName = extractObjectName(mediaUrl);
const blob = await fileService.getFilePreviewStream(objectName);

// 改为
const fileId = mediaContent?.media_info?.file_id;
const blob = await fileService.getFileById(fileId);
```

#### 1.3.5 文件显示组件

**文件位置**：`web/src/components/chat/message/FileMessage.tsx`

**当前实现**：

- 使用 `media_info.url` 获取文件信息
- 通过URL调用下载/预览API

**需要改动**：

- 使用 `media_info.file_id` 替代URL
- 通过文件ID调用API

#### 1.3.6 语音显示组件

**文件位置**：`web/src/components/chat/message/VoiceMessage.tsx`

**需要改动**：同文件显示组件

#### 1.3.7 媒体消息类型定义

**文件位置**：`web/src/types/chat.ts`

**当前实现**：

```typescript
export type MediaInfo = {
  url: string;
  name: string;
  mime_type: string;
  size_bytes: number;
  metadata?: Record<string, any>;
};
```

**需要改动**：

```typescript
export type MediaInfo = {
  file_id: string;  // 新增：文件ID（必需）
  name: string;
  mime_type: string;
  size_bytes: number;
  metadata?: Record<string, any>;
};
```

---

### 1.4 智能体聊天文件上传

#### 1.4.1 Agent文件上传到Dify

**文件位置**：

- `web/src/components/agents/UserInputForm.tsx`
- `web/src/service/agentFileService.ts`

**当前实现**：

- 文件上传到Dify，返回Dify的文件ID（`upload_file_id`）
- 已经是使用文件ID的方式，**无需改动**

**说明**：Agent文件上传功能已经使用文件ID（Dify的文件ID），不需要改动。

---

### 1.5 其他文件使用场景

#### 1.5.1 文件管理器

**文件位置**：`web/src/components/chat/FileManager.tsx`

**需要改动**：

- 文件列表API返回文件ID
- 显示时通过文件ID获取文件信息

#### 1.5.2 文件选择器

**文件位置**：`web/src/components/chat/FileSelector.tsx`

**需要改动**：

- 上传后返回文件ID
- 预览/下载使用文件ID

---

## 🔧 二、后端代码分析

### 2.1 文件上传API

#### 2.1.1 普通文件上传

**文件位置**：`api/app/common/controllers/files.py`

**当前实现**：

- 第32-83行：`upload_file` 端点
- 调用 `file_service.upload_file()` 返回 `file_info_dict`
- 返回的 `FileUploadResponse` 包含 `file_info.file_url`

**需要改动**：

```python
# 当前
file_info_dict = await file_service.upload_file(...)
# file_info_dict 包含 file_url

# 改为
file_info_dict = await file_service.upload_file(...)
# file_info_dict 包含 file_id，不再包含 file_url
```

#### 2.1.2 头像上传

**文件位置**：`api/app/common/controllers/files.py`

**当前实现**：

- 第86-116行：`upload_avatar` 端点
- 返回 `file_info.file_url`（通过 `url_for("public_file")` 生成）

**需要改动**：

- 返回文件ID而非URL

#### 2.1.3 文件服务层

**文件位置**：`api/app/common/services/file_service.py`

**当前实现**：

- 第532-634行：`upload_file` 方法
- 第636-679行：`upload_avatar` 方法
- 返回字典包含 `file_url`、`object_name` 等

**需要改动**：

1. **创建文件记录表**（如果不存在）：
   - 表名：`files`
   - 字段：`id`（文件ID，主键）、`object_name`、`file_name`、`file_size`、`mime_type`、`user_id`、`created_at`、md5等
2. **修改上传方法**：
   - 上传文件后创建文件记录
   - 返回文件ID而非URL
   - 保留object_name用于实际存储

---

### 2.2 文件访问API

#### 2.2.1 文件预览API

**文件位置**：`api/app/common/controllers/files.py`

**当前实现**：

- 第201-283行：`preview_file` 端点
- 通过 `object_name` 参数访问文件

**需要改动**：

```python
# 当前
@router.get("/preview/{object_name:path}")
async def preview_file(object_name: str, ...)

# 改为
@router.get("/files/{file_id}/preview")
async def preview_file(file_id: str, ...)
```

#### 2.2.2 文件下载API

**文件位置**：`api/app/common/controllers/files.py`

**当前实现**：

- 第153-198行：`download_file` 端点
- 通过 `object_name` 参数访问文件

**需要改动**：同预览API

#### 2.2.3 公共文件访问

**文件位置**：`api/app/common/controllers/files.py`

**当前实现**：

- 第119-150行：`public_file` 端点
- 用于头像等公共资源访问

**需要改动**：

```python
# 当前
@router.get("/public/{object_name:path}", name="public_file")

# 改为
@router.get("/files/{file_id}/public")
```

---

### 2.3 文件服务层方法

#### 2.3.1 文件访问方法

**文件位置**：`api/app/common/services/file_service.py`

**需要新增方法**：

```python
def get_file_by_id(self, file_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """根据文件ID获取文件信息"""
    # 从files表查询文件记录
    # 返回文件信息和object_name

def get_file_stream_by_id(self, file_id: str, db: Session) -> Optional[Iterator[bytes]]:
    """根据文件ID获取文件流"""
    file_record = self.get_file_by_id(file_id, db)
    if file_record:
        return self.get_file_stream(file_record['object_name'])
    return None

def can_access_file_by_id(self, file_id: str, user_id: str, db: Session) -> bool:
    """检查用户是否有权限访问文件（通过文件ID）"""
    file_record = self.get_file_by_id(file_id, db)
    if file_record:
        return self.can_access_file(file_record['object_name'], user_id, db)
    return False
```

---

### 2.4 消息模型

#### 2.4.1 Message模型

**文件位置**：`api/app/chat/models/chat.py`

**当前实现**：

- `content` 字段为JSON类型
- 媒体消息的content中包含 `media_info.url`

**需要改动**：

- Schema层：媒体消息content中的 `media_info`.url 改为使用 `media_info.file_id`
- 数据库迁移：现有数据需要迁移（URL -> 文件ID）
- 同步调整“创建媒体消息”请求与服务实现：把 `media_url` 入参改为 `file_id`（后端用 `file_id` 查 `files.object_name` 后再流式/下载），并同步前端 `ChatApiService.createMediaMessage` 的请求字段

---

### 2.5 数据库模型

#### 2.5.1 用户模型

**文件位置**：`api/app/identity_access/models/user.py`

**需要改动**：

- `avatar` 字段改为存储文件ID

#### 2.5.2 数字人模型

**文件位置**：`api/app/digital_humans/models/digital_human.py`

**需要改动**：同用户模型

#### 2.5.3 文件表（新增）

**需要创建新表**：

```python
class File(BaseModel):
    """文件表 - 统一管理所有文件"""
    __tablename__ = "files"
  
    id = Column(String(36), primary_key=True, comment="文件ID")
    object_name = Column(String(500), nullable=False, unique=True, comment="MinIO对象名")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_size = Column(BigInteger, nullable=False, comment="文件大小")
    mime_type = Column(String(100), nullable=False, comment="MIME类型")
    file_type = Column(String(50), nullable=False, comment="文件类型：image/document/audio/video")
    md5 = Column(String(50), nullable=False, comment="MD5")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="上传用户ID")
    business_type = Column(String(50), nullable=True, comment="业务类型：avatar/message/document")
    business_id = Column(String(36), nullable=True, comment="关联业务对象ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
  
    # 索引
    __table_args__ = (
        Index('idx_file_user_id', 'user_id'),
        Index('idx_file_business', 'business_type', 'business_id'),
        Index('idx_file_object_name', 'object_name'),
    )
```

#### 2.5.4 现有上传相关表的关系说明

**upload_sessions表**（已存在）：

- **用途**：管理文件的分片上传会话（断点续传功能）
- **关键字段**：
  - `upload_id`：上传会话的唯一标识
  - `final_object_name`：合并后的文件在MinIO中的对象名
  - `status`：上传状态（uploading/completed/failed/cancelled）
  - `business_type`、`business_id`：业务上下文
- **当前使用**：主要用于大文件的断点续传场景
- **与files表的关系**：
  - `upload_sessions.final_object_name` 对应 `files.object_name`
  - 断点续传完成后，应创建files表记录（**files 不保存 upload_id，仅通过 object_name 可追溯**）

**message_attachments表**（已存在）：

- **历史表，准备删除**（当前代码未实际使用；本方案移除该表，见下文 3.2.4）

**最终方案**：

- `files`：唯一文件信息源（业务侧只存 `file_id`）
- `upload_sessions`：仅用于断点续传“过程态”，完成后落一条 `files` 记录（files 不保存 upload_id）
- `message_attachments`：移除（当前代码未使用，且与目标“消息只存file_id”重复）

---

## 📊 三、数据库结构变更

### 3.1 新增文件表

**表名**：`files`

**字段设计**：

- `id` (VARCHAR(36), PRIMARY KEY) - 文件ID（UUID）
- `object_name` (VARCHAR(500), UNIQUE, NOT NULL) - MinIO对象名
- `file_name` (VARCHAR(255), NOT NULL) - 原始文件名
- `file_size` (BIGINT, NOT NULL) - 文件大小（字节）
- `mime_type` (VARCHAR(100), NOT NULL) - MIME类型
- `file_type` (VARCHAR(50), NOT NULL) - 文件类型
- md5(VARCHAR(50), NOT NULL) - MD5
- `user_id` (VARCHAR(36), FK, NOT NULL) - 上传用户ID
- `business_type` (VARCHAR(50), NULL) - 业务类型
- `business_id` (VARCHAR(36), NULL) - 关联业务对象ID
- `created_at` (TIMESTAMP, NOT NULL) - 创建时间
- `updated_at` (TIMESTAMP, NOT NULL) - 更新时间

**索引**：

- PRIMARY KEY (id)
- UNIQUE INDEX (object_name)
- INDEX (user_id)
- INDEX (business_type, business_id)

### 3.2 修改现有表

#### 3.2.1 users表

- `avatar` 字段：含义从URL改为文件ID

#### 3.2.2 digital_humans表

- `avatar` 字段：含义从URL改为文件ID

#### 3.2.3 messages表

- `content` JSON字段：`media_info.url` 改为 `media_info.file_id`

#### 3.2.4 message_attachments表（移除）

**当前状态**：表已存在，但代码中未实际使用

**决策**：移除该表

**需要改动**：

- 删除 `message_attachments` 表（DDL/迁移）
- 同步移除后端 `Message.attachments` 关系与相关 ORM 模型（避免残留依赖）

#### 3.2.5 upload_sessions表（保持不变）

**当前状态**：用于断点续传功能

**需要改动**：

- 无需修改表结构
- 在上传完成后，需要创建files表记录
- 不在files表中保存 `upload_id/upload_session_id`，追溯依赖 `files.object_name` ↔ `upload_sessions.final_object_name`

### 3.3 数据迁移

需要编写迁移脚本：

1. **创建 `files` 表**
2. **迁移upload_sessions中的数据**：
   - 对于status='completed'的upload_sessions，根据final_object_name创建files记录
   - files.object_name = upload_sessions.final_object_name
   - 不记录 upload_id 到 files（按 object_name 可追溯）
3. **迁移messages中的文件数据**：
   - 解析messages.content JSON中的media_info.url
   - 从URL中提取object_name
   - 查找或创建对应的files记录
   - 更新messages.content中的media_info.url为file_id
4. **迁移头像数据**：
   - 从users.avatar和digital_humans.avatar的URL中提取object_name
   - 查找或创建对应的files记录
   - 更新users.avatar和digital_humans.avatar为文件ID
5. （本方案移除 `message_attachments` 表，无需迁移该表数据）

---

## 🔄 四、API变更

### 4.1 文件上传API响应变更

**当前响应**：

```json
{
  "success": true,
  "message": "文件上传成功",
  "file_info": {
    "file_url": "http://...",
    "file_name": "...",
    "file_size": 12345,
    "file_type": "image",
    "mime_type": "image/jpeg",
    "object_name": "..."
  }
}
```

**新响应**：

```json
{
  "success": true,
  "message": "文件上传成功",
  "file_info": {
    "file_id": "file_xxx",
    "file_name": "...",
    "file_size": 12345,
    "file_type": "image",
    "mime_type": "image/jpeg",
    "url": "/api/v1/files/file_xxx/preview"
  }
}
```

说明：

- `url` 属于 **派生字段**（便于前端直接用），但业务数据库与消息体中 **只存 `file_id`**，不落库 `url`

### 4.2 文件访问API变更

**当前**：

- `GET /files/preview/{object_name:path}`
- `GET /files/download/{object_name:path}`

**新API**：

- `GET /files/{file_id}/preview`
- `GET /files/{file_id}/download`
- `GET /files/{file_id}/info` - 获取文件信息

### 4.3 Schema变更

**文件位置**：`api/app/common/schemas/file.py`

**需要修改**：

- `FileInfo` 模型：`file_url` 改为 `file_id`
- 所有使用 `FileInfo` 的地方

---

## 📝 五、改动清单总结

### 5.1 前端改动清单

#### 核心组件

- [ ] `web/src/components/profile/DigitalHumanForm.tsx` - 数字人头像上传
- [ ] `web/src/components/profile/BasicInfoPanel.tsx` - 用户头像上传
- [ ] `web/src/components/chat/MessageInput.tsx` - 文件/图片/录音上传
- [ ] `web/src/components/chat/message/ImageMessage.tsx` - 图片显示
- [ ] `web/src/components/chat/message/FileMessage.tsx` - 文件显示
- [ ] `web/src/components/chat/message/VoiceMessage.tsx` - 语音显示
- [ ] `web/src/components/chat/message/MediaMessage.tsx` - 媒体消息路由

#### 显示组件

- [ ] `web/src/components/admin/AdminDigitalHumanList.tsx`
- [ ] `web/src/components/profile/DigitalHumanList.tsx`
- [ ] `web/src/components/admin/AdminDigitalHumanDetail.tsx`
- [ ] `web/src/components/ui/AvatarCircle.tsx`
- [ ] `web/src/components/ui/avatar.tsx`
- [ ] `web/src/components/chat/FileManager.tsx`
- [ ] `web/src/components/chat/FileSelector.tsx`

#### 类型定义

- [ ] `web/src/types/chat.ts` - MediaInfo类型
- [ ] `web/src/types/digital-human.ts` - 数字人类型
- [ ] `web/src/types/auth.ts` - 用户类型

#### 服务层

- [ ] `web/src/service/fileService.ts` - 文件服务方法
- [ ] `web/src/service/chat/api.ts` - 消息API
- [ ] `web/src/utils/avatarUrl.ts` - 头像URL工具（可能需要重构）

### 5.2 后端改动清单

#### 控制器

- [ ] `api/app/common/controllers/files.py` - 文件API端点
- [ ] `api/app/ai/controllers/agent_chat.py` - Agent文件上传（已使用ID，无需改动）

#### 服务层

- [ ] `api/app/common/services/file_service.py` - 文件服务方法

#### 模型

- [ ] `api/app/common/models/file.py` - 新增File模型
- [ ] `api/app/identity_access/models/user.py` - 用户模型
- [ ] `api/app/digital_humans/models/digital_human.py` - 数字人模型
- [ ] `api/app/chat/models/message_attachment.py` - 消息附件模型（不需要，可以删除）
- [ ] `api/app/common/models/upload.py` - UploadSession模型（保持不变，但完成后需创建files记录）

#### Schema

- [ ] `api/app/common/schemas/file.py` - 文件Schema

#### 数据库迁移

- [ ] 创建files表的迁移
- [ ] 数据迁移脚本：
  - [ ] upload_sessions -> files（已完成的上传会话）
  - [ ] messages.content中的URL -> file_id
  - [ ] users.avatar和digital_humans.avatar的URL -> file_id

### 5.3 文档更新

- [ ] 更新API文档
- [ ] 更新架构文档
- [ ] 更新开发指南

---

## ⚠️ 六、注意事项

### 6.1 不要向后兼容

### 6.2 数据迁移

- 需要处理历史数据迁移：
  - upload_sessions表中已完成的上传需要创建files记录
  - messages.content中的URL需要转换为file_id
  - users和digital_humans的头像URL需要转换为file_id
- 对于无法找到对应文件的URL，需要标记为无效或清理
- 注意：upload_sessions中的object_name可能与messages.content中的URL格式不同，需要统一处理

### 6.3 性能考虑

- 文件ID访问需要额外一次数据库查询
- 考虑缓存文件信息

### 6.4 权限控制

- 文件访问权限验证逻辑需要调整
- 通过文件ID验证权限

### 6.5 测试覆盖

- 文件上传功能测试
- 文件访问功能测试
- 权限验证测试
- 数据迁移测试

---

## 🎯 七、实施建议

### 7.1 分阶段实施

**第一阶段**：基础设施

1. 创建files表
2. 实现文件服务层的基础方法（创建文件记录、根据file_id查询等）
3. 实现新的文件访问API（通过file_id）
4. 确定 `upload_sessions` 的定位（仅断点续传过程态）以及 `message_attachments`（移除）

**第二阶段**：新数据使用ID

1. 修改文件上传API返回文件ID
2. 前端新上传的文件使用文件ID
3. 新消息使用文件ID存储

**第三阶段**：历史数据迁移

1. 编写数据迁移脚本
2. 迁移现有数据
3. 验证迁移结果

**第四阶段**：全面切换

1. 修改所有显示组件使用文件ID
2. 移除URL相关代码
3. 清理旧代码

### 7.2 风险评估

- 数据迁移风险：需要充分测试
- 性能风险：增加数据库查询，需要优化
- 数据一致性风险：迁移过程中 URL->file_id 映射不完整/重复，需要兜底策略与校验
