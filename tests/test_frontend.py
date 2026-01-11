"""
前端功能测试脚本（API层面）
"""
import requests

BASE_URL = "http://localhost:5173"
API_BASE = "http://localhost:8000/api/admin"

def test_frontend_api_endpoints():
    """测试前端调用的API端点"""
    print("\n" + "=" * 60)
    print("前端API端点测试")
    print("=" * 60)
    
    # 登录获取token
    login_resp = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    test_cases = [
        {
            "name": "Dashboard API",
            "url": f"{API_BASE}/reports/dashboard",
            "method": "GET"
        },
        {
            "name": "作业票列表API",
            "url": f"{API_BASE}/work-tickets",
            "method": "GET",
            "params": {"page": 1, "page_size": 20}
        },
        {
            "name": "施工单位选项API",
            "url": f"{API_BASE}/contractors/options",
            "method": "GET"
        },
        {
            "name": "区域列表API",
            "url": f"{API_BASE}/areas",
            "method": "GET",
            "params": {"page": 1, "page_size": 20}
        },
        {
            "name": "视频列表API",
            "url": f"{API_BASE}/videos",
            "method": "GET",
            "params": {"page": 1, "page_size": 20}
        },
    ]
    
    results = []
    for case in test_cases:
        try:
            if case["method"] == "GET":
                resp = requests.get(case["url"], headers=headers, params=case.get("params"))
            else:
                resp = requests.post(case["url"], headers=headers, json=case.get("params"))
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    print(f"  ✓ {case['name']}: 通过")
                    results.append({"name": case["name"], "status": "PASS"})
                else:
                    print(f"  ✗ {case['name']}: 业务错误 - {data.get('message')}")
                    results.append({"name": case["name"], "status": "FAIL", "error": data.get("message")})
            else:
                print(f"  ✗ {case['name']}: HTTP {resp.status_code}")
                results.append({"name": case["name"], "status": "FAIL", "error": f"HTTP {resp.status_code}"})
        except Exception as e:
            print(f"  ✗ {case['name']}: 异常 - {str(e)}")
            results.append({"name": case["name"], "status": "FAIL", "error": str(e)})
    
    return results

def test_filter_functionality():
    """测试筛选功能"""
    print("\n" + "=" * 60)
    print("筛选功能测试")
    print("=" * 60)
    
    # 登录获取token
    login_resp = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取施工单位选项
    resp_options = requests.get(f"{API_BASE}/contractors/options", headers=headers)
    assert resp_options.status_code == 200
    options = resp_options.json()["data"]
    
    if not options:
        print("  ⚠ 没有施工单位数据，跳过筛选测试")
        return []
    
    contractor_id = options[0]["id"]
    
    test_cases = [
        {
            "name": "按施工单位筛选",
            "params": {"contractor_id": contractor_id}
        },
        {
            "name": "按状态筛选",
            "params": {"status": "IN_PROGRESS"}
        },
        {
            "name": "关键词搜索",
            "params": {"keyword": "焊接"}
        },
        {
            "name": "组合筛选",
            "params": {"contractor_id": contractor_id, "status": "IN_PROGRESS"}
        }
    ]
    
    results = []
    for case in test_cases:
        try:
            resp = requests.get(
                f"{API_BASE}/work-tickets",
                headers=headers,
                params={"page": 1, "page_size": 20, **case["params"]}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    count = len(data["data"]["items"])
                    print(f"  ✓ {case['name']}: 通过 (返回 {count} 条)")
                    results.append({"name": case["name"], "status": "PASS", "count": count})
                else:
                    print(f"  ✗ {case['name']}: 业务错误")
                    results.append({"name": case["name"], "status": "FAIL"})
            else:
                print(f"  ✗ {case['name']}: HTTP {resp.status_code}")
                results.append({"name": case["name"], "status": "FAIL"})
        except Exception as e:
            print(f"  ✗ {case['name']}: 异常 - {str(e)}")
            results.append({"name": case["name"], "status": "FAIL"})
    
    return results

if __name__ == "__main__":
    print("前端功能测试")
    print("=" * 60)
    
    # 测试API端点
    api_results = test_frontend_api_endpoints()
    
    # 测试筛选功能
    filter_results = test_filter_functionality()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"API端点测试: {sum(1 for r in api_results if r['status'] == 'PASS')}/{len(api_results)} 通过")
    print(f"筛选功能测试: {sum(1 for r in filter_results if r['status'] == 'PASS')}/{len(filter_results)} 通过")

