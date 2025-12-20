#!/bin/bash

# 自动化部署脚本
# 用途: 更新代码并重新构建 Docker 容器

set -e  # 遇到错误立即退出

echo "=========================================="
echo "开始自动化部署流程（优化版 - 最小停机时间）"
echo "=========================================="

# 1. 拉取最新代码
echo ""
echo "📥 [1/6] 拉取最新代码..."
git pull

# 2. 先构建新镜像（旧容器仍在运行，服务不中断）
echo ""
echo "🔨 [2/6] 构建新镜像（服务保持在线）..."
sudo docker compose build

# 3. 停止并删除旧容器
echo ""
echo "🛑 [3/6] 停止旧容器..."
sudo docker-compose down

# 4. 清理旧镜像（可选，节省磁盘空间）
echo ""
echo "🗑️  [4/6] 清理悬空镜像..."
sudo docker image prune -f

# 5. 启动新容器（使用已构建的镜像，秒级启动）
echo ""
echo "🚀 [5/6] 启动新容器..."
sudo docker compose up -d

# 6. 显示日志
echo ""
echo "📋 [6/6] 显示容器日志 (按 Ctrl+C 退出)..."
echo "=========================================="
sleep 2
sudo docker-compose logs -f
