# 企业微信本地调试快速开始

## 🚀 5分钟快速配置

### 步骤 1: 获取企业微信凭证

1. 登录 [企业微信管理后台](https://work.weixin.qq.com/)
2. 创建自建应用，获取：
   - **CorpID**：企业ID（我的企业 → 企业信息）
   - **AgentID**：应用ID（应用详情页）
   - **Secret**：应用密钥（应用详情页 → 查看）

### 步骤 2: 配置环境变量

**方式一：使用配置脚本（推荐）**

```bash
cd api
./scripts/setup_wechat_work.sh
```

**方式二：手动配置**

编辑 `api/.env` 文件，添加：

```env
WECHAT_WORK_CORP_ID=wwxxxxxxxxxxxxxxxx
WECHAT_WORK_AGENT_ID=1000001
WECHAT_WORK_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WECHAT_WORK_TOKEN=your_random_token_123456
WECHAT_WORK_ENCODING_AES_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 步骤 3: 安装并启动内网穿透（使用 FRP）

**前提条件**：需要一台有公网 IP 的服务器

```bash
# 安装 FRP 客户端（macOS）
brew install frp

# 配置 FRP 客户端（创建 frpc.ini）
# 详细配置请参考：docs/frp-setup-guide.md

# 启动 FRP 客户端（假设后端运行在 8000 端口）
frpc -c frpc.ini
```

**FRP 配置示例** (`frpc.ini`)：
```ini
[common]
server_addr = your_server_ip_or_domain
server_port = 7000
token = your_secure_token

[web_8000]
type = http
local_ip = 127.0.0.1
local_port = 8000
custom_domains = your-domain.com
```

**注意**：需要将域名解析到 FRP 服务器 IP，并配置 SSL 证书

### 步骤 4: 配置企业微信 Webhook

1. 在企业微信管理后台 → 应用详情 → 接收消息
2. 点击「设置API接收」
3. 填写：
   - **URL**: `https://your-domain.com/api/v1/channels/webhook/wechat-work`（FRP HTTP 模式）
   - **Token**: 与 `.env` 中的 `WECHAT_WORK_TOKEN` 一致
   - **EncodingAESKey**: 与 `.env` 中的 `WECHAT_WORK_ENCODING_AES_KEY` 一致
4. 点击「保存」（会自动验证）

**提示**：如果没有域名，可以使用 TCP 模式 + Nginx 反向代理，详见 [FRP 配置指南](./frp-setup-guide.md)

### 步骤 5: 启动服务并测试

```bash
# 启动后端服务
cd api
source venv/bin/activate
python run_dev.py

# 在另一个终端运行测试
python scripts/test_wechat_work.py
```

### 步骤 6: 测试消息收发

1. 在企业微信中找到你创建的应用
2. 发送一条测试消息
3. 检查后端日志，应该看到消息接收和处理记录

## 📚 详细文档

- [完整配置指南](./wechat-work-local-debug-guide.md)
- [FRP 内网穿透配置指南](./frp-setup-guide.md)
- [架构设计文档](./screenshot-wechat-work-integration.md)

## 🔧 故障排查

### Webhook 验证失败

- 检查 Token 是否匹配
- 检查 URL 是否正确（必须是 HTTPS）
- 确保后端服务正在运行
- 检查 FRP 客户端是否正常运行
- 检查服务器端 FRP 服务是否正常运行
- 检查域名解析是否正确（如果使用域名）
- 检查 SSL 证书是否有效

### 消息接收不到

- 检查 Webhook URL 配置
- 查看后端日志
- 检查企业微信应用日志（应用详情 → 接收消息 → 查看日志）

### 测试脚本报错

运行测试脚本查看详细错误：

```bash
python scripts/test_wechat_work.py
```

## 💡 提示

- 本地调试必须使用内网穿透工具（推荐 FRP，也可使用 ngrok、localtunnel 等）
- 企业微信要求 Webhook URL 必须是 HTTPS
- FRP 需要自己搭建服务器，但完全免费且可控
- 如果使用 FRP HTTP 模式，需要配置域名和 SSL 证书
- Token 和 EncodingAESKey 可以随机生成，但必须保持一致
- 生产环境部署时，使用真实的域名和 HTTPS 证书

