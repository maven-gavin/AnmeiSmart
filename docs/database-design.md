# 安美智能咨询系统数据库设计文档

## 概述

本文档描述了安美智能咨询系统的完整数据库设计，包括所有表结构、字段定义、关系映射和索引设计。系统采用PostgreSQL数据库，使用SQLAlchemy ORM框架进行数据访问。

## 数据库架构

### 核心设计原则

1. **分层架构**：采用用户-角色-扩展表的分离设计
2. **统一标识**：使用带前缀的UUID作为主键
3. **时间戳管理**：所有表都包含创建和更新时间戳
   TODO：应该考虑审计问题，是不是应该加上创建人，更新人？
4. **软删除支持**：通过状态字段而非物理删除
5. **JSON扩展性**：使用JSON字段存储复杂数据结构

### 表关系图

```
用户管理模块:
users ←→ user_roles ←→ roles
  ↓
  ├── customers
  ├── doctors  
  ├── consultants
  ├── operators
  └── administrators

聊天模块:
conversations ←→ messages
  ↓
  └── upload_sessions ←→ upload_chunks

方案生成模块:
plan_generation_sessions ←→ plan_drafts
  ↓
  └── info_completeness

系统配置模块:
system_settings ←→ ai_model_configs
  ↓
  └── dify_configs
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

#### 1.4 医生扩展表 (doctors)

| 字段名         | 数据类型    | 约束                 | 默认值            | 说明     |
| -------------- | ----------- | -------------------- | ----------------- | -------- |
| id             | VARCHAR(36) | PRIMARY KEY          | -                 | 记录ID   |
| user_id        | VARCHAR(36) | UNIQUE, FK, NOT NULL | -                 | 用户ID   |
| specialization | VARCHAR     | NULL                 | -                 | 专科方向 |
| certification  | VARCHAR     | NULL                 | -                 | 资格证书 |
| license_number | VARCHAR     | NULL                 | -                 | 执业证号 |
| created_at     | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 创建时间 |
| updated_at     | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 更新时间 |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (user_id)
- FOREIGN KEY (user_id) REFERENCES users(id)

#### 1.5 顾问扩展表 (consultants)

| 字段名              | 数据类型    | 约束                 | 默认值            | 说明     |
| ------------------- | ----------- | -------------------- | ----------------- | -------- |
| id                  | VARCHAR(36) | PRIMARY KEY          | -                 | 记录ID   |
| user_id             | VARCHAR(36) | UNIQUE, FK, NOT NULL | -                 | 用户ID   |
| expertise           | VARCHAR     | NULL                 | -                 | 专长领域 |
| performance_metrics | TEXT        | NULL                 | -                 | 业绩指标 |
| created_at          | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 创建时间 |
| updated_at          | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 更新时间 |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (user_id)
- FOREIGN KEY (user_id) REFERENCES users(id)

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

#### 1.7 管理员扩展表 (administrators)

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
| customer_id     | VARCHAR(36) | UNIQUE, FK, NOT NULL | -                 | 顾客用户ID           |
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
| id                     | VARCHAR(36) | PRIMARY KEY  | conv_xxx          | 会话ID           |
| title                  | VARCHAR     | NOT NULL     | -                 | 会话标题         |
| customer_id            | VARCHAR(36) | FK, NOT NULL | -                 | 顾客用户ID       |
| assigned_consultant_id | VARCHAR(36) | FK           | NULL              | 分配的顾问用户ID |
| is_active              | BOOLEAN     | NOT NULL     | TRUE              | 会话是否激活     |
| consultation_type      | ENUM        | NULL         | -                 | 咨询类型         |
| consultation_summary   | JSON        | NULL         | -                 | 结构化咨询总结   |
| summary                | TEXT        | NULL         | -                 | 会话简短摘要     |
| is_ai_controlled       | BOOLEAN     | NOT NULL     | TRUE              | 是否由AI控制     |
| created_at             | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 创建时间         |
| updated_at             | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 更新时间         |

**索引：**

- PRIMARY KEY (id)
- INDEX (customer_id)
- INDEX (assigned_consultant_id)
- FOREIGN KEY (customer_id) REFERENCES users(id)
- FOREIGN KEY (assigned_consultant_id) REFERENCES users(id)

TODO：

* "咨询类型" 变更为"会话类型"：
* “结构化咨询总结"、”会话简短摘要"，“是否由AI控制" 三个字段不需要

#### 3.2 消息表 (messages)

| 字段名              | 数据类型    | 约束         | 默认值            | 说明           |
| ------------------- | ----------- | ------------ | ----------------- | -------------- |
| id                  | VARCHAR(36) | PRIMARY KEY  | msg_xxx           | 消息ID         |
| conversation_id     | VARCHAR(36) | FK, NOT NULL | -                 | 会话ID         |
| content             | JSON        | NOT NULL     | -                 | 结构化消息内容 |
| type                | ENUM        | NOT NULL     | -                 | 消息主类型     |
| sender_id           | VARCHAR(36) | FK, NOT NULL | -                 | 发送者用户ID   |
| sender_type         | ENUM        | NOT NULL     | -                 | 发送者角色     |
| is_read             | BOOLEAN     | NOT NULL     | FALSE             | 是否已读       |
| is_important        | BOOLEAN     | NOT NULL     | FALSE             | 是否重要       |
| timestamp           | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 消息时间戳     |
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
- FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
- FOREIGN KEY (sender_id) REFERENCES users(id)
- FOREIGN KEY (reply_to_message_id) REFERENCES messages(id)

### 4. 文件上传模块

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

### 5. 方案生成模块

#### 5.1 方案生成会话表 (plan_generation_sessions)

| 字段名              | 数据类型    | 约束         | 默认值            | 说明                     |
| ------------------- | ----------- | ------------ | ----------------- | ------------------------ |
| id                  | VARCHAR(36) | PRIMARY KEY  | -                 | 会话ID                   |
| conversation_id     | VARCHAR(36) | FK, NOT NULL | -                 | 关联的对话会话ID         |
| customer_id         | VARCHAR(36) | FK, NOT NULL | -                 | 客户ID                   |
| consultant_id       | VARCHAR(36) | FK, NOT NULL | -                 | 顾问ID                   |
| status              | ENUM        | NOT NULL     | 'collecting'      | 会话状态                 |
| required_info       | JSON        | NOT NULL     | -                 | 必需信息清单             |
| extracted_info      | JSON        | NULL         | -                 | 从对话中提取的结构化信息 |
| interaction_history | JSON        | NULL         | -                 | 人机交互历史记录         |
| session_metadata    | JSON        | NULL         | -                 | 会话元数据               |
| performance_metrics | JSON        | NULL         | -                 | 性能指标                 |
| created_at          | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 创建时间                 |
| updated_at          | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 更新时间                 |

**索引：**

- PRIMARY KEY (id)
- INDEX (conversation_id)
- INDEX (customer_id)
- INDEX (consultant_id)
- INDEX (status)
- FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
- FOREIGN KEY (customer_id) REFERENCES users(id)
- FOREIGN KEY (consultant_id) REFERENCES users(id)

#### 5.2 方案草稿表 (plan_drafts)

| 字段名          | 数据类型    | 约束         | 默认值            | 说明                 |
| --------------- | ----------- | ------------ | ----------------- | -------------------- |
| id              | VARCHAR(36) | PRIMARY KEY  | -                 | 草稿ID               |
| session_id      | VARCHAR(36) | FK, NOT NULL | -                 | 关联的方案生成会话ID |
| version         | INTEGER     | NOT NULL     | 1                 | 版本号               |
| parent_version  | INTEGER     | NULL         | -                 | 父版本号             |
| status          | ENUM        | NOT NULL     | 'draft'           | 草稿状态             |
| content         | JSON        | NOT NULL     | -                 | 结构化的方案内容     |
| feedback        | JSON        | NULL         | -                 | 反馈意见             |
| improvements    | JSON        | NULL         | -                 | 改进记录             |
| generation_info | JSON        | NULL         | -                 | 生成信息             |
| created_at      | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 创建时间             |
| updated_at      | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- INDEX (session_id)
- INDEX (status)
- FOREIGN KEY (session_id) REFERENCES plan_generation_sessions(id) ON DELETE CASCADE

#### 5.3 信息完整性表 (info_completeness)

| 字段名                 | 数据类型    | 约束                 | 默认值            | 说明                 |
| ---------------------- | ----------- | -------------------- | ----------------- | -------------------- |
| id                     | VARCHAR(36) | PRIMARY KEY          | -                 | 记录ID               |
| session_id             | VARCHAR(36) | FK, UNIQUE, NOT NULL | -                 | 关联的方案生成会话ID |
| basic_info_status      | ENUM        | NOT NULL             | 'missing'         | 基础信息状态         |
| basic_info_score       | FLOAT       | NOT NULL             | 0.0               | 基础信息完整度评分   |
| concerns_status        | ENUM        | NOT NULL             | 'missing'         | 关注点信息状态       |
| concerns_score         | FLOAT       | NOT NULL             | 0.0               | 关注点完整度评分     |
| budget_status          | ENUM        | NOT NULL             | 'missing'         | 预算信息状态         |
| budget_score           | FLOAT       | NOT NULL             | 0.0               | 预算完整度评分       |
| timeline_status        | ENUM        | NOT NULL             | 'missing'         | 时间安排状态         |
| timeline_score         | FLOAT       | NOT NULL             | 0.0               | 时间安排完整度评分   |
| medical_history_status | ENUM        | NOT NULL             | 'missing'         | 病史信息状态         |
| medical_history_score  | FLOAT       | NOT NULL             | 0.0               | 病史完整度评分       |
| expectations_status    | ENUM        | NOT NULL             | 'missing'         | 期望信息状态         |
| expectations_score     | FLOAT       | NOT NULL             | 0.0               | 期望完整度评分       |
| completeness_score     | FLOAT       | NOT NULL             | 0.0               | 总体完整度评分       |
| missing_fields         | JSON        | NULL                 | -                 | 缺失信息详情         |
| guidance_questions     | JSON        | NULL                 | -                 | AI生成的引导问题     |
| suggestions            | JSON        | NULL                 | -                 | 改进建议             |
| last_analysis_at       | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 最后分析时间         |
| analysis_version       | INTEGER     | NOT NULL             | 1                 | 分析版本号           |
| created_at             | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 创建时间             |
| updated_at             | TIMESTAMP   | NOT NULL             | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- UNIQUE INDEX (session_id)
- FOREIGN KEY (session_id) REFERENCES plan_generation_sessions(id) ON DELETE CASCADE

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

#### 6.3 Dify配置表 (dify_configs)

| 字段名          | 数据类型      | 约束        | 默认值                | 说明                              |
| --------------- | ------------- | ----------- | --------------------- | --------------------------------- |
| id              | VARCHAR(36)   | PRIMARY KEY | mdl_xxx               | Dify配置ID                        |
| config_name     | VARCHAR(255)  | NOT NULL    | -                     | 配置名称                          |
| base_url        | VARCHAR(1024) | NOT NULL    | 'http://localhost/v1' | Dify API基础URL                   |
| chat_app_id     | VARCHAR(255)  | NULL        | -                     | 聊天应用ID                        |
| chat_api_key    | TEXT          | NULL        | -                     | 聊天应用API密钥（加密存储）       |
| beauty_app_id   | VARCHAR(255)  | NULL        | -                     | 医美方案专家应用ID                |
| beauty_api_key  | TEXT          | NULL        | -                     | 医美方案专家API密钥（加密存储）   |
| summary_app_id  | VARCHAR(255)  | NULL        | -                     | 咨询总结工作流应用ID              |
| summary_api_key | TEXT          | NULL        | -                     | 咨询总结工作流API密钥（加密存储） |
| enabled         | BOOLEAN       | NOT NULL    | TRUE                  | 是否启用                          |
| description     | TEXT          | NULL        | -                     | 配置描述                          |
| timeout_seconds | INTEGER       | NOT NULL    | 30                    | 请求超时时间（秒）                |
| max_retries     | INTEGER       | NOT NULL    | 3                     | 最大重试次数                      |
| created_at      | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP     | 创建时间                          |
| updated_at      | TIMESTAMP     | NOT NULL    | CURRENT_TIMESTAMP     | 更新时间                          |

**索引：**

- PRIMARY KEY (id)
- INDEX (enabled)

### 7. 个人中心模块

#### 7.1 用户偏好设置表 (user_preferences)

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

#### 7.2 用户默认角色设置表 (user_default_roles)

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

#### 7.3 登录历史表 (login_history)

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

### 8. 顾问业务模块

#### 8.1 项目类型表 (project_types)

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

#### 8.2 模拟图像表 (simulation_images)

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
| consultant_id        | VARCHAR(36)  | FK, NOT NULL | -                 | 顾问ID               |
| created_at           | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 创建时间             |
| updated_at           | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 更新时间             |

**索引：**

- PRIMARY KEY (id)
- INDEX (customer_id)
- INDEX (project_type_id)
- INDEX (consultant_id)
- FOREIGN KEY (customer_id) REFERENCES customers(user_id)
- FOREIGN KEY (project_type_id) REFERENCES project_types(id)
- FOREIGN KEY (consultant_id) REFERENCES consultants(user_id)

#### 8.3 个性化方案表 (personalized_plans)

| 字段名              | 数据类型     | 约束         | 默认值            | 说明                     |
| ------------------- | ------------ | ------------ | ----------------- | ------------------------ |
| id                  | VARCHAR(36)  | PRIMARY KEY  | -                 | 方案ID                   |
| customer_id         | VARCHAR(36)  | FK, NOT NULL | -                 | 客户ID                   |
| customer_name       | VARCHAR(100) | NOT NULL     | -                 | 客户姓名                 |
| consultant_id       | VARCHAR(36)  | FK, NOT NULL | -                 | 顾问ID                   |
| consultant_name     | VARCHAR(100) | NOT NULL     | -                 | 顾问姓名                 |
| customer_profile    | JSON         | NULL         | -                 | 客户画像信息（JSON格式） |
| projects            | JSON         | NOT NULL     | -                 | 推荐项目列表（JSON格式） |
| total_cost          | FLOAT        | NOT NULL     | 0.0               | 总费用                   |
| estimated_timeframe | VARCHAR(100) | NULL         | -                 | 预计时间框架             |
| status              | ENUM         | NOT NULL     | 'DRAFT'           | 方案状态                 |
| notes               | TEXT         | NULL         | -                 | 方案备注                 |
| created_at          | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 创建时间                 |
| updated_at          | TIMESTAMP    | NOT NULL     | CURRENT_TIMESTAMP | 更新时间                 |

**索引：**

- PRIMARY KEY (id)
- INDEX (customer_id)
- INDEX (consultant_id)
- INDEX (status)
- FOREIGN KEY (customer_id) REFERENCES customers(user_id)
- FOREIGN KEY (consultant_id) REFERENCES consultants(user_id)

#### 8.4 方案版本表 (plan_versions)

| 字段名         | 数据类型    | 约束         | 默认值            | 说明                     |
| -------------- | ----------- | ------------ | ----------------- | ------------------------ |
| id             | VARCHAR(36) | PRIMARY KEY  | -                 | 版本ID                   |
| plan_id        | VARCHAR(36) | FK, NOT NULL | -                 | 方案ID                   |
| version_number | INTEGER     | NOT NULL     | -                 | 版本号                   |
| projects       | JSON        | NOT NULL     | -                 | 项目列表快照（JSON格式） |
| total_cost     | FLOAT       | NOT NULL     | -                 | 总费用快照               |
| notes          | TEXT        | NULL         | -                 | 版本备注                 |
| created_at     | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 创建时间                 |
| updated_at     | TIMESTAMP   | NOT NULL     | CURRENT_TIMESTAMP | 更新时间                 |

**索引：**

- PRIMARY KEY (id)
- INDEX (plan_id)
- FOREIGN KEY (plan_id) REFERENCES personalized_plans(id)

#### 8.5 项目模板表 (project_templates)

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

#### 8.6 客户偏好表 (customer_preferences)

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
- `consultant`: 顾问
- `doctor`: 医生
- `ai`: AI系统
- `system`: 系统

### 咨询类型枚举 (consultation_type)

- `initial`: 初次咨询
- `follow_up`: 复诊咨询
- `emergency`: 紧急咨询
- `specialized`: 专项咨询
- `other`: 其他

### 方案生成会话状态枚举 (plan_session_status)

- `collecting`: 收集中
- `generating`: 生成中
- `optimizing`: 优化中
- `reviewing`: 审核中
- `completed`: 已完成
- `failed`: 失败
- `cancelled`: 已取消

### 方案草稿状态枚举 (plan_draft_status)

- `draft`: 草稿
- `reviewing`: 审核中
- `approved`: 已确认
- `rejected`: 已拒绝
- `archived`: 已归档

### 信息状态枚举 (info_status)

- `missing`: 缺失
- `partial`: 部分
- `complete`: 完整

### 管理员级别枚举 (AdminLevel)

- `basic`: 基础管理员
- `advanced`: 高级管理员
- `super`: 超级管理员

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

- 方案版本管理
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

*本文档版本：v1.0*
*最后更新：2024年1月*
*维护者：开发团队*
