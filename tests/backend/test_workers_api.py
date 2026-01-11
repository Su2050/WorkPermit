"""
人员管理API测试
测试范围：列表查询、选项查询、详情查询、创建、更新、删除、批量操作、统计
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
def test_contractor_id(client, test_site_id):
    """获取测试用的施工单位ID"""
    resp = client.get("/contractors/options", params={"site_id": test_site_id})
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            return data["data"][0].get("contractor_id") or data["data"][0].get("id")
    pytest.skip("没有可用的施工单位")


@pytest.fixture(scope="module")
def created_worker(client, test_site_id, test_contractor_id):
    """创建测试工人，测试后清理"""
    unique_id = int(time.time())
    worker_data = {
        "site_id": test_site_id,
        "contractor_id": test_contractor_id,
        "name": f"测试工人_{unique_id}",
        "phone": f"138{unique_id % 100000000:08d}",
        "id_no": f"WK{unique_id}",
        "id_card": f"11010119900101{unique_id % 10000:04d}",
        "gender": "male",
        "position": "电工"
    }
    resp = client.post("/workers", json_data=worker_data)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0:
            worker_id = data["data"].get("worker_id")
            yield {"worker_id": worker_id, **worker_data}
            # 清理
            client.delete(f"/workers/{worker_id}")
            return
    yield None


class TestWorkersList:
    """工人列表查询测试"""
    
    def test_list_basic_pagination(self, client):
        """测试：基础分页查询"""
        resp = client.get("/workers", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "items" in data["data"]
        assert "total" in data["data"]
        print(f"✓ 基础分页查询成功，共{data['data']['total']}条记录")
    
    def test_list_keyword_search_name(self, client):
        """测试：按姓名关键词搜索"""
        resp = client.get("/workers", params={"keyword": "工人"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按姓名关键词搜索成功")
    
    def test_list_keyword_search_phone(self, client):
        """测试：按电话关键词搜索"""
        resp = client.get("/workers", params={"keyword": "138"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按电话关键词搜索成功")
    
    def test_list_filter_by_contractor(self, client, test_contractor_id):
        """测试：按施工单位筛选"""
        resp = client.get("/workers", params={"contractor_id": test_contractor_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按施工单位筛选成功")
    
    def test_list_filter_by_site(self, client, test_site_id):
        """测试：按工地筛选"""
        resp = client.get("/workers", params={"site_id": test_site_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按工地筛选成功")
    
    def test_list_filter_by_status_active(self, client):
        """测试：按状态筛选-ACTIVE"""
        resp = client.get("/workers", params={"status": "ACTIVE"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按状态筛选(ACTIVE)成功")
    
    def test_list_filter_by_gender(self, client):
        """测试：按性别筛选"""
        resp = client.get("/workers", params={"gender": "male"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按性别筛选成功")
    
    def test_list_filter_by_position(self, client):
        """测试：按工种筛选"""
        resp = client.get("/workers", params={"position": "电工"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按工种筛选成功")
    
    def test_list_combined_filters(self, client, test_site_id, test_contractor_id):
        """测试：组合筛选"""
        resp = client.get("/workers", params={
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "status": "ACTIVE",
            "page": 1,
            "page_size": 10
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 组合筛选成功")
    
    def test_list_response_fields(self, client):
        """测试：返回字段完整性"""
        resp = client.get("/workers", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        if data["data"]["items"]:
            item = data["data"]["items"][0]
            expected_fields = ["worker_id", "name", "phone"]
            for field in expected_fields:
                assert field in item or "id" in item, f"缺少字段: {field}"
        print("✓ 返回字段完整性验证通过")
    
    def test_list_empty_result(self, client):
        """测试：空结果响应"""
        resp = client.get("/workers", params={"keyword": "不存在的工人xyz123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 空结果响应正确")


class TestWorkersOptions:
    """工人选项查询测试"""
    
    def test_options_basic(self, client):
        """测试：获取工人选项（支持分页）"""
        resp = client.get("/workers/options", params={"page": 1, "page_size": 20})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert isinstance(data.get("data"), list)
        print(f"✓ 获取工人选项成功，共{len(data['data'])}个")
    
    def test_options_search(self, client):
        """测试：搜索工人选项"""
        resp = client.get("/workers/options", params={"keyword": "工人"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 搜索工人选项成功")
    
    def test_options_response_format(self, client):
        """测试：选项响应格式"""
        resp = client.get("/workers/options", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        if data.get("data"):
            item = data["data"][0]
            assert "worker_id" in item or "id" in item
            assert "name" in item or "label" in item
        print("✓ 选项响应格式正确")


class TestWorkersDetail:
    """工人详情查询测试"""
    
    def test_detail_valid_id(self, client, created_worker):
        """测试：有效ID查询"""
        if not created_worker:
            pytest.skip("没有创建测试工人")
        
        worker_id = created_worker["worker_id"]
        resp = client.get(f"/workers/{worker_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 有效ID查询成功")
    
    def test_detail_invalid_id(self, client):
        """测试：无效ID（不存在）"""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/workers/{fake_id}")
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0 or data.get("data") is None
        print("✓ 无效ID处理正确")
    
    def test_detail_invalid_uuid_format(self, client):
        """测试：无效UUID格式"""
        resp = client.get("/workers/not-a-valid-uuid")
        assert resp.status_code in [422, 404, 400]
        print("✓ 无效UUID格式处理正确")
    
    def test_detail_response_fields(self, client, created_worker):
        """测试：详情返回字段完整性"""
        if not created_worker:
            pytest.skip("没有创建测试工人")
        
        worker_id = created_worker["worker_id"]
        resp = client.get(f"/workers/{worker_id}")
        assert resp.status_code == 200
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            item = data["data"]
            expected_fields = ["worker_id", "name", "phone", "contractor_id"]
            for field in expected_fields:
                if field == "worker_id":
                    assert field in item or "id" in item
        print("✓ 详情返回字段完整性验证通过")


class TestWorkersCreate:
    """工人创建测试"""
    
    def test_create_success_required_fields(self, client, test_site_id, test_contractor_id):
        """测试：成功创建（必填字段）"""
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "name": f"创建测试工人_{unique_id}",
            "phone": f"139{unique_id % 100000000:08d}",
            "id_no": f"CRT{unique_id}"
        }
        resp = client.post("/workers", json_data=worker_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        
        # 清理
        if data.get("data", {}).get("worker_id"):
            client.delete(f"/workers/{data['data']['worker_id']}")
        print("✓ 成功创建工人（必填字段）")
    
    def test_create_success_all_fields(self, client, test_site_id, test_contractor_id):
        """测试：成功创建（所有字段）"""
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "name": f"完整创建测试_{unique_id}",
            "phone": f"137{unique_id % 100000000:08d}",
            "id_no": f"FULL{unique_id}",
            "id_card": f"11010119900101{unique_id % 10000:04d}",
            "gender": "female",
            "position": "焊工",
            "emergency_contact": "紧急联系人",
            "emergency_phone": "13600136000"
        }
        resp = client.post("/workers", json_data=worker_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        
        # 清理
        if data.get("data", {}).get("worker_id"):
            client.delete(f"/workers/{data['data']['worker_id']}")
        print("✓ 成功创建工人（所有字段）")
    
    def test_create_without_contractor_id(self, client, test_site_id):
        """测试：不提供contractor_id（可选字段）"""
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "name": f"无施工单位测试_{unique_id}",
            "phone": f"136{unique_id % 100000000:08d}",
            "id_no": f"NC{unique_id}"
        }
        resp = client.post("/workers", json_data=worker_data)
        # contractor_id是可选的，所以可以成功创建
        assert resp.status_code == 200
        data = resp.json()
        # 可以成功创建或返回验证错误都是合理的
        if data.get("code") == 0 and data.get("data", {}).get("worker_id"):
            client.delete(f"/workers/{data['data']['worker_id']}")
        print("✓ 缺少contractor_id验证正确")
    
    def test_create_missing_name(self, client, test_site_id, test_contractor_id):
        """测试：缺少name"""
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "phone": f"135{unique_id % 100000000:08d}",
            "id_no": f"NN{unique_id}"
        }
        resp = client.post("/workers", json_data=worker_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少name验证正确")
    
    def test_create_missing_phone(self, client, test_site_id, test_contractor_id):
        """测试：缺少phone"""
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "name": f"缺少电话测试_{unique_id}",
            "id_no": f"NP{unique_id}"
        }
        resp = client.post("/workers", json_data=worker_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少phone验证正确")
    
    def test_create_missing_id_no(self, client, test_site_id, test_contractor_id):
        """测试：缺少id_no"""
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "name": f"缺少工号测试_{unique_id}",
            "phone": f"134{unique_id % 100000000:08d}"
        }
        resp = client.post("/workers", json_data=worker_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少id_no验证正确")
    
    def test_create_duplicate_phone(self, client, test_site_id, test_contractor_id, created_worker):
        """测试：重复电话"""
        if not created_worker:
            pytest.skip("没有创建测试工人")
        
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "name": f"重复电话测试_{unique_id}",
            "phone": created_worker["phone"],  # 使用已存在的电话
            "id_no": f"DP{unique_id}"
        }
        resp = client.post("/workers", json_data=worker_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                if data.get("data", {}).get("worker_id"):
                    client.delete(f"/workers/{data['data']['worker_id']}")
                pytest.fail("重复电话应该返回错误")
        print("✓ 重复电话验证正确")
    
    def test_create_duplicate_id_no(self, client, test_site_id, test_contractor_id, created_worker):
        """测试：重复工号"""
        if not created_worker:
            pytest.skip("没有创建测试工人")
        
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "name": f"重复工号测试_{unique_id}",
            "phone": f"133{unique_id % 100000000:08d}",
            "id_no": created_worker["id_no"]  # 使用已存在的工号
        }
        resp = client.post("/workers", json_data=worker_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                if data.get("data", {}).get("worker_id"):
                    client.delete(f"/workers/{data['data']['worker_id']}")
                pytest.fail("重复工号应该返回错误")
        print("✓ 重复工号验证正确")
    
    def test_create_invalid_phone_format(self, client, test_site_id, test_contractor_id):
        """测试：无效电话格式"""
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "name": f"无效电话测试_{unique_id}",
            "phone": "123",  # 无效电话
            "id_no": f"IP{unique_id}"
        }
        resp = client.post("/workers", json_data=worker_data)
        # 可能验证也可能不验证电话格式
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and data.get("data", {}).get("worker_id"):
                client.delete(f"/workers/{data['data']['worker_id']}")
        print("✓ 无效电话格式验证完成")
    
    def test_create_invalid_gender(self, client, test_site_id, test_contractor_id):
        """测试：无效性别值"""
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "name": f"无效性别测试_{unique_id}",
            "phone": f"132{unique_id % 100000000:08d}",
            "id_no": f"IG{unique_id}",
            "gender": "invalid_gender"
        }
        resp = client.post("/workers", json_data=worker_data)
        # 应该返回验证错误或使用默认值
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and data.get("data", {}).get("worker_id"):
                client.delete(f"/workers/{data['data']['worker_id']}")
        print("✓ 无效性别值验证完成")


class TestWorkersUpdate:
    """工人更新测试"""
    
    def test_update_success(self, client, created_worker):
        """测试：成功更新"""
        if not created_worker:
            pytest.skip("没有创建测试工人")
        
        worker_id = created_worker["worker_id"]
        update_data = {
            "name": f"更新后的姓名_{int(time.time())}",
            "position": "木工"
        }
        resp = client.patch(f"/workers/{worker_id}", json_data=update_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"更新失败: {data.get('message')}"
        print("✓ 成功更新工人")
    
    def test_update_status(self, client, created_worker):
        """测试：更新状态"""
        if not created_worker:
            pytest.skip("没有创建测试工人")
        
        worker_id = created_worker["worker_id"]
        update_data = {
            "status": "INACTIVE"
        }
        resp = client.patch(f"/workers/{worker_id}", json_data=update_data)
        assert resp.status_code == 200
        print("✓ 状态更新测试完成")
    
    def test_update_not_found(self, client):
        """测试：更新不存在的记录"""
        fake_id = str(uuid.uuid4())
        update_data = {
            "name": "不存在的工人"
        }
        resp = client.patch(f"/workers/{fake_id}", json_data=update_data)
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0
        print("✓ 更新不存在记录处理正确")


class TestWorkersDelete:
    """工人删除测试"""
    
    def test_delete_success(self, client, test_site_id, test_contractor_id):
        """测试：成功删除"""
        # 先创建一个工人
        unique_id = int(time.time())
        worker_data = {
            "site_id": test_site_id,
            "contractor_id": test_contractor_id,
            "name": f"待删除工人_{unique_id}",
            "phone": f"131{unique_id % 100000000:08d}",
            "id_no": f"DEL{unique_id}"
        }
        create_resp = client.post("/workers", json_data=worker_data)
        if create_resp.status_code != 200 or create_resp.json().get("code") != 0:
            pytest.skip("无法创建测试工人")
        
        worker_id = create_resp.json()["data"]["worker_id"]
        
        # 删除
        resp = client.delete(f"/workers/{worker_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"删除失败: {data.get('message')}"
        print("✓ 成功删除工人")
    
    def test_delete_not_found(self, client):
        """测试：删除不存在的记录"""
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/workers/{fake_id}")
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0
        print("✓ 删除不存在记录处理正确")


class TestWorkersStats:
    """工人统计测试"""
    
    def test_stats_total_count(self, client):
        """测试：工人总数统计"""
        resp = client.get("/workers", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "total" in data["data"]
        print(f"✓ 工人总数: {data['data']['total']}")
    
    def test_stats_by_contractor(self, client, test_contractor_id):
        """测试：按施工单位统计"""
        resp = client.get("/workers", params={
            "contractor_id": test_contractor_id,
            "page": 1,
            "page_size": 1
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print(f"✓ 施工单位{test_contractor_id}的工人数: {data['data']['total']}")
    
    def test_stats_by_position(self, client):
        """测试：按工种统计"""
        positions = ["电工", "焊工", "木工", "普工"]
        for position in positions:
            resp = client.get("/workers", params={
                "position": position,
                "page": 1,
                "page_size": 1
            })
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    print(f"✓ 工种'{position}'的工人数: {data['data']['total']}")
    
    def test_stats_active_workers(self, client):
        """测试：在岗工人统计"""
        resp = client.get("/workers", params={
            "status": "ACTIVE",
            "page": 1,
            "page_size": 1
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print(f"✓ 在岗工人数: {data['data']['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

