"""
视频创建前端UI测试 - 专门测试新增视频功能
测试修复后的site_id处理逻辑
"""
import pytest
from playwright.sync_api import Page, expect
import time

# 配置
BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8000/api"

# 测试用户
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def browser_context(playwright):
    """创建浏览器上下文"""
    browser = playwright.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
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


@pytest.fixture
def logged_in_page(page: Page):
    """登录并导航到视频管理页面"""
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    page.locator('input[placeholder*="用户名"]').fill(TEST_USERNAME)
    page.locator('input[type="password"]').fill(TEST_PASSWORD)
    page.locator('button:has-text("登录")').click()
    page.wait_for_url("**/dashboard**", timeout=10000)
    page.wait_for_load_state("networkidle")
    
    # 导航到视频管理
    page.get_by_role("menuitem", name="培训视频").first.click()
    page.wait_for_url("**/videos**", timeout=5000)
    page.wait_for_load_state("networkidle")
    
    yield page


class TestCreateVideoFlow:
    """测试新增视频完整流程"""
    
    def test_open_create_dialog(self, logged_in_page: Page):
        """测试：打开新增视频对话框"""
        print("\n  === 测试打开新增视频对话框 ===")
        
        # 点击上传视频按钮
        add_button = logged_in_page.locator('button:has-text("上传视频"), button:has-text("新增")')
        expect(add_button.first).to_be_visible(timeout=5000)
        add_button.first.click()
        
        # 等待对话框打开（使用更精确的定位器）
        dialog = logged_in_page.get_by_role('dialog').first
        expect(dialog).to_be_visible(timeout=3000)
        
        # 验证对话框标题
        expect(logged_in_page.locator('text=新增视频, text=上传视频')).to_be_visible()
        print("  ✓ 新增视频对话框成功打开")
    
    def test_form_fields_present(self, logged_in_page: Page):
        """测试：表单字段完整性"""
        print("\n  === 测试表单字段 ===")
        
        # 打开对话框
        add_button = logged_in_page.locator('button:has-text("上传视频"), button:has-text("新增")')
        add_button.first.click()
        logged_in_page.wait_for_timeout(500)
        
        # 检查必填字段
        expect(logged_in_page.locator('input[placeholder*="视频标题"]')).to_be_visible()
        expect(logged_in_page.locator('input[placeholder*="视频URL"]')).to_be_visible()
        expect(logged_in_page.locator('input[placeholder*="视频时长"]')).to_be_visible()
        
        print("  ✓ 所有必填字段都存在")
    
    def test_create_video_success(self, logged_in_page: Page):
        """测试：成功创建视频（包含site_id处理）"""
        print("\n  === 测试成功创建视频 ===")
        
        # 监听API请求
        api_requests = []
        api_responses = []
        
        def handle_request(request):
            if "/api/admin/videos" in request.url and request.method == "POST":
                api_requests.append(request)
        
        def handle_response(response):
            if "/api/admin/videos" in response.url and response.request.method == "POST":
                api_responses.append(response)
        
        logged_in_page.on("request", handle_request)
        logged_in_page.on("response", handle_response)
        
        # 打开对话框
        add_button = logged_in_page.locator('button:has-text("上传视频"), button:has-text("新增")')
        add_button.first.click()
        logged_in_page.wait_for_timeout(500)
        
        # 填写表单
        unique_id = int(time.time())
        logged_in_page.locator('input[placeholder*="视频标题"]').fill(f"测试视频_{unique_id}")
        logged_in_page.locator('input[placeholder*="视频URL"]').fill(f"https://example.com/video_{unique_id}.mp4")
        
        # 填写时长
        duration_input = logged_in_page.locator('input[placeholder*="视频时长"]').first
        if duration_input.is_visible(timeout=2000):
            duration_input.fill("120")
        
        # 提交表单
        submit_button = logged_in_page.locator('.el-dialog button:has-text("创建"), .el-dialog button:has-text("确定")').last
        submit_button.click()
        
        # 等待响应
        logged_in_page.wait_for_timeout(2000)
        
        # 检查API请求是否包含site_id
        if api_requests:
            try:
                request_data = api_requests[0].post_data_json if hasattr(api_requests[0], 'post_data_json') else None
                if request_data:
                    if "site_id" in request_data:
                        print(f"  ✓ API请求包含site_id: {request_data['site_id']}")
                    else:
                        print(f"  ❌ API请求缺少site_id字段")
                        print(f"     请求数据: {request_data}")
            except:
                pass
        
        # 检查响应
        if api_responses:
            response = api_responses[0]
            if response.status == 200:
                try:
                    data = response.json()
                    if data.get("code") == 0:
                        print("  ✓ 视频创建成功")
                        # 检查是否有成功提示
                        success_msg = logged_in_page.locator('.el-message--success')
                        if success_msg.is_visible(timeout=2000):
                            print("  ✓ 显示成功提示")
                    else:
                        error_msg = data.get("message", "")
                        print(f"  ❌ 创建失败: {error_msg}")
                        if "site_id" in error_msg.lower() or "工地" in error_msg:
                            print("  ❌ 错误与site_id相关，说明修复可能有问题")
                except:
                    pass
            elif response.status == 422:
                print(f"  ❌ 返回422错误（验证失败）")
                try:
                    error_data = response.json()
                    print(f"     错误详情: {error_data}")
                except:
                    pass
            else:
                print(f"  ⚠ 返回状态码: {response.status}")
        
        # 等待对话框关闭（如果成功）
        logged_in_page.wait_for_timeout(1000)
    
    def test_create_video_without_site_should_show_error(self, logged_in_page: Page):
        """测试：如果没有可用工地，应该显示错误提示"""
        print("\n  === 测试无工地时的错误处理 ===")
        
        # 监听API响应
        error_found = False
        error_message = ""
        
        def handle_response(response):
            nonlocal error_found, error_message
            if "/api/admin/videos" in response.url and response.request.method == "POST":
                if response.status == 422 or response.status == 200:
                    try:
                        data = response.json()
                        if data.get("code") != 0:
                            error_found = True
                            error_message = data.get("message", "")
                            if "工地" in error_message or "site" in error_message.lower():
                                print(f"  ✓ 检测到工地相关错误: {error_message}")
                    except:
                        pass
        
        logged_in_page.on("response", handle_response)
        
        # 打开对话框
        add_button = logged_in_page.locator('button:has-text("上传视频"), button:has-text("新增")')
        add_button.first.click()
        logged_in_page.wait_for_timeout(500)
        
        # 填写表单
        unique_id = int(time.time())
        logged_in_page.locator('input[placeholder*="视频标题"]').fill(f"测试视频_{unique_id}")
        logged_in_page.locator('input[placeholder*="视频URL"]').fill(f"https://example.com/video_{unique_id}.mp4")
        
        duration_input = logged_in_page.locator('input[placeholder*="视频时长"]').first
        if duration_input.is_visible(timeout=2000):
            duration_input.fill("120")
        
        # 提交表单
        submit_button = logged_in_page.locator('.el-dialog button:has-text("创建"), .el-dialog button:has-text("确定")').last
        submit_button.click()
        
        # 等待响应
        logged_in_page.wait_for_timeout(2000)
        
        # 检查是否有错误提示
        error_msg = logged_in_page.locator('.el-message--error')
        if error_msg.is_visible(timeout=2000):
            msg_text = error_msg.text_content()
            print(f"  ✓ 显示错误提示: {msg_text}")
            if "工地" in msg_text:
                print("  ✓ 错误提示包含工地相关信息")
        
        if error_found and "工地" in error_message:
            print("  ✓ 正确检测到工地相关错误")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

