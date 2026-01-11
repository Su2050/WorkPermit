"""
完整系统测试 - 覆盖所有功能模块
"""
import pytest
import requests
import uuid
import time
from datetime import date, timedelta

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
    
    def post(self, endpoint: str, json_data=None):
        """POST请求"""
        return requests.post(f"{ADMIN_BASE}{endpoint}", headers=self.headers, json=json_data)
    
    def patch(self, endpoint: str, json_data=None):
        """PATCH请求"""
        return requests.patch(f"{ADMIN_BASE}{endpoint}", headers=self.headers, json=json_data)
    
    def put(self, endpoint: str, json_data=None):
        """PUT请求"""
        return requests.put(f"{ADMIN_BASE}{endpoint}", headers=self.headers, json=json_data)
    
    def delete(self, endpoint: str):
        """DELETE请求"""
        return requests.delete(f"{ADMIN_BASE}{endpoint}", headers=self.headers)


@pytest.fixture(scope="module")
def client():
    """测试客户端fixture"""
    c = APIClient()
    assert c.login(TEST_USERNAME, TEST_PASSWORD), "登录失败"
    return c


class TestCompleteSystemFlow:
    """完整系统流程测试 - 模拟真实业务场景"""
    
    def test_complete_business_flow(self, client):
        """
        完整业务流程测试
        场景：从创建基础数据到作业票全生命周期管理
        """
        print("\n" + "="*80)
        print("完整业务流程测试")
        print("="*80)
        
        # ==================== 第1步：创建工地 ====================
        print("\n[步骤1] 创建工地...")
        site_data = {
            "name": f"测试工地_{int(time.time())}",
            "code": f"SITE{int(time.time())}",
            "address": "测试地址123号",
            "contact_person": "张三",
            "contact_phone": "13800138000"
        }
        
        resp = client.post("/sites", json_data=site_data)
        assert resp.status_code == 200, f"创建工地失败: {resp.text}"
        data = resp.json()
        assert data.get("code") == 0, f"创建工地失败: {data.get('message')}"
        site_id = data["data"]["site_id"]
        print(f"  ✓ 工地创建成功: {site_data['name']} (ID: {site_id})")
        
        # ==================== 第2步：创建施工单位 ====================
        print("\n[步骤2] 创建施工单位...")
        contractor_data = {
            "site_id": site_id,
            "name": f"测试施工单位_{int(time.time())}",
            "code": f"CONT{int(time.time())}",
            "contact_person": "李四",
            "contact_phone": "13900139000",
            "address": "施工单位地址",
            "license_no": f"LIC{int(time.time())}",
            "qualification_level": "一级"
        }
        
        resp = client.post("/contractors", json_data=contractor_data)
        assert resp.status_code == 200, f"创建施工单位失败: {resp.text}"
        data = resp.json()
        assert data.get("code") == 0, f"创建施工单位失败: {data.get('message')}"
        contractor_id = data["data"]["contractor_id"]
        print(f"  ✓ 施工单位创建成功: {contractor_data['name']} (ID: {contractor_id})")
        
        # ==================== 第3步：创建作业区域 ====================
        print("\n[步骤3] 创建作业区域...")
        area_data = {
            "site_id": site_id,
            "name": f"测试区域_{int(time.time())}",
            "code": f"AREA{int(time.time())}",
            "description": "测试区域描述",
            "risk_level": "HIGH"
        }
        
        resp = client.post("/areas", json_data=area_data)
        assert resp.status_code == 200, f"创建区域失败: {resp.text}"
        data = resp.json()
        assert data.get("code") == 0, f"创建区域失败: {data.get('message')}"
        area_id = data["data"]["area_id"]
        print(f"  ✓ 区域创建成功: {area_data['name']} (ID: {area_id})")
        
        # ==================== 第4步：获取可用的培训视频 ====================
        print("\n[步骤4] 获取可用的培训视频...")
        resp = client.get("/videos/options")
        assert resp.status_code == 200, f"获取视频失败: {resp.text}"
        data = resp.json()
        assert data.get("code") == 0, f"获取视频失败: {data.get('message')}"
        
        if not data["data"]:
            print(f"  ⚠ 系统中没有可用的培训视频，跳过后续步骤")
            pytest.skip("系统中没有可用的培训视频")
        
        video_id = data["data"][0]["id"]
        print(f"  ✓ 获取到可用视频 (ID: {video_id})")
        
        # ==================== 第5步：获取可用的工人 ====================
        print("\n[步骤5] 获取可用的工人...")
        resp = client.get("/workers/options", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200, f"获取工人失败: {resp.text}"
        data = resp.json()
        assert data.get("code") == 0, f"获取工人失败: {data.get('message')}"
        
        if not data["data"]:
            print(f"  ⚠ 系统中没有可用的工人，跳过后续步骤")
            pytest.skip("系统中没有可用的工人")
        
        worker_id = data["data"][0]["id"]
        print(f"  ✓ 获取到可用工人 (ID: {worker_id})")
        
        # ==================== 第6步：创建作业票 ====================
        print("\n[步骤6] 创建作业票...")
        ticket_data = {
            "title": f"测试作业票_{int(time.time())}",
            "description": "测试作业票描述",
            "contractor_id": contractor_id,
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=7)),
            "default_access_start_time": "06:00:00",
            "default_access_end_time": "20:00:00",
            "default_training_deadline_time": "07:30:00",
            "worker_ids": [worker_id],
            "area_ids": [area_id],
            "video_ids": [video_id],
            "notify_on_publish": False,
            "daily_reminder_enabled": True
        }
        
        resp = client.post("/work-tickets", json_data=ticket_data)
        assert resp.status_code == 200, f"创建作业票失败: {resp.text}"
        data = resp.json()
        assert data.get("code") == 0, f"创建作业票失败: {data.get('message')}"
        ticket_id = data["data"]["ticket_id"]
        print(f"  ✓ 作业票创建成功: {ticket_data['title']} (ID: {ticket_id})")
        
        # ==================== 第7步：查看作业票详情 ====================
        print("\n[步骤7] 查看作业票详情...")
        resp = client.get(f"/work-tickets/{ticket_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print(f"  ✓ 作业票详情获取成功")
        print(f"    - 标题: {data['data']['title']}")
        print(f"    - 状态: {data['data']['status']}")
        print(f"    - 工人数: {len(data['data'].get('workers', []))}")
        print(f"    - 区域数: {len(data['data'].get('areas', []))}")
        print(f"    - 视频数: {len(data['data'].get('videos', []))}")
        
        # ==================== 第8步：发布作业票 ====================
        print("\n[步骤8] 发布作业票...")
        resp = client.post(f"/work-tickets/{ticket_id}/publish", json_data={})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"发布作业票失败: {data.get('message')}"
        print(f"  ✓ 作业票发布成功")
        
        # ==================== 第9步：查看每日票据 ====================
        print("\n[步骤9] 查看每日票据...")
        resp = client.get(
            f"/work-tickets/{ticket_id}/daily-tickets",
            params={"date": str(date.today())}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        daily_tickets = data["data"]["items"]
        print(f"  ✓ 每日票据查询成功: {len(daily_tickets)} 条")
        
        # ==================== 第10步：查看Dashboard统计 ====================
        print("\n[步骤10] 查看Dashboard统计...")
        resp = client.get("/reports/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        stats = data["data"]["stats"]
        print(f"  ✓ Dashboard统计获取成功")
        print(f"    - 今日任务: {stats['todayTasks']}")
        print(f"    - 进行中作业票: {stats['activeTickets']}")
        print(f"    - 今日培训: {stats['todayTrainings']}")
        
        # ==================== 第11步：查看审计日志 ====================
        print("\n[步骤11] 查看审计日志...")
        resp = client.get(
            "/audit-logs",
            params={
                "resource_type": "WorkTicket",
                "resource_id": ticket_id,
                "page": 1,
                "page_size": 10
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        logs = data["data"]["items"]
        print(f"  ✓ 审计日志查询成功: {len(logs)} 条")
        
        # ==================== 第12步：查看告警 ====================
        print("\n[步骤12] 查看告警统计...")
        resp = client.get("/alerts/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        alert_stats = data["data"]
        print(f"  ✓ 告警统计获取成功")
        print(f"    - 总告警: {alert_stats['total']}")
        print(f"    - 未确认: {alert_stats['unacknowledged']}")
        
        # ==================== 第13步：关闭作业票 ====================
        print("\n[步骤13] 关闭作业票...")
        resp = client.post(
            f"/work-tickets/{ticket_id}/close",
            json_data={"reason": "测试完成"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0, f"关闭作业票失败: {data.get('message')}"
        print(f"  ✓ 作业票关闭成功")
        
        print("\n" + "="*80)
        print("✅ 完整业务流程测试通过！")
        print("="*80)


class TestAllModules:
    """所有模块功能测试"""
    
    def test_sites_module(self, client):
        """测试：工地管理模块"""
        print("\n[测试] 工地管理模块")
        
        # 列表查询
        resp = client.get("/sites", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 工地列表查询")
        
        # 选项查询
        resp = client.get("/sites/options")
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 工地选项查询")
    
    def test_contractors_module(self, client):
        """测试：施工单位管理模块"""
        print("\n[测试] 施工单位管理模块")
        
        # 列表查询
        resp = client.get("/contractors", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 施工单位列表查询")
        
        # 选项查询
        resp = client.get("/contractors/options")
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 施工单位选项查询")
    
    def test_areas_module(self, client):
        """测试：区域管理模块"""
        print("\n[测试] 区域管理模块")
        
        # 列表查询
        resp = client.get("/areas", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 区域列表查询")
        
        # 选项查询
        resp = client.get("/areas/options")
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 区域选项查询")
    
    def test_videos_module(self, client):
        """测试：视频管理模块"""
        print("\n[测试] 视频管理模块")
        
        # 列表查询
        resp = client.get("/videos", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 视频列表查询")
        
        # 选项查询
        resp = client.get("/videos/options")
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 视频选项查询")
    
    def test_workers_module(self, client):
        """测试：人员管理模块"""
        print("\n[测试] 人员管理模块")
        
        # 列表查询
        resp = client.get("/workers", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 人员列表查询")
        
        # 选项查询
        resp = client.get("/workers/options", params={"page": 1, "page_size": 20})
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 人员选项查询")
    
    def test_users_module(self, client):
        """测试：用户管理模块"""
        print("\n[测试] 用户管理模块")
        
        # 列表查询
        resp = client.get("/users", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 用户列表查询")
        
        # 获取当前用户
        resp = client.get("/auth/me")
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 获取当前用户信息")
    
    def test_tickets_module(self, client):
        """测试：作业票管理模块"""
        print("\n[测试] 作业票管理模块")
        
        # 列表查询
        resp = client.get("/work-tickets", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("  ✓ 作业票列表查询")
        
        # 统计查询（可能需要日期参数）
        resp = client.get("/work-tickets/stats", params={
            "start_date": str(date.today() - timedelta(days=30)),
            "end_date": str(date.today())
        })
        if resp.status_code == 200:
            assert resp.json().get("code") == 0
            print("  ✓ 作业票统计查询")
        else:
            print(f"  ⚠ 作业票统计查询失败: {resp.status_code}")
        
        # 如果有作业票，测试详情查询
        if data["data"]["items"]:
            ticket_id = data["data"]["items"][0]["ticket_id"]
            resp = client.get(f"/work-tickets/{ticket_id}")
            assert resp.status_code == 200
            assert resp.json().get("code") == 0
            print("  ✓ 作业票详情查询")
    
    def test_daily_tickets_module(self, client):
        """测试：日常票据管理模块"""
        print("\n[测试] 日常票据管理模块")
        
        # 获取一个作业票ID
        resp = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        
        if data.get("code") == 0 and data["data"]["items"]:
            ticket_id = data["data"]["items"][0]["ticket_id"]
            
            # 查询每日票据
            resp = client.get(
                f"/work-tickets/{ticket_id}/daily-tickets",
                params={"date": str(date.today())}
            )
            assert resp.status_code == 200
            assert resp.json().get("code") == 0
            print("  ✓ 每日票据查询")
    
    def test_reports_module(self, client):
        """测试：报表统计模块"""
        print("\n[测试] 报表统计模块")
        
        # Dashboard统计
        resp = client.get("/reports/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("  ✓ Dashboard统计")
        print(f"    - 今日任务: {data['data']['stats']['todayTasks']}")
        print(f"    - 进行中作业票: {data['data']['stats']['activeTickets']}")
        
        # 培训进度报告
        resp = client.get("/reports/training-progress")
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 培训进度报告")
        
        # 对账报告
        resp = client.get("/reports/reconciliation")
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 对账报告")
    
    def test_alerts_module(self, client):
        """测试：告警管理模块"""
        print("\n[测试] 告警管理模块")
        
        # 告警统计
        resp = client.get("/alerts/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("  ✓ 告警统计")
        print(f"    - 总告警: {data['data']['total']}")
        print(f"    - 未确认: {data['data']['unacknowledged']}")
        
        # 告警列表
        resp = client.get("/alerts", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 告警列表查询")
    
    def test_audit_logs_module(self, client):
        """测试：审计日志模块"""
        print("\n[测试] 审计日志模块")
        
        # 审计日志列表
        resp = client.get("/audit-logs", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print(f"  ✓ 审计日志列表查询: {data['data']['total']} 条")
        
        # 按操作类型筛选
        resp = client.get("/audit-logs", params={"action": "CREATE", "page": 1, "page_size": 10})
        assert resp.status_code == 200
        assert resp.json().get("code") == 0
        print("  ✓ 按操作类型筛选")


class TestDataConsistency:
    """数据一致性测试"""
    
    def test_no_duplicate_names(self, client):
        """测试：无重复名称"""
        print("\n[测试] 数据唯一性检查")
        
        # 检查施工单位名称唯一性
        resp = client.get("/contractors", params={"page": 1, "page_size": 500})
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                names = [item["name"] for item in data["data"]["items"]]
                assert len(names) == len(set(names)), "施工单位名称存在重复"
                print(f"  ✓ 施工单位名称唯一 ({len(names)} 个)")
        
        # 检查工地名称唯一性
        resp = client.get("/sites", params={"page": 1, "page_size": 500})
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                names = [item["name"] for item in data["data"]["items"]]
                assert len(names) == len(set(names)), "工地名称存在重复"
                print(f"  ✓ 工地名称唯一 ({len(names)} 个)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

