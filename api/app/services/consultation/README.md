# 咨询服务 - DDD分层架构

## 概述

咨询服务模块采用领域驱动设计（DDD）分层架构，将咨询、方案生成、顾问管理等功能整合到一个统一的领域边界内。

## 架构设计

### 分层结构

```
api/app/services/consultation/
├── __init__.py                    # 模块入口
├── application/                   # 应用层
│   ├── __init__.py
│   ├── consultation_application_service.py    # 咨询应用服务
│   ├── plan_generation_application_service.py # 方案生成应用服务
│   └── consultant_application_service.py      # 顾问应用服务
├── domain/                       # 领域层
│   ├── __init__.py
│   ├── entities/                 # 实体
│   │   ├── __init__.py
│   │   ├── consultation.py       # 咨询聚合根
│   │   ├── plan.py              # 方案聚合根
│   │   └── consultant.py        # 顾问实体
│   ├── value_objects/           # 值对象
│   │   ├── __init__.py
│   │   ├── consultation_status.py # 咨询状态
│   │   └── plan_status.py       # 方案状态
│   ├── consultation_domain_service.py
│   ├── plan_generation_domain_service.py
│   └── consultant_domain_service.py
├── infrastructure/              # 基础设施层
│   ├── __init__.py
│   ├── repositories/            # 仓储
│   │   ├── __init__.py
│   │   ├── consultation_repository.py
│   │   ├── plan_repository.py
│   │   └── consultant_repository.py
│   └── external_services/       # 外部服务
│       ├── __init__.py
│       └── ai_service.py        # AI服务集成
└── converters/                  # 数据转换层
    ├── __init__.py
    ├── consultation_converter.py
    ├── plan_converter.py
    └── consultant_converter.py
```

## 领域概念

### 聚合根

1. **Consultation（咨询聚合根）**
   - 管理咨询会话的生命周期
   - 包含客户信息、顾问分配、状态管理
   - 支持状态转换：待处理 → 进行中 → 已完成/已取消

2. **Plan（方案聚合根）**
   - 管理方案的生命周期
   - 包含方案内容、版本控制、审核流程
   - 支持状态转换：草稿 → 生成中 → 审核中 → 已批准/已拒绝

### 实体

3. **Consultant（顾问实体）**
   - 管理顾问信息和能力
   - 包含专业领域、工作经验、状态管理

### 值对象

4. **ConsultationStatus（咨询状态）**
   - PENDING: 待处理
   - IN_PROGRESS: 进行中
   - COMPLETED: 已完成
   - CANCELLED: 已取消
   - ARCHIVED: 已归档

5. **PlanStatus（方案状态）**
   - DRAFT: 草稿
   - GENERATING: 生成中
   - REVIEWING: 审核中
   - APPROVED: 已批准
   - REJECTED: 已拒绝
   - ARCHIVED: 已归档

## 应用服务

### ConsultationApplicationService
- 创建咨询用例
- 分配顾问用例
- 完成/取消咨询用例
- 查询咨询列表用例

### PlanGenerationApplicationService
- 创建方案用例
- 开始/完成方案生成用例
- 批准/拒绝方案用例
- 查询方案列表用例

### ConsultantApplicationService
- 创建/更新顾问用例
- 激活/停用顾问用例
- 查询顾问列表用例
- 获取工作负载用例

## 领域服务

领域服务直接位于 `domain/` 目录下，处理跨聚合的业务逻辑：

### ConsultationDomainService
- 咨询创建验证
- 顾问分配检查
- 状态转换验证
- 咨询摘要生成

### PlanGenerationDomainService
- 方案创建验证
- 内容验证
- 状态转换检查
- 方案摘要生成

### ConsultantDomainService
- 顾问创建验证
- 专业能力检查
- 工作负载管理

## 数据转换

采用统一的转换器模式，每个聚合根都有对应的转换器：

- **ConsultationConverter**: 咨询数据转换
- **PlanConverter**: 方案数据转换
- **ConsultantConverter**: 顾问数据转换

转换器位于 `converters/` 目录中，负责：
- 领域实体与API Schema之间的转换
- 领域实体与ORM模型之间的转换
- 请求数据与领域对象参数之间的转换

## 仓储模式

每个聚合根都有对应的仓储实现：

- **ConsultationRepository**: 咨询数据访问
- **PlanRepository**: 方案数据访问
- **ConsultantRepository**: 顾问数据访问

## 外部服务集成

### AIService
- 咨询信息分析
- 方案内容生成
- 方案优化
- 咨询总结生成

## 使用示例

### 创建咨询

```python
from app.services.consultation import ConsultationApplicationService

# 创建咨询
consultation = await consultation_app_service.create_consultation_use_case(
    ConsultationCreate(
        customer_id="customer-123",
        title="客户咨询",
        metadata={"type": "general"}
    )
)
```

### 生成方案

```python
from app.services.consultation import PlanGenerationApplicationService

# 创建方案
plan = await plan_app_service.create_plan_use_case(
    PlanCreate(
        consultation_id="consultation-123",
        customer_id="customer-123",
        consultant_id="consultant-456",
        title="个性化方案",
        content={"summary": "方案摘要", "recommendations": []}
    )
)
```

## 设计原则

1. **单一职责**: 每个类只负责一个明确的职责
2. **依赖倒置**: 依赖抽象而非具体实现
3. **开闭原则**: 对扩展开放，对修改关闭
4. **领域驱动**: 以业务概念为核心设计代码结构
5. **分层架构**: 清晰的职责分离和依赖方向

## 扩展指南

### 添加新的聚合根

1. 在 `domain/entities/` 中创建实体
2. 在 `domain/value_objects/` 中创建值对象
3. 在 `converters/` 中创建转换器
4. 在 `infrastructure/repositories/` 中创建仓储
5. 在 `application/` 中创建应用服务

### 添加新的领域服务

1. 在 `domain/domain_services/` 中创建领域服务
2. 实现跨聚合的业务逻辑
3. 在应用服务中注入和使用

### 添加新的外部服务

1. 在 `infrastructure/external_services/` 中创建服务
2. 实现与外部系统的集成
3. 在应用服务中注入和使用
