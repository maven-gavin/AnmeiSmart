# MCP工具分组server_code字段实现文档

## 功能概述

为MCP工具分组管理系统添加了`server_code`字段，实现了每个分组拥有独立的MCP Server URL用于外部系统接入。

## 实现特性

### 1. 核心功能
- ✅ 每个MCP分组自动生成唯一的`server_code`
- ✅ server_code格式：16字符URL安全字符串（如：`sm1m39DzCmoqmjp6`）
- ✅ 完整MCP Server URL格式：`http://[domain]/mcp/server/[server_code]/mcp`
- ✅ 管理员可以在界面中复制完整的MCP Server URL
- ✅ 只有启用的分组才显示可复制的Server URL

### 2. 数据库变更
- ✅ 添加`server_code`字段到`mcp_tool_groups`表
- ✅ 字段类型：`String(32), nullable=True, unique=True, index=True`
- ✅ 添加唯一性约束：`uq_mcp_groups_server_code`
- ✅ 创建数据库迁移：`0c496d1b37a1_添加mcp分组server_code字段.py`

### 3. 后端实现
- ✅ 更新`MCPToolGroup`数据库模型
- ✅ 更新`MCPGroupInfo` Schema添加`server_code`字段
- ✅ 添加`MCPServerUrlResponse` Schema用于API响应
- ✅ 扩展`MCPGroupService`服务类：
  - `_generate_server_code()`: 生成唯一server_code
  - `build_mcp_server_url()`: 构建完整URL
  - `get_group_server_url()`: 获取分组的完整URL
  - `ensure_server_code()`: 确保分组有server_code
- ✅ 添加新API端点：`GET /mcp/admin/groups/{group_id}/server-url`

### 4. 前端实现
- ✅ 更新`MCPGroup`接口添加`server_code`字段
- ✅ 添加`getGroupServerUrl()`服务方法
- ✅ 更新`useMCPConfigs` hook添加URL获取功能
- ✅ 更新`MCPConfigPanel`组件：
  - 新增"MCP Server URL"列
  - 显示server_code路径预览
  - 复制完整URL按钮
  - 复制成功状态提示
  - 禁用分组显示灰色状态

## 用户界面

### 分组列表表格
| 序号 | 分组名称 | 分组描述 | API密钥 | MCP Server URL | 工具数量 | 状态 | 创建时间 | 操作 |
|------|----------|----------|---------|----------------|----------|------|----------|------|
| 1 | 测试分组 | 描述信息 | `mcp_key_***` [📋] | `/mcp/server/****/mcp` [📋] | 3个 | ✅ | 2025-08-16 | ... |

### URL复制功能
- 当分组启用时，显示server_code路径预览和复制按钮
- 点击复制按钮获取完整URL（包含当前域名）
- 复制成功后按钮显示绿色勾选图标
- 当分组禁用时，显示"分组已禁用"灰色文字

## API接口

### 获取MCP Server URL
```http
GET /api/v1/mcp/admin/groups/{group_id}/server-url?base_url={base_url}
Authorization: Bearer {admin_token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "server_url": "http://localhost:8000/mcp/server/sm1m39DzCmoqmjp6/mcp",
    "server_code": "sm1m39DzCmoqmjp6"
  },
  "message": "MCP Server URL获取成功"
}
```

## 业务逻辑

### server_code生成规则
1. 新建分组时自动生成16字符的URL安全字符串
2. 确保server_code在全局范围内唯一
3. 对于现有分组，调用API时自动生成server_code（懒加载）

### URL构建规则
1. 基础URL可通过API参数自定义，默认从当前请求域名获取
2. URL格式：`{base_url}/mcp/server/{server_code}/mcp`
3. 前端自动使用`window.location`获取当前域名

### 权限控制
- 只有管理员可以获取完整的MCP Server URL
- 普通用户在分组列表中只能看到server_code路径预览
- 通过API密钥进行MCP工具调用权限验证

## 测试验证

### 功能测试
- ✅ 创建新分组自动生成server_code
- ✅ server_code全局唯一性验证
- ✅ 完整URL获取和构建功能
- ✅ 前端UI复制功能正常
- ✅ 管理员权限验证通过

### API测试
```bash
# 测试脚本运行结果
🧪 测试MCP分组server_code功能...
📝 尝试登录...
✅ 登录成功
📝 创建测试MCP分组...
✅ 分组创建成功
   分组ID: f85bdd71-3650-4a72-b349-00f39596cf59
   Server Code: sm1m39DzCmoqmjp6
📝 获取MCP Server URL...
✅ Server URL获取成功
   完整URL: http://localhost:8000/mcp/server/sm1m39DzCmoqmjp6/mcp
   Server Code: sm1m39DzCmoqmjp6
📝 验证分组列表中的server_code...
✅ 在分组列表中找到测试分组
   Server Code: sm1m39DzCmoqmjp6
📝 清理测试数据...
✅ 测试分组已删除

🎉 MCP server_code功能测试完成！
```

## 技术细节

### 数据库迁移
```sql
-- 添加server_code字段
ALTER TABLE mcp_tool_groups 
ADD COLUMN server_code VARCHAR(32) NULL 
COMMENT 'MCP服务器代码（用于URL路径）';

-- 创建唯一索引
CREATE UNIQUE INDEX ix_mcp_tool_groups_server_code 
ON mcp_tool_groups (server_code);

-- 创建唯一约束
ALTER TABLE mcp_tool_groups 
ADD CONSTRAINT uq_mcp_groups_server_code 
UNIQUE (server_code);
```

### 核心算法
```python
@staticmethod
def _generate_server_code() -> str:
    """生成唯一的服务器代码"""
    return secrets.token_urlsafe(12)  # 生成16字符的URL安全字符串

@staticmethod
def build_mcp_server_url(server_code: str, base_url: str = None) -> str:
    """构建完整的MCP Server URL"""
    if not base_url:
        base_url = "http://localhost:8000"
    base_url = base_url.rstrip('/')
    return f"{base_url}/mcp/server/{server_code}/mcp"
```

## 文件变更清单

### 后端文件
- `api/app/db/models/mcp.py` - 添加server_code字段
- `api/app/schemas/mcp.py` - 更新Schema添加server_code和URL响应
- `api/app/services/mcp_group_service.py` - 扩展服务类功能
- `api/app/api/v1/endpoints/mcp_config.py` - 添加新API端点
- `api/migrations/versions/0c496d1b37a1_*.py` - 数据库迁移文件

### 前端文件
- `web/src/service/mcpConfigService.ts` - 添加URL获取服务方法
- `web/src/hooks/useMCPConfigs.ts` - 扩展hook功能
- `web/src/components/settings/MCPConfigPanel.tsx` - 更新UI组件

## 部署说明

1. **数据库迁移**：运行`alembic upgrade head`应用数据库变更
2. **后端重启**：重启后端服务以加载新的API端点
3. **前端重构**：重新构建前端应用
4. **功能验证**：登录管理后台验证MCP分组管理功能

## 使用示例

### 外部系统集成
```json
{
  "mcpServerUrl": "http://your-domain.com/mcp/server/sm1m39DzCmoqmjp6/mcp",
  "apiKey": "mcp_key_xxxxxxxxxxxx",
  "description": "用于Dify Agent的MCP工具集成"
}
```

### Dify MCP配置
```json
{
  "mcpServers": {
    "anmei-smart": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "env": {
        "FETCH_MCP_SERVER_URL": "http://your-domain.com/mcp/server/sm1m39DzCmoqmjp6/mcp",
        "FETCH_MCP_API_KEY": "mcp_key_xxxxxxxxxxxx"
      }
    }
  }
}
```

---

**实现完成时间**: 2025-08-16  
**测试状态**: ✅ 全部通过  
**部署状态**: 🚀 准备就绪
