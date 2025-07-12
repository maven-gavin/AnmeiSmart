# AI辅助方案生成 API 文档

## 概述

AI辅助方案生成功能提供了完整的RESTful API接口，支持方案生成会话管理、信息分析、方案生成、优化调整等核心功能。所有API接口遵循统一的设计规范，支持标准的HTTP状态码和JSON格式。

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证说明

所有API请求需要在Header中包含有效的JWT Token：

```http
Authorization: Bearer <your-jwt-token>
```

## API接口列表

### 1. 会话管理接口

#### 1.1 创建方案生成会话

**接口**: `POST /plan-generation/sessions/`

**描述**: 创建新的方案生成会话

**请求参数**:
```json
{
  "conversation_id": "string",
  "customer_id": "string", 
  "consultant_id": "string",
  "session_metadata": {
    "created_by": "consultant",
    "creation_context": "chat_interface"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "session_123",
    "conversation_id": "conv_456",
    "customer_id": "cust_789",
    "consultant_id": "cons_101",
    "status": "collecting",
    "required_info": ["basic_info", "concerns", "budget", "timeline", "expectations"],
    "extracted_info": {},
    "interaction_history": [],
    "created_at": "2025-01-13T10:30:00Z",
    "updated_at": "2025-01-13T10:30:00Z"
  }
}
```

#### 1.2 获取会话详情

**接口**: `GET /plan-generation/sessions/{session_id}`

**描述**: 获取指定会话的详细信息

**路径参数**:
- `session_id` (string): 会话ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "session_123",
    "conversation_id": "conv_456",
    "customer_id": "cust_789",
    "consultant_id": "cons_101",
    "status": "generating",
    "required_info": ["basic_info", "concerns", "budget", "timeline", "expectations"],
    "extracted_info": {
      "basic_info": {
        "name": "李小姐",
        "age": 28,
        "skin_type": "敏感性"
      },
      "concerns": ["双眼皮", "眼袋"],
      "budget": "10000-15000",
      "timeline": "3个月内"
    },
    "interaction_history": [
      {
        "timestamp": "2025-01-13T10:30:00Z",
        "action": "session_created",
        "actor": "consultant",
        "details": {}
      }
    ],
    "created_at": "2025-01-13T10:30:00Z",
    "updated_at": "2025-01-13T10:45:00Z"
  }
}
```

#### 1.3 通过对话ID获取会话

**接口**: `GET /plan-generation/sessions/by-conversation/{conversation_id}`

**描述**: 根据对话ID获取关联的方案生成会话

**路径参数**:
- `conversation_id` (string): 对话ID

**响应示例**: 同1.2接口响应格式

#### 1.4 更新会话状态

**接口**: `PUT /plan-generation/sessions/{session_id}/status`

**描述**: 更新会话状态

**路径参数**:
- `session_id` (string): 会话ID

**请求参数**:
```json
{
  "status": "generating",
  "status_metadata": {
    "reason": "user_triggered",
    "timestamp": "2025-01-13T10:45:00Z"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "会话状态更新成功",
  "data": {
    "session_id": "session_123",
    "old_status": "collecting",
    "new_status": "generating",
    "updated_at": "2025-01-13T10:45:00Z"
  }
}
```

### 2. 信息分析接口

#### 2.1 分析对话信息

**接口**: `POST /plan-generation/analyze-conversation`

**描述**: 分析对话内容，提取客户信息并评估完整性

**请求参数**:
```json
{
  "conversation_id": "conv_456",
  "force_analysis": false,
  "analysis_options": {
    "include_sentiment": true,
    "include_suggestions": true
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_456",
    "analysis_id": "analysis_789",
    "completeness_score": 0.85,
    "missing_categories": ["medical_history"],
    "extracted_info": {
      "basic_info": {
        "name": "李小姐",
        "age": 28,
        "skin_type": "敏感性"
      },
      "concerns": ["双眼皮", "眼袋"],
      "budget": "10000-15000",
      "timeline": "3个月内",
      "expectations": "自然效果"
    },
    "suggestions": [
      "建议与客户确认是否有相关手术史",
      "了解客户的过敏史和用药情况",
      "确认客户对手术风险的了解程度"
    ],
    "can_generate_plan": true,
    "confidence_score": 0.92,
    "analyzed_at": "2025-01-13T10:45:00Z"
  }
}
```

#### 2.2 获取信息完整性

**接口**: `GET /plan-generation/sessions/{session_id}/completeness`

**描述**: 获取会话的信息完整性评估

**路径参数**:
- `session_id` (string): 会话ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "session_id": "session_123",
    "basic_info": "complete",
    "concerns": "complete", 
    "budget": "complete",
    "timeline": "partial",
    "medical_history": "missing",
    "completeness_score": 0.75,
    "missing_categories": ["medical_history"],
    "suggestions": [
      "建议了解客户的既往手术史",
      "确认客户是否有过敏史"
    ],
    "last_updated": "2025-01-13T10:45:00Z"
  }
}
```

### 3. 方案生成接口

#### 3.1 生成方案

**接口**: `POST /plan-generation/generate-plan`

**描述**: 基于分析结果生成个性化方案

**请求参数**:
```json
{
  "conversation_id": "conv_456",
  "force_generation": false,
  "generation_options": {
    "template_type": "comprehensive",
    "include_timeline": true,
    "include_cost_breakdown": true,
    "style_preferences": {
      "tone": "professional",
      "detail_level": "detailed"
    }
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "generation_id": "gen_456",
    "session_id": "session_123",
    "draft_id": "draft_789",
    "status": "completed",
    "generated_content": {
      "summary": "基于您的需求，我们为您推荐以下个性化医美方案...",
      "customer_info": {
        "name": "李小姐",
        "age": 28,
        "concerns": ["双眼皮", "眼袋"]
      },
      "treatments": [
        {
          "name": "双眼皮成形术",
          "description": "采用微创技术，恢复期短",
          "expected_result": "自然双眼皮效果",
          "priority": "高"
        }
      ],
      "timeline": [
        {
          "phase": "术前准备",
          "duration": "1-2周",
          "description": "术前检查和准备"
        },
        {
          "phase": "手术实施", 
          "duration": "2-3小时",
          "description": "手术操作"
        },
        {
          "phase": "术后恢复",
          "duration": "2-4周",
          "description": "恢复期护理"
        }
      ],
      "cost": {
        "双眼皮成形术": "8000",
        "术后护理": "1000",
        "总计": "9000"
      },
      "precautions": [
        "术前避免阿司匹林类药物",
        "术后注意伤口护理",
        "定期复查"
      ]
    },
    "quality_score": 0.95,
    "generation_time": 28.5,
    "generated_at": "2025-01-13T11:00:00Z"
  }
}
```

#### 3.2 获取生成状态

**接口**: `GET /plan-generation/generate-plan/{generation_id}/status`

**描述**: 获取方案生成的实时状态

**路径参数**:
- `generation_id` (string): 生成任务ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "generation_id": "gen_456",
    "status": "processing",
    "progress": 0.65,
    "current_stage": "content_generation",
    "estimated_remaining_time": 15,
    "started_at": "2025-01-13T11:00:00Z",
    "last_updated": "2025-01-13T11:00:28Z"
  }
}
```

### 4. 方案管理接口

#### 4.1 获取方案草稿列表

**接口**: `GET /plan-generation/sessions/{session_id}/drafts`

**描述**: 获取会话的所有方案草稿

**路径参数**:
- `session_id` (string): 会话ID

**查询参数**:
- `limit` (int, optional): 返回数量限制，默认10
- `offset` (int, optional): 偏移量，默认0
- `status` (string, optional): 过滤状态

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total": 3,
    "drafts": [
      {
        "id": "draft_789",
        "session_id": "session_123",
        "version": 1,
        "content": {
          "summary": "基于您的需求，我们为您推荐...",
          "treatments": [...],
          "timeline": [...],
          "cost": {...},
          "precautions": [...]
        },
        "status": "approved",
        "feedback": [],
        "improvements": [],
        "quality_score": 0.95,
        "created_at": "2025-01-13T11:00:00Z",
        "updated_at": "2025-01-13T11:15:00Z"
      }
    ]
  }
}
```

#### 4.2 获取方案草稿详情

**接口**: `GET /plan-generation/drafts/{draft_id}`

**描述**: 获取指定方案草稿的详细信息

**路径参数**:
- `draft_id` (string): 草稿ID

**响应示例**: 同4.1中单个草稿的格式

#### 4.3 更新方案草稿

**接口**: `PUT /plan-generation/drafts/{draft_id}`

**描述**: 更新方案草稿内容

**路径参数**:
- `draft_id` (string): 草稿ID

**请求参数**:
```json
{
  "content": {
    "summary": "更新后的方案概要...",
    "treatments": [...],
    "timeline": [...],
    "cost": {...}
  },
  "status": "reviewing",
  "update_metadata": {
    "updated_by": "consultant",
    "update_reason": "customer_feedback"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "方案草稿更新成功",
  "data": {
    "draft_id": "draft_789",
    "version": 2,
    "updated_fields": ["content", "status"],
    "updated_at": "2025-01-13T11:30:00Z"
  }
}
```

### 5. 方案优化接口

#### 5.1 优化方案

**接口**: `POST /plan-generation/optimize-plan`

**描述**: 基于要求优化现有方案

**请求参数**:
```json
{
  "draft_id": "draft_789",
  "optimization_type": "cost",
  "requirements": {
    "description": "降低费用预算，控制在8000元以内",
    "type": "cost",
    "priority": "high"
  },
  "optimization_options": {
    "preserve_quality": true,
    "maintain_timeline": false
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "optimization_id": "opt_123",
    "original_draft_id": "draft_789",
    "optimized_draft_id": "draft_890",
    "optimization_type": "cost",
    "changes_made": [
      {
        "category": "treatments",
        "change": "adjusted_pricing",
        "description": "优化项目组合，降低总费用"
      },
      {
        "category": "timeline",
        "change": "timeline_adjusted", 
        "description": "调整时间安排以配合新方案"
      }
    ],
    "cost_comparison": {
      "original": "9000",
      "optimized": "7500",
      "savings": "1500"
    },
    "quality_impact": {
      "original_score": 0.95,
      "optimized_score": 0.92,
      "impact_level": "minimal"
    },
    "optimized_at": "2025-01-13T11:45:00Z"
  }
}
```

#### 5.2 获取优化状态

**接口**: `GET /plan-generation/optimize-plan/{optimization_id}/status`

**描述**: 获取方案优化的实时状态

**路径参数**:
- `optimization_id` (string): 优化任务ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "optimization_id": "opt_123",
    "status": "completed",
    "progress": 1.0,
    "current_stage": "finalization",
    "optimization_time": 18.3,
    "started_at": "2025-01-13T11:45:00Z",
    "completed_at": "2025-01-13T11:45:18Z"
  }
}
```

### 6. 反馈管理接口

#### 6.1 提交反馈

**接口**: `POST /plan-generation/drafts/{draft_id}/feedback`

**描述**: 为方案草稿提交反馈

**路径参数**:
- `draft_id` (string): 草稿ID

**请求参数**:
```json
{
  "feedback_type": "improvement",
  "category": "content",
  "rating": 4,
  "comments": "整体方案很好，建议增加术后护理的详细说明",
  "suggestions": [
    "增加术后护理指导",
    "提供更多恢复期的注意事项"
  ],
  "submitter": {
    "type": "customer",
    "id": "cust_789"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "feedback_id": "feedback_456",
    "draft_id": "draft_789",
    "feedback_type": "improvement",
    "category": "content",
    "rating": 4,
    "comments": "整体方案很好，建议增加术后护理的详细说明",
    "suggestions": [
      "增加术后护理指导",
      "提供更多恢复期的注意事项"
    ],
    "status": "pending",
    "submitted_at": "2025-01-13T12:00:00Z"
  }
}
```

#### 6.2 获取反馈列表

**接口**: `GET /plan-generation/drafts/{draft_id}/feedback`

**描述**: 获取方案草稿的所有反馈

**路径参数**:
- `draft_id` (string): 草稿ID

**查询参数**:
- `feedback_type` (string, optional): 反馈类型过滤
- `status` (string, optional): 状态过滤

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total": 2,
    "feedback": [
      {
        "feedback_id": "feedback_456",
        "feedback_type": "improvement",
        "category": "content",
        "rating": 4,
        "comments": "整体方案很好，建议增加术后护理的详细说明",
        "suggestions": ["增加术后护理指导"],
        "status": "addressed",
        "submitter": {
          "type": "customer",
          "id": "cust_789"
        },
        "submitted_at": "2025-01-13T12:00:00Z",
        "addressed_at": "2025-01-13T12:15:00Z"
      }
    ]
  }
}
```

### 7. 统计和监控接口

#### 7.1 获取生成统计

**接口**: `GET /plan-generation/statistics`

**描述**: 获取方案生成的统计信息

**查询参数**:
- `start_date` (string, optional): 开始日期 (ISO format)
- `end_date` (string, optional): 结束日期 (ISO format)
- `consultant_id` (string, optional): 顾问ID过滤

**响应示例**:
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2025-01-01T00:00:00Z",
      "end_date": "2025-01-13T23:59:59Z"
    },
    "summary": {
      "total_sessions": 156,
      "total_plans_generated": 142,
      "success_rate": 0.951,
      "average_generation_time": 32.5,
      "average_quality_score": 0.927
    },
    "breakdown_by_day": [
      {
        "date": "2025-01-13",
        "sessions_created": 12,
        "plans_generated": 11,
        "success_rate": 0.917,
        "average_time": 28.3
      }
    ],
    "top_optimization_types": [
      {"type": "cost", "count": 45},
      {"type": "timeline", "count": 32},
      {"type": "content", "count": 28}
    ]
  }
}
```

#### 7.2 健康检查

**接口**: `GET /plan-generation/health`

**描述**: 检查API服务健康状态

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-01-13T12:30:00Z",
    "version": "1.0.0",
    "uptime": 86400,
    "dependencies": {
      "database": "connected",
      "ai_service": "available",
      "cache": "operational"
    },
    "performance": {
      "avg_response_time": 245,
      "requests_per_minute": 12.5,
      "error_rate": 0.002
    }
  }
}
```

## 错误处理

### 错误响应格式

所有错误响应都遵循统一的格式：

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "conversation_id",
      "issue": "缺少必需参数"
    },
    "timestamp": "2025-01-13T12:30:00Z",
    "request_id": "req_789"
  }
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `FORBIDDEN` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `INTERNAL_SERVER_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | AI服务不可用 |
| `GENERATION_TIMEOUT` | 504 | 方案生成超时 |

## 使用示例

### 完整的方案生成流程

```javascript
// 1. 创建会话
const session = await fetch('/api/v1/plan-generation/sessions/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    conversation_id: 'conv_456',
    customer_id: 'cust_789',
    consultant_id: 'cons_101',
    session_metadata: {
      created_by: 'consultant',
      creation_context: 'chat_interface'
    }
  })
});

// 2. 分析对话信息
const analysis = await fetch('/api/v1/plan-generation/analyze-conversation', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    conversation_id: 'conv_456',
    force_analysis: true
  })
});

// 3. 生成方案
const generation = await fetch('/api/v1/plan-generation/generate-plan', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    conversation_id: 'conv_456',
    generation_options: {
      template_type: 'comprehensive',
      include_timeline: true,
      include_cost_breakdown: true
    }
  })
});

// 4. 优化方案（可选）
const optimization = await fetch('/api/v1/plan-generation/optimize-plan', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    draft_id: 'draft_789',
    optimization_type: 'cost',
    requirements: {
      description: '降低费用预算，控制在8000元以内',
      type: 'cost'
    }
  })
});
```

## 速率限制

为确保服务稳定性，API实施以下速率限制：

- **普通接口**: 每分钟100请求
- **方案生成接口**: 每分钟10请求
- **方案优化接口**: 每分钟5请求

当超过速率限制时，API将返回429状态码和以下响应：

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超过限制",
    "details": {
      "limit": 10,
      "window": "1 minute",
      "retry_after": 30
    }
  }
}
```

## 版本控制

API采用URL路径版本控制，当前版本为v1。未来版本升级时，会保持向后兼容性，并提前通知弃用计划。

## 支持和反馈

如果您在使用API过程中遇到问题，请通过以下方式联系我们：

- **技术文档**: [完整技术文档链接]
- **问题反馈**: [GitHub Issues链接]
- **技术支持**: [联系方式]

---

*本文档最后更新时间：2025-01-13* 