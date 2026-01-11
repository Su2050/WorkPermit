# Zeabur 平台详细部署指南

## 📋 部署前准备清单

- ✅ Git 仓库已初始化
- ✅ 代码已推送到远程仓库
- ✅ 补充前端 Dockerfile 和 Nginx 配置
- ✅ 优化后端启动流程
- ⬜ 注册 Zeabur 账号
- ⬜ 配置部署服务

---

## 第一阶段：准备配置文件（已完成）

所有必要的配置文件已经创建并提交到 Git 仓库：

- ✅ `admin-web/Dockerfile` - 前端多阶段构建配置
- ✅ `admin-web/nginx.conf` - Nginx 反向代理配置
- ✅ `admin-web/.dockerignore` - Docker 构建忽略文件
- ✅ `backend/Dockerfile` - 后端优化配置（含启动脚本）
- ✅ `backend/.dockerignore` - Docker 构建忽略文件
- ✅ `backend/scripts/init_production.py` - 生产环境初始化脚本

---

## 第二阶段：Zeabur 平台配置（Web 操作）

### 2.1 注册 Zeabur 账号

**步骤：**

1. 访问 https://zeabur.com
2. 点击右上角「Sign In」
3. 选择「Continue with GitHub」（推荐）
4. 授权 Zeabur 访问你的 GitHub 账号
5. 完成注册后进入控制台

**注意事项：**
- 使用 GitHub 登录可以直接关联代码仓库
- 新用户赠送 $5 免费额度

---

### 2.2 创建项目

**步骤：**

1. 进入 Zeabur 控制台
2. 点击「Create Project」按钮
3. 填写项目信息：
   - **Project Name**: `work-permit-system`
   - **Region**: 选择「Hong Kong」（国内访问最快）
4. 点击「Create」

---

### 2.3 部署 PostgreSQL 数据库

**步骤：**

1. 在项目页面，点击「Add Service」
2. 选择「Prebuilt Service」
3. 找到「PostgreSQL」，点击「Deploy」
4. 配置参数：
   - **Service Name**: `postgres`（保持默认）
   - **Version**: `15`
   - **Username**: `postgres`（自动生成）
   - **Password**: 自动生成（会显示在环境变量中）
   - **Database**: `work_permit`
5. 点击「Deploy」，等待约 30 秒启动完成

**重要：** 部署完成后，Zeabur 会自动生成以下环境变量：
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DATABASE`
- `DATABASE_URL`（完整连接字符串）

---

### 2.4 部署 Redis

**步骤：**

1. 点击「Add Service」
2. 选择「Prebuilt Service」→「Redis」
3. 配置参数：
   - **Service Name**: `redis`
   - **Version**: `7`
4. 点击「Deploy」

**自动生成的环境变量：**
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`
- `REDIS_CONNECTION_STRING`

---

### 2.5 部署 MinIO（可选）

**步骤：**

1. 点击「Add Service」
2. 选择「Prebuilt Service」→「MinIO」
3. 配置参数：
   - **Service Name**: `minio`
   - **Root User**: `minioadmin`
   - **Root Password**: `minioadmin123`
4. 点击「Deploy」

**自动生成的环境变量：**
- `MINIO_ENDPOINT`
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`

---

### 2.6 部署后端服务

**步骤：**

1. 点击「Add Service」
2. 选择「Git Repository」
3. 如果是第一次，需要授权 Zeabur 访问你的 GitHub
4. 选择仓库：`WorkPermit`（你的仓库名）
5. 配置构建参数：
   - **Service Name**: `backend`（**必须使用这个名称**，前端 Nginx 配置依赖此名称）
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Dockerfile Path**: `Dockerfile`
6. 点击「Deploy」

**配置环境变量：**

在服务部署后，点击服务卡片 → 「Variables」标签，添加以下环境变量：

```env
# 数据库连接（使用 Zeabur 内部服务引用）
# 注意：需要修改协议为 asyncpg
DATABASE_URL=postgresql+asyncpg://${POSTGRES.USERNAME}:${POSTGRES.PASSWORD}@${POSTGRES.HOST}:${POSTGRES.PORT}/${POSTGRES.DATABASE}

# Redis 连接
REDIS_URL=${REDIS.CONNECTION_STRING}
CELERY_BROKER_URL=${REDIS.CONNECTION_STRING}
CELERY_RESULT_BACKEND=${REDIS.CONNECTION_STRING}

# 应用配置
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars
DEBUG=false
LOG_LEVEL=INFO
APP_NAME=作业票管理系统
APP_VERSION=1.0.0

# CORS 配置（稍后添加前端域名）
CORS_ORIGINS=["*"]

# MinIO 配置（如果部署了 MinIO）
MINIO_ENDPOINT=${MINIO.HOST}:${MINIO.PORT}
MINIO_ACCESS_KEY=${MINIO.ROOT_USER}
MINIO_SECRET_KEY=${MINIO.ROOT_PASSWORD}
MINIO_SECURE=false
MINIO_BUCKET=work-permit
```

**重要提示：**
- `${POSTGRES.DATABASE_URL}` 是 Zeabur 的服务引用语法
- `SECRET_KEY` 必须修改为随机字符串（至少 32 位）
- 可以使用在线工具生成：https://randomkeygen.com/
- **后端服务名称必须为 `backend`**，否则前端 Nginx 无法正确代理

**保存环境变量后，服务会自动重启**

---

### 2.7 部署前端服务

**步骤：**

1. 点击「Add Service」
2. 选择「Git Repository」
3. 选择同一个仓库
4. 配置构建参数：
   - **Service Name**: `admin-web`
   - **Branch**: `main`
   - **Root Directory**: `admin-web`
   - **Dockerfile Path**: `Dockerfile`
5. 点击「Deploy」

**配置环境变量：**

在「Variables」标签中添加：

```env
# API 地址（使用相对路径，通过 Nginx 代理）
VITE_API_BASE_URL=/api
```

**配置构建参数（Build Args）：**

在「Settings」→「Build」→「Build Arguments」中添加：

```
VITE_API_BASE_URL=/api
```

---

### 2.8 配置服务间通信

**关键步骤：** 让前端 Nginx 能够访问后端服务

1. 进入前端服务（admin-web）
2. 点击「Networking」标签
3. 在「Private Networking」部分，确保能看到 `backend` 服务
4. Zeabur 会自动配置内部 DNS，使得 `http://backend:8000` 可以访问

**验证：** 前端 Nginx 配置中的 `proxy_pass http://backend:8000` 会自动解析到后端服务

---

### 2.9 配置公网访问域名

**步骤：**

1. 进入前端服务（admin-web）
2. 点击「Networking」标签
3. 在「Domains」部分，点击「Generate Domain」
4. Zeabur 会自动分配一个域名，格式：`work-permit-xxx.zeabur.app`
5. 等待 DNS 生效（约 1-2 分钟）

**获取的域名示例：**
- 前端访问：`https://work-permit-abc123.zeabur.app`
- 后端 API：`https://work-permit-abc123.zeabur.app/api/docs`

---

### 2.10 更新后端 CORS 配置

**重要：** 需要将前端域名添加到后端 CORS 白名单

1. 复制前端域名（如 `https://work-permit-abc123.zeabur.app`）
2. 进入后端服务 → 「Variables」
3. 修改 `CORS_ORIGINS` 环境变量：

```env
CORS_ORIGINS=["https://work-permit-abc123.zeabur.app"]
```

4. 保存后服务会自动重启

---

## 第三阶段：初始化数据库

### 3.1 方式一：使用 Zeabur 终端（推荐）

**步骤：**

1. 进入后端服务（backend）
2. 点击「Logs」标签，查看启动日志
3. 确认看到「Running database migrations...」和「Starting application...」
4. 如果迁移成功，点击「Terminal」标签
5. 在终端中运行：

```bash
python scripts/init_production.py
```

6. 看到「✅ 管理员账号创建成功」即表示成功

---

### 3.2 方式二：使用本地连接（备选）

**步骤：**

1. 在 Zeabur 中获取 PostgreSQL 的公网连接信息：
   - 进入 postgres 服务
   - 点击「Networking」→「Expose」
   - 复制公网连接字符串
2. 在本地终端运行：

```bash
cd /Users/suliangliang/Documents/AI_coding_demo/backend

# 设置环境变量
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/dbname"

# 运行迁移
alembic upgrade head

# 初始化数据
python scripts/init_production.py
```

---

## 第四阶段：验证部署

### 4.1 检查服务状态

在 Zeabur 项目页面，确认所有服务状态为「Running」：

- ✅ postgres - Running
- ✅ redis - Running
- ✅ backend - Running
- ✅ admin-web - Running

---

### 4.2 测试后端 API

访问：`https://your-domain.zeabur.app/api/health`

**预期响应：**

```json
{
  "status": "healthy",
  "app": "作业票管理系统",
  "version": "1.0.0"
}
```

---

### 4.3 测试前端访问

访问：`https://your-domain.zeabur.app`

**预期结果：**
- 看到登录页面
- 输入账号密码：`admin` / `admin123`
- 成功登录进入系统

---

### 4.4 测试 API 文档

访问：`https://your-domain.zeabur.app/api/docs`

**预期结果：**
- 看到 Swagger UI 文档
- 可以展开接口查看详情

---

## 第五阶段：部署 Celery Worker（可选）

如果需要异步任务功能（如告警推送、定时任务），需要部署 Celery：

### 5.1 创建 Celery Worker 服务

**步骤：**

1. 点击「Add Service」→「Git Repository」
2. 选择同一个仓库
3. 配置：
   - **Service Name**: `celery-worker`
   - **Root Directory**: `backend`
   - **Dockerfile Path**: `Dockerfile`
4. 在「Settings」→「Start Command」中覆盖启动命令：

```bash
celery -A app.tasks.celery_app worker --loglevel=info --queues=notification,access,scheduler
```

5. 配置环境变量（与 backend 相同）

---

### 5.2 创建 Celery Beat 服务（定时任务）

**步骤：**

1. 点击「Add Service」→「Git Repository」
2. 配置：
   - **Service Name**: `celery-beat`
   - **Root Directory**: `backend`
3. 启动命令：

```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## 故障排查指南

### 问题 1：前端无法访问后端 API

**症状：** 浏览器控制台显示 `ERR_NAME_NOT_RESOLVED` 或 `502 Bad Gateway`

**排查步骤：**

1. 检查后端服务是否正常运行（Zeabur 控制台查看状态）
2. 检查前端 Nginx 配置中的 `proxy_pass http://backend:8000`
3. 确认服务名称是否正确（必须是 `backend`）
4. 查看前端服务日志：`Logs` 标签

**解决方案：**
- 确保后端服务名称为 `backend`
- 重新部署前端服务

---

### 问题 2：数据库连接失败

**症状：** 后端日志显示 `could not connect to server`

**排查步骤：**

1. 检查 PostgreSQL 服务状态
2. 验证 `DATABASE_URL` 环境变量格式：
   ```
   postgresql+asyncpg://user:pass@host:port/dbname
   ```
3. 确认协议是 `postgresql+asyncpg`（不是 `postgresql`）

**解决方案：**
- 修改 `DATABASE_URL` 环境变量
- 重启后端服务

---

### 问题 3：构建超时

**症状：** 构建过程卡在 `npm install` 或 `pip install`

**排查步骤：**

1. 查看构建日志
2. 检查是否使用了国内镜像源

**解决方案：**
- 确认 Dockerfile 中已配置镜像源
- 在 Zeabur 设置中增加构建超时时间（Settings → Build Timeout）

---

### 问题 4：CORS 错误

**症状：** 浏览器控制台显示 `Access-Control-Allow-Origin` 错误

**排查步骤：**

1. 检查后端 `CORS_ORIGINS` 环境变量
2. 确认前端域名已添加到白名单

**解决方案：**
```env
CORS_ORIGINS=["https://your-frontend-domain.zeabur.app"]
```

---

### 问题 5：管理员账号创建失败

**症状：** 运行 `init_production.py` 时报错

**排查步骤：**

1. 检查数据库连接是否正常
2. 查看后端服务日志，确认数据库迁移是否成功
3. 确认表结构是否正确创建

**解决方案：**
- 先运行 `alembic upgrade head` 确保数据库表已创建
- 检查 `SysUser` 表是否存在

---

## 成本估算

### 免费额度使用情况

| 服务 | 资源配置 | 月费用 |
|------|---------|--------|
| PostgreSQL | 0.25 vCPU, 256MB | $2.5 |
| Redis | 0.1 vCPU, 128MB | $1.0 |
| Backend | 0.5 vCPU, 512MB | $5.0 |
| Frontend | 0.25 vCPU, 256MB | $2.5 |
| **合计** | | **$11/月** |

**免费额度：** $5/月（约 100 小时运行时间）

**节省成本建议：**
- 仅在工作日启动服务（8小时/天 × 22天 = 176小时/月）
- 实际费用：$11 × (176/730) ≈ **$2.65/月**（在免费额度内）

---

## 持续部署流程

配置完成后，后续更新只需：

```bash
# 1. 修改代码
# 2. 提交到 Git
git add .
git commit -m "feat: 新功能"
git push origin main

# 3. Zeabur 自动检测并重新部署（约 2-3 分钟）
```

---

## 后续优化建议

### 短期（1-2周）
- ✅ 修改默认管理员密码
- ✅ 配置数据库定期备份
- ✅ 监控服务运行状态

### 中期（1个月）
- 🔄 评估是否需要升级到付费版
- 🔄 配置自定义域名（如 `work.yourcompany.com`）
- 🔄 启用 Zeabur 的日志聚合功能

### 长期（3个月+）
- 📊 根据用户增长考虑迁移到专用服务器
- 🔐 配置更严格的安全策略
- 📈 优化数据库性能

---

## 总结

### ✅ 完成后你将拥有：

1. **稳定的公网访问地址**：`https://xxx.zeabur.app`
2. **自动 HTTPS 证书**：无需手动配置
3. **自动化部署**：Git 推送即部署
4. **服务监控**：实时查看日志和状态
5. **零运维成本**：无需管理服务器

### ⏱️ 预计时间：

- 准备配置文件：✅ 已完成
- Zeabur 平台配置：30 分钟
- 测试验证：15 分钟
- **总计：约 45 分钟**

### 📞 技术支持：

- Zeabur 官方文档：https://zeabur.com/docs
- Discord 社区：https://discord.gg/zeabur
- GitHub Issues：项目仓库提问

---

## 快速参考

### 关键环境变量速查表

**后端服务（backend）：**
```env
DATABASE_URL=postgresql+asyncpg://${POSTGRES.USERNAME}:${POSTGRES.PASSWORD}@${POSTGRES.HOST}:${POSTGRES.PORT}/${POSTGRES.DATABASE}
REDIS_URL=${REDIS.CONNECTION_STRING}
CELERY_BROKER_URL=${REDIS.CONNECTION_STRING}
CELERY_RESULT_BACKEND=${REDIS.CONNECTION_STRING}
SECRET_KEY=<生成32位随机字符串>
CORS_ORIGINS=["https://your-domain.zeabur.app"]
```

**前端服务（admin-web）：**
```env
VITE_API_BASE_URL=/api
```

### 服务名称要求

- **后端服务名称必须为 `backend`**（前端 Nginx 配置依赖此名称）
- 前端服务名称可以是任意值（如 `admin-web`）
- 数据库和 Redis 服务名称保持默认即可

### 测试账号

- 用户名：`admin`
- 密码：`admin123`
- 角色：系统管理员（SysAdmin）

---

**祝部署顺利！** 🚀

