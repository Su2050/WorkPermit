"""
前端测试 Playwright 配置
统一的浏览器配置和登录fixture - 优化版（复用登录状态）
"""
import pytest
import os
import time

# 测试配置
BASE_URL = "http://localhost:5173"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"
AUTH_STATE_FILE = os.path.join(os.path.dirname(__file__), ".auth_state.json")


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """配置浏览器启动参数"""
    return {
        **browser_type_launch_args,
        "args": [
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
        ],
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """配置浏览器上下文参数"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "locale": "zh-CN",
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def authenticated_context(browser, browser_context_args):
    """
    Session 级别的已登录浏览器上下文
    只在测试会话开始时登录一次，后续所有测试复用登录状态
    """
    # 创建上下文
    context = browser.new_context(**browser_context_args)
    page = context.new_page()
    page.set_default_timeout(30000)
    
    # 执行登录
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    
    username_input = page.locator("input[type='text'], input[placeholder*='用户']").first
    password_input = page.locator("input[type='password']").first
    
    username_input.fill(TEST_USERNAME)
    password_input.fill(TEST_PASSWORD)
    
    login_button = page.locator("button[type='submit'], button:has-text('登录')").first
    login_button.click()
    
    # 等待登录成功
    try:
        page.wait_for_url("**/dashboard**", timeout=10000)
    except:
        pass
    
    page.wait_for_load_state("networkidle")
    
    # 保存登录状态
    context.storage_state(path=AUTH_STATE_FILE)
    
    page.close()
    context.close()
    
    # 返回带登录状态的新上下文
    authenticated_ctx = browser.new_context(
        **browser_context_args,
        storage_state=AUTH_STATE_FILE
    )
    
    yield authenticated_ctx
    
    # 清理
    authenticated_ctx.close()
    # 删除状态文件
    if os.path.exists(AUTH_STATE_FILE):
        os.remove(AUTH_STATE_FILE)


@pytest.fixture(scope="function")
def page(authenticated_context):
    """
    为每个测试创建新页面（复用登录状态）
    使用 session 级别的 authenticated_context，避免重复登录
    """
    page = authenticated_context.new_page()
    page.set_default_timeout(15000)  # 缩短超时时间
    page.set_default_navigation_timeout(15000)
    yield page
    try:
        page.close()
    except Exception:
        pass


@pytest.fixture
def logged_in_page(page):
    """
    已登录的页面（兼容旧测试代码）
    由于 page 已经复用了登录状态，这里直接返回即可
    """
    # 确保在正确的页面状态
    current_url = page.url
    if "login" in current_url:
        # 如果意外在登录页，重新登录
        username_input = page.locator("input[type='text'], input[placeholder*='用户']").first
        password_input = page.locator("input[type='password']").first
        
        username_input.fill(TEST_USERNAME)
        password_input.fill(TEST_PASSWORD)
        
        login_button = page.locator("button[type='submit'], button:has-text('登录')").first
        login_button.click()
        
        try:
            page.wait_for_url("**/dashboard**", timeout=10000)
        except:
            pass
        
        page.wait_for_load_state("networkidle")
    
    return page
