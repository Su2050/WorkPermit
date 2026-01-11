# 作业许可证管理系统 - 自动化测试

## 📁 目录结构

```
tests/
├── backend/                    # 后端API测试
│   ├── test_areas_api.py      # 作业区域API测试
│   ├── test_videos_api.py     # 培训视频API测试
│   ├── test_contractors_api.py # 施工单位API测试
│   ├── test_workers_api.py    # 人员管理API测试
│   ├── test_users_api.py      # 用户管理API测试
│   ├── test_reports_api.py    # 报表中心API测试
│   ├── test_alerts_api.py     # 告警中心API测试
│   └── test_settings_api.py   # 系统设置API测试
├── frontend/                   # 前端UI测试
│   ├── test_login_ui.py       # 登录模块UI测试
│   ├── test_dashboard_ui.py   # 仪表盘UI测试
│   ├── test_areas_ui.py       # 作业区域UI测试
│   ├── test_videos_ui.py      # 培训视频UI测试
│   ├── test_contractors_ui.py # 施工单位UI测试
│   ├── test_workers_ui.py     # 人员管理UI测试
│   ├── test_users_ui.py       # 用户管理UI测试
│   ├── test_reports_ui.py     # 报表中心UI测试
│   ├── test_alerts_ui.py      # 告警中心UI测试
│   └── test_settings_ui.py    # 系统设置UI测试
├── integration/                # 集成测试
│   └── test_full_workflow.py  # 完整业务流程测试
├── test_api.py                # 综合API测试（旧版）
├── test_system_comprehensive.py # 系统综合测试
├── test_performance.py        # 性能测试
├── test_frontend_ui.py        # 前端UI测试（旧版）
├── test_ticket_detail_422.py  # 作业票详情422错误测试
├── run_all_tests.py           # 测试运行脚本
├── requirements.txt           # 测试依赖
├── 完整测试计划文档.md         # 详细测试计划
├── 快速参考.md                 # 快速命令参考
└── README.md                  # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd tests
pip install -r requirements.txt

# 安装Playwright浏览器（前端测试需要）
playwright install chromium
```

### 2. 环境准备

确保后端服务已启动：
```bash
cd ../backend
source /path/to/your/venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

确保前端服务已启动（UI测试需要）：
```bash
cd ../admin-web
npm run dev
```

### 3. 运行测试

#### 运行所有API测试
```bash
# 后端API测试
pytest backend/ -v

# 综合API测试
pytest test_api.py -v

# 系统综合测试（推荐）
pytest test_system_comprehensive.py -v
```

#### 运行前端UI测试
```bash
# 所有前端测试
pytest frontend/ -v

# 特定模块测试
pytest frontend/test_login_ui.py -v
```

#### 运行集成测试
```bash
pytest integration/ -v
```

#### 运行性能测试
```bash
pytest test_performance.py -v
```

#### 运行全部测试
```bash
pytest -v
```

## 📊 测试覆盖范围

### 后端API测试 (8个模块)

| 模块 | 测试文件 | 测试项 |
|------|---------|--------|
| 作业区域 | test_areas_api.py | 创建/查询/更新/删除/分页 |
| 培训视频 | test_videos_api.py | 创建/查询/更新/删除/统计 |
| 施工单位 | test_contractors_api.py | 创建/查询/更新/删除/选项 |
| 人员管理 | test_workers_api.py | 创建/查询/更新/删除/搜索 |
| 用户管理 | test_users_api.py | 创建/查询/更新/删除/权限 |
| 报表中心 | test_reports_api.py | 作业票统计/安全分析/导出 |
| 告警中心 | test_alerts_api.py | 告警列表/处理/统计 |
| 系统设置 | test_settings_api.py | 参数配置/设备管理 |

### 前端UI测试 (10个模块)

| 模块 | 测试文件 | 测试项 |
|------|---------|--------|
| 登录 | test_login_ui.py | 登录/登出/表单验证 |
| 仪表盘 | test_dashboard_ui.py | 统计卡片/图表/快捷操作 |
| 作业区域 | test_areas_ui.py | 列表/新增/编辑/删除弹窗 |
| 培训视频 | test_videos_ui.py | 列表/新增/编辑/播放 |
| 施工单位 | test_contractors_ui.py | 列表/新增/编辑/删除 |
| 人员管理 | test_workers_ui.py | 列表/新增/编辑/删除/搜索 |
| 用户管理 | test_users_ui.py | 列表/新增/编辑/权限配置 |
| 报表中心 | test_reports_ui.py | 报表展示/筛选/导出 |
| 告警中心 | test_alerts_ui.py | 告警列表/处理/标记已读 |
| 系统设置 | test_settings_ui.py | 参数配置/设备管理 |

### 集成测试

| 测试场景 | 说明 |
|----------|------|
| 完整业务流程 | 工地创建 → 施工单位 → 区域 → 人员 → 作业票 → 审批 |
| 数据一致性 | 关联数据的完整性验证 |
| 权限测试 | 不同角色的访问控制 |
| 多租户隔离 | site_id数据隔离验证 |

### 性能测试

| 测试项 | 阈值 |
|--------|------|
| 登录响应 | < 500ms |
| 列表查询 | < 300ms |
| 并发请求 | 10并发 < 1s |
| 大数据量 | 1000条 < 3s |

## 🔧 配置说明

### 测试配置

测试配置位于各测试文件中，主要参数：
- `BASE_URL`: API基础URL，默认 `http://localhost:8000`
- `FRONTEND_URL`: 前端URL，默认 `http://localhost:5173`
- `ADMIN_USERNAME`: 管理员用户名
- `ADMIN_PASSWORD`: 管理员密码

### 自定义配置

可以通过环境变量覆盖默认配置：
```bash
export TEST_BASE_URL=http://your-api-server:8000
export TEST_FRONTEND_URL=http://your-frontend:5173
pytest -v
```

## 📝 编写新测试

### API测试示例

```python
import pytest
import requests

class TestMyModule:
    """我的模块测试"""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # 登录获取token
        resp = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        self.token = resp.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list(self):
        """获取列表测试"""
        resp = requests.get(
            f"{self.BASE_URL}/admin/my-module",
            headers=self.headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
```

### UI测试示例

```python
import pytest
from playwright.sync_api import Page, expect

class TestMyModuleUI:
    """我的模块UI测试"""
    
    BASE_URL = "http://localhost:5173"
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        self.page = page
        # 登录
        page.goto(f"{self.BASE_URL}/login")
        page.fill('[placeholder="用户名"]', 'admin')
        page.fill('[placeholder="密码"]', 'admin123')
        page.click('button:has-text("登录")')
        page.wait_for_url("**/dashboard")
    
    def test_navigation(self):
        """导航测试"""
        self.page.click('text=我的模块')
        expect(self.page).to_have_url("**/my-module")
```

## 🔄 CI/CD 集成

项目已配置GitHub Actions自动化测试，位于 `.github/workflows/test.yml`。

每次推送到 `main` 或 `develop` 分支，或创建Pull Request时，会自动运行：
1. 后端API测试
2. 前端UI测试
3. 集成测试

## 📈 测试报告

### 生成HTML报告
```bash
pytest --html=report.html --self-contained-html
```

### 生成覆盖率报告
```bash
pytest --cov=../backend/app --cov-report=html
```

### 生成Allure报告
```bash
pytest --alluredir=./allure-results
allure serve ./allure-results
```

## ❓ 常见问题

### Q: 前端测试运行失败？
A: 确保已安装Playwright浏览器：`playwright install chromium`

### Q: API测试连接失败？
A: 检查后端服务是否在8000端口运行

### Q: 测试数据清理？
A: 测试使用唯一时间戳命名，避免数据冲突

### Q: 如何只运行某个模块的测试？
A: 使用pytest的-k参数：`pytest -k "test_areas" -v`

## 📞 联系方式

如有问题，请联系开发团队。
