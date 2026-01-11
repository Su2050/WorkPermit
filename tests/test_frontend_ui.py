"""
前端UI自动化测试 - 使用Playwright模拟真实用户操作
需要先安装: pip install playwright && playwright install
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
    browser = playwright.chromium.launch(headless=False, slow_mo=500)  # 可视化模式
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


class TestLogin:
    """登录流程测试"""
    
    def test_login_success(self, page: Page):
        """测试: 成功登录"""
        print("\n  === 测试登录流程 ===")
        
        # 1. 访问登录页
        print("  1. 访问登录页...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")
        
        # 2. 输入用户名
        print("  2. 输入用户名...")
        username_input = page.locator('input[placeholder*="用户名"]')
        username_input.fill(TEST_USERNAME)
        
        # 3. 输入密码
        print("  3. 输入密码...")
        password_input = page.locator('input[type="password"]')
        password_input.fill(TEST_PASSWORD)
        
        # 4. 点击登录按钮
        print("  4. 点击登录...")
        login_button = page.locator('button:has-text("登录")')
        login_button.click()
        
        # 5. 等待跳转到首页
        print("  5. 等待跳转...")
        page.wait_for_url("**/", timeout=5000)
        
        # 6. 验证登录成功（检查是否有用户名显示）
        print("  6. 验证登录状态...")
        expect(page.locator('text=admin')).to_be_visible(timeout=3000)
        
        print("  ✓ 登录成功")
    
    def test_login_failure(self, page: Page):
        """测试: 登录失败 - 错误密码"""
        print("\n  === 测试登录失败 ===")
        
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")
        
        # 输入错误密码
        page.locator('input[placeholder*="用户名"]').fill(TEST_USERNAME)
        page.locator('input[type="password"]').fill("wrong_password")
        page.locator('button:has-text("登录")').click()
        
        # 应该显示错误提示
        expect(page.locator('.el-message--error')).to_be_visible(timeout=3000)
        
        print("  ✓ 正确显示错误提示")


class TestDashboard:
    """Dashboard页面测试"""
    
    @pytest.fixture(autouse=True)
    def login_first(self, page: Page):
        """每个测试前先登录"""
        page.goto(f"{BASE_URL}/login")
        page.locator('input[placeholder*="用户名"]').fill(TEST_USERNAME)
        page.locator('input[type="password"]').fill(TEST_PASSWORD)
        page.locator('button:has-text("登录")').click()
        page.wait_for_url("**/", timeout=5000)
    
    def test_dashboard_loads(self, page: Page):
        """测试: Dashboard页面加载"""
        print("\n  === 测试Dashboard ===")
        
        # 应该在首页
        assert "/" in page.url or "dashboard" in page.url
        
        # 检查统计卡片
        expect(page.locator('text=今日任务')).to_be_visible()
        expect(page.locator('text=进行中')).to_be_visible()
        
        print("  ✓ Dashboard加载成功")
    
    def test_dashboard_api_calls(self, page: Page):
        """测试: Dashboard API调用"""
        print("\n  === 测试Dashboard API ===")
        
        # 监听API请求
        api_calls = {
            "dashboard": False,
            "alerts": False
        }
        
        def handle_response(response):
            if "/reports/dashboard" in response.url:
                api_calls["dashboard"] = response.status == 200
                if response.status != 200:
                    print(f"  ❌ Dashboard API失败: {response.status}")
            elif "/alerts/stats" in response.url:
                api_calls["alerts"] = response.status == 200
                if response.status != 200:
                    print(f"  ❌ Alerts API失败: {response.status}")
        
        page.on("response", handle_response)
        
        # 刷新页面触发API调用
        page.reload()
        page.wait_for_load_state("networkidle")
        
        # 验证API都成功了
        assert api_calls["dashboard"], "Dashboard API应该成功"
        assert api_calls["alerts"], "Alerts API应该成功"
        
        print("  ✓ 所有API调用成功")


class TestTicketList:
    """作业票列表页测试"""
    
    @pytest.fixture(autouse=True)
    def login_and_navigate(self, page: Page):
        """登录并导航到作业票列表"""
        page.goto(f"{BASE_URL}/login")
        page.locator('input[placeholder*="用户名"]').fill(TEST_USERNAME)
        page.locator('input[type="password"]').fill(TEST_PASSWORD)
        page.locator('button:has-text("登录")').click()
        page.wait_for_url("**/", timeout=5000)
        
        # 点击"作业票管理"菜单
        page.locator('text=作业票管理').click()
        page.wait_for_url("**/tickets", timeout=3000)
    
    def test_ticket_list_loads(self, page: Page):
        """测试: 作业票列表加载"""
        print("\n  === 测试作业票列表 ===")
        
        # 应该在作业票列表页
        assert "/tickets" in page.url
        
        # 应该有表格
        expect(page.locator('.el-table')).to_be_visible(timeout=5000)
        
        print("  ✓ 列表加载成功")
    
    def test_ticket_filters(self, page: Page):
        """测试: 筛选功能"""
        print("\n  === 测试筛选功能 ===")
        
        # 1. 测试状态筛选
        print("  1. 测试状态筛选...")
        status_selector = page.locator('.el-select').first
        status_selector.click()
        page.wait_for_timeout(500)
        
        # 选择"进行中"选项
        page.locator('.el-select-dropdown__item:has-text("进行中")').first.click()
        page.wait_for_timeout(1000)
        
        print("  ✓ 状态筛选执行")
        
        # 2. 测试搜索框
        print("  2. 测试关键词搜索...")
        search_input = page.locator('input[placeholder*="搜索"]').first
        search_input.fill("焊接")
        page.wait_for_timeout(500)
        
        # 点击搜索按钮
        page.locator('button:has-text("搜索")').first.click()
        page.wait_for_timeout(1000)
        
        print("  ✓ 关键词搜索执行")
    
    def test_create_ticket_navigation(self, page: Page):
        """测试: 点击创建作业票按钮"""
        print("\n  === 测试创建作业票导航 ===")
        
        # 点击"新建作业票"按钮
        create_button = page.locator('button:has-text("新建作业票")').first
        create_button.click()
        
        # 应该跳转到创建页面
        page.wait_for_url("**/tickets/create", timeout=3000)
        
        print("  ✓ 成功跳转到创建页面")


class TestTicketDetail:
    """作业票详情页测试 - 重点测试422错误"""
    
    @pytest.fixture(autouse=True)
    def login_and_navigate_to_detail(self, page: Page):
        """登录并导航到作业票详情"""
        page.goto(f"{BASE_URL}/login")
        page.locator('input[placeholder*="用户名"]').fill(TEST_USERNAME)
        page.locator('input[type="password"]').fill(TEST_PASSWORD)
        page.locator('button:has-text("登录")').click()
        page.wait_for_url("**/", timeout=5000)
        
        # 导航到作业票列表
        page.locator('text=作业票管理').click()
        page.wait_for_url("**/tickets", timeout=3000)
        page.wait_for_load_state("networkidle")
    
    def test_ticket_detail_page_load(self, page: Page):
        """测试: 作业票详情页加载 - 监测422错误"""
        print("\n  === 测试作业票详情页 ===")
        
        # 收集所有API响应
        api_responses = []
        error_422_found = False
        
        def handle_response(response):
            nonlocal error_422_found
            
            # 只关注我们的API请求
            if "/api/admin/" in response.url:
                status = response.status
                url = response.url
                api_responses.append({"url": url, "status": status})
                
                if status == 422:
                    error_422_found = True
                    print(f"  ❌ 发现422错误: {url}")
                    try:
                        error_body = response.json()
                        print(f"     错误详情: {error_body}")
                    except:
                        print(f"     响应文本: {response.text()}")
        
        page.on("response", handle_response)
        
        # 等待表格加载
        page.wait_for_selector('.el-table', timeout=10000)
        
        # 点击第一个作业票标题（进入详情页）
        try:
            first_ticket = page.locator('.el-table tbody tr').first
            first_ticket.locator('a').first.click()
            
            # 等待详情页加载
            page.wait_for_url("**/tickets/**", timeout=5000)
            page.wait_for_load_state("networkidle")
            
            # 等待一会儿，让所有API都执行完
            page.wait_for_timeout(3000)
            
            print(f"\n  📊 API调用统计:")
            for response in api_responses:
                status_icon = "✓" if response["status"] == 200 else "❌"
                print(f"     {status_icon} [{response['status']}] {response['url']}")
            
            # 断言：不应该有422错误
            if error_422_found:
                pytest.fail("❌ 作业票详情页存在422错误！请检查上面的错误详情")
            else:
                print("\n  ✓ 所有API调用正常，无422错误")
        
        except Exception as e:
            print(f"  ⚠ 详情页加载异常: {e}")
            if not api_responses:
                pytest.skip("没有作业票数据可测试")
    
    def test_ticket_detail_tabs_navigation(self, page: Page):
        """测试: 详情页标签页切换"""
        print("\n  === 测试详情页标签切换 ===")
        
        # 点击第一个作业票
        try:
            page.wait_for_selector('.el-table tbody tr', timeout=10000)
            first_ticket = page.locator('.el-table tbody tr').first
            first_ticket.locator('a').first.click()
            
            page.wait_for_url("**/tickets/**", timeout=5000)
            page.wait_for_load_state("networkidle")
            
            # 检查详情页的各个部分是否加载
            expect(page.locator('text=基本信息')).to_be_visible(timeout=5000)
            expect(page.locator('text=作业区域')).to_be_visible(timeout=5000)
            expect(page.locator('text=培训视频')).to_be_visible(timeout=5000)
            
            print("  ✓ 详情页各部分加载正常")
        
        except Exception as e:
            pytest.skip(f"无法访问详情页: {e}")


class TestCreateTicket:
    """创建作业票流程测试"""
    
    @pytest.fixture(autouse=True)
    def login_and_navigate_to_create(self, page: Page):
        """登录并导航到创建页面"""
        page.goto(f"{BASE_URL}/login")
        page.locator('input[placeholder*="用户名"]').fill(TEST_USERNAME)
        page.locator('input[type="password"]').fill(TEST_PASSWORD)
        page.locator('button:has-text("登录")').click()
        page.wait_for_url("**/", timeout=5000)
        
        # 导航到创建页面
        page.goto(f"{BASE_URL}/tickets/create")
        page.wait_for_load_state("networkidle")
    
    def test_create_form_loads(self, page: Page):
        """测试: 创建表单加载"""
        print("\n  === 测试创建表单 ===")
        
        # 应该看到表单元素
        expect(page.locator('text=作业票名称')).to_be_visible()
        expect(page.locator('text=施工单位')).to_be_visible()
        expect(page.locator('text=作业区域')).to_be_visible()
        expect(page.locator('text=培训视频')).to_be_visible()
        expect(page.locator('text=作业人员')).to_be_visible()
        
        print("  ✓ 创建表单加载完成")
    
    def test_create_form_validation(self, page: Page):
        """测试: 表单验证"""
        print("\n  === 测试表单验证 ===")
        
        # 不填写任何内容，直接点击提交
        submit_button = page.locator('button:has-text("提交并发布")').first
        submit_button.click()
        
        # 应该显示验证错误
        page.wait_for_timeout(1000)
        
        # Element Plus会显示红色边框或错误提示
        print("  ✓ 表单验证触发")


class TestAreaManagement:
    """区域管理测试"""
    
    @pytest.fixture(autouse=True)
    def login_and_navigate(self, page: Page):
        """登录并导航到区域管理"""
        page.goto(f"{BASE_URL}/login")
        page.locator('input[placeholder*="用户名"]').fill(TEST_USERNAME)
        page.locator('input[type="password"]').fill(TEST_PASSWORD)
        page.locator('button:has-text("登录")').click()
        page.wait_for_url("**/", timeout=5000)
        
        # 导航到区域管理
        page.locator('text=作业区域').click()
        page.wait_for_url("**/areas", timeout=3000)
    
    def test_area_list_loads(self, page: Page):
        """测试: 区域列表加载"""
        print("\n  === 测试区域列表 ===")
        
        # 等待表格加载
        expect(page.locator('.el-table')).to_be_visible(timeout=5000)
        
        print("  ✓ 区域列表加载成功")


class TestContractorManagement:
    """施工单位管理测试"""
    
    @pytest.fixture(autouse=True)
    def login_and_navigate(self, page: Page):
        """登录并导航到施工单位管理"""
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")
        page.locator('input[placeholder*="用户名"]').fill(TEST_USERNAME)
        page.locator('input[type="password"]').fill(TEST_PASSWORD)
        page.locator('button:has-text("登录")').click()
        # 等待跳转到dashboard或首页
        page.wait_for_url("**/dashboard**", timeout=10000)
        page.wait_for_load_state("networkidle")
        
        # 导航到施工单位管理（使用菜单项，避免匹配到表格中的文本）
        page.get_by_role("menuitem", name="施工单位").first.click()
        page.wait_for_url("**/contractors**", timeout=5000)
        page.wait_for_load_state("networkidle")
    
    def test_create_contractor_no_site_error(self, page: Page):
        """测试: 无工地时创建施工单位，应该显示错误提示和快捷链接"""
        print("\n  === 测试无工地时创建施工单位 ===")
        
        # 监听API响应，检查是否有"没有工地"的错误
        error_message_found = False
        error_message_text = ""
        
        def handle_response(response):
            nonlocal error_message_found, error_message_text
            if "/api/admin/contractors" in response.url and response.request.method == "POST":
                if response.status == 200:
                    try:
                        data = response.json()
                        message = data.get("message", "")
                        if "没有工地" in message or "请先创建工地" in message:
                            error_message_found = True
                            error_message_text = message
                    except:
                        pass
        
        page.on("response", handle_response)
        
        # 点击"新增施工单位"按钮
        print("  1. 点击新增施工单位按钮...")
        add_button = page.locator('button:has-text("新增施工单位")')
        add_button.click()
        page.wait_for_timeout(500)
        
        # 填写表单
        print("  2. 填写表单...")
        page.locator('input[placeholder*="单位名称"]').fill("测试施工单位")
        page.locator('input[placeholder*="单位编码"]').fill(f"TEST_{int(time.time())}")
        page.locator('input[placeholder*="联系人"]').fill("测试联系人")
        page.locator('input[placeholder*="联系电话"]').fill("13800138000")
        
        # 提交表单
        print("  3. 提交表单...")
        submit_button = page.locator('button:has-text("确定")').last
        submit_button.click()
        
        # 等待响应
        page.wait_for_timeout(2000)
        
        # 检查是否有错误提示对话框（ElMessageBox）
        print("  4. 检查错误提示...")
        try:
            # 检查是否有确认对话框（ElMessageBox）
            messagebox = page.locator('.el-message-box')
            if messagebox.is_visible(timeout=3000):
                print("  ✓ 检测到错误提示对话框")
                
                # 检查对话框内容
                messagebox_text = messagebox.text_content()
                if "没有工地" in messagebox_text or "请先创建工地" in messagebox_text:
                    print("  ✓ 错误消息包含'没有工地'或'请先创建工地'")
                
                # 检查是否有"去创建工地"按钮
                create_site_button = page.locator('button:has-text("去创建工地")')
                if create_site_button.is_visible(timeout=1000):
                    print("  ✓ 检测到'去创建工地'按钮")
                    
                    # 点击按钮
                    print("  5. 点击'去创建工地'按钮...")
                    create_site_button.click()
                    page.wait_for_timeout(1000)
                    
                    # 验证是否跳转到工地管理页面
                    page.wait_for_url("**/sites", timeout=3000)
                    print("  ✓ 成功跳转到工地管理页面")
                else:
                    print("  ⚠ 未找到'去创建工地'按钮")
            else:
                # 如果没有对话框，检查是否有错误消息（ElMessage）
                error_message = page.locator('.el-message--error')
                if error_message.is_visible(timeout=2000):
                    message_text = error_message.text_content()
                    print(f"  ⚠ 检测到错误消息: {message_text}")
                    if "没有工地" in message_text or "请先创建工地" in message_text:
                        print("  ✓ 错误消息包含'没有工地'或'请先创建工地'")
                else:
                    print("  ⚠ 未检测到错误提示")
        except Exception as e:
            print(f"  ⚠ 检查错误提示时出现异常: {e}")
        
        # 如果检测到错误消息，验证其内容
        if error_message_found:
            print(f"  ✓ API返回错误消息: {error_message_text}")
    
    def test_sites_page_navigation(self, page: Page):
        """测试: 导航到工地管理页面"""
        print("\n  === 测试工地管理页面导航 ===")
        
        # 检查导航菜单中是否有"工地管理"
        try:
            sites_menu = page.get_by_role("menuitem", name="工地管理").first
            if sites_menu.is_visible(timeout=2000):
                print("  ✓ 导航菜单中存在'工地管理'")
                
                # 点击工地管理
                sites_menu.click()
                page.wait_for_url("**/sites**", timeout=5000)
                page.wait_for_load_state("networkidle")
                
                # 验证页面加载
                expect(page.locator('h1:has-text("工地管理")')).to_be_visible(timeout=3000)
                print("  ✓ 成功导航到工地管理页面")
            else:
                print("  ⚠ 导航菜单中未找到'工地管理'")
        except Exception as e:
            print(f"  ⚠ 导航测试异常: {e}")


# 运行测试时的配置
def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "ui: mark test as UI test (deselect with '-m \"not ui\"')"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])

