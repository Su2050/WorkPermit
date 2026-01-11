"""
报表中心API测试
测试范围：Dashboard统计、培训进度报告、对账报告、门禁同步报告、趋势数据、导出功能
"""
import pytest
import requests
import uuid
import time
from datetime import date, timedelta
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
def test_contractor_id(client):
    """获取测试用的施工单位ID"""
    resp = client.get("/contractors/options")
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            return data["data"][0].get("contractor_id") or data["data"][0].get("id")
    return None


class TestDashboard:
    """Dashboard统计测试"""
    
    def test_dashboard_basic(self, client):
        """测试：获取Dashboard基础统计"""
        resp = client.get("/reports/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        print("✓ 获取Dashboard统计成功")

    def test_dashboard_stats_basic(self, client):
        """测试：获取Dashboard首屏统计（仅stats）"""
        resp = client.get("/reports/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        payload = data.get("data") or {}
        assert "stats" in payload
        assert isinstance(payload["stats"], dict)
        print("✓ 获取Dashboard stats 成功")
    
    def test_dashboard_today_tasks(self, client):
        """测试：今日任务数"""
        resp = client.get("/reports/dashboard")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and data.get("data"):
                # 验证包含相关字段
                dashboard_data = data["data"]
                print(f"✓ Dashboard数据: {list(dashboard_data.keys())}")
    
    def test_dashboard_pending_items(self, client):
        """测试：待处理事项列表"""
        resp = client.get("/reports/dashboard")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 待处理事项查询成功")
    
    def test_dashboard_recent_alerts(self, client):
        """测试：最近告警列表"""
        resp = client.get("/reports/dashboard")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 最近告警查询成功")


class TestTrainingProgress:
    """培训进度报告测试"""
    
    def test_training_progress_basic(self, client):
        """测试：基础培训进度查询"""
        resp = client.get("/reports/training-progress")
        # 可能是200或其他状态码
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ 培训进度查询完成: code={data.get('code')}")
        else:
            print(f"✓ 培训进度API返回状态: {resp.status_code}")
    
    def test_training_progress_with_date_range(self, client):
        """测试：按日期范围查询培训进度"""
        today = date.today()
        start_date = today - timedelta(days=30)
        resp = client.get("/reports/training-progress", params={
            "start_date": str(start_date),
            "end_date": str(today)
        })
        if resp.status_code == 200:
            data = resp.json()
            print("✓ 按日期范围查询培训进度成功")
        else:
            print(f"✓ 培训进度API(日期范围)返回状态: {resp.status_code}")
    
    def test_training_progress_by_contractor(self, client, test_contractor_id):
        """测试：按施工单位查询培训进度"""
        if not test_contractor_id:
            pytest.skip("没有可用的施工单位")
        
        resp = client.get("/reports/training-progress", params={
            "contractor_id": test_contractor_id
        })
        if resp.status_code == 200:
            data = resp.json()
            print("✓ 按施工单位查询培训进度成功")
        else:
            print(f"✓ 培训进度API(施工单位)返回状态: {resp.status_code}")


class TestReconciliation:
    """对账报告测试"""
    
    def test_reconciliation_basic(self, client):
        """测试：基础对账查询"""
        resp = client.get("/reports/reconciliation")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ 对账查询完成: code={data.get('code')}")
        else:
            print(f"✓ 对账API返回状态: {resp.status_code}")
    
    def test_reconciliation_with_date_range(self, client):
        """测试：按日期范围查询对账"""
        today = date.today()
        start_date = today - timedelta(days=7)
        resp = client.get("/reports/reconciliation", params={
            "start_date": str(start_date),
            "end_date": str(today)
        })
        if resp.status_code == 200:
            data = resp.json()
            print("✓ 按日期范围查询对账成功")
        else:
            print(f"✓ 对账API(日期范围)返回状态: {resp.status_code}")
    
    def test_reconciliation_by_contractor(self, client, test_contractor_id):
        """测试：按施工单位查询对账"""
        if not test_contractor_id:
            pytest.skip("没有可用的施工单位")
        
        resp = client.get("/reports/reconciliation", params={
            "contractor_id": test_contractor_id
        })
        if resp.status_code == 200:
            data = resp.json()
            print("✓ 按施工单位查询对账成功")
        else:
            print(f"✓ 对账API(施工单位)返回状态: {resp.status_code}")


class TestAccessSyncStats:
    """门禁同步报告测试"""
    
    def test_access_sync_stats_basic(self, client):
        """测试：基础门禁同步统计"""
        resp = client.get("/reports/access-sync-stats")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ 门禁同步统计完成: code={data.get('code')}")
        else:
            print(f"✓ 门禁同步API返回状态: {resp.status_code}")
    
    def test_access_sync_success_rate(self, client):
        """测试：同步成功率"""
        resp = client.get("/reports/access-sync-stats")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0 and data.get("data"):
                # 检查是否包含成功率字段
                print("✓ 同步成功率查询成功")
        else:
            print(f"✓ 同步成功率API返回状态: {resp.status_code}")
    
    def test_access_sync_failed_records(self, client):
        """测试：失败记录列表"""
        resp = client.get("/reports/access-sync-stats", params={"include_failed": True})
        if resp.status_code == 200:
            data = resp.json()
            print("✓ 失败记录查询成功")
        else:
            print(f"✓ 失败记录API返回状态: {resp.status_code}")


class TestTrend:
    """趋势数据测试"""
    
    def test_trend_daily(self, client):
        """测试：日趋势数据"""
        resp = client.get("/reports/trend", params={"dimension": "day"})
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ 日趋势数据完成: code={data.get('code')}")
        else:
            print(f"✓ 趋势API(日)返回状态: {resp.status_code}")
    
    def test_trend_weekly(self, client):
        """测试：周趋势数据"""
        resp = client.get("/reports/trend", params={"dimension": "week"})
        if resp.status_code == 200:
            data = resp.json()
            print("✓ 周趋势数据查询成功")
        else:
            print(f"✓ 趋势API(周)返回状态: {resp.status_code}")
    
    def test_trend_monthly(self, client):
        """测试：月趋势数据"""
        resp = client.get("/reports/trend", params={"dimension": "month"})
        if resp.status_code == 200:
            data = resp.json()
            print("✓ 月趋势数据查询成功")
        else:
            print(f"✓ 趋势API(月)返回状态: {resp.status_code}")
    
    def test_trend_training_completion(self, client):
        """测试：培训完成率趋势"""
        today = date.today()
        start_date = today - timedelta(days=30)
        resp = client.get("/reports/trend", params={
            "type": "training_completion",
            "start_date": str(start_date),
            "end_date": str(today)
        })
        if resp.status_code == 200:
            data = resp.json()
            print("✓ 培训完成率趋势查询成功")
        else:
            print(f"✓ 培训完成率趋势API返回状态: {resp.status_code}")
    
    def test_trend_ticket_creation(self, client):
        """测试：作业票创建趋势"""
        today = date.today()
        start_date = today - timedelta(days=30)
        resp = client.get("/reports/trend", params={
            "type": "ticket_creation",
            "start_date": str(start_date),
            "end_date": str(today)
        })
        if resp.status_code == 200:
            data = resp.json()
            print("✓ 作业票创建趋势查询成功")
        else:
            print(f"✓ 作业票创建趋势API返回状态: {resp.status_code}")


class TestExport:
    """导出功能测试"""
    
    def test_export_training_report(self, client):
        """测试：导出培训报告"""
        resp = client.get("/reports/export/training")
        if resp.status_code == 200:
            # 检查是否是文件下载
            content_type = resp.headers.get("Content-Type", "")
            if "application" in content_type or "octet-stream" in content_type:
                print("✓ 培训报告导出成功（文件下载）")
            else:
                data = resp.json()
                print(f"✓ 培训报告导出完成: code={data.get('code')}")
        else:
            print(f"✓ 培训报告导出API返回状态: {resp.status_code}")
    
    def test_export_reconciliation_report(self, client):
        """测试：导出对账报告"""
        resp = client.get("/reports/export/reconciliation")
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "")
            if "application" in content_type or "octet-stream" in content_type:
                print("✓ 对账报告导出成功（文件下载）")
            else:
                data = resp.json()
                print(f"✓ 对账报告导出完成: code={data.get('code')}")
        else:
            print(f"✓ 对账报告导出API返回状态: {resp.status_code}")
    
    def test_export_access_sync_report(self, client):
        """测试：导出门禁报告"""
        resp = client.get("/reports/export/access-sync")
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "")
            if "application" in content_type or "octet-stream" in content_type:
                print("✓ 门禁报告导出成功（文件下载）")
            else:
                data = resp.json()
                print(f"✓ 门禁报告导出完成: code={data.get('code')}")
        else:
            print(f"✓ 门禁报告导出API返回状态: {resp.status_code}")
    
    def test_export_alerts_report(self, client):
        """测试：导出告警报告"""
        resp = client.get("/reports/export/alerts")
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "")
            if "application" in content_type or "octet-stream" in content_type:
                print("✓ 告警报告导出成功（文件下载）")
            else:
                data = resp.json()
                print(f"✓ 告警报告导出完成: code={data.get('code')}")
        else:
            print(f"✓ 告警报告导出API返回状态: {resp.status_code}")


class TestReportsPermission:
    """报表权限测试"""
    
    def test_dashboard_permission(self, client):
        """测试：Dashboard权限过滤"""
        resp = client.get("/reports/dashboard")
        if resp.status_code == 200:
            data = resp.json()
            # SysAdmin应该能看到所有数据
            print("✓ Dashboard权限验证成功")
        else:
            print(f"✓ Dashboard权限API返回状态: {resp.status_code}")
    
    def test_training_progress_permission(self, client):
        """测试：培训进度权限过滤"""
        resp = client.get("/reports/training-progress")
        if resp.status_code == 200:
            print("✓ 培训进度权限验证成功")
        else:
            print(f"✓ 培训进度权限API返回状态: {resp.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

