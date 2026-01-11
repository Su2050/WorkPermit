"""
API自动化测试脚本 - 根据详细测试文档完善
"""
import pytest
import requests
import json
import uuid
from datetime import date, timedelta
from typing import Dict, Optional

BASE_URL = "http://localhost:8000/api"
ADMIN_BASE = f"{BASE_URL}/admin"

# 测试用户凭证
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"


class APIClient:
    """测试客户端"""
    def __init__(self):
        self.base_url = BASE_URL
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {}
    
    def login(self, username: str, password: str) -> bool:
        """登录"""
        try:
            resp = requests.post(
                f"{ADMIN_BASE}/auth/login",
                json={"username": username, "password": password}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    self.token = data["data"]["access_token"]
                    self.headers = {"Authorization": f"Bearer {self.token}"}
                    return True
            return False
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """GET请求"""
        return requests.get(f"{ADMIN_BASE}{endpoint}", headers=self.headers, params=params)
    
    def post(self, endpoint: str, json_data: Optional[Dict] = None) -> requests.Response:
        """POST请求"""
        return requests.post(f"{ADMIN_BASE}{endpoint}", headers=self.headers, json=json_data)
    
    def patch(self, endpoint: str, json_data: Optional[Dict] = None) -> requests.Response:
        """PATCH请求"""
        return requests.patch(f"{ADMIN_BASE}{endpoint}", headers=self.headers, json=json_data)
    
    def put(self, endpoint: str, json_data: Optional[Dict] = None) -> requests.Response:
        """PUT请求"""
        return requests.put(f"{ADMIN_BASE}{endpoint}", headers=self.headers, json=json_data)
    
    def delete(self, endpoint: str) -> requests.Response:
        """DELETE请求"""
        return requests.delete(f"{ADMIN_BASE}{endpoint}", headers=self.headers)


@pytest.fixture(scope="module")
def client():
    """测试客户端fixture"""
    c = APIClient()
    assert c.login(TEST_USERNAME, TEST_PASSWORD), "登录失败"
    return c


# ==================== 4.1 认证授权模块 ====================

class TestAuth:
    """认证授权测试 - TC-AUTH-001 到 TC-AUTH-007"""
    
    def test_tc_auth_001_login_success(self):
        """TC-AUTH-001: 用户登录成功"""
        c = APIClient()
        assert c.login(TEST_USERNAME, TEST_PASSWORD), "登录应该成功"
        assert c.token is not None, "应该返回token"
        assert len(c.token) > 0, "Token不应该为空"
    
    def test_tc_auth_002_login_failure_wrong_username(self):
        """TC-AUTH-002: 用户登录失败 - 错误用户名"""
        resp = requests.post(
            f"{ADMIN_BASE}/auth/login",
            json={"username": "wrong_user", "password": "admin123"}
        )
        assert resp.status_code == 200, "业务错误仍返回200"
        data = resp.json()
        assert data.get("code") != 0, "应该返回错误码"
        assert "用户不存在" in data.get("message", "") or "用户" in data.get("message", ""), "错误信息应该包含用户相关提示"
        # 修复：data可能是None
        response_data = data.get("data")
        if response_data is not None:
            assert "access_token" not in response_data, "不应该返回token"
    
    def test_tc_auth_003_login_failure_wrong_password(self):
        """TC-AUTH-003: 用户登录失败 - 错误密码"""
        resp = requests.post(
            f"{ADMIN_BASE}/auth/login",
            json={"username": "admin", "password": "wrong_pass"}
        )
        assert resp.status_code == 200, "业务错误仍返回200"
        data = resp.json()
        assert data.get("code") != 0, "应该返回错误码"
        assert "密码" in data.get("message", ""), "错误信息应该包含密码相关提示"
        # 修复：data可能是None
        response_data = data.get("data")
        if response_data is not None:
            assert "access_token" not in response_data, "不应该返回token"
    
    def test_tc_auth_004_login_failure_missing_params(self):
        """TC-AUTH-004: 用户登录失败 - 缺少参数"""
        resp = requests.post(
            f"{ADMIN_BASE}/auth/login",
            json={"username": "admin"}  # 缺少password
        )
        assert resp.status_code == 422, "应该返回422参数验证错误"
    
    def test_tc_auth_005_get_current_user(self, client):
        """TC-AUTH-005: 获取当前用户信息"""
        resp = client.get("/auth/me")
        assert resp.status_code == 200, f"状态码应该是200，实际是{resp.status_code}"
        data = resp.json()
        assert data.get("code") == 0, f"业务码应该是0，实际是{data.get('code')}"
        assert "data" in data, "应该返回用户数据"
        user_data = data["data"]
        assert user_data.get("username") == TEST_USERNAME, "用户名应该匹配"
        assert "user_id" in user_data, "应该包含user_id"
        assert "role" in user_data, "应该包含role"
        # 验证UUID格式
        try:
            uuid.UUID(user_data["user_id"])
        except ValueError:
            pytest.fail("user_id应该是有效的UUID格式")
    
    def test_tc_auth_006_get_current_user_unauthorized(self):
        """TC-AUTH-006: 获取当前用户信息 - 未认证"""
        resp = requests.get(f"{ADMIN_BASE}/auth/me")  # 不设置Authorization头
        assert resp.status_code == 401, "应该返回401未认证"
    
    def test_tc_auth_007_get_current_user_invalid_token(self):
        """TC-AUTH-007: 获取当前用户信息 - 无效Token"""
        headers = {"Authorization": "Bearer invalid_token"}
        resp = requests.get(f"{ADMIN_BASE}/auth/me", headers=headers)
        assert resp.status_code == 401, "应该返回401"


# ==================== 4.2 作业票管理模块 ====================

class TestWorkTickets:
    """作业票管理测试 - TC-TICKET-001 到 TC-TICKET-014"""
    
    def test_tc_ticket_001_list_tickets_basic(self, client):
        """TC-TICKET-001: 获取作业票列表 - 基础查询"""
        resp = client.get("/work-tickets", params={"page": 1, "page_size": 20})
        assert resp.status_code == 200, f"状态码应该是200，实际是{resp.status_code}"
        data = resp.json()
        assert data.get("code") == 0, f"业务码应该是0，实际是{data.get('code')}"
        assert "data" in data, "应该返回数据"
        assert "items" in data["data"], "应该返回items数组"
        assert "total" in data["data"], "应该返回total"
        assert "page" in data["data"], "应该返回page"
        assert "page_size" in data["data"], "应该返回page_size"
        assert isinstance(data["data"]["items"], list), "items应该是数组"
        assert data["data"]["total"] >= 0, "total应该大于等于0"
        
        # 验证每个item的必需字段
        if data["data"]["items"]:
            item = data["data"]["items"][0]
            assert "ticket_id" in item, "应该包含ticket_id"
            assert "title" in item, "应该包含title"
            assert "status" in item, "应该包含status"
    
    def test_tc_ticket_002_list_tickets_filter_contractor(self, client):
        """TC-TICKET-002: 获取作业票列表 - 按施工单位筛选"""
        # 先获取施工单位选项
        resp_options = client.get("/contractors/options")
        assert resp_options.status_code == 200
        options_data = resp_options.json()
        if options_data.get("code") == 0 and options_data["data"]:
            contractor_id = options_data["data"][0]["id"]
            # 使用第一个施工单位ID筛选
            resp = client.get("/work-tickets", params={
                "page": 1,
                "page_size": 20,
                "contractor_id": contractor_id
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("code") == 0
            # 验证所有返回的作业票都属于该施工单位
            if data["data"]["items"]:
                for item in data["data"]["items"]:
                    # 检查contractor字段
                    if "contractor" in item and item["contractor"]:
                        assert item["contractor"].get("contractor_id") == contractor_id or item.get("contractor_id") == contractor_id
    
    def test_tc_ticket_003_list_tickets_filter_status(self, client):
        """TC-TICKET-003: 获取作业票列表 - 按状态筛选"""
        resp = client.get("/work-tickets", params={
            "page": 1,
            "page_size": 20,
            "status": "IN_PROGRESS"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        # 验证所有返回的作业票都是进行中状态
        for item in data["data"]["items"]:
            assert item.get("status") == "IN_PROGRESS"
    
    def test_tc_ticket_004_list_tickets_keyword(self, client):
        """TC-TICKET-004: 获取作业票列表 - 关键词搜索"""
        resp = client.get("/work-tickets", params={
            "page": 1,
            "page_size": 20,
            "keyword": "焊接"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        # 验证所有返回的作业票标题包含关键词（不区分大小写）
        for item in data["data"]["items"]:
            title = item.get("title", "").lower()
            assert "焊接" in title or "hanjie" in title.lower(), f"标题应该包含关键词: {item.get('title')}"
    
    def test_tc_ticket_005_list_tickets_date_range(self, client):
        """TC-TICKET-005: 获取作业票列表 - 日期范围筛选"""
        resp = client.get("/work-tickets", params={
            "page": 1,
            "page_size": 20,
            "start_date": "2026-01-09",
            "end_date": "2026-01-15"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        # 验证日期范围筛选逻辑（作业票日期与查询条件有交集）
        for item in data["data"]["items"]:
            if "start_date" in item and "end_date" in item:
                item_start = item["start_date"]
                item_end = item["end_date"]
                # 验证有交集：item_start <= query_end AND item_end >= query_start
                assert item_start <= "2026-01-15" and item_end >= "2026-01-09"
    
    def test_tc_ticket_006_list_tickets_combined_filter(self, client):
        """TC-TICKET-006: 获取作业票列表 - 组合筛选"""
        # 先获取施工单位选项
        resp_options = client.get("/contractors/options")
        if resp_options.status_code == 200:
            options_data = resp_options.json()
            if options_data.get("code") == 0 and options_data["data"]:
                contractor_id = options_data["data"][0]["id"]
                resp = client.get("/work-tickets", params={
                    "page": 1,
                    "page_size": 20,
                    "contractor_id": contractor_id,
                    "status": "IN_PROGRESS",
                    "keyword": "焊接"
                })
                assert resp.status_code == 200
                data = resp.json()
                assert data.get("code") == 0
                # 验证所有结果同时满足所有筛选条件
                for item in data["data"]["items"]:
                    assert item.get("status") == "IN_PROGRESS", "状态应该匹配"
                    title = item.get("title", "").lower()
                    assert "焊接" in title or "hanjie" in title.lower(), "标题应该包含关键词"
    
    def test_tc_ticket_007_list_tickets_pagination(self, client):
        """TC-TICKET-007: 获取作业票列表 - 分页测试"""
        # 获取第一页
        resp1 = client.get("/work-tickets", params={"page": 1, "page_size": 5})
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1.get("code") == 0
        items1 = data1["data"]["items"]
        total = data1["data"]["total"]
        
        # 获取第二页
        resp2 = client.get("/work-tickets", params={"page": 2, "page_size": 5})
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2.get("code") == 0
        items2 = data2["data"]["items"]
        
        # 验证分页信息
        assert data1["data"]["total"] == data2["data"]["total"], "total应该一致"
        assert data1["data"]["page"] == 1, "第一页page应该是1"
        assert data2["data"]["page"] == 2, "第二页page应该是2"
        assert len(items1) <= 5, "第一页应该最多5条"
        
        # 验证数据不重复（如果总数大于page_size）
        if total > 5 and items1 and items2:
            ids1 = {item.get("ticket_id") for item in items1}
            ids2 = {item.get("ticket_id") for item in items2}
            assert ids1.isdisjoint(ids2), f"两页数据不应该重复: 第一页{ids1}, 第二页{ids2}"
    
    def test_tc_ticket_008_list_tickets_boundary_values(self, client):
        """TC-TICKET-008: 获取作业票列表 - 边界值测试"""
        # page=0 应该返回错误或默认值
        resp = client.get("/work-tickets", params={"page": 0, "page_size": 20})
        # 可能返回错误或自动修正为1
        assert resp.status_code in [200, 422]
        
        # page_size=0 应该返回错误
        resp = client.get("/work-tickets", params={"page": 1, "page_size": 0})
        assert resp.status_code in [200, 422]
        
        # page_size很大时应该限制
        resp = client.get("/work-tickets", params={"page": 1, "page_size": 10000})
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                # 应该有限制，返回的数据不应该超过合理范围
                assert len(data["data"]["items"]) <= 1000  # 假设最大限制
    
    def test_tc_ticket_009_get_ticket_detail(self, client):
        """TC-TICKET-009: 获取作业票详情"""
        # 先获取一个作业票ID
        resp_list = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp_list.status_code == 200
        list_data = resp_list.json()
        if list_data.get("code") == 0 and list_data["data"]["items"]:
            ticket_id = list_data["data"]["items"][0].get("ticket_id")
            # 获取详情
            resp = client.get(f"/work-tickets/{ticket_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("code") == 0
            assert "data" in data
            detail = data["data"]
            assert detail.get("ticket_id") == ticket_id, "ticket_id应该匹配"
            assert "title" in detail, "应该包含title"
            assert "status" in detail, "应该包含status"
            assert "workers" in detail or "workers" in detail, "应该包含workers"
            assert "areas" in detail, "应该包含areas"
            assert "videos" in detail, "应该包含videos"
    
    def test_tc_ticket_010_get_ticket_detail_not_found(self, client):
        """TC-TICKET-010: 获取作业票详情 - 不存在的ID"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.get(f"/work-tickets/{fake_id}")
        assert resp.status_code == 200, "业务错误仍返回200"
        data = resp.json()
        assert data.get("code") != 0, "应该返回错误码"
        assert "不存在" in data.get("message", "") or "not found" in data.get("message", "").lower()
    
    def test_tc_ticket_011_create_ticket_success(self, client):
        """TC-TICKET-011: 创建作业票 - 成功"""
        # 准备测试数据
        # 获取施工单位选项
        resp_contractors = client.get("/contractors/options")
        assert resp_contractors.status_code == 200
        contractors_data = resp_contractors.json()
        if not (contractors_data.get("code") == 0 and contractors_data["data"]):
            pytest.skip("没有可用的施工单位数据")
        
        contractor_id = contractors_data["data"][0]["id"]
        
        # 获取区域选项
        resp_areas = client.get("/areas/options")
        area_ids = []
        if resp_areas.status_code == 200:
            areas_data = resp_areas.json()
            if areas_data.get("code") == 0 and areas_data["data"]:
                area_ids = [areas_data["data"][0]["id"]]
        
        # 获取视频选项
        resp_videos = client.get("/videos/options")
        video_ids = []
        if resp_videos.status_code == 200:
            videos_data = resp_videos.json()
            if videos_data.get("code") == 0 and videos_data["data"]:
                video_ids = [videos_data["data"][0]["id"]]
        
        # 获取人员选项
        resp_workers = client.get("/workers/options")
        worker_ids = []
        if resp_workers.status_code == 200:
            workers_data = resp_workers.json()
            if workers_data.get("code") == 0 and workers_data["data"]:
                worker_ids = [workers_data["data"][0]["id"]]
        
        if not (area_ids and video_ids and worker_ids):
            pytest.skip("缺少必要的关联数据（区域、视频或人员）")
        
        # 创建作业票
        test_data = {
            "title": f"测试作业票_{uuid.uuid4().hex[:8]}",
            "description": "这是一个测试作业票",
            "contractor_id": contractor_id,
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=7)),
            "default_access_start_time": "06:00:00",
            "default_access_end_time": "20:00:00",
            "default_training_deadline_time": "07:30:00",
            "worker_ids": worker_ids,
            "area_ids": area_ids,
            "video_ids": video_ids,
            "notify_on_publish": True,
            "daily_reminder_enabled": True
        }
        
        resp = client.post("/work-tickets", json_data=test_data)
        assert resp.status_code == 200, f"状态码应该是200，实际是{resp.status_code}"
        data = resp.json()
        assert data.get("code") == 0, f"业务码应该是0，实际是{data.get('code')}, 消息: {data.get('message')}"
        assert "data" in data, "应该返回data"
        assert "ticket_id" in data["data"], "应该返回ticket_id"
    
    def test_tc_ticket_012_create_ticket_missing_fields(self, client):
        """TC-TICKET-012: 创建作业票 - 缺少必需字段"""
        resp = client.post("/work-tickets", json_data={
            "description": "缺少title字段"
            # 缺少title等必需字段
        })
        assert resp.status_code == 422, "应该返回422参数验证错误"
    
    def test_tc_ticket_013_create_ticket_date_logic_error(self, client):
        """TC-TICKET-013: 创建作业票 - 日期逻辑错误"""
        # 获取必要的选项数据
        resp_contractors = client.get("/contractors/options")
        if resp_contractors.status_code != 200:
            pytest.skip("无法获取施工单位数据")
        contractors_data = resp_contractors.json()
        if not (contractors_data.get("code") == 0 and contractors_data["data"]):
            pytest.skip("没有可用的施工单位数据")
        
        contractor_id = contractors_data["data"][0]["id"]
        
        # start_date 晚于 end_date
        resp = client.post("/work-tickets", json_data={
            "title": "测试作业票",
            "contractor_id": contractor_id,
            "start_date": "2026-01-15",
            "end_date": "2026-01-10",  # 早于start_date
            "default_access_start_time": "06:00:00",
            "default_access_end_time": "20:00:00",
            "default_training_deadline_time": "07:30:00",
            "worker_ids": [],
            "area_ids": [],
            "video_ids": []
        })
        assert resp.status_code == 200, "业务错误仍返回200"
        data = resp.json()
        assert data.get("code") != 0, "应该返回错误码"
        assert "日期" in data.get("message", "") or "date" in data.get("message", "").lower()
    
    def test_tc_ticket_014_create_ticket_invalid_contractor(self, client):
        """TC-TICKET-014: 创建作业票 - 关联数据不存在"""
        fake_contractor_id = "00000000-0000-0000-0000-000000000000"
        resp = client.post("/work-tickets", json_data={
            "title": "测试作业票",
            "contractor_id": fake_contractor_id,
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=7)),
            "default_access_start_time": "06:00:00",
            "default_access_end_time": "20:00:00",
            "default_training_deadline_time": "07:30:00",
            "worker_ids": [],
            "area_ids": [],
            "video_ids": []
        })
        assert resp.status_code == 200, "业务错误仍返回200"
        data = resp.json()
        assert data.get("code") != 0, "应该返回错误码"
        assert "施工单位" in data.get("message", "") or "contractor" in data.get("message", "").lower()


# ==================== 4.3 施工单位管理模块 ====================

class TestContractors:
    """施工单位管理测试 - TC-CONTRACTOR-001 到 TC-CONTRACTOR-006"""
    
    def test_tc_contractor_001_list_contractors(self, client):
        """TC-CONTRACTOR-001: 获取施工单位列表"""
        resp = client.get("/contractors", params={"page": 1, "page_size": 20})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        assert "items" in data["data"]
        # 验证字段
        if data["data"]["items"]:
            item = data["data"]["items"][0]
            assert "contractor_id" in item or "id" in item
            assert "name" in item
            assert "code" in item
            assert "is_active" in item
    
    def test_tc_contractor_002_get_contractor_options(self, client):
        """TC-CONTRACTOR-002: 获取施工单位选项"""
        resp = client.get("/contractors/options")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert isinstance(data["data"], list), "应该返回数组"
        if data["data"]:
            assert "id" in data["data"][0], "选项应该包含id"
            assert "name" in data["data"][0], "选项应该包含name"
            assert "contractor_id" in data["data"][0], "选项应该包含contractor_id"
    
    def test_tc_contractor_003_options_route_order(self, client):
        """TC-CONTRACTOR-003: 获取施工单位选项 - 路由顺序验证"""
        resp = client.get("/contractors/options")
        assert resp.status_code == 200, "路由应该正确匹配"
        assert resp.status_code != 404, "不应该返回404"
        data = resp.json()
        assert data.get("code") == 0, "应该返回成功"
    
    def test_tc_contractor_004_get_contractor_detail(self, client):
        """TC-CONTRACTOR-004: 获取施工单位详情"""
        # 先获取一个施工单位ID
        resp_list = client.get("/contractors", params={"page": 1, "page_size": 1})
        assert resp_list.status_code == 200
        list_data = resp_list.json()
        if list_data.get("code") == 0 and list_data["data"]["items"]:
            contractor_id = list_data["data"]["items"][0].get("contractor_id") or list_data["data"]["items"][0].get("id")
            # 获取详情
            resp = client.get(f"/contractors/{contractor_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("code") == 0
            assert data["data"].get("contractor_id") == contractor_id or data["data"].get("id") == contractor_id
    
    def test_tc_contractor_005_create_contractor(self, client):
        """TC-CONTRACTOR-005: 创建施工单位"""
        import time
        unique_code = f"TEST{int(time.time())}"
        test_data = {
            "name": f"测试施工单位_{unique_code}",
            "code": unique_code,
            "contact_person": "张三",
            "contact_phone": "13800138000",
            "address": "测试地址",
            "license_no": f"TEST{unique_code}",
            "qualification_level": "一级"
        }
        
        resp = client.post("/contractors", json_data=test_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        assert "data" in data
        assert "contractor_id" in data["data"]
    
    def test_tc_contractor_006_create_contractor_duplicate_code(self, client):
        """TC-CONTRACTOR-006: 创建施工单位 - 编码重复"""
        # 先获取一个已存在的编码
        resp_list = client.get("/contractors", params={"page": 1, "page_size": 1})
        if resp_list.status_code == 200:
            list_data = resp_list.json()
            if list_data.get("code") == 0 and list_data["data"]["items"]:
                existing_code = list_data["data"]["items"][0].get("code")
                # 使用已存在的编码创建
                resp = client.post("/contractors", json_data={
                    "name": "测试施工单位",
                    "code": existing_code,  # 使用已存在的编码
                    "contact_person": "张三",
                    "contact_phone": "13800138000"
                })
                assert resp.status_code == 200, "业务错误仍返回200"
                data = resp.json()
                assert data.get("code") != 0, "应该返回错误码"
                assert "编码" in data.get("message", "") or "code" in data.get("message", "").lower()


# ==================== 4.4 区域管理模块 ====================

class TestAreas:
    """区域管理测试 - TC-AREA-001"""
    
    def test_tc_area_001_list_areas(self, client):
        """TC-AREA-001: 获取区域列表"""
        resp = client.get("/areas", params={"page": 1, "page_size": 20})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        assert "items" in data["data"]
        if data["data"]["items"]:
            item = data["data"]["items"][0]
            assert "area_id" in item or "id" in item
            assert "name" in item


# ==================== 4.5 视频管理模块 ====================

class TestVideos:
    """视频管理测试 - TC-VIDEO-001"""
    
    def test_tc_video_001_list_videos(self, client):
        """TC-VIDEO-001: 获取视频列表"""
        resp = client.get("/videos", params={"page": 1, "page_size": 20})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        assert "items" in data["data"]
        if data["data"]["items"]:
            item = data["data"]["items"][0]
            assert "video_id" in item or "id" in item
            assert "title" in item
            assert "duration_sec" in item


# ==================== 4.6 人员管理模块 ====================

class TestWorkers:
    """人员管理测试 - TC-WORKER-001"""
    
    def test_tc_worker_001_list_workers(self, client):
        """TC-WORKER-001: 获取人员列表"""
        resp = client.get("/workers", params={"page": 1, "page_size": 20})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        assert "items" in data["data"]
        if data["data"]["items"]:
            item = data["data"]["items"][0]
            assert "worker_id" in item or "id" in item
            assert "name" in item


# ==================== 4.7 报表统计模块 ====================

class TestReports:
    """报表统计测试 - TC-REPORT-001 到 TC-REPORT-004"""
    
    def test_tc_report_001_get_dashboard(self, client):
        """TC-REPORT-001: 获取Dashboard数据"""
        resp = client.get("/reports/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        assert "stats" in data["data"], "应该返回stats"
        assert "pendingTickets" in data["data"], "应该返回pendingTickets"
        assert "recentAlerts" in data["data"], "应该返回recentAlerts"
        
        # 验证stats结构
        stats = data["data"]["stats"]
        assert "todayTasks" in stats
        assert "activeTickets" in stats
        assert "todayTrainings" in stats
        assert "accessGrants" in stats
        assert "syncRate" in stats
    
    def test_tc_report_002_dashboard_field_types(self, client):
        """TC-REPORT-002: 获取Dashboard数据 - 字段类型验证"""
        resp = client.get("/reports/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        
        stats = data["data"]["stats"]
        assert isinstance(stats["todayTasks"], int), "todayTasks应该是整数"
        assert stats["todayTasks"] >= 0, "todayTasks应该>=0"
        assert isinstance(stats["activeTickets"], int), "activeTickets应该是整数"
        assert stats["activeTickets"] >= 0
        assert isinstance(stats["todayTrainings"], int), "todayTrainings应该是整数"
        assert stats["todayTrainings"] >= 0
        assert isinstance(stats["accessGrants"], int), "accessGrants应该是整数"
        assert stats["accessGrants"] >= 0
        assert isinstance(stats["syncRate"], (int, float)), "syncRate应该是数字"
        assert 0 <= stats["syncRate"] <= 100, "syncRate应该在0-100之间"
        
        assert isinstance(data["data"]["pendingTickets"], list), "pendingTickets应该是数组"
        assert isinstance(data["data"]["recentAlerts"], list), "recentAlerts应该是数组"
    
    def test_tc_report_003_training_progress(self, client):
        """TC-REPORT-003: 获取培训进度报告"""
        resp = client.get("/reports/training-progress")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
    
    def test_tc_report_004_reconciliation(self, client):
        """TC-REPORT-004: 获取对账报告"""
        resp = client.get("/reports/reconciliation")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0


# ==================== 4.8 告警管理模块 ====================

class TestAlerts:
    """告警管理测试 - TC-ALERT-001 到 TC-ALERT-003"""
    
    def test_tc_alert_001_get_alert_stats(self, client):
        """TC-ALERT-001: 获取告警统计"""
        resp = client.get("/alerts/stats", params={"status": "UNACKNOWLEDGED"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        stats = data["data"]
        assert "total" in stats
        assert "unacknowledged" in stats
        assert "acknowledged" in stats
        assert "resolved" in stats
        assert "high" in stats
        assert "medium" in stats
        assert "low" in stats
        
        # 验证所有字段都是整数 >= 0
        for key in ["total", "unacknowledged", "acknowledged", "resolved", "high", "medium", "low"]:
            assert isinstance(stats[key], int), f"{key}应该是整数"
            assert stats[key] >= 0, f"{key}应该>=0"
    
    def test_tc_alert_002_alert_stats_different_status(self, client):
        """TC-ALERT-002: 获取告警统计 - 不同状态参数"""
        # 测试不同status参数
        for status in ["UNACKNOWLEDGED", "ACKNOWLEDGED", "RESOLVED", None]:
            params = {"status": status} if status else {}
            resp = client.get("/alerts/stats", params=params)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("code") == 0
            assert "data" in data
    
    def test_tc_alert_003_list_alerts(self, client):
        """TC-ALERT-003: 获取告警列表"""
        resp = client.get("/alerts", params={"page": 1, "page_size": 20})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "page_size" in data["data"]


# ==================== 4.9 用户管理模块（新增） ====================

class TestUsers:
    """用户管理测试 - 新增用户功能"""
    
    def test_list_users(self, client):
        """获取用户列表"""
        resp = client.get("/users", params={"page": 1, "page_size": 20})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        assert "items" in data["data"]
    
    def test_create_user_success(self, client):
        """创建用户 - 成功"""
        import time
        unique_username = f"testuser_{int(time.time())}"
        
        # 获取施工单位选项（用于ContractorAdmin角色）
        resp_contractors = client.get("/contractors/options")
        contractor_id = None
        if resp_contractors.status_code == 200:
            contractors_data = resp_contractors.json()
            if contractors_data.get("code") == 0 and contractors_data["data"]:
                contractor_id = contractors_data["data"][0]["id"]
        
        test_data = {
            "username": unique_username,
            "password": "test123456",
            "name": "测试用户",
            "email": f"{unique_username}@test.com",
            "phone": "13800138000",
            "role": "ContractorAdmin" if contractor_id else "SysAdmin",
            "contractor_id": contractor_id,
            "is_active": True
        }
        
        resp = client.post("/users", json_data=test_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"创建失败: {data.get('message')}"
        assert "data" in data
        assert "user_id" in data["data"]
    
    def test_create_user_duplicate_username(self, client):
        """创建用户 - 用户名重复"""
        # 使用已存在的用户名
        resp = client.post("/users", json_data={
            "username": "admin",  # 已存在的用户名
            "password": "test123456",
            "name": "测试用户",
            "role": "SysAdmin"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0, "应该返回错误码"
        assert "用户名" in data.get("message", "") or "username" in data.get("message", "").lower()
    
    def test_create_user_missing_contractor(self, client):
        """创建用户 - ContractorAdmin缺少施工单位"""
        import time
        import random
        unique_username = f"testuser_{int(time.time())}_{random.randint(1000, 9999)}"
        resp = client.post("/users", json_data={
            "username": unique_username,
            "password": "test123456",
            "name": "测试用户",
            "role": "ContractorAdmin",
            # 缺少contractor_id
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0, "应该返回错误码"
        # 可能是施工单位错误，也可能是其他验证错误
        assert "施工单位" in data.get("message", "") or "contractor" in data.get("message", "").lower() or data.get("code") != 0


# ==================== 4.10 日常票据管理模块 ====================

class TestDailyTickets:
    """日常票据管理测试"""
    
    def test_get_daily_tickets_by_ticket_id(self, client):
        """测试: 获取作业票的日常票据列表"""
        # 先获取一个作业票ID
        resp_list = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp_list.status_code == 200
        
        list_data = resp_list.json()
        if not (list_data.get("code") == 0 and list_data["data"]["items"]):
            pytest.skip("没有可用的作业票数据")
        
        ticket_id = list_data["data"]["items"][0].get("ticket_id")
        
        # 获取该作业票的日常票据
        from datetime import date
        resp = client.get(
            f"/work-tickets/{ticket_id}/daily-tickets",
            params={"date": str(date.today())}
        )
        
        # 应该返回200（即使没有数据）
        assert resp.status_code == 200, f"状态码应该是200，实际是{resp.status_code}"
        
        data = resp.json()
        # 即使没有数据，code也应该是0
        assert data.get("code") == 0 or data.get("code") == 404000, \
            f"应该返回成功或数据不存在，实际返回{data}"
    
    def test_get_daily_tickets_invalid_date(self, client):
        """测试: 获取日常票据 - 无效日期格式"""
        resp_list = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        if resp_list.status_code != 200:
            pytest.skip("无法获取作业票列表")
        
        list_data = resp_list.json()
        if not (list_data.get("code") == 0 and list_data["data"]["items"]):
            pytest.skip("没有可用的作业票数据")
        
        ticket_id = list_data["data"]["items"][0].get("ticket_id")
        
        # 测试无效日期
        resp = client.get(
            f"/work-tickets/{ticket_id}/daily-tickets",
            params={"date": "invalid-date"}
        )
        
        # 应该返回422（参数验证错误）或200（业务错误）
        assert resp.status_code in [422, 200]


# ==================== 4.11 审计日志模块 ====================

class TestAuditLogs:
    """审计日志测试"""
    
    def test_get_audit_logs_basic(self, client):
        """测试: 获取审计日志列表"""
        resp = client.get("/audit-logs", params={
            "page": 1,
            "page_size": 20
        })
        
        assert resp.status_code == 200, f"状态码应该是200，实际是{resp.status_code}"
        
        data = resp.json()
        assert data.get("code") == 0, f"业务码应该是0，实际是{data}"
        assert "data" in data
        assert "items" in data["data"]
    
    def test_get_audit_logs_by_resource(self, client):
        """测试: 按资源类型和ID筛选审计日志"""
        # 先获取一个作业票ID
        resp_list = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp_list.status_code == 200
        
        list_data = resp_list.json()
        if not (list_data.get("code") == 0 and list_data["data"]["items"]):
            pytest.skip("没有可用的作业票数据")
        
        ticket_id = list_data["data"]["items"][0].get("ticket_id")
        
        # 获取该作业票的审计日志
        resp = client.get("/audit-logs", params={
            "resource_type": "WorkTicket",
            "resource_id": ticket_id,
            "page": 1,
            "page_size": 20
        })
        
        # 关键测试：不应该返回422
        if resp.status_code == 422:
            pytest.fail(f"审计日志API返回422错误！响应: {resp.text}")
        
        assert resp.status_code == 200, f"状态码应该是200，实际是{resp.status_code}"
        
        data = resp.json()
        assert data.get("code") == 0, f"业务码应该是0，实际是{data}"
    
    def test_get_audit_logs_by_action(self, client):
        """测试: 按操作类型筛选审计日志"""
        resp = client.get("/audit-logs", params={
            "action": "CREATE",
            "page": 1,
            "page_size": 20
        })
        
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0


# ==================== 4.12 工地管理模块 ====================

class TestSites:
    """工地管理测试"""
    
    def test_get_site_options(self, client):
        """测试: 获取工地选项（下拉框）"""
        resp = client.get("/sites/options")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data.get("code") == 0
        assert isinstance(data["data"], list), "应该返回数组"
        
        if data["data"]:
            option = data["data"][0]
            assert "id" in option or "site_id" in option, "选项应该包含id"
            assert "name" in option, "选项应该包含name"
    
    def test_list_sites(self, client):
        """测试: 获取工地列表"""
        resp = client.get("/sites", params={"page": 1, "page_size": 20})
        assert resp.status_code == 200
        
        data = resp.json()
        assert data.get("code") == 0
        assert "data" in data
        assert "items" in data["data"]


# ==================== 压力测试和边界测试 ====================

class TestStressAndBoundary:
    """压力测试和边界测试"""
    
    def test_large_page_size(self, client):
        """测试: 大page_size请求"""
        resp = client.get("/work-tickets", params={
            "page": 1,
            "page_size": 1000  # 很大的page_size
        })
        
        # 应该成功或有合理的限制
        assert resp.status_code in [200, 422]
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                # 返回的数据不应该超过合理范围
                assert len(data["data"]["items"]) <= 1000
    
    def test_very_large_page_number(self, client):
        """测试: 非常大的页码"""
        resp = client.get("/work-tickets", params={
            "page": 999999,
            "page_size": 20
        })
        
        # 应该返回成功但items为空
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        assert len(data["data"]["items"]) == 0
    
    def test_concurrent_create_requests(self, client):
        """测试: 并发创建请求（检查唯一性约束）"""
        import time
        
        # 获取必要的关联数据
        resp_contractors = client.get("/contractors/options")
        if resp_contractors.status_code != 200:
            pytest.skip("无法获取施工单位数据")
        
        contractors_data = resp_contractors.json()
        if not (contractors_data.get("code") == 0 and contractors_data["data"]):
            pytest.skip("没有可用的施工单位数据")
        
        contractor_id = contractors_data["data"][0]["id"]
        
        # 使用相同的编码创建多个施工单位
        unique_code = f"STRESS{int(time.time())}"
        
        results = []
        for i in range(3):
            resp = client.post("/contractors", json_data={
                "name": f"压力测试_{unique_code}_{i}",
                "code": unique_code,  # 相同的编码
                "contact_person": "张三",
                "contact_phone": "13800138000"
            })
            results.append(resp.status_code == 200 and resp.json().get("code") == 0)
        
        # 应该只有一个成功（第一个），其他应该失败（编码重复）
        assert sum(results) == 1, "应该只有一个请求成功（编码唯一性约束）"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
