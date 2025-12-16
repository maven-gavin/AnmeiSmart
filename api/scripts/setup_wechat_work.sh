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

# 检查 ngrok
echo "🔍 检查内网穿透工具..."
if command -v ngrok &> /dev/null; then
    echo "✅ 已安装 ngrok"
    echo ""
    echo "📡 启动内网穿透（在另一个终端运行）："
    echo "   ngrok http 8000"
    echo ""
    echo "   复制显示的 HTTPS URL，格式类似："
    echo "   https://xxxx-xxxx-xxxx.ngrok.io"
    echo ""
    read -p "请输入 ngrok 的 HTTPS URL（不含路径）: " NGROK_URL
    
    WEBHOOK_URL="${NGROK_URL}/api/v1/channels/webhook/wechat-work"
    echo ""
    echo "📋 请在企业微信管理后台配置以下 Webhook URL："
    echo "   $WEBHOOK_URL"
    echo ""
else
    echo "⚠️  未检测到 ngrok"
    echo ""
    echo "请安装 ngrok 或使用其他内网穿透工具："
    echo "  - macOS: brew install ngrok"
    echo "  - 或访问: https://ngrok.com/download"
    echo ""
    echo "启动 ngrok 后，在企业微信管理后台配置 Webhook URL："
    echo "  https://your-ngrok-url.ngrok.io/api/v1/channels/webhook/wechat-work"
    echo ""
fi

echo "=========================================="
echo "✅ 配置完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 启动后端服务: python run_dev.py"
echo "2. 启动内网穿透: ngrok http 8000"
echo "3. 在企业微信管理后台配置 Webhook URL"
echo "4. 运行测试脚本: python scripts/test_wechat_work.py"
echo ""

