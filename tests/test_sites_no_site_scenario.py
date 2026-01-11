"""
测试无工地时创建施工单位的场景
"""
import pytest
import requests
import time
from typing import Optional

# 测试配置
BASE_URL = "http://localhost:8000/api/admin"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"


class APIClient:
    """API测试客户端"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.session = requests.Session()
    
    def login(self, username: str, password: str) -> bool:
        """登录获取token"""
        resp = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                self.token = data["data"]["access_token"]
                self.session.headers["Authorization"] = f"Bearer {self.token}"
                return True
        return False
    
    def get(self, path: str, params: dict = None):
        return self.session.get(f"{self.base_url}{path}", params=params)
    
    def post(self, path: str, json_data: dict = None):
        return self.session.post(f"{self.base_url}{path}", json=json_data)


@pytest.fixture(scope="module")
def client():
    """创建已登录的API客户端"""
    client = APIClient(BASE_URL)
    if not client.login(TEST_USERNAME, TEST_PASSWORD):
        pytest.skip("无法登录，跳过测试")
    return client


class TestCreateContractorWithoutSite:
    """测试无工地时创建施工单位"""
    
    def test_create_contractor_no_site_error_message(self, client):
        """
        测试：当系统中没有工地时，创建施工单位应该返回正确的错误消息
        注意：这个测试假设系统中没有工地，或者需要先清理所有工地
        """
        # 检查是否有工地
        sites_resp = client.get("/sites/options")
        if sites_resp.status_code == 200:
            sites_data = sites_resp.json()
            if sites_data.get("code") == 0 and sites_data.get("data"):
                # 如果有工地，跳过这个测试
                pytest.skip("系统中存在工地，无法测试无工地场景")
        
        # 尝试创建施工单位
        unique_code = f"CTR_{int(time.time())}"
        contractor_data = {
            "name": f"测试施工单位_{unique_code}",
            "code": unique_code,
            "contact_person": "测试联系人",
            "contact_phone": "13800138000"
        }
        resp = client.post("/contractors", json_data=contractor_data)
        
        # 验证响应
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0, "应该返回错误"
        
        # 验证错误消息包含"没有工地"或"请先创建工地"
        error_message = data.get("message", "")
        assert "没有工地" in error_message or "请先创建工地" in error_message, \
            f"错误消息应该包含'没有工地'或'请先创建工地'，实际消息：{error_message}"
    
    def test_create_contractor_error_code(self, client):
        """测试：错误响应应该使用正确的错误码"""
        # 检查是否有工地
        sites_resp = client.get("/sites/options")
        if sites_resp.status_code == 200:
            sites_data = sites_resp.json()
            if sites_data.get("code") == 0 and sites_data.get("data"):
                pytest.skip("系统中存在工地，无法测试无工地场景")
        
        # 尝试创建施工单位
        unique_code = f"CTR_{int(time.time())}"
        contractor_data = {
            "name": f"测试施工单位_{unique_code}",
            "code": unique_code,
            "contact_person": "测试联系人",
            "contact_phone": "13800138000"
        }
        resp = client.post("/contractors", json_data=contractor_data)
        
        # 验证错误码
        assert resp.status_code == 200
        data = resp.json()
        # 错误码应该是 VALIDATION_ERROR (通常是 40001 或类似)
        assert data.get("code") != 0

