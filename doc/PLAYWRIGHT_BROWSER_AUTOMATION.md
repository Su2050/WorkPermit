# Playwright 浏览器自动化测试方法

## 概述

本文档介绍如何使用 Playwright 自动化操作浏览器进行前端 UI 测试。Playwright 是 Microsoft 开发的浏览器自动化库，可以模拟真实用户在浏览器中的操作。

## 工作原理

### 1. 工具介绍

**Playwright** 通过浏览器驱动控制真实浏览器（Chrome、Firefox、Safari 等），模拟用户操作，实现自动化测试。

### 2. 核心步骤

#### 步骤1：启动浏览器

```python
browser = playwright.chromium.launch(headless=False, slow_mo=500)
```

- `headless=False`：显示浏览器窗口（可视化模式）
- `slow_mo=500`：每个操作延迟 500ms，方便观察执行过程
- `headless=True`：后台运行（不可见模式）

#### 步骤2：创建页面上下文

```python
context = browser.new_context(
    viewport={"width": 1920, "height": 1080},
    ignore_https_errors=True
)
page = context.new_page()
```

- 创建独立的浏览器上下文（类似无痕窗口）
- 设置视口大小（模拟不同屏幕尺寸）
- `ignore_https_errors=True`：忽略 HTTPS 证书错误

#### 步骤3：模拟用户操作

**访问页面：**
```python
page.goto("http://localhost:5173/login")
page.wait_for_load_state("networkidle")  # 等待页面完全加载
```

**定位元素：**
```python
# 方式1：使用 CSS 选择器
page.locator('input[placeholder*="用户名"]')

# 方式2：使用文本内容
page.locator('button:has-text("登录")')

# 方式3：使用角色定位（推荐，更稳定）
page.get_by_role("menuitem", name="施工单位").first
```

**填写表单：**
```python
page.locator('input[placeholder*="用户名"]').fill("admin")
page.locator('input[type="password"]').fill("admin123")
```

**点击按钮：**
```python
page.locator('button:has-text("登录")').click()
```

**等待页面跳转：**
```python
page.wait_for_url("**/dashboard**", timeout=5000)
page.wait_for_load_state("networkidle")
```

**监听网络请求：**
```python
def handle_response(response):
    if "/api/admin/contractors" in response.url:
        if response.status == 200:
            data = response.json()
            # 检查响应数据
            message = data.get("message", "")
            if "没有工地" in message:
                print(f"检测到错误: {message}")

page.on("response", handle_response)
```

## 实际执行流程示例

以下是一个完整的测试流程：

```python
def test_login_and_navigate(self, page: Page):
    """测试登录并导航"""
    # 1. 访问登录页
    page.goto("http://localhost:5173/login")
    page.wait_for_load_state("networkidle")
    
    # 2. 填写登录表单
    page.locator('input[placeholder*="用户名"]').fill("admin")
    page.locator('input[type="password"]').fill("admin123")
    
    # 3. 点击登录按钮
    page.locator('button:has-text("登录")').click()
    
    # 4. 等待跳转到首页
    page.wait_for_url("**/dashboard**", timeout=10000)
    page.wait_for_load_state("networkidle")
    
    # 5. 点击侧边栏菜单
    page.get_by_role("menuitem", name="施工单位").first.click()
    
    # 6. 等待页面跳转
    page.wait_for_url("**/contractors**", timeout=5000)
    page.wait_for_load_state("networkidle")
    
    # 7. 验证页面元素
    expect(page.locator('h1:has-text("施工单位管理")')).to_be_visible(timeout=3000)
```

## 运行测试时的实际过程

当运行测试时，Playwright 会：

1. **启动浏览器**：打开 Chrome 浏览器窗口
2. **访问页面**：在新标签页中打开 `http://localhost:5173/login`
3. **定位元素**：找到用户名输入框
4. **输入文本**：自动输入 "admin"
5. **定位密码框**：找到密码输入框
6. **输入密码**：自动输入 "admin123"
7. **点击按钮**：点击登录按钮
8. **等待跳转**：等待页面跳转到 dashboard
9. **继续操作**：执行后续的测试步骤

整个过程就像真实用户在操作浏览器一样！

## 为什么能看到浏览器窗口？

因为设置了 `headless=False`，浏览器会显示出来。如果设置为 `headless=True`，浏览器会在后台运行（不可见）。

## 优势

### 1. 真实浏览器环境
- 使用真实浏览器引擎（Chromium、Firefox、WebKit）
- 完全模拟用户行为
- 支持 JavaScript 执行

### 2. 自动化能力
- 可重复执行，无需手动操作
- 可以集成到 CI/CD 流程
- 支持并行执行多个测试

### 3. 强大的监听能力
- 监听所有网络请求和响应
- 捕获 API 调用结果
- 检查 HTTP 状态码和响应数据

### 4. 调试功能
- 可以截图保存测试过程
- 可以录制视频
- 支持慢动作执行（slow_mo）

### 5. 多浏览器支持
- 可以同时在 Chrome、Firefox、Safari 上测试
- 确保跨浏览器兼容性

## 与手动测试的对比

| 特性 | 手动测试 | Playwright 自动化测试 |
|------|---------|---------------------|
| **执行方式** | 需要人工操作 | 代码自动执行 |
| **一致性** | 容易出错 | 每次执行完全一致 |
| **速度** | 慢（分钟级） | 快（秒级） |
| **网络监听** | 无法捕获 | 可以监听所有网络活动 |
| **可重复性** | 难以重复 | 可以无限重复 |
| **CI/CD 集成** | 不支持 | 完全支持 |
| **成本** | 人力成本高 | 一次编写，多次使用 |

## 常用 API 参考

### 页面导航
```python
page.goto(url)                    # 访问 URL
page.go_back()                    # 后退
page.go_forward()                 # 前进
page.reload()                     # 刷新
```

### 元素定位
```python
page.locator(selector)            # CSS 选择器
page.get_by_role(role, name)      # 角色定位（推荐）
page.get_by_text(text)            # 文本定位
page.get_by_label(label)          # 标签定位
```

### 元素操作
```python
element.click()                   # 点击
element.fill(text)                # 填写文本
element.type(text)                # 输入文本（模拟键盘）
element.select_option(value)       # 选择选项
element.check()                   # 勾选复选框
element.uncheck()                 # 取消勾选
```

### 等待操作
```python
page.wait_for_url(pattern)        # 等待 URL 匹配
page.wait_for_load_state(state)   # 等待加载状态
page.wait_for_selector(selector)  # 等待元素出现
element.wait_for()                # 等待元素可见
```

### 断言验证
```python
expect(element).to_be_visible()   # 元素可见
expect(element).to_have_text(text) # 文本匹配
expect(element).to_be_enabled()   # 元素启用
expect(page).to_have_url(url)     # URL 匹配
```

### 网络监听
```python
page.on("request", handler)       # 监听请求
page.on("response", handler)      # 监听响应
page.route(url, handler)          # 拦截请求
```

## 安装和配置

### 1. 安装 Playwright

```bash
pip install playwright pytest-playwright
```

### 2. 安装浏览器驱动

```bash
playwright install chromium
```

### 3. 基本测试结构

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="module")
def browser_context(playwright):
    """创建浏览器上下文"""
    browser = playwright.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    yield context
    context.close()
    browser.close()

@pytest.fixture
def page(browser_context):
    """创建新页面"""
    page = browser_context.new_page()
    yield page
    page.close()

def test_example(page: Page):
    """示例测试"""
    page.goto("http://localhost:5173")
    expect(page.locator("h1")).to_be_visible()
```

## 最佳实践

### 1. 使用稳定的选择器
```python
# ❌ 不推荐：依赖 CSS 类名（可能变化）
page.locator('.btn-primary')

# ✅ 推荐：使用角色定位
page.get_by_role("button", name="提交")

# ✅ 推荐：使用 data-testid
page.locator('[data-testid="submit-btn"]')
```

### 2. 添加适当的等待
```python
# ❌ 不推荐：硬等待
time.sleep(2)

# ✅ 推荐：等待特定条件
page.wait_for_load_state("networkidle")
page.wait_for_url("**/dashboard**")
```

### 3. 使用 Page Object 模式
```python
class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.locator('input[placeholder*="用户名"]')
        self.password_input = page.locator('input[type="password"]')
        self.login_button = page.locator('button:has-text("登录")')
    
    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
```

### 4. 错误处理和调试
```python
def test_with_debugging(page: Page):
    try:
        page.goto("http://localhost:5173")
        # 如果失败，截图保存
    except Exception as e:
        page.screenshot(path="error.png")
        raise
```

## 总结

Playwright 是一个强大的浏览器自动化工具，可以：

- ✅ 模拟真实用户操作
- ✅ 监听网络请求和响应
- ✅ 支持多浏览器测试
- ✅ 集成到 CI/CD 流程
- ✅ 提供丰富的调试功能

通过 Playwright，我们可以编写自动化测试来验证前端功能，提高测试效率和可靠性。

## 相关资源

- [Playwright 官方文档](https://playwright.dev/python/)
- [Playwright Python API](https://playwright.dev/python/docs/api/class-playwright)
- [项目测试文件](../tests/test_frontend_ui.py)

