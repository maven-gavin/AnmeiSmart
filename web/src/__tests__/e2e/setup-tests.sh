#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== 安美智享自动化测试环境设置 ===${NC}"
echo -e "${YELLOW}该脚本帮助你启动测试所需的服务${NC}"

# 检查操作系统
if [[ "$OSTYPE" == "win"* ]]; then
    echo -e "${YELLOW}检测到Windows操作系统${NC}"
    IS_WINDOWS=true
else
    IS_WINDOWS=false
fi

# 验证后端API服务是否可用
check_api() {
    echo -e "${BLUE}检查API服务 (端口 8000)...${NC}"
    
    local API_URL="http://127.0.0.1:8000/api/v1/chat/health"
    
    if [[ "$IS_WINDOWS" == true ]]; then
        # Windows PowerShell
        API_STATUS=$(powershell -Command "try { \$response = Invoke-WebRequest -Uri '$API_URL' -UseBasicParsing -ErrorAction Stop; \$response.StatusCode } catch { 'Error' }")
    else
        # Linux/Mac curl
        API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL" 2>/dev/null || echo "Error")
    fi
    
    if [[ "$API_STATUS" == "200" ]]; then
        echo -e "${GREEN}✓ API服务运行正常${NC}"
        return 0
    else
        echo -e "${RED}✗ API服务不可用${NC}"
        return 1
    fi
}

# 验证前端服务是否可用
check_frontend() {
    echo -e "${BLUE}检查前端服务 (端口 3000)...${NC}"
    
    local FRONTEND_URL="http://127.0.0.1:3000"
    
    if [[ "$IS_WINDOWS" == true ]]; then
        # Windows PowerShell
        FRONTEND_STATUS=$(powershell -Command "try { \$response = Invoke-WebRequest -Uri '$FRONTEND_URL' -UseBasicParsing -ErrorAction Stop; \$response.StatusCode } catch { 'Error' }")
    else
        # Linux/Mac curl
        FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null || echo "Error")
    fi
    
    if [[ "$FRONTEND_STATUS" == "200" ]]; then
        echo -e "${GREEN}✓ 前端服务运行正常${NC}"
        return 0
    else
        echo -e "${RED}✗ 前端服务不可用${NC}"
        return 1
    fi
}

# 启动后端API服务
start_api() {
    echo -e "${BLUE}启动API服务...${NC}"
    
    if [[ "$IS_WINDOWS" == true ]]; then
        # Windows PowerShell 
        powershell -Command "cd ..\\..\\..\\..\\api; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &"
    else
        # Linux/Mac
        cd ../../../../api && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
    fi
    
    echo -e "${YELLOW}等待API服务启动...${NC}"
    sleep 5
    
    if check_api; then
        echo -e "${GREEN}API服务已成功启动${NC}"
    else
        echo -e "${RED}API服务启动失败，请手动检查${NC}"
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "${BLUE}启动前端服务...${NC}"
    
    if [[ "$IS_WINDOWS" == true ]]; then
        # Windows PowerShell
        powershell -Command "cd ..\\..\\..\\..; npm run dev &"
    else
        # Linux/Mac
        cd ../../../../ && npm run dev &
    fi
    
    echo -e "${YELLOW}等待前端服务启动...${NC}"
    sleep 10
    
    if check_frontend; then
        echo -e "${GREEN}前端服务已成功启动${NC}"
    else
        echo -e "${RED}前端服务启动失败，请手动检查${NC}"
    fi
}

# 运行测试
run_tests() {
    echo -e "${BLUE}运行端到端测试...${NC}"
    
    if [[ "$IS_WINDOWS" == true ]]; then
        # Windows PowerShell
        powershell -Command "cd ..\\..\\..\\..; npx playwright test"
    else
        # Linux/Mac
        cd ../../../../ && npx playwright test
    fi
}

# 主流程
main() {
    # 检查服务状态
    API_RUNNING=false
    FRONTEND_RUNNING=false
    
    if check_api; then
        API_RUNNING=true
    fi
    
    if check_frontend; then
        FRONTEND_RUNNING=true
    fi
    
    # 启动缺少的服务
    if [[ "$API_RUNNING" == false ]]; then
        echo -e "${YELLOW}API服务未运行，尝试启动...${NC}"
        start_api
    fi
    
    if [[ "$FRONTEND_RUNNING" == false ]]; then
        echo -e "${YELLOW}前端服务未运行，尝试启动...${NC}"
        start_frontend
    fi
    
    # 最终检查
    echo -e "${BLUE}最终检查服务状态...${NC}"
    API_OK=false
    FRONTEND_OK=false
    
    if check_api; then
        API_OK=true
    fi
    
    if check_frontend; then
        FRONTEND_OK=true
    fi
    
    # 如果服务都运行正常，运行测试
    if [[ "$API_OK" == true && "$FRONTEND_OK" == true ]]; then
        echo -e "${GREEN}所有服务运行正常，准备开始测试${NC}"
        run_tests
    else
        echo -e "${RED}部分服务未能正常启动，无法执行测试${NC}"
        echo -e "${YELLOW}请尝试手动启动服务:${NC}"
        echo -e "${YELLOW}1. 启动API服务: cd api && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000${NC}"
        echo -e "${YELLOW}2. 启动前端服务: cd web && npm run dev${NC}"
        echo -e "${YELLOW}3. 运行测试: cd web && npx playwright test${NC}"
    fi
}

# 执行主流程
main 