# 安美智能咨询系统数据库设计文档

## 概述

本文档描述了安美智能咨询系统的完整数据库设计，包括所有表结构、字段定义、关系映射和索引设计。系统采用PostgreSQL数据库，使用SQLAlchemy ORM框架进行数据访问。

## 数据库架构

### 核心设计原则

1. **分层架构**：采用用户-角色-扩展表的分离设计
2. **统一标识**：使用带前缀的UUID作为主键
3. **时间戳管理**：所有表都包含创建和更新时间戳
4. **软删除支持**：通过状态字段而非物理删除
5. **JSON扩展性**：使用JSON字段存储复杂数据结构
6. **加密存储**：敏感数据（如API密钥）使用Fernet对称加密
7. **模块化设计**：按业务功能分离表结构，支持微服务架构

### 表关系图

```
用户管理模块:
users ←→ user_roles ←→ roles
  ↓
  ├── customers
  ├── operators
  ├── admins
  └── digital_humans

聊天模块:
conversations ←→ messages ←→ message_attachments
  ↓                    ↓
  └── conversation_participants  upload_sessions ←→ upload_chunks

通讯录模块:
friendships ←→ friendship_tags ←→ contact_tags
  ↓
  └── contact_groups ←→ contact_group_members

系统配置模块:
system_settings ←→ ai_model_configs
  ↓
  └── agent_configs

MCP工具模块:
mcp_tool_groups ←→ mcp_tools
  ↓
  └── mcp_call_logs

数字人模块:
digital_humans ←→ digital_human_agent_configs
  ↓
  └── consultation_records ←→ pending_tasks

个人中心模块:
user_preferences
user_default_roles
login_history

运营业务模块:
project_types
simulation_images
project_templates
customer_preferences
```

## 详细表结构

### 1. 用户管理模块

#### 1.1 角色表 (roles)

| 字段名      | 数据类型    | 约束             | 默认值            | 说明                 |
| ----------- | ----------- | ---------------- | ----------------- | -------------------- |
| id          | VARCHAR(36) | PRIMARY KEY      | role_xxx          | 角色ID（带前缀UUID） |
| name        | VARCHAR     | UNIQUE, NOT NULL | -                 | 角色名称             |
| description | VARCHAR     | NULL             | -                 | 角色描述             |
| created_at  | TIMESTAMP   | NOT NULL         | CURRENT_TIMESTAMP | 创建时间             |
| updated_at  | TIMESTAMP   | NOT NULL         | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (name)

#### 1.2 用户表 (users)

| 字段名          | 数据类型    | 约束             | 默认值            | 说明                 |
| --------------- | ----------- | ---------------- | ----------------- | -------------------- |
| id              | VARCHAR(36) | PRIMARY KEY      | usr_xxx           | 用户ID（带前缀UUID） |
| email           | VARCHAR     | UNIQUE, NOT NULL | -                 | 邮箱地址             |
| username        | VARCHAR     | UNIQUE, NOT NULL | -                 | 用户名               |
| hashed_password | VARCHAR     | NOT NULL         | -                 | 加密密码             |
| phone           | VARCHAR     | UNIQUE           | NULL              | 手机号               |
| avatar          | VARCHAR     | NULL             | -                 | 头像URL              |
| is_active       | BOOLEAN     | NOT NULL         | TRUE              | 是否激活             |
| created_at      | TIMESTAMP   | NOT NULL         | CURRENT_TIMESTAMP | 创建时间             |
| updated_at      | TIMESTAMP   | NOT NULL         | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (email)
- UNIQUE INDEX (username)
- UNIQUE INDEX (phone)

#### 1.3 用户角色关联表 (user_roles)

| 字段名      | 数据类型    | 约束            | 默认值            | 说明     |
| ----------- | ----------- | --------------- | ----------------- | -------- |
| user_id     | VARCHAR(36) | PRIMARY KEY, FK | -                 | 用户ID   |
| role_id     | VARCHAR(36) | PRIMARY KEY, FK | -                 | 角色ID   |
| assigned_at | TIMESTAMP   | NOT NULL        | CURRENT_TIMESTAMP | 分配时间 |

**索引：**

- PRIMARY KEY (user_id, role_id)
- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
- FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE

#### 1.6 运营人员扩展表 (operators)

| 字段名           | 数据类型    | 约束                 | 默认值            | 说明     |
| ---------------- | ----------- | -------------------- | ----------------- | -------- |
| id               | VARCHAR(36) | PRIMARY KEY          | -                 | 记录ID   |
| user_id          | VARCHAR(36) | UNIQUE, FK, NOT NULL | -                 | 用户ID   |
| department       | VARCHAR     | NULL                 | -                 | 所属部门 |
| responsibilities | TEXT        | NULL                 | -                 | 职责描述 |
| created_at       | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 创建时间 |
| updated_at       | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 更新时间 |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (user_id)
- FOREIGN KEY (user_id) REFERENCES users(id)

#### 1.7 管理员扩展表 (admins)

| 字段名             | 数据类型    | 约束                 | 默认值            | 说明       |
| ------------------ | ----------- | -------------------- | ----------------- | ---------- |
| id                 | VARCHAR(36) | PRIMARY KEY          | -                 | 记录ID     |
| user_id            | VARCHAR(36) | UNIQUE, FK, NOT NULL | -                 | 用户ID     |
| admin_level        | VARCHAR     | NOT NULL             | 'basic'           | 管理员级别 |
| access_permissions | TEXT        | NULL                 | -                 | 权限描述   |
| created_at         | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 创建时间   |
| updated_at         | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 更新时间   |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (user_id)
- FOREIGN KEY (user_id) REFERENCES users(id)

### 2. 客户管理模块

#### 2.1 客户扩展表 (customers)

| 字段名          | 数据类型    | 约束                 | 默认值            | 说明     |
| --------------- | ----------- | -------------------- | ----------------- | -------- |
| id              | VARCHAR(36) | PRIMARY KEY          | -                 | 记录ID   |
| user_id         | VARCHAR(36) | UNIQUE, FK, NOT NULL | -                 | 用户ID   |
| medical_history | TEXT        | NULL                 | -                 | 病史     |
| allergies       | TEXT        | NULL                 | -                 | 过敏史   |
| preferences     | TEXT        | NULL                 | -                 | 偏好     |
| created_at      | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 创建时间 |
| updated_at      | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 更新时间 |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (user_id)
- FOREIGN KEY (user_id) REFERENCES users(id)

#### 2.2 客户档案表 (customer_profiles)

| 字段名          | 数据类型    | 约束                 | 默认值            | 说明                 |
| --------------- | ----------- | -------------------- | ----------------- | -------------------- |
| id              | VARCHAR(36) | PRIMARY KEY          | prof_xxx          | 档案ID               |
| customer_id     | VARCHAR(36) | UNIQUE, FK, NOT NULL | -                 | 客户用户ID           |
| medical_history | TEXT        | NULL                 | -                 | 病史                 |
| allergies       | TEXT        | NULL                 | -                 | 过敏史（JSON字符串） |
| preferences     | TEXT        | NULL                 | -                 | 偏好                 |
| tags            | TEXT        | NULL                 | -                 | 标签（JSON字符串）   |
| risk_notes      | JSON        | NULL                 | -                 | 风险提示信息         |
| created_at      | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 创建时间             |
| updated_at      | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (customer_id)
- FOREIGN KEY (customer_id) REFERENCES customers(user_id)

### 3. 聊天模块

#### 3.1 会话表 (conversations)

| 字段名                 | 数据类型    | 约束         | 默认值            | 说明             |
| ---------------------- | ----------- | ------------ | ----------------- | ---------------- |
| id                       | VARCHAR(36) | PRIMARY KEY  | conv_xxx          | 会话ID               |
| title                    | VARCHAR     | NOT NULL     | -                 | 会话标题             |
| chat_mode                | VARCHAR(50) | NOT NULL     | 'single'          | 会话模式：单聊、群聊 |
| owner_id                 | VARCHAR(36) | FK, NOT NULL | -                 | 会话所有者用户ID     |
| tag                      | VARCHAR(50) | NOT NULL     | 'chat'            | 会话标签：chat(普通聊天)、consultation(咨询会话) |
| is_pinned                | BOOLEAN     | NOT NULL     | FALSE             | 是否置顶             |
| pinned_at                | TIMESTAMP   | NULL         | -                 | 置顶时间             |
| first_participant_id     | VARCHAR(36) | FK           | NULL              | 第一个参与者用户ID   |
| is_active                | BOOLEAN     | NOT NULL     | TRUE              | 会话是否激活         |
| is_archived              | BOOLEAN     | NOT NULL     | FALSE             | 是否已归档           |
| message_count            | INTEGER     | NOT NULL     | 0                 | 消息总数             |
| unread_count             | INTEGER     | NOT NULL     | 0                 | 未读消息数           |
| last_message_at          | TIMESTAMP   | NULL         | -                 | 最后消息时间         |
| created_at             | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 创建时间         |
| updated_at             | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 更新时间         |

**索引：**

- PRIMARY KEY (id)
- INDEX (owner_id)
- INDEX (chat_mode)
- INDEX (is_active)
- INDEX (tag)
- INDEX (is_pinned, pinned_at)
- INDEX (first_participant_id)
- FOREIGN KEY (owner_id) REFERENCES users(id)
- FOREIGN KEY (first_participant_id) REFERENCES users(id)


* “结构化咨询总结"、”会话简短摘要"，“是否由AI控制" 三个字段不需要

#### 3.2 消息表 (messages)

| 字段名              | 数据类型    | 约束         | 默认值            | 说明           |
| ------------------- | ----------- | ------------ | ----------------- | -------------- |
| id                  | VARCHAR(36) | PRIMARY KEY  | msg_xxx           | 消息ID         |
| conversation_id     | VARCHAR(36) | FK, NOT NULL | -                 | 会话ID         |
| content             | JSON        | NOT NULL     | -                 | 结构化消息内容 |
| type                | ENUM        | NOT NULL     | -                 | 消息主类型     |
| sender_id           | VARCHAR(36) | FK           | NULL              | 发送者用户ID   |
| sender_digital_human_id | VARCHAR(36) | FK           | NULL              | 发送者数字人ID |
| sender_type         | ENUM        | NOT NULL     | -                 | 发送者类型     |
| is_read             | BOOLEAN     | NOT NULL     | FALSE             | 是否已读       |
| is_important        | BOOLEAN     | NOT NULL     | FALSE             | 是否重要       |
| timestamp           | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 消息时间戳     |
| requires_confirmation | BOOLEAN     | NOT NULL     | FALSE             | 是否需要确认（半接管模式） |
| is_confirmed        | BOOLEAN     | NOT NULL     | TRUE              | 是否已确认     |
| confirmed_by        | VARCHAR(36) | FK           | NULL              | 确认人ID       |
| confirmed_at        | TIMESTAMP   | NULL         | -                 | 确认时间       |
| reply_to_message_id | VARCHAR(36) | FK           | NULL              | 回复的消息ID   |
| reactions           | JSON        | NULL         | -                 | 消息回应       |
| extra_metadata      | JSON        | NULL         | -                 | 附加元数据     |
| created_at          | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 创建时间       |
| updated_at          | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 更新时间       |

**索引：**

- PRIMARY KEY (id)
- INDEX (conversation_id)
- INDEX (type)
- INDEX (sender_id)
- INDEX (sender_digital_human_id)
- INDEX (timestamp)
- FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
- FOREIGN KEY (sender_id) REFERENCES users(id)
- FOREIGN KEY (sender_digital_human_id) REFERENCES digital_humans(id)
- FOREIGN KEY (reply_to_message_id) REFERENCES messages(id)
- FOREIGN KEY (confirmed_by) REFERENCES users(id)

### 4. 通讯录模块

#### 4.1 好友关系表 (friendships)

| 字段名                 | 数据类型    | 约束         | 默认值            | 说明                 |
| ---------------------- | ----------- | ------------ | ----------------- | -------------------- |
| id                     | VARCHAR(36) | PRIMARY KEY  | friendship_xxx    | 好友关系ID           |
| user_id                | VARCHAR(36) | FK, NOT NULL | -                 | 用户ID               |
| friend_id              | VARCHAR(36) | FK, NOT NULL | -                 | 好友用户ID           |
| status                 | VARCHAR(20) | NOT NULL     | 'pending'         | 好友状态             |
| nickname               | VARCHAR(100)| NULL         | -                 | 给好友设置的昵称     |
| remark                 | TEXT        | NULL         | -                 | 好友备注             |
| source                 | VARCHAR(50) | NULL         | -                 | 添加来源             |
| is_starred             | BOOLEAN     | NOT NULL     | FALSE             | 是否星标好友         |
| is_muted               | BOOLEAN     | NOT NULL     | FALSE             | 是否免打扰           |
| is_pinned              | BOOLEAN     | NOT NULL     | FALSE             | 是否置顶显示         |
| is_blocked             | BOOLEAN     | NOT NULL     | FALSE             | 是否已屏蔽           |
| requested_at           | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 请求时间             |
| accepted_at            | TIMESTAMP   | NULL         | -                 | 接受时间             |
| last_interaction_at    | TIMESTAMP   | NULL         | -                 | 最后互动时间         |
| interaction_count      | INTEGER     | NOT NULL     | 0                 | 互动次数             |
| created_at             | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 创建时间             |
| updated_at             | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- INDEX (user_id, friend_id)
- INDEX (status)
- INDEX (created_at)
- INDEX (last_interaction_at)
- UNIQUE (user_id, friend_id)
- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
- FOREIGN KEY (friend_id) REFERENCES users(id) ON DELETE CASCADE

### 5. 数字人模块

#### 5.1 数字人表 (digital_humans)

| 字段名              | 数据类型    | 约束         | 默认值            | 说明                 |
| ------------------- | ----------- | ------------ | ----------------- | -------------------- |
| id                  | VARCHAR(36) | PRIMARY KEY  | dh_xxx            | 数字人ID             |
| name                | VARCHAR(255)| NOT NULL     | -                 | 数字人名称           |
| avatar              | VARCHAR(1024)| NULL        | -                 | 数字人头像URL        |
| description         | TEXT        | NULL         | -                 | 数字人描述           |
| type                | VARCHAR(50) | NOT NULL     | 'personal'        | 数字人类型           |
| status              | VARCHAR(20) | NOT NULL     | 'active'          | 数字人状态           |
| is_system_created   | BOOLEAN     | NOT NULL     | FALSE             | 是否系统创建         |
| personality         | JSON        | NULL         | -                 | 性格特征配置         |
| greeting_message    | TEXT        | NULL         | -                 | 默认打招呼消息       |
| welcome_message     | TEXT        | NULL         | -                 | 欢迎消息模板         |
| user_id             | VARCHAR(36) | FK, NOT NULL | -                 | 所属用户ID           |
| conversation_count  | INTEGER     | NOT NULL     | 0                 | 会话总数             |
| message_count       | INTEGER     | NOT NULL     | 0                 | 消息总数             |
| last_active_at      | TIMESTAMP   | NULL         | -                 | 最后活跃时间         |
| created_at          | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 创建时间             |
| updated_at          | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- INDEX (user_id)
- INDEX (status)
- INDEX (type)
- FOREIGN KEY (user_id) REFERENCES users(id)

### 6. 文件上传模块

#### 4.1 上传会话表 (upload_sessions)

| 字段名            | 数据类型     | 约束             | 默认值            | 说明               |
| ----------------- | ------------ | ---------------- | ----------------- | ------------------ |
| id                | VARCHAR(36)  | PRIMARY KEY      | -                 | 记录ID             |
| upload_id         | VARCHAR(64)  | UNIQUE, NOT NULL | -                 | 上传ID             |
| file_name         | VARCHAR(255) | NOT NULL         | -                 | 原始文件名         |
| file_size         | BIGINT       | NOT NULL         | -                 | 文件总大小（字节） |
| chunk_size        | INTEGER      | NOT NULL         | -                 | 分片大小（字节）   |
| total_chunks      | INTEGER      | NOT NULL         | -                 | 总分片数           |
| conversation_id   | VARCHAR(36)  | FK, NOT NULL     | -                 | 关联会话ID         |
| user_id           | VARCHAR(36)  | FK, NOT NULL     | -                 | 上传用户ID         |
| status            | VARCHAR(20)  | NOT NULL         | 'uploading'       | 上传状态           |
| final_object_name | VARCHAR(500) | NULL             | -                 | 合并后的文件对象名 |
| created_at        | TIMESTAMP    | NOT NULL         | CURRENT_TIMESTAMP | 创建时间           |
| updated_at        | TIMESTAMP    | NOT NULL         | CURRENT_TIMESTAMP | 更新时间           |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (upload_id)
- INDEX (conversation_id)
- INDEX (user_id)
- FOREIGN KEY (conversation_id) REFERENCES conversations(id)
- FOREIGN KEY (user_id) REFERENCES users(id)

#### 4.2 上传分片表 (upload_chunks)

| 字段名      | 数据类型     | 约束         | 默认值            | 说明                  |
| ----------- | ------------ | ------------ | ----------------- | --------------------- |
| id          | VARCHAR(36)  | PRIMARY KEY  | -                 | 记录ID                |
| upload_id   | VARCHAR(64)  | FK, NOT NULL | -                 | 关联上传ID            |
| chunk_index | INTEGER      | NOT NULL     | -                 | 分片索引（从0开始）   |
| object_name | VARCHAR(500) | NOT NULL     | -                 | 分片在MinIO中的对象名 |
| chunk_size  | INTEGER      | NOT NULL     | -                 | 分片实际大小（字节）  |
| status      | VARCHAR(20)  | NOT NULL     | 'uploading'       | 分片状态              |
| checksum    | VARCHAR(64)  | NULL         | -                 | 分片校验和            |
| created_at  | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 创建时间              |
| updated_at  | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 更新时间              |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (upload_id, chunk_index)
- FOREIGN KEY (upload_id) REFERENCES upload_sessions(upload_id)

### 6. 系统配置模块

#### 6.1 系统设置表 (system_settings)

| 字段名                    | 数据类型      | 约束        | 默认值             | 说明             |
| ------------------------- | ------------- | ----------- | ------------------ | ---------------- |
| id                        | VARCHAR(36)   | PRIMARY KEY | sys_xxx            | 系统设置ID       |
| site_name                 | VARCHAR(255)  | NOT NULL    | '安美智能咨询系统' | 站点名称         |
| logo_url                  | VARCHAR(1024) | NULL        | '/logo.png'        | 站点Logo URL     |
| default_model_id          | VARCHAR(255)  | NULL        | -                  | 默认AI模型ID     |
| maintenance_mode          | BOOLEAN       | NOT NULL    | FALSE              | 维护模式开关     |
| user_registration_enabled | BOOLEAN       | NOT NULL    | TRUE               | 是否允许用户注册 |
| created_at                | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP  | 创建时间         |
| updated_at                | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP  | 更新时间         |

**索引：**

- PRIMARY KEY (id)

#### 6.2 AI模型配置表 (ai_model_configs)

| 字段名      | 数据类型      | 约束        | 默认值            | 说明                |
| ----------- | ------------- | ----------- | ----------------- | ------------------- |
| id          | VARCHAR(36)   | PRIMARY KEY | mdl_xxx           | 模型配置ID          |
| model_name  | VARCHAR(255)  | NOT NULL    | -                 | 模型名称            |
| api_key     | TEXT          | NULL        | -                 | API密钥（加密存储） |
| base_url    | VARCHAR(1024) | NULL        | -                 | API基础URL          |
| max_tokens  | INTEGER       | NOT NULL    | 2000              | 最大Token数         |
| temperature | FLOAT         | NOT NULL    | 0.7               | 采样温度            |
| enabled     | BOOLEAN       | NOT NULL    | TRUE              | 是否启用            |
| provider    | VARCHAR(255)  | NOT NULL    | 'openai'          | 服务商              |
| description | TEXT          | NULL        | -                 | 模型描述            |
| created_at  | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP | 创建时间            |
| updated_at  | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP | 更新时间            |

**索引：**

- PRIMARY KEY (id)
- INDEX (provider, enabled)

#### 6.3 Agent配置表 (agent_configs)

| 字段名          | 数据类型      | 约束        | 默认值                | 说明                      |
| --------------- | ------------- | ----------- | --------------------- | ------------------------- |
| id              | VARCHAR(36)   | PRIMARY KEY | agent_xxx             | Agent配置ID               |
| environment     | VARCHAR(100)  | NOT NULL    | -                     | 环境名称（dev/test/prod） |
| app_id          | VARCHAR(255)  | NOT NULL    | -                     | 应用ID                    |
| app_name        | VARCHAR(255)  | NOT NULL    | -                     | 应用名称                  |
| api_key         | TEXT          | NOT NULL    | -                     | API密钥（加密存储）       |
| base_url        | VARCHAR(1024) | NOT NULL    | 'http://localhost/v1' | Agent API基础URL          |
| timeout_seconds | INTEGER       | NOT NULL    | 30                    | 请求超时时间（秒）        |
| max_retries     | INTEGER       | NOT NULL    | 3                     | 最大重试次数              |
| enabled         | BOOLEAN       | NOT NULL    | TRUE                  | 是否启用配置              |
| description     | TEXT          | NULL        | -                     | 配置描述                  |
| agent_type      | VARCHAR(100)  | NULL        | -                     | 智能体类型                |
| capabilities    | JSON          | NULL        | -                     | 智能体能力配置            |
| created_at      | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP     | 创建时间                  |
| updated_at      | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP     | 更新时间                  |

**索引：**

- PRIMARY KEY (id)
- INDEX (environment)
- INDEX (enabled)
- UNIQUE INDEX (environment, app_id)

### 8. MCP工具模块

#### 8.1 MCP工具分组表 (mcp_tool_groups)

| 字段名              | 数据类型      | 约束        | 默认值            | 说明                 |
| ------------------- | ------------- | ----------- | ----------------- | -------------------- |
| id                  | VARCHAR(36)   | PRIMARY KEY | -                 | 分组ID               |
| name                | VARCHAR(100)  | NOT NULL    | -                 | 分组名称             |
| description         | TEXT          | NULL        | -                 | 分组描述             |
| api_key             | TEXT          | NOT NULL    | -                 | API密钥（加密存储）  |
| hashed_api_key      | VARCHAR(64)   | NULL        | -                 | API密钥哈希           |
| server_code         | VARCHAR(32)   | NULL        | -                 | MCP服务器代码        |
| user_tier_access    | JSON          | NOT NULL    | ["internal"]      | 允许访问的用户层级   |
| allowed_roles       | JSON          | NOT NULL    | []                | 允许访问的角色列表   |
| enabled             | BOOLEAN       | NOT NULL    | TRUE              | 是否启用             |
| created_by          | VARCHAR(36)   | NOT NULL    | -                 | 创建者ID             |
| created_at          | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP | 创建时间             |
| updated_at          | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- INDEX (enabled)
- INDEX (created_by)
- INDEX (created_at)
- UNIQUE (name)
- UNIQUE (api_key)
- UNIQUE (server_code)

#### 8.2 MCP工具表 (mcp_tools)

| 字段名              | 数据类型      | 约束        | 默认值            | 说明                 |
| ------------------- | ------------- | ----------- | ----------------- | -------------------- |
| id                  | VARCHAR(36)   | PRIMARY KEY | -                 | 工具ID               |
| group_id            | VARCHAR(36)   | FK, NOT NULL| -                 | 分组ID               |
| tool_name           | VARCHAR(255)  | NOT NULL    | -                 | 工具名称             |
| description         | TEXT          | NULL        | -                 | 工具描述             |
| input_schema        | JSON          | NULL        | -                 | 输入参数模式         |
| output_schema       | JSON          | NULL        | -                 | 输出参数模式         |
| enabled             | BOOLEAN       | NOT NULL    | TRUE              | 是否启用             |
| created_at          | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP | 创建时间             |
| updated_at          | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- INDEX (group_id, enabled)
- INDEX (tool_name)
- INDEX (created_at)
- UNIQUE (group_id, tool_name)

#### 8.3 MCP调用日志表 (mcp_call_logs)

| 字段名              | 数据类型      | 约束        | 默认值            | 说明                 |
| ------------------- | ------------- | ----------- | ----------------- | -------------------- |
| id                  | VARCHAR(36)   | PRIMARY KEY | -                 | 日志ID               |
| tool_id             | VARCHAR(36)   | FK, NOT NULL| -                 | 工具ID               |
| user_id             | VARCHAR(36)   | FK, NOT NULL| -                 | 用户ID               |
| request_data        | JSON          | NULL        | -                 | 请求数据             |
| response_data       | JSON          | NULL        | -                 | 响应数据             |
| status              | VARCHAR(20)   | NOT NULL    | -                 | 调用状态             |
| error_message       | TEXT          | NULL        | -                 | 错误信息             |
| execution_time      | FLOAT         | NULL        | -                 | 执行时间（秒）       |
| created_at          | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP | 创建时间             |

**索引：**

- PRIMARY KEY (id)
- INDEX (tool_id)
- INDEX (user_id)
- INDEX (status)
- INDEX (created_at)
- FOREIGN KEY (tool_id) REFERENCES mcp_tools(id)
- FOREIGN KEY (user_id) REFERENCES users(id)

### 9. 个人中心模块

#### 9.1 用户偏好设置表 (user_preferences)

| 字段名               | 数据类型    | 约束                 | 默认值            | 说明             |
| -------------------- | ----------- | -------------------- | ----------------- | ---------------- |
| id                   | VARCHAR(36) | PRIMARY KEY          | -                 | 偏好设置ID       |
| user_id              | VARCHAR(36) | FK, UNIQUE, NOT NULL | -                 | 用户ID           |
| notification_enabled | BOOLEAN     | NOT NULL             | TRUE              | 是否启用通知     |
| email_notification   | BOOLEAN     | NOT NULL             | TRUE              | 是否启用邮件通知 |
| push_notification    | BOOLEAN     | NOT NULL             | TRUE              | 是否启用推送通知 |
| created_at           | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 创建时间         |
| updated_at           | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 更新时间         |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (user_id)
- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE

#### 9.2 用户默认角色设置表 (user_default_roles)

| 字段名       | 数据类型    | 约束                 | 默认值            | 说明         |
| ------------ | ----------- | -------------------- | ----------------- | ------------ |
| id           | VARCHAR(36) | PRIMARY KEY          | -                 | 记录ID       |
| user_id      | VARCHAR(36) | FK, UNIQUE, NOT NULL | -                 | 用户ID       |
| default_role | VARCHAR(50) | NOT NULL             | -                 | 默认角色名称 |
| created_at   | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 创建时间     |
| updated_at   | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 更新时间     |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (user_id)
- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE

#### 9.3 登录历史表 (login_history)

| 字段名     | 数据类型     | 约束         | 默认值            | 说明             |
| ---------- | ------------ | ------------ | ----------------- | ---------------- |
| id         | VARCHAR(36)  | PRIMARY KEY  | -                 | 登录记录ID       |
| user_id    | VARCHAR(36)  | FK, NOT NULL | -                 | 用户ID           |
| ip_address | VARCHAR(45)  | NULL         | -                 | 登录IP地址       |
| user_agent | TEXT         | NULL         | -                 | 用户代理信息     |
| login_time | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 登录时间         |
| login_role | VARCHAR(50)  | NULL         | -                 | 登录时使用的角色 |
| location   | VARCHAR(100) | NULL         | -                 | 登录地点         |
| created_at | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 创建时间         |
| updated_at | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 更新时间         |

**索引：**

- PRIMARY KEY (id)
- INDEX (user_id)
- INDEX (login_time)
- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE

### 10. 运营业务模块

#### 10.1 项目类型表 (project_types)

| 字段名      | 数据类型     | 约束             | 默认值            | 说明                     |
| ----------- | ------------ | ---------------- | ----------------- | ------------------------ |
| id          | VARCHAR(36)  | PRIMARY KEY      | -                 | 项目类型ID               |
| name        | VARCHAR(100) | UNIQUE, NOT NULL | -                 | 项目类型名称             |
| label       | VARCHAR(100) | NOT NULL         | -                 | 项目类型显示名称         |
| description | TEXT         | NULL             | -                 | 项目类型描述             |
| parameters  | JSON         | NULL             | -                 | 项目参数配置（JSON格式） |
| is_active   | BOOLEAN      | NOT NULL         | TRUE              | 是否激活                 |
| category    | VARCHAR(50)  | NULL             | -                 | 项目分类                 |
| created_at  | TIMESTAMP    | NOT NULL         | CURRENT_TIMESTAMP | 创建时间                 |
| updated_at  | TIMESTAMP    | NOT NULL         | CURRENT_TIMESTAMP | 更新时间                 |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (name)

#### 10.2 模拟图像表 (simulation_images)

| 字段名               | 数据类型     | 约束         | 默认值            | 说明                 |
| -------------------- | ------------ | ------------ | ----------------- | -------------------- |
| id                   | VARCHAR(36)  | PRIMARY KEY  | -                 | 模拟图像ID           |
| customer_id          | VARCHAR(36)  | FK, NOT NULL | -                 | 客户ID               |
| customer_name        | VARCHAR(100) | NOT NULL     | -                 | 客户姓名             |
| original_image_path  | VARCHAR(500) | NOT NULL     | -                 | 原始图像路径         |
| simulated_image_path | VARCHAR(500) | NOT NULL     | -                 | 模拟图像路径         |
| project_type_id      | VARCHAR(36)  | FK, NOT NULL | -                 | 项目类型ID           |
| parameters           | JSON         | NULL         | -                 | 模拟参数（JSON格式） |
| notes                | TEXT         | NULL         | -                 | 备注                 |
| operator_id          | VARCHAR(36)  | FK, NOT NULL | -                 | 运营人员ID           |
| created_at           | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 创建时间             |
| updated_at           | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- INDEX (customer_id)
- INDEX (project_type_id)
- INDEX (operator_id)
- FOREIGN KEY (customer_id) REFERENCES customers(user_id)
- FOREIGN KEY (project_type_id) REFERENCES project_types(id)
- FOREIGN KEY (operator_id) REFERENCES users(id)

#### 10.3 项目模板表 (project_templates)

| 字段名            | 数据类型     | 约束        | 默认值            | 说明                     |
| ----------------- | ------------ | ----------- | ----------------- | ------------------------ |
| id                | VARCHAR(36)  | PRIMARY KEY | -                 | 模板ID                   |
| name              | VARCHAR(100) | NOT NULL    | -                 | 项目名称                 |
| description       | TEXT         | NULL        | -                 | 项目描述                 |
| category          | VARCHAR(50)  | NULL        | -                 | 项目分类                 |
| base_cost         | FLOAT        | NOT NULL    | -                 | 基础费用                 |
| duration          | VARCHAR(50)  | NULL        | -                 | 持续时间                 |
| recovery_time     | VARCHAR(50)  | NULL        | -                 | 恢复时间                 |
| expected_results  | TEXT         | NULL        | -                 | 预期效果                 |
| risks             | JSON         | NULL        | -                 | 风险列表（JSON格式）     |
| is_active         | BOOLEAN      | NOT NULL    | TRUE              | 是否激活                 |
| suitable_age_min  | INTEGER      | NULL        | -                 | 适用最小年龄             |
| suitable_age_max  | INTEGER      | NULL        | -                 | 适用最大年龄             |
| suitable_concerns | JSON         | NULL        | -                 | 适用关注问题（JSON格式） |
| created_at        | TIMESTAMP    | NOT NULL    | CURRENT_TIMESTAMP | 创建时间                 |
| updated_at        | TIMESTAMP    | NOT NULL    | CURRENT_TIMESTAMP | 更新时间                 |

**索引：**

- PRIMARY KEY (id)
- INDEX (category)
- INDEX (is_active)

#### 10.6 客户偏好表 (customer_preferences)

| 字段名                       | 数据类型    | 约束                 | 默认值            | 说明                     |
| ---------------------------- | ----------- | -------------------- | ----------------- | ------------------------ |
| id                           | VARCHAR(36) | PRIMARY KEY          | -                 | 偏好ID                   |
| customer_id                  | VARCHAR(36) | FK, UNIQUE, NOT NULL | -                 | 客户ID                   |
| preferred_budget_min         | FLOAT       | NULL                 | -                 | 最小预算偏好             |
| preferred_budget_max         | FLOAT       | NULL                 | -                 | 最大预算偏好             |
| preferred_recovery_time      | VARCHAR(50) | NULL                 | -                 | 偏好恢复时间             |
| preferred_project_categories | JSON        | NULL                 | -                 | 偏好项目分类（JSON格式） |
| concerns_history             | JSON        | NULL                 | -                 | 历史关注问题（JSON格式） |
| risk_tolerance               | VARCHAR(20) | NOT NULL             | 'medium'          | 风险承受度               |
| created_at                   | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 创建时间                 |
| updated_at                   | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 更新时间                 |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (customer_id)
- FOREIGN KEY (customer_id) REFERENCES customers(user_id)

## 枚举类型定义

### 消息类型枚举 (message_type)

- `text`: 纯文本消息
- `media`: 媒体文件消息
- `system`: 系统事件消息
- `structured`: 结构化卡片消息

### 发送者类型枚举 (sender_type)

- `customer`: 客户
- `operator`: 运营人员
- `system`: 系统
- `digital_human`: 数字人

### 咨询类型枚举 (consultation_type)

- `initial`: 初次咨询
- `follow_up`: 复诊咨询
- `emergency`: 紧急咨询
- `specialized`: 专项咨询
- `other`: 其他

### 信息状态枚举 (info_status)

- `missing`: 缺失
- `partial`: 部分
- `complete`: 完整

### 管理员级别枚举 (AdminLevel)

- `basic`: 基础管理员
- `advanced`: 高级管理员
- `super`: 超级管理员

### 数字人类型枚举 (digital_human_type)

- `personal`: 个人
- `business`: 商务
- `specialized`: 专业
- `system`: 系统

### 数字人状态枚举 (digital_human_status)

- `active`: 活跃
- `inactive`: 非活跃
- `maintenance`: 维护中

### 好友状态枚举 (friendship_status)

- `pending`: 待确认
- `accepted`: 已接受
- `blocked`: 已屏蔽
- `deleted`: 已删除

## 数据安全特性

### 1. API密钥加密存储

- 使用Fernet对称加密算法
- 支持向后兼容的明文到密文迁移
- 提供安全的加密/解密接口

### 2. 用户认证

- 密码使用bcrypt加密存储
- 支持JWT令牌认证
- 实现基于角色的访问控制

### 3. 数据完整性

- 外键约束确保数据一致性
- 级联删除保护数据完整性
- 唯一索引防止重复数据

## 性能优化

### 1. 索引策略

- 主键自动索引
- 外键字段索引
- 查询频繁字段索引
- 复合索引优化多字段查询

### 2. 查询优化

- 使用JSON字段存储复杂数据
- 避免N+1查询问题
- 合理使用延迟加载

### 3. 数据分区

- 按时间分区历史数据
- 大表分片存储
- 冷热数据分离

## 扩展性设计

### 1. 模块化设计

- 按业务功能分离表结构
- 支持水平扩展
- 微服务架构友好

### 2. JSON字段扩展

- 灵活存储复杂数据结构
- 支持动态字段扩展
- 向后兼容性保证

### 3. 版本控制

- 数据迁移支持
- 兼容性维护

## 维护建议

### 1. 定期维护

- 定期清理过期数据
- 优化数据库性能
- 备份重要数据

### 2. 监控告警

- 监控数据库性能
- 设置容量告警
- 异常情况处理

### 3. 数据备份

- 定期全量备份
- 增量备份策略
- 灾难恢复计划

---

*本文档版本：v2.0*
*最后更新：2024年12月*
*维护者：开发团队*

## 更新日志

### v2.0 (2024-12)
- 重构会话表结构，将type字段改为chat_mode和tag
- 添加会话参与者表和消息附件表
- 新增通讯录模块，包含好友关系、标签、分组等功能
- 新增数字人模块，支持数字人管理和配置
- 新增MCP工具模块，支持工具分组和调用日志
- 更新消息表，支持数字人发送和确认机制
- 将Dify配置表重命名为Agent配置表
- 添加API密钥加密存储功能
- 更新所有相关索引和外键约束
- 新增多个枚举类型定义

### v1.0 (2024-01)
- 初始版本，包含基础用户管理和聊天功能
