#!/bin/bash
# 安美智享智能医美服务系统 - 数据库迁移工作流示例脚本
# 本脚本演示如何在修改模型后应用数据库迁移

# 设置颜色
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 步骤1: 检测模型变更
echo -e "${GREEN}步骤1: 检测模型变更...${NC}"
python migration.py detect

# 步骤2: 创建迁移文件
echo -e "\n${GREEN}步骤2: 创建迁移文件...${NC}"
echo -n "请输入迁移说明 (例如: '添加新字段'): "
read migrationMessage
if [ -z "$migrationMessage" ]; then
    migrationMessage="模型更新"
fi
python migration.py create --message "$migrationMessage"

# 步骤3: 应用迁移
echo -e "\n${GREEN}步骤3: 应用迁移...${NC}"
python migration.py upgrade

# 步骤4: 填充测试数据
echo -e "\n${GREEN}步骤4: 是否需要更新测试数据?${NC}"
echo -n "是否更新测试数据? (y/n): "
read updateTestData
if [ "$updateTestData" = "y" ] || [ "$updateTestData" = "Y" ]; then
    python seed_db.py
    echo -e "${GREEN}测试数据已更新${NC}"
fi

echo -e "\n${GREEN}数据库迁移流程完成!${NC}" 