"""
人员创建 - site_id 字段测试
专门测试修复后的 site_id 必填字段验证
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
    
    def post(self, path: str, json_data: dict = None):
        return self.session.post(f"{self.base_url}{path}", json=json_data)


@pytest.fixture(scope="module")
def client():
    """创建已登录的API客户端"""
    client = APIClient(BASE_URL)
    if not client.login(TEST_USERNAME, TEST_PASSWORD):
        pytest.skip("无法登录，跳过测试")
    return client


@pytest.fixture(scope="module")
def test_site_id(client):
    """获取测试用的工地ID"""
    resp = client.session.get(f"{BASE_URL}/sites/options")
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            return data["data"][0].get("site_id") or data["data"][0].get("id")
    pytest.skip("没有可用的工地")


@pytest.fixture(scope="module")
def test_contractor_id(client, test_site_id):
    """获取测试用的施工单位ID"""
    resp = client.session.get(f"{BASE_URL}/contractors/options")
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            return data["data"][0].get("contractor_id") or data["data"][0].get("id")
    pytest.skip("没有可用的施工单位")


class TestWorkerCreateSiteId:
    """测试人员创建时的site_id字段"""
    
    def test_create_worker_without_site_id_should_fail(self, client, test_contractor_id):
        """测试：创建人员时不提供site_id应该返回422错误"""
        unique_id = int(time.time())
        worker_data = {
            # 缺少 site_id
            "contractor_id": test_contractor_id,
            "name": f"测试人员_{unique_id}",
            "phone": f"138{unique_id % 100000000:08d}",
            "id_no": f"41082119990909{unique_id % 10000:04d}"
        }
        resp = client.post("/workers", json_data=worker_data)
        
        # 应该返回422错误（验证失败）
        assert resp.status_code == 422, f"期望422错误，实际状态码: {resp.status_code}"
        print(f"✓ 缺少site_id时正确返回422错误")
    
    def test_create_worker_with_site_id_should_success(self, client, test_site_id, test_contractor_id):
        """测试：创建人员时提供site_id应该成功"""
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,  # 提供site_id
            "contractor_id": test_contractor_id,
            "name": f"测试人员_{unique_id}",
            "phone": f"139{unique_id % 100000000:08d}",
            "id_no": f"41082119990909{unique_id % 10000:04d}"
        }
        resp = client.post("/workers", json_data=worker_data)
        
        assert resp.status_code == 200, f"创建失败，状态码: {resp.status_code}"
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        assert "worker_id" in data.get("data", {}), "响应中缺少worker_id"
        
        # 清理
        worker_id = data["data"]["worker_id"]
        client.session.delete(f"{BASE_URL}/workers/{worker_id}")
        print(f"✓ 提供site_id时成功创建人员")
    
    def test_create_worker_with_invalid_site_id_should_fail(self, client, test_contractor_id):
        """测试：创建人员时提供无效的site_id应该失败"""
        unique_id = int(time.time())
        worker_data = {
            "site_id": "00000000-0000-0000-0000-000000000000",  # 无效的UUID
            "contractor_id": test_contractor_id,
            "name": f"测试人员_{unique_id}",
            "phone": f"137{unique_id % 100000000:08d}",
            "id_no": f"41082119990909{unique_id % 10000:04d}"
        }
        resp = client.post("/workers", json_data=worker_data)
        
        # 应该返回错误（404、403或500都是合理的错误）
        assert resp.status_code in [200, 404, 403, 500], f"期望错误，实际状态码: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0, "应该返回错误"
        print(f"✓ 无效site_id时正确返回错误（状态码: {resp.status_code}）")

