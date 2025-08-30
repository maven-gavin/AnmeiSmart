# DDD目录结构规范指南

## 概述

本文档基于DDD（领域驱动设计）架构原则，定义了项目中服务模块的标准目录结构规范。该规范确保代码组织的一致性、可维护性和可扩展性。

## 标准目录结构

### 完整DDD分层目录结构

```
api/app/services/{domain}/
├── __init__.py                    # 模块入口，导出主要应用服务
├── application/                   # 应用层 - 用例编排和事务管理
│   ├── __init__.py
│   ├── {domain}_application_service.py
│   └── {sub_domain}_application_service.py
├── domain/                        # 领域层 - 核心业务逻辑
│   ├── __init__.py
│   ├── entities/                  # 聚合根和实体
│   │   ├── __init__.py
│   │   ├── {aggregate_root}.py
│   │   └── {entity}.py
│   ├── value_objects/            # 值对象
│   │   ├── __init__.py
│   │   ├── {value_object}.py
│   │   └── {enum}.py
│   ├── {domain}_domain_service.py
│   └── {sub_domain}_domain_service.py
├── infrastructure/               # 基础设施层 - 数据访问和外部服务
│   ├── __init__.py
│   ├── repositories/             # 仓储实现
│   │   ├── __init__.py
│   │   ├── {aggregate_root}_repository.py
│   │   └── {entity}_repository.py
│   └── external_services/        # 外部服务集成
│       ├── __init__.py
│       └── {external_service}.py
└── converters/                   # 数据转换层 - 格式转换
    ├── __init__.py
    ├── {aggregate_root}_converter.py
    └── {entity}_converter.py
```

## 目录命名规范

### 顶层目录
- **推荐**: 使用领域名称作为服务目录名
- **位置**: `api/app/services/{domain}/`
- **示例**: `consultation/`, `user/`, `order/`

### 应用层目录
- **推荐**: 使用 `application/` 目录
- **职责**: 用例编排、事务管理、依赖注入
- **命名**: 应用服务文件使用 `{domain}_application_service.py` 格式

### 领域层目录
- **推荐**: 使用 `domain/` 目录
- **职责**: 核心业务逻辑、领域规则、聚合设计
- **子目录**:
  - `entities/`: 聚合根和实体
  - `value_objects/`: 值对象和枚举
  - 领域服务直接放在 `domain/` 目录下

### 基础设施层目录
- **推荐**: 使用 `infrastructure/` 目录
- **职责**: 数据访问、外部服务集成、技术实现
- **子目录**:
  - `repositories/`: 仓储实现
  - `external_services/`: 外部服务集成

### 转换器目录
- **推荐**: 使用 `converters/` 目录
- **职责**: 数据格式转换、API Schema映射
- **命名**: 转换器文件使用 `{aggregate_root}_converter.py` 格式

## 文件命名规范

### 聚合根和实体
- **文件命名**: `{aggregate_root}.py`, `{entity}.py`
- **类命名**: `{AggregateRoot}`, `{Entity}`
- **示例**: `consultation.py` → `Consultation`, `plan.py` → `Plan`

### 值对象
- **文件命名**: `{value_object}.py`
- **类命名**: `{ValueObject}`
- **示例**: `consultation_status.py` → `ConsultationStatus`

### 领域服务
- **文件命名**: `{domain}_domain_service.py`
- **类命名**: `{Domain}DomainService`
- **示例**: `consultation_domain_service.py` → `ConsultationDomainService`

### 应用服务
- **文件命名**: `{domain}_application_service.py`
- **类命名**: `{Domain}ApplicationService`
- **示例**: `consultation_application_service.py` → `ConsultationApplicationService`

### 仓储
- **文件命名**: `{aggregate_root}_repository.py`
- **类命名**: `{AggregateRoot}Repository`
- **示例**: `consultation_repository.py` → `ConsultationRepository`

### 转换器
- **文件命名**: `{aggregate_root}_converter.py`
- **类命名**: `{AggregateRoot}Converter`
- **示例**: `consultation_converter.py` → `ConsultationConverter`

## 实际示例：咨询服务模块

```
api/app/services/consultation/
├── __init__.py                    # 导出主要应用服务
├── application/                   # 应用层
│   ├── __init__.py
│   ├── consultation_application_service.py
│   ├── plan_generation_application_service.py
│   └── consultant_application_service.py
├── domain/                        # 领域层
│   ├── __init__.py
│   ├── entities/                  # 聚合根和实体
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

## 目录结构最佳实践

### 1. 分层原则
- **依赖方向**: 确保依赖方向指向领域层
- **职责分离**: 每层只负责自己的职责
- **接口隔离**: 上层通过接口依赖下层，不依赖具体实现

### 2. 目录组织原则
- **单一职责**: 每个目录只包含相关功能的文件
- **高内聚低耦合**: 相关功能放在一起，减少跨目录依赖
- **可扩展性**: 目录结构支持功能扩展和重构

### 3. 命名一致性
- **统一风格**: 所有目录和文件使用一致的命名风格
- **语义化命名**: 目录和文件名应反映其内容和用途
- **避免缩写**: 使用完整的单词，避免缩写造成歧义

### 4. 文件组织原则
- **按类型分组**: 相同类型的文件放在同一目录下
- **按功能分组**: 相关功能的文件可以放在同一目录下
- **避免过深嵌套**: 目录嵌套不超过4层

## 常见目录结构模式

### 模式1：标准DDD分层（推荐）
```
{domain}/
├── application/
├── domain/
├── infrastructure/
└── converters/
```

### 模式2：按功能分组
```
{domain}/
├── core/              # 核心业务逻辑
├── application/       # 应用服务
├── infrastructure/    # 基础设施
└── shared/           # 共享组件
```

### 模式3：按模块分组
```
{domain}/
├── {sub_domain1}/
├── {sub_domain2}/
└── shared/
```

## 目录结构检查清单

### 创建新服务时
- [ ] 是否遵循标准DDD分层结构？
- [ ] 目录命名是否符合规范？
- [ ] 文件命名是否符合规范？
- [ ] 是否包含必要的 `__init__.py` 文件？
- [ ] 导入路径是否正确？

### 重构现有服务时
- [ ] 是否保持了向后兼容性？
- [ ] 是否更新了所有相关导入？
- [ ] 是否更新了文档？
- [ ] 是否进行了充分的测试？

## 注意事项

### 1. 避免的反模式
- ❌ 不要创建过深的目录嵌套
- ❌ 不要使用不一致的命名风格
- ❌ 不要将不同职责的文件混在一起
- ❌ 不要忽略 `__init__.py` 文件

### 2. 性能考虑
- 合理使用 `__init__.py` 文件控制导入
- 避免循环导入
- 使用延迟导入减少启动时间

### 3. 团队协作
- 建立团队统一的目录结构规范
- 在代码审查中检查目录结构合规性
- 定期重构和优化目录结构

## 总结

遵循DDD目录结构规范可以带来以下好处：

1. **一致性**: 统一的目录结构便于理解和维护
2. **可维护性**: 清晰的职责分离便于修改和扩展
3. **可扩展性**: 标准化的结构支持功能扩展
4. **团队协作**: 统一的规范减少沟通成本
5. **代码质量**: 规范的目录结构有助于提高代码质量

通过遵循本规范，团队可以建立统一的代码组织标准，提高开发效率和代码质量。
