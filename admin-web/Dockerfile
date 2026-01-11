# ============ 构建阶段 ============
FROM node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json ./

# 安装依赖（使用国内镜像加速）
# 注意：构建阶段需要 devDependencies（如 vite）
RUN npm config set registry https://registry.npmmirror.com && \
    npm ci

# 复制源代码
COPY . .

# 构建参数（从环境变量注入）
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# 构建生产版本
RUN npm run build

# ============ 运行阶段 ============
FROM nginx:1.25-alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]

