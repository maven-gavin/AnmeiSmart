# 企业微信本地调试配置指南

## 1. 准备工作

### 1.1 企业微信应用配置

1. **登录企业微信管理后台**
   - 访问：https://work.weixin.qq.com/
   - 使用管理员账号登录

2. **创建自建应用**
   - 进入「应用管理」→「自建」
   - 点击「创建应用」
   - 填写应用名称（如：智能客服系统）
   - 上传应用 Logo（可选）
   - 点击「创建」

3. **获取应用凭证**
   - 在应用详情页面，记录以下信息：
     - **AgentID**：应用ID（在应用详情页可见）
     - **Secret**：应用密钥（点击「查看」获取，需要管理员确认）
     - **CorpID**：企业ID（在「我的企业」→「企业信息」中查看）

4. **配置可信域名（可选，用于网页授权）**
   - 在应用详情页，找到「网页授权及JS-SDK」
   - 设置可信域名（如：`localhost:3000` 或你的域名）

### 1.2 配置接收消息

1. **设置接收消息服务器**
   - 在应用详情页，找到「接收消息」
   - 点击「设置API接收」
   - 填写以下信息：
     - **URL**：`https://your-frp-domain.com/api/v1/channels/webhook/wechat-work` 或 `https://your-server-ip:port/api/v1/channels/webhook/wechat-work`
       - 本地调试需要使用内网穿透工具（推荐使用 FRP，见下方）
     - **Token**：自定义一个字符串（如：`your_random_token_123456`）
     - **EncodingAESKey**：点击「随机获取」或手动输入43位字符
   - 点击「保存」

2. **验证服务器**
   - 保存后，企业微信会立即发送 GET 请求验证服务器
   - 如果验证失败，检查：
     - URL 是否正确
     - Token 是否匹配
     - 服务器是否正常运行

## 2. 本地环境配置

### 2.1 安装内网穿透工具（推荐 FRP）

**方式一：使用 FRP（推荐）**

FRP 是一个开源的内网穿透工具，需要自己搭建服务器。详细配置请参考：[FRP 配置指南](./frp-setup-guide.md)

**快速开始：**

1. **服务器端配置**（需要一台有公网 IP 的服务器）
   - 下载并配置 FRP 服务端
   - 启动服务端服务

2. **客户端配置**（本地开发机）
   ```bash
   # macOS
   brew install frp
   
   # 或从 GitHub 下载：https://github.com/fatedier/frp/releases
   ```

3. **创建客户端配置文件** `frpc.ini`：
   ```ini
   [common]
   server_addr = your_server_ip_or_domain
   server_port = 7000
   token = your_secure_token

   [web_8000]
   type = http
   local_ip = 127.0.0.1
   local_port = 8000
   custom_domains = your-domain.com  # 需要将域名解析到服务器IP
   ```

4. **启动客户端**：
   ```bash
   frpc -c frpc.ini
   ```

**方式二：使用其他工具**
- **ngrok**：`brew install ngrok`（简单但有限制）
- **localtunnel**：`npm install -g localtunnel`
- **serveo**：无需安装，直接使用 SSH

### 2.2 启动内网穿透

**使用 FRP：**

```bash
# 启动 FRP 客户端（假设后端运行在 8000 端口）
frpc -c frpc.ini

# 如果配置了域名，可以通过以下 URL 访问：
# https://your-domain.com/api/v1/channels/webhook/wechat-work
# 
# 如果使用 TCP 模式，需要通过服务器 IP 和端口访问：
# https://your-server-ip:6000/api/v1/channels/webhook/wechat-work
```

**注意**：企业微信要求 HTTPS，所以：
- 如果使用 HTTP 模式，需要配置域名和 SSL 证书
- 如果使用 TCP 模式，需要在服务器端配置 Nginx 反向代理和 SSL 证书

### 2.3 配置环境变量

在 `api/.env` 文件中添加以下配置：

```env
# 企业微信配置
WECHAT_WORK_CORP_ID=wwxxxxxxxxxxxxxxxx
WECHAT_WORK_AGENT_ID=1000001
WECHAT_WORK_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WECHAT_WORK_TOKEN=your_random_token_123456
WECHAT_WORK_ENCODING_AES_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**获取这些值：**
- `WECHAT_WORK_CORP_ID`：企业ID（企业信息页面）
- `WECHAT_WORK_AGENT_ID`：应用ID（应用详情页）
- `WECHAT_WORK_SECRET`：应用密钥（应用详情页）
- `WECHAT_WORK_TOKEN`：接收消息时设置的 Token
- `WECHAT_WORK_ENCODING_AES_KEY`：接收消息时设置的 EncodingAESKey

### 2.4 更新企业微信 Webhook URL

将内网穿透的 URL 更新到企业微信应用配置中：

**如果使用 FRP HTTP 模式（推荐）：**
```
https://your-domain.com/api/v1/channels/webhook/wechat-work
```

**如果使用 FRP TCP 模式：**
```
https://your-server-ip:6000/api/v1/channels/webhook/wechat-work
```
（需要在服务器端配置 Nginx 反向代理和 SSL 证书）

**如果使用其他工具（如 ngrok）：**
```
https://your-tunnel-url/api/v1/channels/webhook/wechat-work
```

## 3. 启动本地服务

### 3.1 启动后端服务

```bash
cd api
source venv/bin/activate
python run_dev.py
```

确保服务运行在 `http://localhost:8000`

### 3.2 验证 Webhook 端点

```bash
# 测试 GET 端点（验证）
curl "http://localhost:8000/api/v1/channels/webhook/wechat-work?msg_signature=test&timestamp=1234567890&nonce=test&echostr=test"

# 应该返回 "test"（验证成功）或错误信息
```

## 4. 测试消息收发

### 4.1 测试接收消息

1. 在企业微信中，找到你创建的应用
2. 发送一条文本消息
3. 检查后端日志，应该看到：
   ```
   INFO: 收到企业微信消息: <xml>...</xml>
   INFO: 成功处理企业微信消息: msg_xxx
   ```

### 4.2 测试发送消息

可以通过 API 或代码测试发送消息到企业微信：

```python
# 测试脚本
from app.channels.services.channel_service import ChannelService
from app.channels.adapters.wechat_work.adapter import WeChatWorkAdapter
from app.chat.models.chat import Message
import os

# 配置
config = {
    "corp_id": os.getenv("WECHAT_WORK_CORP_ID"),
    "agent_id": os.getenv("WECHAT_WORK_AGENT_ID"),
    "secret": os.getenv("WECHAT_WORK_SECRET"),
}

adapter = WeChatWorkAdapter(config)
# 发送测试消息
success = await adapter.send_message(
    message=test_message,
    channel_user_id="user_id_from_wechat"
)
```

## 5. 常见问题排查

### 5.1 Webhook 验证失败

**问题**：企业微信提示"验证失败"

**解决方案**：
1. 检查 Token 是否匹配
2. 检查 URL 是否正确（必须是 HTTPS）
3. 检查服务器是否可访问
4. 查看后端日志中的错误信息

### 5.2 消息接收不到

**问题**：发送消息后，后端没有收到

**解决方案**：
1. 检查 Webhook URL 配置是否正确
2. 检查 FRP 客户端是否正常运行（`frpc -c frpc.ini`）
3. 检查 FRP 服务器端是否正常运行
4. 检查后端服务是否运行
5. 检查域名解析是否正确（如果使用 HTTP 模式）
6. 检查 SSL 证书是否有效
7. 查看企业微信应用日志（应用详情页 → 接收消息 → 查看日志）

### 5.3 消息发送失败

**问题**：发送消息到企业微信失败

**解决方案**：
1. 检查 access_token 是否有效
2. 检查 AgentID 是否正确
3. 检查用户ID是否正确（必须是企业微信用户ID）
4. 查看后端日志中的错误信息

## 6. 调试技巧

### 6.1 查看详细日志

在后端代码中，已添加详细的日志输出：
- Webhook 接收日志
- 消息处理日志
- API 调用日志

FRP 客户端日志：
- 日志文件：`frpc.log`（在运行 frpc 的目录）
- 查看实时日志：`tail -f frpc.log`

### 6.2 使用企业微信测试工具

企业微信提供了测试工具：
- 应用详情页 → 「接口调试工具」
- 可以测试各种 API 调用

### 6.3 本地测试脚本

可以创建测试脚本快速验证配置：

```python
# scripts/test_wechat_work.py
import asyncio
import os
from app.channels.adapters.wechat_work.client import WeChatWorkClient

async def test():
    client = WeChatWorkClient(
        corp_id=os.getenv("WECHAT_WORK_CORP_ID"),
        agent_id=os.getenv("WECHAT_WORK_AGENT_ID"),
        secret=os.getenv("WECHAT_WORK_SECRET")
    )
    
    # 测试获取 access_token
    token = await client.get_access_token()
    print(f"✅ Access Token: {token[:20]}...")
    
    # 测试发送消息（需要替换为真实的用户ID）
    # success = await client.send_text_message("user_id", "测试消息")
    # print(f"发送结果: {success}")

if __name__ == "__main__":
    asyncio.run(test())
```

## 7. 生产环境部署

本地调试成功后，部署到生产环境时：

1. **更新 Webhook URL** 为生产环境地址
2. **使用环境变量** 管理敏感信息
3. **配置 HTTPS** 证书（企业微信要求 HTTPS）
4. **设置防火墙规则** 允许企业微信服务器访问
5. **监控日志** 确保消息正常收发
6. **使用 systemd/launchd** 管理 FRP 客户端服务，确保自动启动和重启
7. **配置域名和 SSL** 证书（推荐使用 Let's Encrypt 免费证书）

## 8. 安全注意事项

1. **不要将 Secret 提交到代码仓库**
2. **使用环境变量管理敏感信息**
3. **定期轮换 Token 和 EncodingAESKey**
4. **验证 Webhook 请求的签名**（当前为临时实现，生产环境需要完整实现）
5. **限制 Webhook 端点的访问来源**

