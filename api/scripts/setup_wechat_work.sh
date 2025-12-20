#!/bin/bash
# 企业微信快速配置脚本

set -e

echo "=========================================="
echo "企业微信本地调试配置助手"
echo "=========================================="
echo ""

# 检查 .env 文件
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  未找到 .env 文件，正在从 env.example 创建..."
    cp env.example .env
    echo "✅ 已创建 .env 文件"
fi

echo "📝 请按照以下步骤配置企业微信："
echo ""
echo "1. 登录企业微信管理后台: https://work.weixin.qq.com/"
echo "2. 进入「应用管理」→「自建」→ 创建应用"
echo "3. 在应用详情页获取以下信息："
echo "   - AgentID（应用ID）"
echo "   - Secret（应用密钥）"
echo "   - CorpID（企业ID，在「我的企业」→「企业信息」中）"
echo ""
echo "4. 配置接收消息："
echo "   - 在应用详情页找到「接收消息」"
echo "   - 点击「设置API接收」"
echo "   - 设置 Token 和 EncodingAESKey"
echo "   - URL 暂时留空，稍后配置"
echo ""

# 读取配置
read -p "请输入 CorpID: " CORP_ID
read -p "请输入 AgentID: " AGENT_ID
read -p "请输入 Secret: " SECRET
read -p "请输入 Token: " TOKEN
read -p "请输入 EncodingAESKey: " ENCODING_AES_KEY

# 更新 .env 文件
echo ""
echo "📝 正在更新 .env 文件..."

# 使用 sed 或 awk 更新配置，如果不存在则追加
if grep -q "WECHAT_WORK_CORP_ID" "$ENV_FILE"; then
    sed -i.bak "s|WECHAT_WORK_CORP_ID=.*|WECHAT_WORK_CORP_ID=$CORP_ID|" "$ENV_FILE"
else
    echo "WECHAT_WORK_CORP_ID=$CORP_ID" >> "$ENV_FILE"
fi

if grep -q "WECHAT_WORK_AGENT_ID" "$ENV_FILE"; then
    sed -i.bak "s|WECHAT_WORK_AGENT_ID=.*|WECHAT_WORK_AGENT_ID=$AGENT_ID|" "$ENV_FILE"
else
    echo "WECHAT_WORK_AGENT_ID=$AGENT_ID" >> "$ENV_FILE"
fi

if grep -q "WECHAT_WORK_SECRET" "$ENV_FILE"; then
    sed -i.bak "s|WECHAT_WORK_SECRET=.*|WECHAT_WORK_SECRET=$SECRET|" "$ENV_FILE"
else
    echo "WECHAT_WORK_SECRET=$SECRET" >> "$ENV_FILE"
fi

if grep -q "WECHAT_WORK_TOKEN" "$ENV_FILE"; then
    sed -i.bak "s|WECHAT_WORK_TOKEN=.*|WECHAT_WORK_TOKEN=$TOKEN|" "$ENV_FILE"
else
    echo "WECHAT_WORK_TOKEN=$TOKEN" >> "$ENV_FILE"
fi

if grep -q "WECHAT_WORK_ENCODING_AES_KEY" "$ENV_FILE"; then
    sed -i.bak "s|WECHAT_WORK_ENCODING_AES_KEY=.*|WECHAT_WORK_ENCODING_AES_KEY=$ENCODING_AES_KEY|" "$ENV_FILE"
else
    echo "WECHAT_WORK_ENCODING_AES_KEY=$ENCODING_AES_KEY" >> "$ENV_FILE"
fi

# 清理备份文件
rm -f "$ENV_FILE.bak"

echo "✅ 配置已更新到 .env 文件"
echo ""

# 检查 FRP
echo "🔍 检查内网穿透工具..."
if command -v frpc &> /dev/null; then
    echo "✅ 已安装 FRP 客户端"
    echo ""
    echo "📡 配置 FRP 客户端："
    echo ""
    read -p "请输入 FRP 服务器地址: " FRP_SERVER
    read -p "请输入 FRP 服务器端口 (默认 7000): " FRP_PORT
    FRP_PORT=${FRP_PORT:-7000}
    read -p "请输入 FRP Token: " FRP_TOKEN
    read -p "请输入域名（如果使用 HTTP 模式，留空则使用 TCP 模式）: " FRP_DOMAIN
    
    # 创建 FRP 配置文件（TOML 格式）
    FRPC_CONFIG="frpc.toml"
    echo ""
    echo "📝 正在创建 FRP 客户端配置文件: $FRPC_CONFIG"
    
    cat > "$FRPC_CONFIG" << EOF
# FRP 客户端配置（FRP 0.65.0+）
serverAddr = "$FRP_SERVER"
serverPort = $FRP_PORT

[auth]
method = "token"
token = "$FRP_TOKEN"

[log]
to = "./frpc.log"
level = "info"
maxDays = 3

EOF

    if [ -n "$FRP_DOMAIN" ]; then
        # HTTP 模式
        cat >> "$FRPC_CONFIG" << EOF
[[proxies]]
name = "web_8000_http"
type = "http"
localIP = "127.0.0.1"
localPort = 8000
customDomains = ["$FRP_DOMAIN"]
EOF
        WEBHOOK_URL="https://${FRP_DOMAIN}/api/v1/channels/webhook/wechat-work"
        echo ""
        echo "✅ 已配置 FRP HTTP 模式"
        echo "📋 请在企业微信管理后台配置以下 Webhook URL："
        echo "   $WEBHOOK_URL"
        echo ""
        echo "⚠️  注意：需要将域名 $FRP_DOMAIN 解析到 FRP 服务器 IP，并配置 SSL 证书"
    else
        # TCP 模式
        read -p "请输入远程端口（服务器端映射的端口，默认 6000）: " REMOTE_PORT
        REMOTE_PORT=${REMOTE_PORT:-6000}
        cat >> "$FRPC_CONFIG" << EOF
[[proxies]]
name = "web_8000_tcp"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8000
remotePort = $REMOTE_PORT
EOF
        echo ""
        echo "✅ 已配置 FRP TCP 模式"
        echo "📋 请在企业微信管理后台配置以下 Webhook URL："
        echo "   https://${FRP_SERVER}:${REMOTE_PORT}/api/v1/channels/webhook/wechat-work"
        echo ""
        echo "⚠️  注意：需要在服务器端配置 Nginx 反向代理和 SSL 证书"
    fi
    
    echo ""
    echo "🚀 启动 FRP 客户端（在另一个终端运行）："
    echo "   frpc -c $FRPC_CONFIG"
    echo "   或使用启动脚本: ./scripts/start_frpc.sh"
    echo ""
else
    echo "⚠️  未检测到 FRP 客户端"
    echo ""
    echo "请安装 FRP 客户端："
    echo "  - macOS: brew install frp"
    echo "  - 或从 GitHub 下载: https://github.com/fatedier/frp/releases"
    echo ""
    echo "详细配置请参考: docs/frp-setup-guide.md"
    echo ""
    echo "配置 FRP 后，在企业微信管理后台配置 Webhook URL："
    echo "  - HTTP 模式: https://your-domain.com/api/v1/channels/webhook/wechat-work"
    echo "  - TCP 模式: https://your-server-ip:port/api/v1/channels/webhook/wechat-work"
    echo ""
fi

echo "=========================================="
echo "✅ 配置完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 启动后端服务: python run_dev.py"
echo "2. 启动 FRP 客户端: ./scripts/start_frpc.sh"
echo "   或手动启动: frpc -c frpc.toml"
echo "3. 在企业微信管理后台配置 Webhook URL（见上方提示）"
echo "4. 运行测试脚本: python scripts/test_wechat_work.py"
echo ""
echo "📚 更多信息请参考: docs/frp-setup-guide.md"
echo ""

