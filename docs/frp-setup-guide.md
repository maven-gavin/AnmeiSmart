# FRP 内网穿透配置指南

> **版本说明**：本文档适用于 **FRP 0.65.0** 及以上版本，使用 **TOML** 格式配置文件。

## 什么是 FRP

FRP (Fast Reverse Proxy) 是一个高性能的反向代理应用，可以帮助你轻松地进行内网穿透，将内网服务暴露到公网。

### 重要变更（0.65.0 版本）

- ✅ **配置文件格式**：从 INI 格式改为 **TOML** 格式（`.toml` 扩展名）
- ✅ **配置项命名**：采用驼峰命名法（camelCase），如 `serverAddr`、`localPort`
- ✅ **代理配置**：使用 `[[proxies]]` 数组格式定义多个代理
- ✅ **认证配置**：统一使用 `[auth]` 配置块

## 方案选择

### 方案一：使用自己的 FRP 服务器（推荐）

如果你有自己的服务器，可以搭建 FRP 服务端，完全控制且免费。

### 方案二：使用公共 FRP 服务

可以使用一些免费的公共 FRP 服务（注意安全风险）。

## 方案一：自建 FRP 服务器

### 1. 服务器端配置

#### 1.1 下载 FRP

```bash
# 访问 https://github.com/fatedier/frp/releases
# 下载对应系统的版本（Linux amd64）
wget https://github.com/fatedier/frp/releases/download/v0.65.0/frp_0.65.0_linux_amd64.tar.gz
tar -xzf frp_0.65.0_linux_amd64.tar.gz
cd frp_0.65.0_linux_amd64
```

#### 1.2 配置服务器端 (frps.toml)

**注意**：FRP 0.65.0 使用 TOML 格式配置文件，不再支持 INI 格式。

创建配置文件 `frps.toml`：

```toml
# 服务端绑定地址和端口
bindAddr = "0.0.0.0"
bindPort = 7000

# 认证配置
[auth]
method = "token"
token = "your_secure_token_here"

# Web 管理界面配置（可选）
[webServer]
addr = "0.0.0.0"
port = 7500
user = "admin"
password = "your_password"

# 日志配置
[log]
to = "/var/log/frps.log"
level = "info"
maxDays = 3
```

#### 1.3 启动服务器

```bash
# 前台运行（测试用）
./frps -c frps.toml

# 后台运行（生产环境）
nohup ./frps -c frps.toml > /dev/null 2>&1 &

# 或使用 systemd 服务（推荐）
sudo vim /etc/systemd/system/frps.service
```

**systemd 服务配置示例：**

```ini
[Unit]
Description=Frp Server Service
After=network.target

[Service]
Type=simple
User=nobody
Restart=on-failure
RestartSec=5s
ExecStart=/path/to/frps -c /path/to/frps.toml
ExecReload=/bin/kill -s HUP $MAINPID

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable frps
sudo systemctl start frps
```

#### 1.4 防火墙配置

```bash
# 开放必要端口
sudo ufw allow 7000/tcp  # FRP 服务端口
sudo ufw allow 7500/tcp  # Dashboard 端口（如果启用）
sudo ufw allow 6000:6010/tcp  # 客户端映射端口范围（根据需要调整）
```

### 2. 客户端配置（本地开发机）

#### 2.1 下载 FRP 客户端

```bash
# macOS
brew install frp
# 或手动下载：https://github.com/fatedier/frp/releases

# Windows/Linux
# 从 GitHub releases 下载对应版本
```

#### 2.2 配置客户端 (frpc.toml)

**注意**：FRP 0.65.0 使用 TOML 格式配置文件，不再支持 INI 格式。

创建配置文件 `frpc.toml`：

```toml
# 服务器地址和端口
serverAddr = "your_server_ip_or_domain"
serverPort = 7000

# 认证配置（与服务器端一致）
[auth]
method = "token"
token = "your_secure_token_here"

# 日志配置
[log]
to = "./frpc.log"
level = "info"
maxDays = 3

# TCP 模式代理配置
[[proxies]]
name = "web_8000_tcp"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8000
remotePort = 6000  # 服务器端映射的端口

# HTTP 模式代理配置（如果需要 HTTPS，使用此模式并配置域名）
[[proxies]]
name = "web_8000_http"
type = "http"
localIP = "127.0.0.1"
localPort = 8000
customDomains = ["your-domain.com"]  # 需要将域名解析到服务器IP
```

#### 2.3 启动客户端

```bash
# 前台运行（测试用）
frpc -c frpc.toml

# 后台运行
nohup frpc -c frpc.toml > /dev/null 2>&1 &

# macOS 使用 launchd（推荐）
# 创建 ~/Library/LaunchAgents/frpc.plist
```

**macOS launchd 配置示例：**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>frpc</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/frpc</string>
        <string>-c</string>
        <string>/path/to/frpc.toml</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/frpc.plist
```

### 3. 使用方式

配置完成后，你的本地服务可以通过以下方式访问：

- **TCP 模式**: `http://your_server_ip:6000` → 映射到本地 `http://localhost:8000`
- **HTTP 模式**: `https://your-domain.com` → 映射到本地 `http://localhost:8000`

## 方案二：使用公共 FRP 服务

### 1. 查找公共 FRP 服务

可以使用一些免费的公共 FRP 服务（注意：这些服务可能不稳定，仅用于测试）：

- 搜索 "免费 frp 服务" 或 "public frp server"
- 注意安全风险，不要传输敏感数据

### 2. 配置客户端

使用公共服务的地址和端口配置 `frpc.toml`：

```toml
serverAddr = "public_frp_server.com"
serverPort = 7000

[auth]
method = "token"
token = "public_token"  # 如果有的话

[[proxies]]
name = "web_8000"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8000
remotePort = 6000
```

## 企业微信 Webhook 配置

使用 FRP 后，企业微信 Webhook URL 配置为：

- **TCP 模式**: `http://your_server_ip:6000/api/v1/channels/webhook/wechat-work`
- **HTTP 模式**: `https://your-domain.com/api/v1/channels/webhook/wechat-work`

**注意**：企业微信要求 HTTPS，所以：
1. 如果使用 TCP 模式，需要在服务器端配置 Nginx 反向代理并配置 SSL 证书
2. 如果使用 HTTP 模式，FRP 支持直接配置域名和 SSL

### Nginx 反向代理配置（TCP 模式 + HTTPS）

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:6000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 快速配置脚本

### 客户端自动启动脚本

创建 `scripts/start_frpc.sh`：

```bash
#!/bin/bash
FRPC_CONFIG="/path/to/frpc.toml"
FRPC_BIN="/usr/local/bin/frpc"

if [ ! -f "$FRPC_CONFIG" ]; then
    echo "❌ FRP 配置文件不存在: $FRPC_CONFIG"
    exit 1
fi

if ! command -v frpc &> /dev/null; then
    echo "❌ FRP 客户端未安装"
    echo "安装方法: brew install frp"
    exit 1
fi

echo "🚀 启动 FRP 客户端..."
frpc -c "$FRPC_CONFIG"
```

## 故障排查

### 1. 连接失败

- 检查服务器地址和端口是否正确
- 检查防火墙是否开放端口
- 检查 token 是否匹配

### 2. 端口被占用

- 修改 `remotePort` 为其他端口
- 检查服务器端端口是否被占用

### 3. 无法访问映射的服务

- 检查本地服务是否正常运行
- 检查 `localIP` 和 `localPort` 是否正确
- 检查服务器端防火墙规则

### 4. TOML 配置格式错误

- 确保使用 `.toml` 扩展名，而不是 `.ini`
- 检查 TOML 语法是否正确（注意大小写和格式）
- 使用 TOML 验证工具检查配置文件

## 安全建议

1. **使用强 token**：设置复杂的认证 token
2. **限制访问**：使用防火墙限制访问来源
3. **使用 HTTPS**：生产环境必须使用 HTTPS
4. **定期更新**：保持 FRP 版本更新
5. **监控日志**：定期检查日志，发现异常访问

## 与 ngrok 对比

| 特性 | FRP | ngrok |
|------|-----|-------|
| 开源 | ✅ 是 | ❌ 否（有开源版本） |
| 自建服务器 | ✅ 需要 | ❌ 不需要 |
| 免费 | ✅ 完全免费 | ⚠️ 有限制 |
| 配置复杂度 | ⚠️ 中等 | ✅ 简单 |
| 性能 | ✅ 高 | ⚠️ 中等 |
| 控制权 | ✅ 完全控制 | ❌ 依赖第三方 |

## 版本说明

本文档适用于 **FRP 0.65.0** 及以上版本。

### 主要变更（0.65.0）

1. **配置文件格式**：从 INI 格式改为 TOML 格式
2. **配置项命名**：采用驼峰命名法（camelCase）
3. **代理配置**：使用 `[[proxies]]` 数组格式
4. **认证方式**：统一使用 `[auth]` 配置块

### 从旧版本迁移

如果你使用的是旧版本（0.52.x 及以下），需要：

1. 升级到 0.65.0 版本
2. 将 `.ini` 配置文件转换为 `.toml` 格式
3. 更新配置项名称（参考本文档）
4. 更新启动命令中的配置文件路径

## 参考资源

- FRP 官方文档：https://gofrp.org/zh-cn/docs/
- FRP 配置文件说明：https://gofrp.org/zh-cn/docs/features/common/configure/
- GitHub 仓库：https://github.com/fatedier/frp
- 配置文件示例：https://github.com/fatedier/frp/tree/dev/conf
- TOML 格式规范：https://toml.io/cn/

