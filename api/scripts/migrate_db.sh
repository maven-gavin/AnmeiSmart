#!/bin/bash
# 安美智享智能医美服务系统 - 数据库UUID迁移脚本

# 设置颜色
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 激活虚拟环境
if [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
    echo -e "${CYAN}激活虚拟环境...${NC}"
    source "${PROJECT_ROOT}/venv/bin/activate"
else
    echo -e "${YELLOW}警告: 未找到虚拟环境, 尝试使用系统Python环境${NC}"
fi

# 捕获错误
set -e

# 显示执行步骤
echo -e "${GREEN}===== 安美智享数据库UUID迁移工具 =====${NC}"
echo -e "${YELLOW}此工具将数据库主键从整数类型迁移到UUID类型${NC}"

# 执行迁移脚本
cd "$PROJECT_ROOT"
python -m scripts.migrate_to_uuid $@

# 完成
echo -e "${GREEN}操作完成!${NC}" 