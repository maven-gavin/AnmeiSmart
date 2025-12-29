# Copilot 模式：任务意图路由（Dify 配置指南）

## 目标
- **输入**：员工正常聊天文本（不需要填 `scene_key`）
- **处理**：后端调用 Dify（LLM）做“意图路由”，输出 `scene_key`
- **输出**：
  - 命中任务/敏感规则后，后端通过 WebSocket 广播 `system_notification`，前端 toast 及时提示“去处理”

---

## 一、后端实现约定（你只需要按这个配置 Dify）

后端会在缺省 `scene_key` 时调用 Dify Router，并要求 **只输出 JSON**：

```json
{ "scene_key": "sales_delivery", "intent": "urge_shipment", "confidence": 0.86 }
```

- **scene_key**：必须是候选列表中的一个；无法判断时返回 `null`
- **intent**：可选（便于分析/埋点/提示文案），不强制
- **confidence**：可选

后端候选场景来自数据库中启用的任务路由规则 `task_routing_rules.enabled=true` 的 `scene_key` 去重列表。

---

## 二、在 Dify 创建 Router 应用

### 1) 推荐：创建一个 Chat 类型应用（最省事）
- **App Type**：Chat
- **模型**：任意你现有可用的 LLM（建议支持中文、稳定输出 JSON）
- **System Prompt**（建议直接粘贴）：

```text
你是企业聊天副驾驶的“意图路由器”。
你的任务：根据用户文本的语义，从候选场景列表中选择最匹配的 scene_key。
必须只输出 JSON，不要输出任何解释、markdown、代码块标记。

输出格式：
{ "scene_key": string|null, "intent": string|null, "confidence": number|null }

规则：
- 如果无法判断或不属于任何候选场景，scene_key=null。
- scene_key 必须严格等于候选列表中的一个值。
```

说明：后端会把 `候选 scene_key 列表` 与 `用户文本` 拼进 query 里，所以 Dify 不需要额外表单字段。

### 2) 获取 API Key
在 Dify 应用里生成 **API Key**（每个 App 一个 Key）。

---

## 三、在 AnmeiSmart 后台录入 Router 配置（必须）

进入管理后台的 **Agent 配置**（项目里对应 `agent_configs` 表），新增一条：

- **app_name**：`任务意图路由器`（必须，后端按这个名称查找）
- **app_id**：随意（例如 `task_router`）
- **base_url**：你的 Dify 地址（例如 `http://localhost/v1` 或 `https://api.dify.ai/v1`）
- **api_key**：上一步拿到的 Dify App API Key
- **enabled**：开启
- **agent_type**：可选

> 不需要环境变量；后端会从数据库读取并解密 api_key。

---

## 四、验证路径（你可直接这样验收）

1. 打开聊天页面，正常发一条客户消息（例如“这个单子今天必须发货了，麻烦催一下”）
2. 后端会自动走 `/api/v1/tasks/route`：
   - 无 `scene_key` → Dify router → 得到 scene_key → 生成任务/敏感拦截（如果命中）
3. 命中时前端会收到 WebSocket `system_notification`，弹 toast，并可点击“去处理”跳转任务中心。


