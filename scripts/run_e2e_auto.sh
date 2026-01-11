#!/bin/bash

# ========================================
# E2E自动化测试脚本（Mac版本）
# 功能：检查服务状态、等待服务就绪、运行可视化E2E测试
# ========================================

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  E2E 自动化测试启动器（Mac版本）${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# ========================================
# 1. 检查服务状态
# ========================================
echo -e "${YELLOW}[1/4] 检查服务状态...${NC}"

# 检查前端服务
FRONTEND_URL="http://localhost:5173"
echo -n "  检查前端服务 ($FRONTEND_URL)... "
if curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ 运行中${NC}"
    FRONTEND_RUNNING=true
else
    echo -e "${RED}✗ 未运行${NC}"
    FRONTEND_RUNNING=false
fi

# 检查后端服务
BACKEND_URL="http://localhost:8000/api/health"
echo -n "  检查后端服务 ($BACKEND_URL)... "
if curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL" | grep -q "200"; then
    echo -e "${GREEN}✓ 运行中${NC}"
    BACKEND_RUNNING=true
else
    echo -e "${RED}✗ 未运行${NC}"
    BACKEND_RUNNING=false
fi

# 如果服务未运行，提示用户
if [ "$FRONTEND_RUNNING" = false ] || [ "$BACKEND_RUNNING" = false ]; then
    echo ""
    echo -e "${RED}错误: 服务未完全启动！${NC}"
    echo ""
    echo "请先启动所有服务："
    if [ "$FRONTEND_RUNNING" = false ]; then
        echo -e "  ${YELLOW}前端:${NC} cd admin-web && npm run dev"
    fi
    if [ "$BACKEND_RUNNING" = false ]; then
        echo -e "  ${YELLOW}后端:${NC} cd backend && python -m uvicorn app.main:app --reload"
    fi
    echo ""
    exit 1
fi

# ========================================
# 2. 等待服务就绪
# ========================================
echo ""
echo -e "${YELLOW}[2/4] 等待服务完全就绪...${NC}"
MAX_RETRIES=30
RETRY_INTERVAL=1

for i in $(seq 1 $MAX_RETRIES); do
    if curl -s "$BACKEND_URL" | grep -q "healthy"; then
        echo -e "  ${GREEN}✓ 后端服务就绪${NC}"
        break
    fi
    echo -n "  等待中... ($i/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
    echo -ne "\r"
done

if [ $i -eq $MAX_RETRIES ]; then
    echo -e "${RED}  ✗ 后端服务未在规定时间内就绪${NC}"
    exit 1
fi

# ========================================
# 3. 设置环境变量
# ========================================
echo ""
echo -e "${YELLOW}[3/4] 配置测试环境...${NC}"

# 设置可视化模式
export SHOW_BROWSER=true
echo -e "  ${GREEN}✓${NC} SHOW_BROWSER=${SHOW_BROWSER}"

# 设置操作速度（毫秒）
export SLOW_MO=500
echo -e "  ${GREEN}✓${NC} SLOW_MO=${SLOW_MO}"

# 设置测试基础URL
export BASE_URL="http://localhost:5173"
echo -e "  ${GREEN}✓${NC} BASE_URL=${BASE_URL}"

# ========================================
# 4. 运行E2E测试
# ========================================
echo ""
echo -e "${YELLOW}[4/4] 运行E2E测试...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 运行pytest
cd "$PROJECT_ROOT"
pytest tests/test_e2e_business_workflow.py -v -s --tb=short

# 保存退出码
EXIT_CODE=$?

# ========================================
# 测试结果汇总
# ========================================
echo ""
echo -e "${GREEN}========================================${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}  ✓ E2E测试全部通过！${NC}"
else
    echo -e "${RED}  ✗ E2E测试失败 (退出码: $EXIT_CODE)${NC}"
fi
echo -e "${GREEN}========================================${NC}"
echo ""

exit $EXIT_CODE
