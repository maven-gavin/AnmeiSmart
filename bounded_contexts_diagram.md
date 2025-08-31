# 医美智能咨询系统 - 限界上下文图

```mermaid
graph TB
    subgraph "用户身份与权限上下文"
        A1[User 聚合根]
        A2[Role]
        A3[Doctor/Consultant/Operator/Administrator]
        A4[UserPreferences]
        A5[LoginHistory]
    end

    subgraph "客户管理上下文"
        B1[Customer 聚合根]
        B2[CustomerProfile]
    end

    subgraph "通讯录上下文"
        C1[Friendship 聚合根]
        C2[ContactTag]
        C3[ContactGroup]
        C4[ContactPrivacySetting]
        C5[InteractionRecord]
    end

    subgraph "聊天通信上下文"
        D1[Conversation 聚合根]
        D2[Message]
        D3[ConversationParticipant]
        D4[MessageAttachment]
    end

    subgraph "医美咨询上下文"
        E1[PersonalizedPlan 聚合根]
        E2[PlanGenerationSession 聚合根]
        E3[ProjectType]
        E4[SimulationImage]
        E5[PlanDraft]
        E6[InfoCompleteness]
    end

    subgraph "数字人上下文"
        F1[DigitalHuman 聚合根]
        F2[ConsultationRecord 聚合根]
        F3[PendingTask 聚合根]
        F4[DigitalHumanAgentConfig]
    end

    subgraph "系统配置上下文"
        G1[SystemSettings 聚合根]
        G2[AIModelConfig]
        G3[AgentConfig]
    end

    subgraph "文件管理上下文"
        H1[UploadSession 聚合根]
        H2[MCPToolGroup 聚合根]
        H3[UploadChunk]
        H4[MCPTool]
        H5[MCPCallLog]
    end

    %% 上下文间的关系
    A1 -.->|"用户身份"| B1
    A1 -.->|"用户身份"| C1
    A1 -.->|"会话所有者"| D1
    A1 -.->|"顾问/客户"| E1
    A1 -.->|"数字人所有者"| F1
    A1 -.->|"上传者"| H1

    D1 -.->|"咨询会话"| E2
    E2 -.->|"生成方案"| E1
    F1 -.->|"参与咨询"| F2
    F2 -.->|"关联会话"| D1

    H1 -.->|"文件附件"| D4
    G2 -.->|"AI配置"| E2
    G3 -.->|"智能体配置"| F4

    %% 样式定义
    classDef aggregate fill:#e1f5fe,stroke:#01579b,stroke-width:3px
    classDef entity fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef valueObject fill:#e8f5e8,stroke:#1b5e20,stroke-width:1px

    class A1,B1,C1,D1,E1,E2,F1,F2,F3,G1,H1,H2 aggregate
    class A2,A3,B2,C2,C3,C4,D2,D3,D4,E3,E4,E5,E6,F4,G2,G3,H3,H4,H5 entity
    class A4,A5,C5 valueObject
```

## 限界上下文详细说明

### 1. 用户身份与权限上下文 (Identity & Access Management)
- **核心职责：** 用户身份认证、角色权限管理、登录历史追踪
- **聚合根：** User
- **关键业务规则：** 用户可以有多个角色，角色决定访问权限

### 2. 客户管理上下文 (Customer Management)  
- **核心职责：** 客户信息管理、医疗档案维护
- **聚合根：** Customer
- **关键业务规则：** 客户信息与用户身份分离，支持医疗数据管理

### 3. 通讯录上下文 (Contact Management)
- **核心职责：** 好友关系管理、联系人分组、隐私控制
- **聚合根：** Friendship
- **关键业务规则：** 双向好友关系、分组管理、隐私设置

### 4. 聊天通信上下文 (Chat & Communication)
- **核心职责：** 会话管理、消息传递、文件共享
- **聚合根：** Conversation
- **关键业务规则：** 支持多参与者、消息类型丰富、文件附件

### 5. 医美咨询上下文 (Medical Beauty Consultation)
- **核心职责：** 医美方案生成、项目推荐、客户偏好分析
- **聚合根：** PersonalizedPlan, PlanGenerationSession
- **关键业务规则：** AI辅助方案生成、信息完整性跟踪、版本管理

### 6. 数字人上下文 (Digital Human)
- **核心职责：** 数字人管理、智能体配置、任务调度
- **聚合根：** DigitalHuman, ConsultationRecord, PendingTask
- **关键业务规则：** 数字人可参与咨询、任务自动分配

### 7. 系统配置上下文 (System Configuration)
- **核心职责：** 系统设置、AI模型配置、智能体管理
- **聚合根：** SystemSettings
- **关键业务规则：** 配置加密存储、环境隔离

### 8. 文件管理上下文 (File Management)
- **核心职责：** 文件上传、MCP工具管理、调用日志
- **聚合根：** UploadSession, MCPToolGroup
- **关键业务规则：** 断点续传、工具权限控制、调用监控
