"""
工地管理API测试
测试范围：列表查询、选项查询、详情查询、创建、更新
"""
import pytest
import requests
import uuid
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
    
    def patch(self, path: str, json_data: dict = None):
        return self.session.patch(f"{self.base_url}{path}", json=json_data)
    
    def delete(self, path: str):
        return self.session.delete(f"{self.base_url}{path}")


@pytest.fixture(scope="module")
def client():
    """创建已登录的API客户端"""
    client = APIClient(BASE_URL)
    if not client.login(TEST_USERNAME, TEST_PASSWORD):
        pytest.skip("无法登录，跳过测试")
    return client


@pytest.fixture(scope="module")
def created_site(client):
    """创建测试工地，测试后清理"""
    # 使用更唯一的时间戳和随机数组合
    import random
    unique_suffix = f"{int(time.time())}_{random.randint(1000, 9999)}"
    unique_code = f"SITE_{unique_suffix}"
    site_data = {
        "name": f"测试工地_{unique_suffix}",
        "code": unique_code,
        "address": "测试地址",
        "description": "测试描述",
        "default_access_start_time": "06:00:00",
        "default_access_end_time": "20:00:00",
        "default_training_deadline": "07:30:00"
    }
    resp = client.post("/sites", json_data=site_data)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0 and "data" in data and "site_id" in data["data"]:
            site_id = data["data"].get("site_id")
            result = {"site_id": site_id, **site_data}
            yield result
            # 清理（如果需要的话，可以在这里删除）
            return
    # 如果创建失败，打印调试信息
    print(f"\n警告: created_site fixture 创建失败")
    print(f"响应状态码: {resp.status_code}")
    try:
        error_data = resp.json()
        print(f"响应内容: {error_data}")
        # 如果是名称或编码重复，尝试使用更唯一的标识
        if error_data.get("code") == 10001 and ("已存在" in error_data.get("message", "")):
            print(f"提示: 工地名称或编码已存在，尝试使用更唯一的标识...")
    except:
        print(f"响应文本: {resp.text[:200] if hasattr(resp, 'text') else 'N/A'}")
    yield None


class TestSitesList:
    """工地列表查询测试"""
    
    def test_list_sites_success(self, client):
        """测试获取工地列表成功"""
        resp = client.get("/sites", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
    
    def test_list_sites_with_keyword(self, client):
        """测试关键词搜索"""
        resp = client.get("/sites", params={"keyword": "测试", "page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
    
    def test_list_sites_with_filter(self, client):
        """测试状态过滤"""
        resp = client.get("/sites", params={"is_active": True, "page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0


class TestSitesOptions:
    """工地选项查询测试"""
    
    def test_get_site_options_success(self, client):
        """测试获取工地选项成功"""
        resp = client.get("/sites/options")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        assert isinstance(data["data"], list)


class TestSitesCreate:
    """工地创建测试"""
    
    def test_create_site_success(self, client):
        """测试创建工地成功"""
        unique_code = f"SITE_{int(time.time())}"
        site_data = {
            "name": f"测试工地_{unique_code}",
            "code": unique_code,
            "address": "测试地址",
            "description": "测试描述",
            "default_access_start_time": "06:00:00",
            "default_access_end_time": "20:00:00",
            "default_training_deadline": "07:30:00"
        }
        resp = client.post("/sites", json_data=site_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "site_id" in data["data"]
    
    def test_create_site_duplicate_name(self, client, created_site):
        """测试创建工地名称重复"""
        if not created_site:
            pytest.skip("没有可用的测试工地")
        site_data = {
            "name": created_site["name"],
            "code": f"SITE_{int(time.time())}",
            "default_access_start_time": "06:00:00",
            "default_access_end_time": "20:00:00",
            "default_training_deadline": "07:30:00"
        }
        resp = client.post("/sites", json_data=site_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0
        assert "已存在" in data.get("message", "")
    
    def test_create_site_duplicate_code(self, client, created_site):
        """测试创建工地编码重复"""
        if not created_site:
            pytest.skip("没有可用的测试工地")
        site_data = {
            "name": f"新工地_{int(time.time())}",
            "code": created_site["code"],
            "default_access_start_time": "06:00:00",
            "default_access_end_time": "20:00:00",
            "default_training_deadline": "07:30:00"
        }
        resp = client.post("/sites", json_data=site_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0
        assert "已存在" in data.get("message", "")
    
    def test_create_site_missing_required_fields(self, client):
        """测试创建工地缺少必填字段"""
        site_data = {
            "name": "测试工地",
            # 缺少 code
        }
        resp = client.post("/sites", json_data=site_data)
        assert resp.status_code == 422  # Validation error


class TestSitesDetail:
    """工地详情查询测试"""
    
    def test_get_site_detail_success(self, client, created_site):
        """测试获取工地详情成功"""
        if not created_site:
            pytest.skip("没有可用的测试工地")
        resp = client.get(f"/sites/{created_site['site_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert data["data"]["name"] == created_site["name"]
        assert data["data"]["code"] == created_site["code"]
    
    def test_get_site_detail_not_found(self, client):
        """测试获取不存在的工地详情"""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/sites/{fake_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0
        assert "不存在" in data.get("message", "")


class TestSitesUpdate:
    """工地更新测试"""
    
    def test_update_site_success(self, client, created_site):
        """测试更新工地成功"""
        if not created_site:
            pytest.skip("没有可用的测试工地")
        update_data = {
            "name": f"更新后的工地_{int(time.time())}",
            "address": "更新后的地址"
        }
        resp = client.patch(f"/sites/{created_site['site_id']}", json_data=update_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
    
    def test_update_site_not_found(self, client):
        """测试更新不存在的工地"""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "新名称"}
        resp = client.patch(f"/sites/{fake_id}", json_data=update_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0
        assert "不存在" in data.get("message", "")

