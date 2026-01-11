"""
性能测试脚本
"""
import pytest
import requests
import time
import statistics
from datetime import datetime

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


def measure_response_time(func, iterations=10):
    """测量响应时间"""
    times = []
    
    for _ in range(iterations):
        start = time.time()
        func()
        end = time.time()
        times.append((end - start) * 1000)  # 转换为毫秒
    
    return {
        "min": min(times),
        "max": max(times),
        "avg": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0
    }


class TestAPIPerformance:
    """API性能测试"""
    
    def test_login_performance(self):
        """测试: 登录接口性能"""
        print("\n  === 登录接口性能测试 ===")
        
        def login():
            requests.post(
                f"{ADMIN_BASE}/auth/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
            )
        
        stats = measure_response_time(login, iterations=20)
        
        print(f"  - 最小响应时间: {stats['min']:.2f}ms")
        print(f"  - 最大响应时间: {stats['max']:.2f}ms")
        print(f"  - 平均响应时间: {stats['avg']:.2f}ms")
        print(f"  - 中位数: {stats['median']:.2f}ms")
        print(f"  - 标准差: {stats['stdev']:.2f}ms")
        
        # 断言：平均响应时间应该小于500ms
        assert stats['avg'] < 500, f"登录接口响应时间过慢: {stats['avg']:.2f}ms"
    
    def test_ticket_list_performance(self, client):
        """测试: 作业票列表接口性能"""
        print("\n  === 作业票列表性能测试 ===")
        
        def get_tickets():
            client.get("/work-tickets", params={"page": 1, "page_size": 20})
        
        stats = measure_response_time(get_tickets, iterations=20)
        
        print(f"  - 最小响应时间: {stats['min']:.2f}ms")
        print(f"  - 最大响应时间: {stats['max']:.2f}ms")
        print(f"  - 平均响应时间: {stats['avg']:.2f}ms")
        print(f"  - 中位数: {stats['median']:.2f}ms")
        print(f"  - 标准差: {stats['stdev']:.2f}ms")
        
        # 断言：平均响应时间应该小于300ms
        assert stats['avg'] < 300, f"列表接口响应时间过慢: {stats['avg']:.2f}ms"
    
    def test_dashboard_performance(self, client):
        """测试: Dashboard接口性能"""
        print("\n  === Dashboard性能测试 ===")
        
        def get_dashboard():
            client.get("/reports/dashboard")
        
        stats = measure_response_time(get_dashboard, iterations=20)
        
        print(f"  - 最小响应时间: {stats['min']:.2f}ms")
        print(f"  - 最大响应时间: {stats['max']:.2f}ms")
        print(f"  - 平均响应时间: {stats['avg']:.2f}ms")
        print(f"  - 中位数: {stats['median']:.2f}ms")
        print(f"  - 标准差: {stats['stdev']:.2f}ms")
        
        # Dashboard可能需要聚合多个数据源，允许稍慢
        assert stats['avg'] < 1000, f"Dashboard接口响应时间过慢: {stats['avg']:.2f}ms"
    
    def test_concurrent_requests(self, client):
        """测试: 并发请求性能"""
        print("\n  === 并发请求测试 ===")
        
        import concurrent.futures
        
        def make_request():
            start = time.time()
            resp = client.get("/work-tickets", params={"page": 1, "page_size": 10})
            elapsed = (time.time() - start) * 1000
            return elapsed, resp.status_code
        
        # 并发10个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        times = [r[0] for r in results]
        statuses = [r[1] for r in results]
        
        print(f"  - 并发请求数: 10")
        print(f"  - 成功请求: {sum(1 for s in statuses if s == 200)}/10")
        print(f"  - 平均响应时间: {statistics.mean(times):.2f}ms")
        print(f"  - 最慢响应: {max(times):.2f}ms")
        
        # 所有请求都应该成功
        assert all(s == 200 for s in statuses), "并发请求应该全部成功"
        
        # 平均响应时间不应该太慢
        assert statistics.mean(times) < 1000, "并发请求响应时间过慢"


class TestDatabasePerformance:
    """数据库查询性能测试"""
    
    def test_large_result_set(self, client):
        """测试: 大结果集查询"""
        print("\n  === 大结果集查询测试 ===")
        
        # 请求大量数据
        start = time.time()
        resp = client.get("/work-tickets", params={"page": 1, "page_size": 100})
        elapsed = (time.time() - start) * 1000
        
        print(f"  - 查询100条记录耗时: {elapsed:.2f}ms")
        
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        
        # 即使请求100条，也应该在合理时间内返回
        assert elapsed < 1000, f"大结果集查询过慢: {elapsed:.2f}ms"
    
    def test_complex_filter_query(self, client):
        """测试: 复杂筛选查询"""
        print("\n  === 复杂筛选查询测试 ===")
        
        # 获取施工单位选项
        resp_options = client.get("/contractors/options")
        if resp_options.status_code != 200:
            pytest.skip("无法获取施工单位数据")
        
        options = resp_options.json()["data"]
        if not options:
            pytest.skip("没有施工单位数据")
        
        contractor_id = options[0]["id"]
        
        # 复杂筛选查询
        start = time.time()
        resp = client.get("/work-tickets", params={
            "page": 1,
            "page_size": 20,
            "contractor_id": contractor_id,
            "status": "IN_PROGRESS",
            "keyword": "焊接",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31"
        })
        elapsed = (time.time() - start) * 1000
        
        print(f"  - 复杂筛选查询耗时: {elapsed:.2f}ms")
        
        assert resp.status_code == 200
        
        # 复杂查询也应该快速
        assert elapsed < 500, f"复杂筛选查询过慢: {elapsed:.2f}ms"


class TestCachePerformance:
    """缓存性能测试"""
    
    def test_repeated_requests(self, client):
        """测试: 重复请求（测试缓存效果）"""
        print("\n  === 重复请求测试（缓存） ===")
        
        # 第一次请求（冷启动）
        start = time.time()
        resp1 = client.get("/contractors/options")
        cold_time = (time.time() - start) * 1000
        
        # 重复10次相同请求
        warm_times = []
        for _ in range(10):
            start = time.time()
            client.get("/contractors/options")
            warm_times.append((time.time() - start) * 1000)
        
        avg_warm_time = statistics.mean(warm_times)
        
        print(f"  - 冷启动响应时间: {cold_time:.2f}ms")
        print(f"  - 预热后平均响应时间: {avg_warm_time:.2f}ms")
        print(f"  - 性能提升: {((cold_time - avg_warm_time) / cold_time * 100):.1f}%")
        
        # 预热后的请求通常会更快（如果有缓存）
        # 但不强制要求，因为可能没有实现缓存


class TestMemoryLeak:
    """内存泄漏测试"""
    
    def test_many_sequential_requests(self, client):
        """测试: 大量连续请求（检测内存泄漏）"""
        print("\n  === 内存泄漏测试 ===")
        
        print("  - 执行1000次连续请求...")
        
        start_time = time.time()
        error_count = 0
        
        for i in range(1000):
            try:
                resp = client.get("/work-tickets", params={"page": 1, "page_size": 10})
                if resp.status_code != 200:
                    error_count += 1
            except Exception as e:
                error_count += 1
                print(f"    请求#{i+1}失败: {e}")
        
        total_time = time.time() - start_time
        
        print(f"  - 总耗时: {total_time:.2f}秒")
        print(f"  - 平均每请求: {(total_time/1000)*1000:.2f}ms")
        print(f"  - 错误数: {error_count}/1000")
        
        # 错误率应该很低
        assert error_count < 10, f"错误率过高: {error_count}/1000"
        
        # 平均响应时间不应该随时间显著增加（内存泄漏的迹象）
        assert (total_time / 1000) * 1000 < 500, "平均响应时间过慢，可能存在内存泄漏"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])

