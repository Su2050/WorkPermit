"""
作业票详情页422错误专项测试
"""
import pytest
import requests
import uuid
from datetime import date

BASE_URL = "http://localhost:8000/api"
ADMIN_BASE = f"{BASE_URL}/admin"

TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"


class APIClient:
    """测试客户端"""
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
    
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
    
    def get(self, endpoint: str, params=None):
        """GET请求"""
        return requests.get(f"{ADMIN_BASE}{endpoint}", headers=self.headers, params=params)


@pytest.fixture(scope="module")
def client():
    """测试客户端fixture"""
    c = APIClient()
    assert c.login(TEST_USERNAME, TEST_PASSWORD), "登录失败"
    return c


class TestTicketDetailAPIs:
    """作业票详情页API测试 - 专门针对422错误"""
    
    def test_get_ticket_detail_valid_id(self, client):
        """测试1: 获取作业票详情 - 有效ID"""
        # 先获取一个有效的作业票ID
        resp_list = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp_list.status_code == 200
        
        list_data = resp_list.json()
        if not (list_data.get("code") == 0 and list_data["data"]["items"]):
            pytest.skip("没有可用的作业票数据")
        
        ticket_id = list_data["data"]["items"][0].get("ticket_id")
        
        # 测试获取详情
        resp = client.get(f"/work-tickets/{ticket_id}")
        assert resp.status_code == 200, f"应该返回200，实际返回{resp.status_code}"
        
        data = resp.json()
        assert data.get("code") == 0, f"应该返回code=0，实际返回{data}"
        assert "data" in data
        
        print(f"  ✓ 作业票详情API正常: {ticket_id}")
    
    def test_get_ticket_detail_invalid_uuid(self, client):
        """测试2: 获取作业票详情 - 无效UUID格式"""
        # 测试各种无效的UUID格式
        invalid_ids = [
            "not-a-uuid",
            "123",
            "xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        ]
        
        for invalid_id in invalid_ids:
            resp = client.get(f"/work-tickets/{invalid_id}")
            # 无效UUID应该返回422（FastAPI自动验证）
            assert resp.status_code == 422, \
                f"无效ID '{invalid_id}' 应该返回422，实际返回{resp.status_code}"
    
    def test_get_daily_tickets_with_valid_date(self, client):
        """测试3: 获取每日票据 - 有效日期"""
        # 先获取一个有效的作业票ID
        resp_list = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp_list.status_code == 200
        
        list_data = resp_list.json()
        if not (list_data.get("code") == 0 and list_data["data"]["items"]):
            pytest.skip("没有可用的作业票数据")
        
        ticket_id = list_data["data"]["items"][0].get("ticket_id")
        
        # 测试获取每日票据（使用今天的日期）
        resp = client.get(
            f"/work-tickets/{ticket_id}/daily-tickets",
            params={"date": str(date.today())}
        )
        
        # 应该返回200（即使没有数据）
        assert resp.status_code == 200, \
            f"应该返回200，实际返回{resp.status_code}\n响应: {resp.text}"
        
        data = resp.json()
        # 即使没有每日票据，也应该返回成功（items为空数组）
        if data.get("code") == 0:
            print(f"  ✓ 每日票据API正常")
        else:
            print(f"  ⚠ 每日票据API返回: {data}")
    
    def test_get_daily_tickets_invalid_date_format(self, client):
        """测试4: 获取每日票据 - 无效日期格式"""
        # 先获取一个有效的作业票ID
        resp_list = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp_list.status_code == 200
        
        list_data = resp_list.json()
        if not (list_data.get("code") == 0 and list_data["data"]["items"]):
            pytest.skip("没有可用的作业票数据")
        
        ticket_id = list_data["data"]["items"][0].get("ticket_id")
        
        # 测试无效的日期格式
        invalid_dates = [
            "2026-13-01",  # 无效月份
            "2026-01-32",  # 无效日期
            "not-a-date",  # 完全无效
            "20260110",    # 格式错误
        ]
        
        for invalid_date in invalid_dates:
            resp = client.get(
                f"/work-tickets/{ticket_id}/daily-tickets",
                params={"date": invalid_date}
            )
            
            # 应该返回422（参数验证错误）或200（业务错误）
            assert resp.status_code in [422, 200], \
                f"无效日期 '{invalid_date}' 应该返回422/200，实际返回{resp.status_code}"
            
            if resp.status_code == 200:
                data = resp.json()
                # 如果返回200，可能业务码不是0
                print(f"  - 无效日期 '{invalid_date}': {data}")
    
    def test_get_audit_logs_with_valid_params(self, client):
        """测试5: 获取审计日志 - 有效参数"""
        # 先获取一个有效的作业票ID
        resp_list = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp_list.status_code == 200
        
        list_data = resp_list.json()
        if not (list_data.get("code") == 0 and list_data["data"]["items"]):
            pytest.skip("没有可用的作业票数据")
        
        ticket_id = list_data["data"]["items"][0].get("ticket_id")
        
        # 测试获取审计日志
        resp = client.get("/audit-logs", params={
            "resource_type": "WorkTicket",
            "resource_id": ticket_id,
            "page": 1,
            "page_size": 20
        })
        
        print(f"  审计日志API状态码: {resp.status_code}")
        
        if resp.status_code == 422:
            print(f"  ❌ 审计日志API返回422! ")
            print(f"  响应内容: {resp.text}")
            detail = resp.json().get("detail", [])
            if isinstance(detail, list):
                for error in detail:
                    print(f"    - 字段 {error.get('loc')}: {error.get('msg')}")
            # 不要断言失败，记录问题
            pytest.fail(f"审计日志API返回422错误: {resp.text}")
        
        assert resp.status_code == 200, \
            f"应该返回200，实际返回{resp.status_code}\n响应: {resp.text}"
        
        data = resp.json()
        assert data.get("code") == 0, f"应该返回code=0，实际返回{data}"
        
        print(f"  ✓ 审计日志API正常")
    
    def test_get_audit_logs_invalid_resource_id(self, client):
        """测试6: 获取审计日志 - 无效resource_id"""
        invalid_ids = [
            "not-a-uuid",
            "123",
            "",
        ]
        
        for invalid_id in invalid_ids:
            resp = client.get("/audit-logs", params={
                "resource_type": "WorkTicket",
                "resource_id": invalid_id,
                "page": 1,
                "page_size": 20
            })
            
            # 无效UUID应该返回422
            assert resp.status_code in [422, 200], \
                f"无效ID '{invalid_id}' 应该返回422/200，实际返回{resp.status_code}"
            
            if resp.status_code == 422:
                print(f"  ✓ 无效ID '{invalid_id}' 正确返回422")
    
    def test_complete_ticket_detail_flow(self, client):
        """测试7: 完整的作业票详情页加载流程"""
        print("\n  === 测试完整流程 ===")
        
        # Step 1: 获取作业票列表
        print("  1. 获取作业票列表...")
        resp_list = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp_list.status_code == 200
        
        list_data = resp_list.json()
        if not (list_data.get("code") == 0 and list_data["data"]["items"]):
            pytest.skip("没有可用的作业票数据")
        
        ticket_id = list_data["data"]["items"][0].get("ticket_id")
        print(f"     ✓ 获取到作业票ID: {ticket_id}")
        
        # Step 2: 获取作业票详情
        print("  2. 获取作业票详情...")
        resp_detail = client.get(f"/work-tickets/{ticket_id}")
        assert resp_detail.status_code == 200
        detail_data = resp_detail.json()
        assert detail_data.get("code") == 0
        print(f"     ✓ 详情: {detail_data['data'].get('title')}")
        
        # Step 3: 获取每日票据
        print("  3. 获取每日票据...")
        resp_daily = client.get(
            f"/work-tickets/{ticket_id}/daily-tickets",
            params={"date": str(date.today())}
        )
        
        if resp_daily.status_code != 200:
            print(f"     ❌ 每日票据API返回{resp_daily.status_code}: {resp_daily.text}")
            pytest.fail(f"每日票据API失败: {resp_daily.status_code}")
        
        daily_data = resp_daily.json()
        if daily_data.get("code") == 0:
            count = len(daily_data["data"].get("items", []))
            print(f"     ✓ 每日票据: {count} 条")
        else:
            print(f"     ⚠ 每日票据: {daily_data.get('message')}")
        
        # Step 4: 获取审计日志
        print("  4. 获取审计日志...")
        resp_audit = client.get("/audit-logs", params={
            "resource_type": "WorkTicket",
            "resource_id": ticket_id,
            "page": 1,
            "page_size": 20
        })
        
        if resp_audit.status_code == 422:
            print(f"     ❌ 审计日志API返回422: {resp_audit.text}")
            pytest.fail(f"审计日志API失败: {resp_audit.text}")
        
        assert resp_audit.status_code == 200
        audit_data = resp_audit.json()
        
        if audit_data.get("code") == 0:
            count = len(audit_data["data"].get("items", []))
            print(f"     ✓ 审计日志: {count} 条")
        else:
            print(f"     ⚠ 审计日志: {audit_data.get('message')}")
        
        print("  === 完整流程测试通过 ===\n")


class TestDataIntegrity:
    """数据完整性测试"""
    
    def test_no_duplicate_contractor_names(self, client):
        """测试: 施工单位名称不应重复"""
        resp = client.get("/contractors", params={"page": 1, "page_size": 1000})
        assert resp.status_code == 200
        
        data = resp.json()
        if data.get("code") == 0:
            items = data["data"]["items"]
            names = [item["name"] for item in items]
            
            # 检查是否有重复
            if len(names) != len(set(names)):
                duplicates = [name for name in names if names.count(name) > 1]
                pytest.fail(f"发现重复的施工单位名称: {set(duplicates)}")
            
            print(f"  ✓ 施工单位名称无重复 ({len(names)} 个)")
    
    def test_no_duplicate_area_names_per_site(self, client):
        """测试: 同一工地内区域名称不应重复"""
        resp = client.get("/areas", params={"page": 1, "page_size": 1000})
        assert resp.status_code == 200
        
        data = resp.json()
        if data.get("code") == 0:
            items = data["data"]["items"]
            
            # 按site_id分组
            sites_areas = {}
            for item in items:
                site_id = item.get("site_id")
                if site_id not in sites_areas:
                    sites_areas[site_id] = []
                sites_areas[site_id].append(item["name"])
            
            # 检查每个工地内是否有重复名称
            for site_id, names in sites_areas.items():
                if len(names) != len(set(names)):
                    duplicates = [name for name in names if names.count(name) > 1]
                    pytest.fail(f"工地 {site_id} 中发现重复的区域名称: {set(duplicates)}")
            
            print(f"  ✓ 区域名称在各工地内无重复")
    
    def test_uuid_format_in_responses(self, client):
        """测试: 所有ID字段应该是有效的UUID格式"""
        # 测试作业票列表
        resp = client.get("/work-tickets", params={"page": 1, "page_size": 5})
        assert resp.status_code == 200
        
        data = resp.json()
        if data.get("code") == 0 and data["data"]["items"]:
            for item in data["data"]["items"]:
                ticket_id = item.get("ticket_id")
                try:
                    uuid.UUID(ticket_id)
                except (ValueError, TypeError, AttributeError):
                    pytest.fail(f"ticket_id不是有效的UUID: {ticket_id}")
            
            print(f"  ✓ 所有ticket_id都是有效的UUID格式")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])

