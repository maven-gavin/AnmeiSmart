## 客户画像飞轮（Customer Insight Flywheel）当前状态记录

更新时间：2026-01-13
范围：后端（客户画像数据模型 + 洞察写回流水线）/ 前端（画像流展示 + 人工录入）

### 1. 需求背景（Why）

我们正在做一个**智能沟通系统**，接收来自不同渠道的客户沟通（站内聊天 + 外部渠道）。目标是：

- **销售与客户沟通**时，系统能在每次客户发消息后：
  - 汇总客户档案 + 客户偏好 + 客户画像 + 历史消息
  - 交给 **SmartBrain（Dify）** 做意图/洞察分析
  - 产出：销售话术建议、待办任务、客户画像沉淀
- 系统能随着沟通变多，**越来越了解客户**（长期记忆）
- 已明确：系统不再是医美专用，不需要记录病史/过敏史等医疗字段

### 2. 总体方案（What / How，不含代码）

#### 2.1 数据模型（双层结构）

- **CustomerProfile（核心档案 / 结构化、少字段）**

  - 用于：列表筛选、快速概览、轻量 BI
  - 主要字段：`life_cycle_stage`、`industry`、`company_scale`、`ai_summary`、`extra_data`
- **CustomerInsight（动态洞察 / 时间流、原子化事实）**

  - 用于：LLM 上下文记忆 + “朋友圈式最新在上”的洞察墙
  - 核心字段：`category`、`content`、`source(ai/human)`、`status(active/archived)`、`confidence`
  - 关键特性：
    - **保留时间线**
    - 支持人工 CRUD
    - 支持状态管理（active/archived）用于处理新旧冲突（最终规则待确认）

#### 2.2 AI 写回闭环（消息 -> 洞察 -> 落库 -> 前端展示）

站内客户发消息成功后：

1. 消息入库成功（Chat create_message）
2. 异步触发洞察任务（不阻塞用户发送）
3. 洞察任务：
   - 拉取最近消息上下文 + 现有 active insights + 现有 ai_summary
   - 调用 Dify（blocking 模式）
   - 要求输出严格 JSON（ai_summary + insights[]）
   - 写入：
     - 更新 `customer_profiles.ai_summary`
     - 追加写入 `customer_insights`（source=ai, created_by_name=SmartBrain）
4. 前端画像页再次拉取 profile 即可看到更新

#### 2.3 前端展示（画像页）

- 画像页改为：
  - 顶部展示核心字段（stage/industry/scale）
  - AI 摘要（ai_summary）
  - 画像流（active_insights，最新在上）
  - 支持人工新增洞察与归档洞察
- **不做兼容层**：前端不再使用医美字段（medical_history/allergies/riskNotes/tags/priority/basicInfo 等）

### 3. 已完成进展（Done）

#### 3.1 后端

- **去医疗化重构**
  - 删除 Customer / CustomerProfile 医疗字段（病史/过敏史/偏好等）
  - 新增 `customer_insights` 表
  - CustomerProfile 增加核心字段：stage/industry/scale/ai_summary/extra_data
- **API**
  - 新增洞察：`POST /customers/{customer_id}/insights`
  - 归档洞察：`DELETE /customers/{customer_id}/insights/{insight_id}`
- **AI 写回闭环（站内客户发消息）**
  - 在 `POST /chat/conversations/{conversation_id}/messages` 成功后：
    - 若发送者主角色为 customer 且会话 tag != channel，则异步触发洞察任务
  - 新增异步 pipeline：创建独立 DB Session 执行洞察提取与落库，失败降级只记录日志
- **多渠道入站（已移除）**
  - 原 channels 模块与企业微信集成已下线；历史 tag=channel 的会话数据可能仍存在，但不再有入站/出站能力
- **配置启用方式**
  - 通过 AgentConfig 表按 `app_name="客户画像洞察器"` 精确匹配启用
  - 未配置时自动跳过洞察提取，不影响主流程

#### 3.2 前端

- 客户档案页已替换为画像流页面（AI摘要 + 时间流 + 人工录入/归档）（待办：待调研这个入口在哪里？）
- 客户列表已从 tags/priority 改为展示 lifeCycleStage （TODO：待调研这个入口在哪里？）
- 统一使用新后端契约（profile + active_insights）
- 会话列表显示来源标签（渠道类型）

### 4. 未完成（Todo / Next）

#### 4.1 状态管理（新事实覆盖旧事实）策略（待解释与拍板）

当前仅做了“追加 + 简单去重”，没有对所有维度做强覆盖归档。

- 待办：明确哪些 category 是“单值覆盖”（如 budget/timeline 等），哪些是“多值并存”（如 preference/need 等）
- 待办：覆盖触发时机（AI 写入、人工写入、或两者）
- 待办：是否需要“同类合并/压缩”来控制 token

#### 4.2 多渠道入站（已下线）

原 channels 模块已移除。若后续重新接入外部 IM，需重新设计 adapter 与身份归一方案。

### 5. 待优化（Nice-to-have / Risk）

- **洞察输出稳定性**
  - Dify 输出 JSON 可能不稳定，需要更强的 schema 校验与容错（目前有基础容错/提取）
- **可观测性**
  - 增加洞察任务的日志字段（耗时、写入条数、失败原因分布）
- **幂等**
  - 目前做了“同类同内容”去重，但缺少“以 message_id 为粒度”的严格幂等键
- **性能**
  - profile 查询 active_insights 可考虑增加索引（profile_id, status, created_at desc）

### 6. 下一步计划

1. 完善洞察覆盖/归档策略（见 §4.1）
2. 提升 Dify 输出稳定性与任务幂等性（见 §5）

### 7. 额外的思考，暂时不实现，待上述任务完成后再沟通分析，现在怎么做还没有想好。
#### 1. 消息触发SmartBrain（dify）要做的几件事情
* 如果是客户发的消息： 结合历史消息，客户洞察信息 猜测客户意图，更新客户画像，记录ai摘要，给出top1销售话术，如果有待办任务生成需要待办的任务。

#### 2. 任务管理的一些思考
* ai或手动创建任务，说明任务内容，相关任务信息，待认领状态。
* 如果该任务与任务治理中的规则匹配，又配置了场景队列，在队列中指定了认领人，就自动派发该任务给指定的人
* 任务被认领或确认执行时，如果对应的任务治理中指定了SOP智能体，就触发该智能体去执行任务，未来也可以推送任务信息给自动化工具（例如：manus，工作流等），去完成任务执行的事情，任务管理本身并不做具体执行的事。
* 任务创建的同时，推送消息给用户或发送邮件，短信；让用户知道有待办的任务
* 

#### 3. 全渠道销售服务系统
* 对本系统更清晰的定位是逐步接入更多的渠道，完成全渠道的聚合IM，让用户越使用，系统越理解用户和沟通的对象
* 后期再接入飞书、钉钉或海外渠道；在架构上就考虑这种扩展，在设计上做抽象思维

#### 4. 数字人管理中配置（配置工作，不需要开发）
* 销冠教官： 负责员工销售与产品的培训工作