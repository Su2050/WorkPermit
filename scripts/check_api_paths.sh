#!/bin/bash
# API路径一致性检查脚本

echo "检查API路径一致性..."

# 检查前端API调用
FRONTEND_APIS=$(grep -r "request\.\(get\|post\|put\|patch\|delete\)" admin-web/src/api --include="*.js" | grep -o "'/[^']*'" | sort -u)

# 检查后端API路由
BACKEND_APIS=$(grep -r "@router\.\(get\|post\|put\|patch\|delete\)" backend/app/api/admin --include="*.py" | grep -o '"[^"]*"' | sort -u)

echo "前端API调用:"
echo "$FRONTEND_APIS"
echo ""
echo "后端API路由:"
echo "$BACKEND_APIS"

# 简单的匹配检查（可以改进）
echo ""
echo "检查完成"
