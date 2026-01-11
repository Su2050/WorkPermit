#!/bin/bash
# 开发环境启动脚本

set -e

echo "=== 作业票管理系统 - 开发环境启动 ==="

# 检查conda环境
if ! conda env list | grep -q "workpermit"; then
    echo "创建conda环境..."
    conda create -n workpermit python=3.11 -y
fi

# 激活conda环境
echo "激活conda环境..."
eval "$(conda shell.bash hook)"
conda activate workpermit

# 检查依赖
if [ ! -d "backend/.venv" ]; then
    echo "安装Python依赖..."
    cd backend
    pip install -r requirements.txt
    cd ..
fi

# 检查Docker服务
if ! docker ps > /dev/null 2>&1; then
    echo "⚠️  Docker未运行，请先启动Docker Desktop"
    echo "然后运行: docker-compose up -d"
    exit 1
fi

# 启动Docker服务
echo "启动Docker服务..."
docker-compose up -d postgres redis minio

# 等待数据库就绪
echo "等待数据库就绪..."
sleep 5

# 运行数据库迁移
echo "运行数据库迁移..."
cd backend
alembic upgrade head
cd ..

echo ""
echo "✅ 环境准备完成！"
echo ""
echo "启动后端服务:"
echo "  cd backend && conda activate workpermit && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "启动Celery Worker:"
echo "  cd backend && conda activate workpermit && celery -A app.tasks.celery_app worker --loglevel=info"
echo ""
echo "启动Celery Beat:"
echo "  cd backend && conda activate workpermit && celery -A app.tasks.celery_app beat --loglevel=info"
echo ""
echo "访问API文档: http://localhost:8000/docs"
echo "访问Celery Flower: http://localhost:5555"

