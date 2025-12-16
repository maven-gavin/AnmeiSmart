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

### 步骤 3: 安装并启动内网穿透

```bash
# 安装 ngrok（如果未安装）
brew install ngrok  # macOS
# 或下载：https://ngrok.com/download

# 启动内网穿透（假设后端运行在 8000 端口）
ngrok http 8000
```

复制显示的 HTTPS URL，例如：`https://xxxx-xxxx-xxxx.ngrok.io`

### 步骤 4: 配置企业微信 Webhook

1. 在企业微信管理后台 → 应用详情 → 接收消息
2. 点击「设置API接收」
3. 填写：
   - **URL**: `https://your-ngrok-url.ngrok.io/api/v1/channels/webhook/wechat-work`
   - **Token**: 与 `.env` 中的 `WECHAT_WORK_TOKEN` 一致
   - **EncodingAESKey**: 与 `.env` 中的 `WECHAT_WORK_ENCODING_AES_KEY` 一致
4. 点击「保存」（会自动验证）

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
- [架构设计文档](./screenshot-wechat-work-integration.md)

## 🔧 故障排查

### Webhook 验证失败

- 检查 Token 是否匹配
- 检查 URL 是否正确（必须是 HTTPS）
- 确保后端服务正在运行
- 检查 ngrok 是否正常运行

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

- 本地调试必须使用内网穿透工具（ngrok、localtunnel 等）
- 企业微信要求 Webhook URL 必须是 HTTPS
- Token 和 EncodingAESKey 可以随机生成，但必须保持一致
- 生产环境部署时，使用真实的域名和 HTTPS 证书

