# 🏗️ 作业票管理系统

建筑工地作业票数字化管理系统，实现从作业票创建、班前教育、门禁授权到出入记录追溯的完整闭环。

---

## 📋 系统概述

- **项目类型**: Web管理后台 + 微信小程序
- **技术栈**: FastAPI + Vue3 + PostgreSQL + Redis
- **开发方式**: AI辅助开发

### 核心功能

| 模块 | 功能描述 |
|-----|---------|
| 作业票管理 | 创建、审批、延期、关闭作业票 |
| 区域管理 | 施工区域划分与门禁关联 |
| 人员管理 | 工人信息、培训记录、门禁授权 |
| 培训视频 | 班前教育视频播放与完成记录 |
| 告警中心 | 异常告警推送与处理 |
| 报表统计 | 多维度数据分析与导出 |

---

## 🚀 快速启动

### 前置要求

- **Docker Desktop** - 运行 PostgreSQL、Redis、MinIO
- **Conda** - Python 环境管理
- **Node.js 18+** - 前端开发

### 1. 启动基础服务

```bash
# 启动 Docker Desktop 应用，然后运行：
cd /Users/suliangliang/Documents/AI_coding_demo
docker-compose up -d postgres redis minio

# 检查服务状态（应该看到三个服务状态为 Up）
docker-compose ps
```

### 2. 启动后端

```bash
# 激活环境
conda activate workpermit

# 进入后端目录
cd backend

# 运行数据库迁移
alembic upgrade head

# 初始化测试数据（可选）
python scripts/init_demo_data.py

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端

```bash
# 新开终端
cd admin-web
npm install
npm run dev
```

### 4. 启动 Celery（可选，用于异步任务）

```bash
# 终端2 - Celery Worker
cd backend && conda activate workpermit
celery -A app.tasks.celery_app worker --loglevel=info

# 终端3 - Celery Beat（定时任务）
celery -A app.tasks.celery_app beat --loglevel=info

# 终端4 - Celery Flower（监控）
celery -A app.tasks.celery_app flower --port=5555
```

---

## 🌐 访问地址

| 服务 | 地址 | 说明 |
|-----|------|------|
| 前端应用 | http://localhost:5173 | Vue3 管理后台 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| ReDoc 文档 | http://localhost:8000/api/redoc | ReDoc |
| Celery Flower | http://localhost:5555 | 任务监控 |
| MinIO 控制台 | http://localhost:9001 | 文件存储 |

---

## 🔐 测试账号

运行测试数据初始化后可使用：

| 角色 | 用户名 | 密码 |
|-----|-------|------|
| 系统管理员 | `admin` | `admin123` |
| 施工单位管理员 | `contractor1` | `contractor123` |

---

## 📁 项目结构

```
AI_coding_demo/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── models/         # 数据模型
│   │   ├── middleware/     # 中间件
│   │   └── tasks/          # Celery 任务
│   ├── scripts/            # 脚本工具
│   └── requirements.txt
├── admin-web/              # Vue3 管理后台
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── api/            # API 封装
│   │   └── router/         # 路由配置
│   └── package.json
├── tests/                  # 测试套件
│   ├── backend/            # 后端 API 测试
│   ├── frontend/           # 前端 UI 测试
│   └── integration/        # 集成测试
└── docker-compose.yml      # Docker 配置
```

---

## 🧪 运行测试

```bash
# 激活环境
conda activate workpermit

# 后端 API 测试
cd tests
python -m pytest backend/ -v

# 前端 UI 测试（需要前后端服务运行）
python -m pytest frontend/ -v

# 全部测试
python -m pytest -v
```

---

## 🔧 常见问题

### Docker 未运行
```bash
# 错误: Cannot connect to the Docker daemon
# 解决: 启动 Docker Desktop 应用，然后重新运行
docker-compose up -d
```

### 数据库连接失败
```bash
# 检查 PostgreSQL 是否运行
docker-compose ps postgres
docker-compose logs postgres
docker-compose restart postgres
```

### 端口被占用
```bash
# 检查端口占用
lsof -i :8000
lsof -i :5173
lsof -i :5432

# 杀死占用进程
kill -9 <PID>
```

### 环境变量未设置
创建 `backend/.env` 文件：
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/work_permit
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
```

---

## 📚 相关文档

| 文档 | 说明 |
|-----|------|
| `项目构建总结.md` | 完整的项目构建过程 |
| `系统测试完整报告.md` | 测试覆盖与结果 |
| `开发问题修复记录.md` | 问题排查与修复 |
| `docs/requirements/` | 需求文档目录 |

### 需求文档 (`docs/requirements/`)

| 文档 | 说明 |
|-----|------|
| `PRD_WorkPermit_for_Cursor_no_citations.md` | 产品需求文档 |
| `PRD_WorkPermit_for_Cursor_with_citations.md` | 产品需求文档(带引用) |
| `第三方系统集成需求文档.md` | 外部系统集成需求 |

---

## 📝 License

MIT License

