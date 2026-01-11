#!/usr/bin/env python3
"""
运行测试脚本
"""
import sys
import subprocess
import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api/admin"

def check_backend_health():
    """检查后端服务是否可用"""
    try:
        resp = requests.get("http://localhost:8000/api/health", timeout=5)
        return resp.status_code == 200
    except:
        return False

def check_backend_login():
    """检查后端登录是否正常"""
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )
        return resp.status_code == 200 and resp.json().get("code") == 0
    except:
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("作业票管理系统 - 自动化测试")
    print("=" * 60)
    print()
    
    # 检查后端服务
    print("1. 检查后端服务状态...")
    if not check_backend_health():
        print("   ❌ 后端服务不可用，请先启动后端服务")
        print("   启动命令: cd backend && python run_dev.py")
        sys.exit(1)
    print("   ✓ 后端服务正常")
    
    # 检查登录
    print("\n2. 检查登录功能...")
    if not check_backend_login():
        print("   ❌ 登录失败，请检查数据库是否已初始化")
        print("   初始化命令: python backend/scripts/init_demo_data.py")
        sys.exit(1)
    print("   ✓ 登录功能正常")
    
    # 运行测试
    print("\n3. 运行测试用例...")
    print("-" * 60)
    
    test_file = Path(__file__).parent / "test_api.py"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short", "--color=yes"],
        cwd=Path(__file__).parent.parent
    )
    
    print("-" * 60)
    print("\n测试完成！")
    
    if result.returncode == 0:
        print("✓ 所有测试通过")
    else:
        print("✗ 部分测试失败")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())


