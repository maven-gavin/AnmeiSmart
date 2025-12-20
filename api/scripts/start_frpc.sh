#!/bin/bash
# FRP 客户端启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FRPC_CONFIG="$API_DIR/frpc.toml"

echo "=========================================="
echo "FRP 客户端启动脚本"
echo "=========================================="
echo ""

# 检查 FRP 客户端是否安装
if ! command -v frpc &> /dev/null; then
    echo "❌ FRP 客户端未安装"
    echo ""
    echo "请先安装 FRP 客户端："
    echo "  - macOS: brew install frp"
    echo "  - 或从 GitHub 下载: https://github.com/fatedier/frp/releases"
    exit 1
fi

echo "✅ FRP 客户端已安装"
echo ""

# 检查配置文件
if [ ! -f "$FRPC_CONFIG" ]; then
    echo "⚠️  配置文件不存在: $FRPC_CONFIG"
    echo ""
    echo "请先创建配置文件："
    echo "  1. 复制示例配置: cp frpc.toml.example frpc.toml"
    echo "  2. 编辑配置文件: vim frpc.toml"
    echo "  3. 或运行配置脚本: ./scripts/setup_wechat_work.sh"
    exit 1
fi

echo "✅ 配置文件存在: $FRPC_CONFIG"
echo ""

# 检查后端服务是否运行
if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "⚠️  后端服务似乎未运行在 localhost:8000"
    echo "   请先启动后端服务: python run_dev.py"
    echo ""
    read -p "是否继续启动 FRP 客户端? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🚀 启动 FRP 客户端..."
echo "   配置文件: $FRPC_CONFIG"
echo "   按 Ctrl+C 停止"
echo ""

# 切换到 API 目录
cd "$API_DIR"

# 启动 FRP 客户端
frpc -c "$FRPC_CONFIG"

