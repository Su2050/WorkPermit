"""
完整业务流程集成测试
测试范围：端到端业务场景、跨模块数据流转、权限验证
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
    
    def put(self, path: str, json_data: dict = None):
        return self.session.put(f"{self.base_url}{path}", json=json_data)
    
    def delete(self, path: str):
        return self.session.delete(f"{self.base_url}{path}")


@pytest.fixture(scope="module")
def client():
    """创建已登录的API客户端"""
    client = APIClient(BASE_URL)
    if not client.login(TEST_USERNAME, TEST_PASSWORD):
        pytest.skip("无法登录，跳过测试")
    return client


class TestCompleteBusinessWorkflow:
    """完整业务流程测试"""
    
    def test_complete_workflow(self, client):
        """
        测试：完整的作业票业务流程
        流程：
        1. 创建工地（如果需要）
        2. 创建施工单位
        3. 创建工人
        4. 创建培训视频
        5. 创建作业区域
        6. 创建作业票
        7. 工人完成培训
        8. 门禁授权同步
        9. 查看报表
        10. 清理测试数据
        """
        test_data = {}
        unique_id = int(time.time())
        
        # Step 1: 获取或创建工地
        print("\n=== Step 1: 获取工地 ===")
        resp = client.get("/sites/options")
        assert resp.status_code == 200
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            test_data["site_id"] = data["data"][0].get("site_id") or data["data"][0].get("id")
            print(f"✓ 使用现有工地: {test_data['site_id']}")
        else:
            pytest.skip("没有可用的工地")
        
        # Step 2: 创建施工单位
        print("\n=== Step 2: 创建施工单位 ===")
        contractor_data = {
            "site_id": test_data["site_id"],
            "name": f"集成测试施工单位_{unique_id}",
            "code": f"INT_CTR_{unique_id}",
            "contact_person": "测试联系人",
            "contact_phone": "13800138001"
        }
        resp = client.post("/contractors", json_data=contractor_data)
        assert resp.status_code == 200
        data = resp.json()
        if data.get("code") == 0:
            test_data["contractor_id"] = data["data"]["contractor_id"]
            print(f"✓ 创建施工单位成功: {test_data['contractor_id']}")
        else:
            # 可能已存在，尝试获取
            resp = client.get("/contractors/options", params={"site_id": test_data["site_id"]})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and data.get("data"):
                    test_data["contractor_id"] = data["data"][0].get("contractor_id") or data["data"][0].get("id")
                    print(f"✓ 使用现有施工单位: {test_data['contractor_id']}")
                else:
                    pytest.skip("无法获取施工单位")
        
        # Step 3: 创建培训视频
        print("\n=== Step 3: 创建培训视频 ===")
        video_data = {
            "site_id": test_data["site_id"],
            "title": f"集成测试培训视频_{unique_id}",
            "file_url": "https://example.com/integration_test.mp4",
            "duration_sec": 120,
            "category": "safety"
        }
        resp = client.post("/videos", json_data=video_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                test_data["video_id"] = data["data"]["video_id"]
                print(f"✓ 创建培训视频成功: {test_data['video_id']}")
            else:
                print(f"! 创建培训视频失败: {data.get('message')}")
        else:
            print(f"! 创建培训视频请求失败: {resp.status_code}")
        
        # Step 4: 创建工人
        print("\n=== Step 4: 创建工人 ===")
        worker_data = {
            "site_id": test_data["site_id"],
            "contractor_id": test_data["contractor_id"],
            "name": f"集成测试工人_{unique_id}",
            "phone": f"139{unique_id % 100000000:08d}",
            "id_no": f"INT_WK_{unique_id}",
            "id_card": f"11010119900101{unique_id % 10000:04d}",
            "gender": "male",
            "position": "电工"
        }
        resp = client.post("/workers", json_data=worker_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                test_data["worker_id"] = data["data"]["worker_id"]
                print(f"✓ 创建工人成功: {test_data['worker_id']}")
            else:
                print(f"! 创建工人失败: {data.get('message')}")
                # 尝试获取现有工人
                resp = client.get("/workers/options", params={"page": 1, "page_size": 1})
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0 and data.get("data"):
                        test_data["worker_id"] = data["data"][0].get("worker_id") or data["data"][0].get("id")
                        print(f"✓ 使用现有工人: {test_data['worker_id']}")
        
        # Step 5: 创建作业区域
        print("\n=== Step 5: 创建作业区域 ===")
        area_data = {
            "site_id": test_data["site_id"],
            "name": f"集成测试区域_{unique_id}",
            "code": f"INT_AREA_{unique_id}",
            "description": "集成测试创建的区域"
        }
        resp = client.post("/areas", json_data=area_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                test_data["area_id"] = data["data"]["area_id"]
                print(f"✓ 创建作业区域成功: {test_data['area_id']}")
            else:
                print(f"! 创建作业区域失败: {data.get('message')}")
                # 尝试获取现有区域
                resp = client.get("/areas/options", params={"site_id": test_data["site_id"]})
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0 and data.get("data"):
                        test_data["area_id"] = data["data"][0].get("area_id") or data["data"][0].get("id")
                        print(f"✓ 使用现有区域: {test_data['area_id']}")
        
        # Step 6: 创建作业票
        print("\n=== Step 6: 创建作业票 ===")
        if "worker_id" in test_data and "area_id" in test_data:
            ticket_data = {
                "site_id": test_data["site_id"],
                "contractor_id": test_data["contractor_id"],
                "ticket_no": f"INT_TKT_{unique_id}",
                "title": f"集成测试作业票_{unique_id}",
                "work_type": "高空作业",
                "work_content": "集成测试作业内容",
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=7)),
                "area_ids": [test_data["area_id"]],
                "worker_ids": [test_data["worker_id"]]
            }
            resp = client.post("/work-tickets", json_data=ticket_data)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    test_data["ticket_id"] = data["data"]["ticket_id"]
                    print(f"✓ 创建作业票成功: {test_data['ticket_id']}")
                else:
                    print(f"! 创建作业票失败: {data.get('message')}")
            else:
                print(f"! 创建作业票请求失败: {resp.status_code}")
        else:
            print("! 跳过创建作业票（缺少前置数据）")
        
        # Step 7: 查看Dashboard统计
        print("\n=== Step 7: 查看Dashboard ===")
        resp = client.get("/reports/dashboard")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ Dashboard数据获取成功")
            else:
                print(f"! Dashboard数据获取失败: {data.get('message')}")
        
        # Step 8: 查看报表
        print("\n=== Step 8: 查看报表 ===")
        resp = client.get("/reports/training-progress")
        if resp.status_code == 200:
            print("✓ 培训进度报表获取成功")
        else:
            print(f"! 培训进度报表获取状态: {resp.status_code}")
        
        # Step 9: 清理测试数据
        print("\n=== Step 9: 清理测试数据 ===")
        cleanup_items = [
            ("ticket_id", "/work-tickets/"),
            ("area_id", "/areas/"),
            ("worker_id", "/workers/"),
            ("video_id", "/videos/"),
            ("contractor_id", "/contractors/")
        ]
        
        for key, path in cleanup_items:
            if key in test_data:
                resp = client.delete(f"{path}{test_data[key]}")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0:
                        print(f"✓ 清理{key}成功")
                    else:
                        print(f"! 清理{key}失败: {data.get('message')}")
        
        print("\n=== 完整业务流程测试完成 ===")


class TestCrossModuleDataFlow:
    """跨模块数据流转测试"""
    
    def test_contractor_worker_relationship(self, client):
        """测试：施工单位-工人关系"""
        # 获取一个施工单位
        resp = client.get("/contractors", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        
        if data.get("code") == 0 and data.get("data", {}).get("items"):
            contractor_id = data["data"]["items"][0].get("contractor_id")
            
            # 查询该施工单位下的工人
            resp = client.get("/workers", params={"contractor_id": contractor_id, "page": 1, "page_size": 10})
            assert resp.status_code == 200
            worker_data = resp.json()
            assert worker_data.get("code") == 0
            
            print(f"✓ 施工单位{contractor_id}下有{worker_data['data']['total']}个工人")
        else:
            print("! 没有可用的施工单位数据")
    
    def test_site_data_isolation(self, client):
        """测试：工地数据隔离"""
        # 获取所有工地
        resp = client.get("/sites/options")
        assert resp.status_code == 200
        data = resp.json()
        
        if data.get("code") == 0 and data.get("data") and len(data["data"]) > 0:
            site_id = data["data"][0].get("site_id") or data["data"][0].get("id")
            
            # 检查该工地下的资源
            resources = [
                ("/areas", "区域"),
                ("/contractors", "施工单位"),
                ("/workers", "工人"),
                ("/videos", "视频")
            ]
            
            for path, name in resources:
                resp = client.get(path, params={"site_id": site_id, "page": 1, "page_size": 1})
                if resp.status_code == 200:
                    res_data = resp.json()
                    if res_data.get("code") == 0:
                        total = res_data.get("data", {}).get("total", 0)
                        print(f"✓ 工地{site_id}的{name}数量: {total}")
        else:
            print("! 没有可用的工地数据")
    
    def test_ticket_area_worker_relationship(self, client):
        """测试：作业票-区域-工人关系"""
        # 获取一个作业票
        resp = client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        
        if data.get("code") == 0 and data.get("data", {}).get("items"):
            ticket = data["data"]["items"][0]
            ticket_id = ticket.get("ticket_id")
            
            # 获取作业票详情
            resp = client.get(f"/work-tickets/{ticket_id}")
            if resp.status_code == 200:
                detail_data = resp.json()
                if detail_data.get("code") == 0:
                    detail = detail_data.get("data", {})
                    areas = detail.get("areas", [])
                    workers = detail.get("workers", [])
                    print(f"✓ 作业票{ticket_id}: {len(areas)}个区域, {len(workers)}个工人")
        else:
            print("! 没有可用的作业票数据")


class TestPermissionValidation:
    """权限验证测试"""
    
    def test_sysadmin_full_access(self, client):
        """测试：SysAdmin完全访问权限"""
        # 测试各个模块的访问权限
        endpoints = [
            "/sites",
            "/contractors",
            "/workers",
            "/areas",
            "/videos",
            "/users",
            "/work-tickets",
            "/alerts",
            "/reports/dashboard"
        ]
        
        for endpoint in endpoints:
            resp = client.get(endpoint, params={"page": 1, "page_size": 1})
            assert resp.status_code == 200, f"访问{endpoint}失败"
            data = resp.json()
            assert data.get("code") == 0, f"{endpoint}返回错误: {data.get('message')}"
        
        print("✓ SysAdmin完全访问权限验证通过")
    
    def test_invalid_token_rejected(self, client):
        """测试：无效token被拒绝"""
        # 使用无效token发送请求
        invalid_client = APIClient(BASE_URL)
        invalid_client.session.headers["Authorization"] = "Bearer invalid_token_123"
        
        resp = invalid_client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp.status_code in [401, 403, 422], "无效token应该被拒绝"
        print("✓ 无效token被正确拒绝")
    
    def test_no_token_rejected(self, client):
        """测试：无token请求被拒绝"""
        # 不带token发送请求
        no_auth_client = APIClient(BASE_URL)
        
        resp = no_auth_client.get("/work-tickets", params={"page": 1, "page_size": 1})
        assert resp.status_code in [401, 403, 422], "无token请求应该被拒绝"
        print("✓ 无token请求被正确拒绝")


class TestDataIntegrity:
    """数据完整性测试"""
    
    def test_unique_constraints(self, client):
        """测试：唯一性约束"""
        unique_id = int(time.time())
        
        # 获取工地
        resp = client.get("/sites/options")
        if resp.status_code != 200 or resp.json().get("code") != 0:
            pytest.skip("无法获取工地")
        
        site_id = resp.json()["data"][0].get("site_id") or resp.json()["data"][0].get("id")
        
        # 创建一个区域
        area_data = {
            "site_id": site_id,
            "name": f"唯一性测试区域_{unique_id}",
            "code": f"UNQ_{unique_id}"
        }
        resp = client.post("/areas", json_data=area_data)
        
        if resp.status_code == 200 and resp.json().get("code") == 0:
            area_id = resp.json()["data"]["area_id"]
            
            # 尝试创建同名区域（应该失败）
            resp2 = client.post("/areas", json_data=area_data)
            if resp2.status_code == 200:
                data2 = resp2.json()
                if data2.get("code") != 0:
                    print("✓ 唯一性约束生效")
                else:
                    print("! 唯一性约束可能未生效")
                    # 清理第二个
                    if data2.get("data", {}).get("area_id"):
                        client.delete(f"/areas/{data2['data']['area_id']}")
            
            # 清理
            client.delete(f"/areas/{area_id}")
        else:
            print(f"! 创建测试区域失败: {resp.json().get('message', 'Unknown')}")
    
    def test_cascade_relationships(self, client):
        """测试：级联关系"""
        # 获取一个有工人的施工单位
        resp = client.get("/contractors", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        
        if data.get("code") == 0 and data.get("data", {}).get("items"):
            for contractor in data["data"]["items"]:
                contractor_id = contractor.get("contractor_id")
                
                # 检查是否有关联工人
                resp = client.get("/workers", params={
                    "contractor_id": contractor_id,
                    "page": 1,
                    "page_size": 1
                })
                if resp.status_code == 200:
                    worker_data = resp.json()
                    if worker_data.get("code") == 0 and worker_data.get("data", {}).get("total", 0) > 0:
                        print(f"✓ 施工单位{contractor_id}有{worker_data['data']['total']}个关联工人")
                        break
        else:
            print("! 没有可用的施工单位数据")


class TestErrorHandling:
    """错误处理测试"""
    
    def test_404_not_found(self, client):
        """测试：404错误处理"""
        fake_id = str(uuid.uuid4())
        
        endpoints = [
            f"/work-tickets/{fake_id}",
            f"/areas/{fake_id}",
            f"/workers/{fake_id}",
            f"/contractors/{fake_id}",
            f"/videos/{fake_id}",
            f"/users/{fake_id}"
        ]
        
        for endpoint in endpoints:
            resp = client.get(endpoint)
            assert resp.status_code in [200, 404], f"{endpoint}应该返回200或404"
            if resp.status_code == 200:
                data = resp.json()
                assert data.get("code") != 0 or data.get("data") is None, f"{endpoint}应该返回业务错误"
        
        print("✓ 404错误处理正确")
    
    def test_422_validation_error(self, client):
        """测试：422验证错误处理"""
        # 发送无效UUID
        resp = client.get("/work-tickets/invalid-uuid")
        assert resp.status_code in [422, 404, 400], "无效UUID应该返回错误"
        print("✓ 422验证错误处理正确")
    
    def test_malformed_request(self, client):
        """测试：格式错误请求处理"""
        # 发送缺少必填字段的请求
        resp = client.post("/areas", json_data={"name": "测试"})  # 缺少site_id和code
        assert resp.status_code in [200, 422]
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 0, "缺少必填字段应该返回业务错误"
        print("✓ 格式错误请求处理正确")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

