#!/bin/bash
# 快速运行E2E测试（简化版）- Mac版本
# 功能：快速运行E2E测试，预设环境变量

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 快速运行E2E测试${NC}"
echo ""

# 设置环境变量（显示浏览器，慢速执行便于观察）
export SHOW_BROWSER=true
export SLOW_MO=500

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# 运行pytest
pytest tests/test_e2e_business_workflow.py -v -s --tb=short

# 检查测试结果
TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 测试完成${NC}"
else
    echo -e "❌ 测试失败（退出码: $TEST_EXIT_CODE）"
fi

exit $TEST_EXIT_CODE

