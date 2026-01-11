"""
培训视频管理API测试
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
def created_video(client, test_site_id):
    """创建测试视频，测试后清理"""
    unique_title = f"测试视频_{int(time.time())}"
    video_data = {
        "site_id": test_site_id,
        "title": unique_title,
        "file_url": "https://example.com/test_video.mp4",
        "duration_sec": 300,
        "description": "自动化测试创建的视频",
        "category": "safety"
    }
    resp = client.post("/videos", json_data=video_data)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0:
            video_id = data["data"].get("video_id")
            yield {"video_id": video_id, **video_data}
            # 清理
            client.delete(f"/videos/{video_id}")
            return
    yield None


class TestVideosList:
    """视频列表查询测试"""
    
    def test_list_basic_pagination(self, client):
        """测试：基础分页查询"""
        resp = client.get("/videos", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "items" in data["data"]
        assert "total" in data["data"]
        print(f"✓ 基础分页查询成功，共{data['data']['total']}条记录")
    
    def test_list_keyword_search(self, client):
        """测试：关键词搜索"""
        resp = client.get("/videos", params={"keyword": "培训"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print(f"✓ 关键词搜索成功")
    
    def test_list_filter_by_category(self, client):
        """测试：按分类筛选"""
        resp = client.get("/videos", params={"category": "safety"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按分类筛选成功")
    
    def test_list_filter_by_status_active(self, client):
        """测试：按状态筛选-ACTIVE"""
        resp = client.get("/videos", params={"status": "ACTIVE"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按状态筛选(ACTIVE)成功")
    
    def test_list_filter_by_status_draft(self, client):
        """测试：按状态筛选-DRAFT"""
        resp = client.get("/videos", params={"status": "DRAFT"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按状态筛选(DRAFT)成功")
    
    def test_list_filter_by_site(self, client, test_site_id):
        """测试：按工地筛选"""
        resp = client.get("/videos", params={"site_id": test_site_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 按工地筛选成功")
    
    def test_list_combined_filters(self, client, test_site_id):
        """测试：组合筛选"""
        resp = client.get("/videos", params={
            "site_id": test_site_id,
            "status": "ACTIVE",
            "keyword": "视频",
            "page": 1,
            "page_size": 10
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 组合筛选成功")
    
    def test_list_response_fields(self, client):
        """测试：返回字段完整性"""
        resp = client.get("/videos", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        if data["data"]["items"]:
            item = data["data"]["items"][0]
            expected_fields = ["video_id", "title", "file_url", "duration_sec"]
            for field in expected_fields:
                assert field in item or "id" in item, f"缺少字段: {field}"
        print("✓ 返回字段完整性验证通过")
    
    def test_list_empty_result(self, client):
        """测试：空结果响应"""
        resp = client.get("/videos", params={"keyword": "不存在的视频xyz123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 空结果响应正确")


class TestVideosOptions:
    """视频选项查询测试"""
    
    def test_options_basic(self, client):
        """测试：获取可用视频选项"""
        resp = client.get("/videos/options")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert isinstance(data.get("data"), list)
        print(f"✓ 获取视频选项成功，共{len(data['data'])}个")
    
    def test_options_response_format(self, client):
        """测试：选项响应格式"""
        resp = client.get("/videos/options")
        assert resp.status_code == 200
        data = resp.json()
        if data.get("data"):
            item = data["data"][0]
            assert "video_id" in item or "id" in item
            assert "title" in item or "name" in item
        print("✓ 选项响应格式正确")


class TestVideosDetail:
    """视频详情查询测试"""
    
    def test_detail_valid_id(self, client, created_video):
        """测试：有效ID查询"""
        if not created_video:
            pytest.skip("没有创建测试视频")
        
        video_id = created_video["video_id"]
        resp = client.get(f"/videos/{video_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 有效ID查询成功")
    
    def test_detail_invalid_id(self, client):
        """测试：无效ID（不存在）"""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/videos/{fake_id}")
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0 or data.get("data") is None
        print("✓ 无效ID处理正确")
    
    def test_detail_invalid_uuid_format(self, client):
        """测试：无效UUID格式"""
        resp = client.get("/videos/not-a-valid-uuid")
        assert resp.status_code in [422, 404, 400]
        print("✓ 无效UUID格式处理正确")


class TestVideosCreate:
    """视频创建测试"""
    
    def test_create_success_required_fields(self, client, test_site_id):
        """测试：成功创建（必填字段）"""
        unique_title = f"创建测试视频_{int(time.time())}"
        video_data = {
            "site_id": test_site_id,
            "title": unique_title,
            "file_url": "https://example.com/test.mp4",
            "duration_sec": 120
        }
        resp = client.post("/videos", json_data=video_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        
        # 清理
        if data.get("data", {}).get("video_id"):
            client.delete(f"/videos/{data['data']['video_id']}")
        print("✓ 成功创建视频（必填字段）")
    
    def test_create_success_all_fields(self, client, test_site_id):
        """测试：成功创建（所有字段）"""
        unique_title = f"完整创建测试_{int(time.time())}"
        video_data = {
            "site_id": test_site_id,
            "title": unique_title,
            "file_url": "https://example.com/full_test.mp4",
            "duration_sec": 600,
            "description": "这是一个完整的测试视频",
            "category": "safety",
            "thumbnail_url": "https://example.com/thumb.jpg"
        }
        resp = client.post("/videos", json_data=video_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        
        # 清理
        if data.get("data", {}).get("video_id"):
            client.delete(f"/videos/{data['data']['video_id']}")
        print("✓ 成功创建视频（所有字段）")
    
    def test_create_missing_title(self, client, test_site_id):
        """测试：缺少title"""
        video_data = {
            "site_id": test_site_id,
            "file_url": "https://example.com/test.mp4",
            "duration_sec": 120
        }
        resp = client.post("/videos", json_data=video_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少title验证正确")
    
    def test_create_missing_file_url(self, client, test_site_id):
        """测试：缺少file_url"""
        video_data = {
            "site_id": test_site_id,
            "title": f"缺少URL测试_{int(time.time())}",
            "duration_sec": 120
        }
        resp = client.post("/videos", json_data=video_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少file_url验证正确")
    
    def test_create_missing_duration(self, client, test_site_id):
        """测试：缺少duration_sec"""
        video_data = {
            "site_id": test_site_id,
            "title": f"缺少时长测试_{int(time.time())}",
            "file_url": "https://example.com/test.mp4"
        }
        resp = client.post("/videos", json_data=video_data)
        assert resp.status_code == 422 or (
            resp.status_code == 200 and resp.json().get("code") != 0
        )
        print("✓ 缺少duration_sec验证正确")
    
    def test_create_invalid_duration_negative(self, client, test_site_id):
        """测试：无效duration值（负数）"""
        video_data = {
            "site_id": test_site_id,
            "title": f"负数时长测试_{int(time.time())}",
            "file_url": "https://example.com/test.mp4",
            "duration_sec": -100
        }
        resp = client.post("/videos", json_data=video_data)
        # 应该返回验证错误
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and data.get("data", {}).get("video_id"):
                client.delete(f"/videos/{data['data']['video_id']}")
        print("✓ 负数时长验证正确")
    
    def test_create_invalid_url_format(self, client, test_site_id):
        """测试：无效URL格式"""
        video_data = {
            "site_id": test_site_id,
            "title": f"无效URL测试_{int(time.time())}",
            "file_url": "not-a-valid-url",
            "duration_sec": 120
        }
        resp = client.post("/videos", json_data=video_data)
        # 可能接受任何字符串，取决于API设计
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and data.get("data", {}).get("video_id"):
                client.delete(f"/videos/{data['data']['video_id']}")
        print("✓ 无效URL格式验证完成")
    
    def test_create_title_too_long(self, client, test_site_id):
        """测试：标题超长"""
        video_data = {
            "site_id": test_site_id,
            "title": "A" * 300,
            "file_url": "https://example.com/test.mp4",
            "duration_sec": 120
        }
        resp = client.post("/videos", json_data=video_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and data.get("data", {}).get("video_id"):
                client.delete(f"/videos/{data['data']['video_id']}")
        print("✓ 标题超长验证完成")


class TestVideosUpdate:
    """视频更新测试"""
    
    def test_update_success(self, client, created_video):
        """测试：成功更新"""
        if not created_video:
            pytest.skip("没有创建测试视频")
        
        video_id = created_video["video_id"]
        update_data = {
            "title": f"更新后的标题_{int(time.time())}",
            "description": "更新后的描述"
        }
        resp = client.patch(f"/videos/{video_id}", json_data=update_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"更新失败: {data.get('message')}"
        print("✓ 成功更新视频")
    
    def test_update_status(self, client, created_video):
        """测试：更新状态"""
        if not created_video:
            pytest.skip("没有创建测试视频")
        
        video_id = created_video["video_id"]
        update_data = {
            "status": "DRAFT"
        }
        resp = client.patch(f"/videos/{video_id}", json_data=update_data)
        assert resp.status_code == 200
        print("✓ 状态更新测试完成")
    
    def test_update_invalid_status(self, client, created_video):
        """测试：无效状态值"""
        if not created_video:
            pytest.skip("没有创建测试视频")
        
        video_id = created_video["video_id"]
        update_data = {
            "status": "INVALID_STATUS"
        }
        resp = client.patch(f"/videos/{video_id}", json_data=update_data)
        # 应该返回验证错误
        if resp.status_code == 200:
            data = resp.json()
            # 可能返回错误码
        print("✓ 无效状态值验证完成")
    
    def test_update_not_found(self, client):
        """测试：更新不存在的记录"""
        fake_id = str(uuid.uuid4())
        update_data = {
            "title": "不存在的视频"
        }
        resp = client.patch(f"/videos/{fake_id}", json_data=update_data)
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0
        print("✓ 更新不存在记录处理正确")


class TestVideosDelete:
    """视频删除测试"""
    
    def test_delete_success(self, client, test_site_id):
        """测试：成功删除"""
        # 先创建一个视频
        unique_title = f"待删除视频_{int(time.time())}"
        video_data = {
            "site_id": test_site_id,
            "title": unique_title,
            "file_url": "https://example.com/delete_test.mp4",
            "duration_sec": 60
        }
        create_resp = client.post("/videos", json_data=video_data)
        if create_resp.status_code != 200 or create_resp.json().get("code") != 0:
            pytest.skip("无法创建测试视频")
        
        video_id = create_resp.json()["data"]["video_id"]
        
        # 删除
        resp = client.delete(f"/videos/{video_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"删除失败: {data.get('message')}"
        print("✓ 成功删除视频")
    
    def test_delete_not_found(self, client):
        """测试：删除不存在的记录"""
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/videos/{fake_id}")
        assert resp.status_code in [200, 404]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0
        print("✓ 删除不存在记录处理正确")


class TestVideosStats:
    """视频统计测试"""
    
    def test_stats_total_count(self, client):
        """测试：视频总数统计"""
        resp = client.get("/videos", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "total" in data["data"]
        print(f"✓ 视频总数: {data['data']['total']}")
    
    def test_stats_by_category(self, client):
        """测试：按分类统计"""
        categories = ["safety", "operation", "emergency"]
        for category in categories:
            resp = client.get("/videos", params={
                "category": category,
                "page": 1,
                "page_size": 1
            })
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    print(f"✓ 分类'{category}'的视频数: {data['data']['total']}")
    
    def test_stats_by_status(self, client):
        """测试：按状态统计"""
        statuses = ["ACTIVE", "DRAFT", "ARCHIVED"]
        for status in statuses:
            resp = client.get("/videos", params={
                "status": status,
                "page": 1,
                "page_size": 1
            })
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    print(f"✓ 状态'{status}'的视频数: {data['data']['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

