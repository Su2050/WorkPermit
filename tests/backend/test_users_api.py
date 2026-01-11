"""
用户管理API测试
测试范围：列表查询、详情查询、创建、更新、删除、密码修改、统计
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
    
    def put(self, path: str, json_data: dict = None):
        return self.session.put(f"{self.base_url}{path}", json=json_data)
    
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
def test_contractor_id(client):
    """获取测试用的施工单位ID"""
    resp = client.get("/contractors/options")
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            return data["data"][0].get("contractor_id") or data["data"][0].get("id")
    pytest.skip("没有可用的施工单位")


@pytest.fixture(scope="module")
def created_user(client, test_contractor_id):
    """创建测试用户，测试后清理"""
    unique_id = int(time.time())
    user_data = {
        "username": f"test_user_{unique_id}",
        "password": "Test123456!",
        "name": f"测试用户_{unique_id}",
        "role": "ContractorAdmin",
        "contractor_id": test_contractor_id,
        "email": f"test_{unique_id}@example.com",
        "phone": f"188{unique_id % 100000000:08d}"
    }
    resp = client.post("/users", json_data=user_data)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0:
            user_id = data["data"].get("user_id")
            yield {"user_id": user_id, **user_data}
            # 清理
            client.delete(f"/users/{user_id}")
            return
    yield None


class TestUsersList:
    """用户列表查询测试"""
    
    def test_list_basic_pagination(self, client):
        """测试：基础分页查询"""
        resp = client.get("/users", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "items" in data["data"]
        assert "total" in data["data"]
        print(f"✓ 基础分页查询成功，共{data['data']['total']}条记录")
    
    def test_list_keyword_search_username(self, client):
        """测试：按用户名关键词搜索"""
        resp = client.get("/users", params={"keyword": "admin"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按用户名关键词搜索成功")
    
    def test_list_keyword_search_name(self, client):
        """测试：按姓名关键词搜索"""
        resp = client.get("/users", params={"keyword": "管理"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按姓名关键词搜索成功")
    
    def test_list_filter_by_role_sysadmin(self, client):
        """测试：按角色筛选-SysAdmin"""
        resp = client.get("/users", params={"role": "SysAdmin"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按角色筛选(SysAdmin)成功")
    
    def test_list_filter_by_role_contractor_admin(self, client):
        """测试：按角色筛选-ContractorAdmin"""
        resp = client.get("/users", params={"role": "ContractorAdmin"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按角色筛选(ContractorAdmin)成功")
    
    def test_list_filter_by_status(self, client):
        """测试：按状态筛选"""
        resp = client.get("/users", params={"is_active": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按状态筛选成功")
    
    def test_list_filter_by_contractor(self, client, test_contractor_id):
        """测试：按施工单位筛选"""
        resp = client.get("/users", params={"contractor_id": test_contractor_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按施工单位筛选成功")
    
    def test_list_response_no_password(self, client):
        """测试：返回字段不包含密码"""
        resp = client.get("/users", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        if data["data"]["items"]:
            item = data["data"]["items"][0]
            assert "password" not in item, "不应该返回密码字段"
            assert "password_hash" not in item, "不应该返回密码哈希字段"
        print("✓ 返回字段不包含密码验证通过")
    
    def test_list_empty_result(self, client):
        """测试：空结果响应"""
        resp = client.get("/users", params={"keyword": "不存在的用户xyz123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 空结果响应正确")


class TestUsersDetail:
    """用户详情查询测试"""
    
    def test_detail_valid_id(self, client, created_user):
        """测试：有效ID查询"""
        if not created_user:
            pytest.skip("没有创建测试用户")
        
        user_id = created_user["user_id"]
        resp = client.get(f"/users/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 有效ID查询成功")
    
    def test_detail_no_password_returned(self, client, created_user):
        """测试：详情不返回密码"""
        if not created_user:
            pytest.skip("没有创建测试用户")
        
        user_id = created_user["user_id"]
        resp = client.get(f"/users/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            assert "password" not in data["data"]
            assert "password_hash" not in data["data"]
        print("✓ 详情不返回密码验证通过")
    
    def test_detail_invalid_id(self, client):
        """测试：无效ID（不存在）"""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/users/{fake_id}")
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0 or data.get("data") is None
        print("✓ 无效ID处理正确")
    
    def test_detail_invalid_uuid_format(self, client):
        """测试：无效UUID格式"""
        resp = client.get("/users/not-a-valid-uuid")
        assert resp.status_code in [422, 404, 400]
        print("✓ 无效UUID格式处理正确")
    
    def test_get_current_user(self, client):
        """测试：获取当前用户信息"""
        resp = client.get("/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "username" in data["data"] or "user" in str(data["data"]).lower()
        print("✓ 获取当前用户信息成功")


class TestUsersCreate:
    """用户创建测试"""
    
    def test_create_sysadmin_success(self, client):
        """测试：成功创建SysAdmin"""
        unique_id = int(time.time())
        user_data = {
            "username": f"sysadmin_{unique_id}",
            "password": "Admin123456!",
            "name": f"系统管理员_{unique_id}",
            "role": "SysAdmin"
        }
        resp = client.post("/users", json_data=user_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        
        # 清理
        if data.get("data", {}).get("user_id"):
            client.delete(f"/users/{data['data']['user_id']}")
        print("✓ 成功创建SysAdmin")
    
    def test_create_contractor_admin_success(self, client, test_contractor_id):
        """测试：成功创建ContractorAdmin"""
        unique_id = int(time.time())
        user_data = {
            "username": f"contractor_admin_{unique_id}",
            "password": "Contractor123!",
            "name": f"施工单位管理员_{unique_id}",
            "role": "ContractorAdmin",
            "contractor_id": test_contractor_id
        }
        resp = client.post("/users", json_data=user_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        
        # 清理
        if data.get("data", {}).get("user_id"):
            client.delete(f"/users/{data['data']['user_id']}")
        print("✓ 成功创建ContractorAdmin")
    
    def test_create_missing_username(self, client):
        """测试：缺少username"""
        user_data = {
            "password": "Test123456!",
            "name": "缺少用户名测试",
            "role": "SysAdmin"
        }
        resp = client.post("/users", json_data=user_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少username验证正确")
    
    def test_create_missing_password(self, client):
        """测试：缺少password"""
        unique_id = int(time.time())
        user_data = {
            "username": f"no_pwd_{unique_id}",
            "name": "缺少密码测试",
            "role": "SysAdmin"
        }
        resp = client.post("/users", json_data=user_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少password验证正确")
    
    def test_create_missing_name(self, client):
        """测试：缺少name"""
        unique_id = int(time.time())
        user_data = {
            "username": f"no_name_{unique_id}",
            "password": "Test123456!",
            "role": "SysAdmin"
        }
        resp = client.post("/users", json_data=user_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少name验证正确")
    
    def test_create_missing_role(self, client):
        """测试：缺少role"""
        unique_id = int(time.time())
        user_data = {
            "username": f"no_role_{unique_id}",
            "password": "Test123456!",
            "name": "缺少角色测试"
        }
        resp = client.post("/users", json_data=user_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少role验证正确")
    
    def test_create_contractor_admin_missing_contractor(self, client):
        """测试：ContractorAdmin缺少contractor_id"""
        unique_id = int(time.time())
        unique_username = f"no_ctr_{unique_id}_{uuid.uuid4().hex[:4]}"
        user_data = {
            "username": unique_username,
            "password": "Test123456!",
            "name": "缺少施工单位测试",
            "role": "ContractorAdmin"
            # 缺少 contractor_id
        }
        resp = client.post("/users", json_data=user_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                if data.get("data", {}).get("user_id"):
                    client.delete(f"/users/{data['data']['user_id']}")
                pytest.fail("ContractorAdmin缺少contractor_id应该返回错误")
            else:
                # 验证错误信息包含施工单位相关内容
                assert "施工单位" in data.get("message", "") or "contractor" in data.get("message", "").lower()
        print("✓ ContractorAdmin缺少contractor_id验证正确")
    
    def test_create_duplicate_username(self, client, created_user):
        """测试：重复用户名"""
        if not created_user:
            pytest.skip("没有创建测试用户")
        
        user_data = {
            "username": created_user["username"],  # 使用已存在的用户名
            "password": "Duplicate123!",
            "name": "重复用户名测试",
            "role": "SysAdmin"
        }
        resp = client.post("/users", json_data=user_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                if data.get("data", {}).get("user_id"):
                    client.delete(f"/users/{data['data']['user_id']}")
                pytest.fail("重复用户名应该返回错误")
        print("✓ 重复用户名验证正确")
    
    def test_create_invalid_email_format(self, client):
        """测试：无效邮箱格式"""
        unique_id = int(time.time())
        user_data = {
            "username": f"bad_email_{unique_id}",
            "password": "Test123456!",
            "name": "无效邮箱测试",
            "role": "SysAdmin",
            "email": "not-a-valid-email"
        }
        resp = client.post("/users", json_data=user_data)
        # 可能验证也可能不验证邮箱格式
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and data.get("data", {}).get("user_id"):
                client.delete(f"/users/{data['data']['user_id']}")
        print("✓ 无效邮箱格式验证完成")
    
    def test_create_weak_password(self, client):
        """测试：弱密码"""
        unique_id = int(time.time())
        user_data = {
            "username": f"weak_pwd_{unique_id}",
            "password": "123",  # 弱密码
            "name": "弱密码测试",
            "role": "SysAdmin"
        }
        resp = client.post("/users", json_data=user_data)
        # 可能验证也可能不验证密码强度
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and data.get("data", {}).get("user_id"):
                client.delete(f"/users/{data['data']['user_id']}")
        print("✓ 弱密码验证完成")


class TestUsersUpdate:
    """用户更新测试"""
    
    def test_update_basic_info(self, client, created_user):
        """测试：更新基本信息"""
        if not created_user:
            pytest.skip("没有创建测试用户")
        
        user_id = created_user["user_id"]
        update_data = {
            "name": f"更新后的姓名_{int(time.time())}",
            "phone": "18800188001"
        }
        resp = client.patch(f"/users/{user_id}", json_data=update_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"更新失败: {data.get('message')}"
        print("✓ 成功更新用户基本信息")
    
    def test_update_status(self, client, created_user):
        """测试：更新状态"""
        if not created_user:
            pytest.skip("没有创建测试用户")
        
        user_id = created_user["user_id"]
        update_data = {
            "is_active": False
        }
        resp = client.patch(f"/users/{user_id}", json_data=update_data)
        assert resp.status_code == 200
        
        # 恢复状态
        update_data["is_active"] = True
        client.patch(f"/users/{user_id}", json_data=update_data)
        print("✓ 状态更新测试完成")
    
    def test_update_not_found(self, client):
        """测试：更新不存在的记录"""
        fake_id = str(uuid.uuid4())
        update_data = {
            "name": "不存在的用户"
        }
        resp = client.patch(f"/users/{fake_id}", json_data=update_data)
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0
        print("✓ 更新不存在记录处理正确")


class TestUsersDelete:
    """用户删除测试"""
    
    def test_delete_success(self, client, test_contractor_id):
        """测试：成功删除"""
        # 先创建一个用户
        unique_id = int(time.time())
        user_data = {
            "username": f"del_user_{unique_id}",
            "password": "Delete123!",
            "name": f"待删除用户_{unique_id}",
            "role": "ContractorAdmin",
            "contractor_id": test_contractor_id
        }
        create_resp = client.post("/users", json_data=user_data)
        if create_resp.status_code != 200 or create_resp.json().get("code") != 0:
            pytest.skip("无法创建测试用户")
        
        user_id = create_resp.json()["data"]["user_id"]
        
        # 删除
        resp = client.delete(f"/users/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"删除失败: {data.get('message')}"
        print("✓ 成功删除用户")
    
    def test_delete_not_found(self, client):
        """测试：删除不存在的记录"""
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/users/{fake_id}")
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0
        print("✓ 删除不存在记录处理正确")
    
    def test_delete_self_forbidden(self, client):
        """测试：不允许删除自己"""
        # 获取当前用户ID
        me_resp = client.get("/auth/me")
        if me_resp.status_code != 200:
            pytest.skip("无法获取当前用户信息")
        
        me_data = me_resp.json()
        if me_data.get("code") != 0:
            pytest.skip("无法获取当前用户信息")
        
        current_user_id = me_data["data"].get("user_id") or me_data["data"].get("id")
        if not current_user_id:
            pytest.skip("无法获取当前用户ID")
        
        # 尝试删除自己
        resp = client.delete(f"/users/{current_user_id}")
        if resp.status_code == 200:
            data = resp.json()
            # 应该返回错误
            assert data.get("code") != 0, "不应该允许删除自己"
        print("✓ 不允许删除自己验证正确")


class TestUsersStats:
    """用户统计测试"""
    
    def test_stats_total_count(self, client):
        """测试：用户总数统计"""
        resp = client.get("/users", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "total" in data["data"]
        print(f"✓ 用户总数: {data['data']['total']}")
    
    def test_stats_by_role(self, client):
        """测试：按角色统计"""
        roles = ["SysAdmin", "ContractorAdmin"]
        for role in roles:
            resp = client.get("/users", params={
                "role": role,
                "page": 1,
                "page_size": 1
            })
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    print(f"✓ 角色'{role}'的用户数: {data['data']['total']}")
    
    def test_stats_active_users(self, client):
        """测试：活跃用户统计"""
        resp = client.get("/users", params={
            "is_active": True,
            "page": 1,
            "page_size": 1
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print(f"✓ 活跃用户数: {data['data']['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

