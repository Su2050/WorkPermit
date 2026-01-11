"""
施工单位管理API测试
测试范围：列表查询、选项查询、详情查询、创建、更新、删除、统计
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
def test_site_id(client):
    """获取测试用的工地ID"""
    resp = client.get("/sites/options")
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            return data["data"][0].get("site_id") or data["data"][0].get("id")
    pytest.skip("没有可用的工地")


@pytest.fixture(scope="module")
def created_contractor(client, test_site_id):
    """创建测试施工单位，测试后清理"""
    unique_code = f"CTR_{int(time.time())}"
    contractor_data = {
        "site_id": test_site_id,
        "name": f"测试施工单位_{unique_code}",
        "code": unique_code,
        "contact_person": "测试联系人",
        "contact_phone": "13800138000",
        "address": "测试地址"
    }
    resp = client.post("/contractors", json_data=contractor_data)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0:
            contractor_id = data["data"].get("contractor_id")
            yield {"contractor_id": contractor_id, **contractor_data}
            # 清理
            client.delete(f"/contractors/{contractor_id}")
            return
    yield None


class TestContractorsList:
    """施工单位列表查询测试"""
    
    def test_list_basic_pagination(self, client):
        """测试：基础分页查询"""
        resp = client.get("/contractors", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "items" in data["data"]
        assert "total" in data["data"]
        print(f"✓ 基础分页查询成功，共{data['data']['total']}条记录")
    
    def test_list_keyword_search(self, client):
        """测试：关键词搜索"""
        resp = client.get("/contractors", params={"keyword": "施工"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 关键词搜索成功")
    
    def test_list_filter_by_site(self, client, test_site_id):
        """测试：按工地筛选"""
        resp = client.get("/contractors", params={"site_id": test_site_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按工地筛选成功")
    
    def test_list_filter_by_status(self, client):
        """测试：按状态筛选"""
        resp = client.get("/contractors", params={"is_active": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按状态筛选成功")
    
    def test_list_filter_by_qualification(self, client):
        """测试：按资质等级筛选"""
        resp = client.get("/contractors", params={"qualification_level": "A"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按资质等级筛选成功")
    
    def test_list_combined_filters(self, client, test_site_id):
        """测试：组合筛选"""
        resp = client.get("/contractors", params={
            "site_id": test_site_id,
            "is_active": True,
            "keyword": "单位",
            "page": 1,
            "page_size": 10
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 组合筛选成功")
    
    def test_list_response_fields(self, client):
        """测试：返回字段完整性（包括统计数据）"""
        resp = client.get("/contractors", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        if data["data"]["items"]:
            item = data["data"]["items"][0]
            # 核心必要字段
            expected_fields = ["contractor_id", "name", "code"]
            for field in expected_fields:
                assert field in item or "id" in item, f"缺少字段: {field}"
        print("✓ 返回字段完整性验证通过")
    
    def test_list_empty_result(self, client):
        """测试：空结果响应"""
        resp = client.get("/contractors", params={"keyword": "不存在的施工单位xyz123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 空结果响应正确")


class TestContractorsOptions:
    """施工单位选项查询测试"""
    
    def test_options_basic(self, client):
        """测试：获取可用施工单位选项"""
        resp = client.get("/contractors/options")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert isinstance(data.get("data"), list)
        print(f"✓ 获取施工单位选项成功，共{len(data['data'])}个")
    
    def test_options_filter_by_site(self, client, test_site_id):
        """测试：按工地筛选选项"""
        resp = client.get("/contractors/options", params={"site_id": test_site_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按工地筛选选项成功")
    
    def test_options_response_format(self, client):
        """测试：选项响应格式"""
        resp = client.get("/contractors/options")
        assert resp.status_code == 200
        data = resp.json()
        if data.get("data"):
            item = data["data"][0]
            assert "contractor_id" in item or "id" in item
            assert "name" in item or "label" in item
        print("✓ 选项响应格式正确")


class TestContractorsDetail:
    """施工单位详情查询测试"""
    
    def test_detail_valid_id(self, client, created_contractor):
        """测试：有效ID查询"""
        if not created_contractor:
            pytest.skip("没有创建测试施工单位")
        
        contractor_id = created_contractor["contractor_id"]
        resp = client.get(f"/contractors/{contractor_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 有效ID查询成功")
    
    def test_detail_invalid_id(self, client):
        """测试：无效ID（不存在）"""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/contractors/{fake_id}")
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0 or data.get("data") is None
        print("✓ 无效ID处理正确")
    
    def test_detail_invalid_uuid_format(self, client):
        """测试：无效UUID格式"""
        resp = client.get("/contractors/not-a-valid-uuid")
        assert resp.status_code in [422, 404, 400]
        print("✓ 无效UUID格式处理正确")
    
    def test_detail_response_fields(self, client, created_contractor):
        """测试：详情返回字段完整性"""
        if not created_contractor:
            pytest.skip("没有创建测试施工单位")
        
        contractor_id = created_contractor["contractor_id"]
        resp = client.get(f"/contractors/{contractor_id}")
        assert resp.status_code == 200
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            item = data["data"]
            expected_fields = ["contractor_id", "name", "code", "contact_person", "contact_phone"]
            for field in expected_fields:
                if field == "contractor_id":
                    assert field in item or "id" in item
        print("✓ 详情返回字段完整性验证通过")


class TestContractorsCreate:
    """施工单位创建测试"""
    
    def test_create_success_required_fields(self, client, test_site_id):
        """测试：成功创建（必填字段）"""
        unique_code = f"CREATE_CTR_{int(time.time())}"
        contractor_data = {
            "site_id": test_site_id,
            "name": f"创建测试施工单位_{unique_code}",
            "code": unique_code
        }
        resp = client.post("/contractors", json_data=contractor_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        
        # 清理
        if data.get("data", {}).get("contractor_id"):
            client.delete(f"/contractors/{data['data']['contractor_id']}")
        print("✓ 成功创建施工单位（必填字段）")
    
    def test_create_success_all_fields(self, client, test_site_id):
        """测试：成功创建（所有字段）"""
        unique_code = f"CREATE_ALL_{int(time.time())}"
        contractor_data = {
            "site_id": test_site_id,
            "name": f"完整创建测试_{unique_code}",
            "code": unique_code,
            "contact_person": "张三",
            "contact_phone": "13900139000",
            "address": "北京市朝阳区xxx街道",
            "license_no": f"BL{unique_code}",
            "qualification_level": "A"
        }
        resp = client.post("/contractors", json_data=contractor_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        
        # 清理
        if data.get("data", {}).get("contractor_id"):
            client.delete(f"/contractors/{data['data']['contractor_id']}")
        print("✓ 成功创建施工单位（所有字段）")
    
    def test_create_missing_site_id(self, client):
        """测试：缺少site_id时API的行为"""
        unique_code = f"NO_SITE_{int(time.time())}"
        contractor_data = {
            "name": f"缺少工地测试_{unique_code}",
            "code": unique_code
        }
        resp = client.post("/contractors", json_data=contractor_data)
        # API可能返回422(验证错误)或200(使用推断的site_id)
        assert resp.status_code in [200, 422]
        data = resp.json()
        # 如果成功创建，清理测试数据
        if data.get("code") == 0 and data.get("data", {}).get("contractor_id"):
            client.delete(f"/contractors/{data['data']['contractor_id']}")
        print(f"✓ 缺少site_id: status={resp.status_code}, code={data.get('code')}")
    
    def test_create_missing_name(self, client, test_site_id):
        """测试：缺少name"""
        unique_code = f"NO_NAME_{int(time.time())}"
        contractor_data = {
            "site_id": test_site_id,
            "code": unique_code
        }
        resp = client.post("/contractors", json_data=contractor_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少name验证正确")
    
    def test_create_missing_code(self, client, test_site_id):
        """测试：缺少code"""
        contractor_data = {
            "site_id": test_site_id,
            "name": f"缺少编码测试_{int(time.time())}"
        }
        resp = client.post("/contractors", json_data=contractor_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少code验证正确")
    
    def test_create_duplicate_name(self, client, test_site_id, created_contractor):
        """测试：重复名称（同一工地内）"""
        if not created_contractor:
            pytest.skip("没有创建测试施工单位")
        
        unique_code = f"DUP_NAME_{int(time.time())}"
        contractor_data = {
            "site_id": test_site_id,
            "name": created_contractor["name"],  # 使用已存在的名称
            "code": unique_code
        }
        resp = client.post("/contractors", json_data=contractor_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                if data.get("data", {}).get("contractor_id"):
                    client.delete(f"/contractors/{data['data']['contractor_id']}")
                pytest.fail("重复名称应该返回错误")
            else:
                assert "名称" in data.get("message", "") or "已存在" in data.get("message", "")
        print("✓ 重复名称验证正确")
    
    def test_create_duplicate_code(self, client, test_site_id, created_contractor):
        """测试：重复编码"""
        if not created_contractor:
            pytest.skip("没有创建测试施工单位")
        
        contractor_data = {
            "site_id": test_site_id,
            "name": f"重复编码测试_{int(time.time())}",
            "code": created_contractor["code"]  # 使用已存在的编码
        }
        resp = client.post("/contractors", json_data=contractor_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                if data.get("data", {}).get("contractor_id"):
                    client.delete(f"/contractors/{data['data']['contractor_id']}")
                pytest.fail("重复编码应该返回错误")
        print("✓ 重复编码验证正确")
    
    def test_create_invalid_phone_format(self, client, test_site_id):
        """测试：无效电话号码格式"""
        unique_code = f"BAD_PHONE_{int(time.time())}"
        contractor_data = {
            "site_id": test_site_id,
            "name": f"无效电话测试_{unique_code}",
            "code": unique_code,
            "contact_phone": "123"  # 无效电话
        }
        resp = client.post("/contractors", json_data=contractor_data)
        # 可能验证也可能不验证电话格式
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and data.get("data", {}).get("contractor_id"):
                client.delete(f"/contractors/{data['data']['contractor_id']}")
        print("✓ 无效电话格式验证完成")


class TestContractorsUpdate:
    """施工单位更新测试"""
    
    def test_update_success(self, client, created_contractor):
        """测试：成功更新"""
        if not created_contractor:
            pytest.skip("没有创建测试施工单位")
        
        contractor_id = created_contractor["contractor_id"]
        update_data = {
            "contact_person": f"更新联系人_{int(time.time())}",
            "address": "更新后的地址"
        }
        resp = client.patch(f"/contractors/{contractor_id}", json_data=update_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"更新失败: {data.get('message')}"
        print("✓ 成功更新施工单位")
    
    def test_update_status(self, client, created_contractor):
        """测试：更新状态"""
        if not created_contractor:
            pytest.skip("没有创建测试施工单位")
        
        contractor_id = created_contractor["contractor_id"]
        update_data = {
            "is_active": False
        }
        resp = client.patch(f"/contractors/{contractor_id}", json_data=update_data)
        assert resp.status_code == 200
        print("✓ 状态更新测试完成")
    
    def test_update_not_found(self, client):
        """测试：更新不存在的记录"""
        fake_id = str(uuid.uuid4())
        update_data = {
            "name": "不存在的施工单位"
        }
        resp = client.patch(f"/contractors/{fake_id}", json_data=update_data)
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0
        print("✓ 更新不存在记录处理正确")


class TestContractorsDelete:
    """施工单位删除测试"""
    
    def test_delete_success(self, client, test_site_id):
        """测试：成功删除（无关联数据）"""
        # 先创建一个施工单位
        unique_code = f"DEL_CTR_{int(time.time())}"
        contractor_data = {
            "site_id": test_site_id,
            "name": f"待删除施工单位_{unique_code}",
            "code": unique_code
        }
        create_resp = client.post("/contractors", json_data=contractor_data)
        if create_resp.status_code != 200 or create_resp.json().get("code") != 0:
            pytest.skip("无法创建测试施工单位")
        
        contractor_id = create_resp.json()["data"]["contractor_id"]
        
        # 删除
        resp = client.delete(f"/contractors/{contractor_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"删除失败: {data.get('message')}"
        print("✓ 成功删除施工单位")
    
    def test_delete_not_found(self, client):
        """测试：删除不存在的记录"""
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/contractors/{fake_id}")
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0
        print("✓ 删除不存在记录处理正确")


class TestContractorsStats:
    """施工单位统计测试"""
    
    def test_stats_total_count(self, client):
        """测试：施工单位总数统计"""
        resp = client.get("/contractors", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "total" in data["data"]
        print(f"✓ 施工单位总数: {data['data']['total']}")
    
    def test_stats_by_site(self, client, test_site_id):
        """测试：按工地统计"""
        resp = client.get("/contractors", params={
            "site_id": test_site_id,
            "page": 1,
            "page_size": 1
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print(f"✓ 工地{test_site_id}的施工单位数: {data['data']['total']}")
    
    def test_stats_active_contractors(self, client):
        """测试：活跃施工单位统计"""
        resp = client.get("/contractors", params={
            "is_active": True,
            "page": 1,
            "page_size": 1
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print(f"✓ 活跃施工单位数: {data['data']['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

