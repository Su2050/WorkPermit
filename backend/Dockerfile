FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（使用国内镜像加速）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制应用代码
COPY . .

# 创建启动脚本
RUN echo '#!/bin/bash\n\
set -e\n\
cd /app\n\
PORT=${PORT:-8000}\n\
echo "Waiting for database..."\n\
sleep 5\n\
echo "Running database migrations..."\n\
alembic upgrade head || echo "Migration failed, continuing..."\n\
echo "Starting application on port $PORT..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# 暴露端口（默认8000，可通过环境变量覆盖）
EXPOSE 8000

# 健康检查（使用环境变量PORT，默认8000）
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD PORT=${PORT:-8000} && curl -f http://localhost:$PORT/api/health || exit 1

# 启动命令
CMD ["/entrypoint.sh"]

