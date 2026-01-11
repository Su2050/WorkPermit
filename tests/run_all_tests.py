#!/usr/bin/env python3
"""
完整的自动化测试套件运行脚本
"""
import sys
import subprocess
import requests
import time
import argparse
from pathlib import Path
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
ADMIN_BASE = f"{BASE_URL}/admin"
FRONTEND_URL = "http://localhost:5173"


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_backend():
    """检查后端服务"""
    try:
        # 检查健康端点
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code in [200, 404]:
            # 尝试登录
            resp = requests.post(
                f"{ADMIN_BASE}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=5
            )
            return resp.status_code == 200 and resp.json().get("code") == 0
    except:
        pass
    return False


def check_frontend():
    """检查前端服务"""
    try:
        resp = requests.get(FRONTEND_URL, timeout=5)
        return resp.status_code == 200
    except:
        return False


def run_test_suite(test_name, test_file, markers=None, verbose=True):
    """运行测试套件"""
    print_header(f"运行测试: {test_name}")
    
    test_path = Path(__file__).parent / test_file
    
    # 构建pytest命令
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "-v" if verbose else "-q",
        "--tb=short",
        f"--html=reports/{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        "--self-contained-html"
    ]
    
    if markers:
        cmd.extend(["-m", markers])
    
    # 运行测试
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    
    return result.returncode == 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行自动化测试套件")
    parser.add_argument("--suite", choices=["all", "api", "ui", "422", "quick"], 
                       default="all", help="选择测试套件")
    parser.add_argument("--no-ui", action="store_true", help="跳过UI测试")
    parser.add_argument("--parallel", action="store_true", help="并行运行测试")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    print_header("作业票管理系统 - 自动化测试套件")
    print(f"  测试套件: {args.suite}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 创建报告目录
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # 1. 检查后端服务
    print("\n[1/4] 检查后端服务...")
    if not check_backend():
        print("  ❌ 后端服务不可用或登录失败")
        print("\n  💡 提示:")
        print("     1. 启动后端: cd backend && python run_dev.py")
        print("     2. 初始化数据: python backend/scripts/init_demo_data.py")
        sys.exit(1)
    print("  ✓ 后端服务正常")
    
    # 2. 检查前端服务（如果需要UI测试）
    if not args.no_ui and args.suite in ["all", "ui"]:
        print("\n[2/4] 检查前端服务...")
        if not check_frontend():
            print("  ⚠️  前端服务不可用，将跳过UI测试")
            print("     启动前端: cd admin-web && npm run dev")
            args.no_ui = True
        else:
            print("  ✓ 前端服务正常")
    else:
        print("\n[2/4] 跳过前端检查（不运行UI测试）")
    
    # 3. 运行测试
    print("\n[3/4] 运行测试用例...")
    print("-" * 70)
    
    results = {}
    
    # 快速测试（只运行关键测试）
    if args.suite == "quick":
        results["快速测试"] = run_test_suite(
            "quick_test",
            "test_api.py",
            markers="not slow",
            verbose=args.verbose
        )
    
    # API测试
    elif args.suite in ["all", "api"]:
        results["API基础测试"] = run_test_suite(
            "api_basic",
            "test_api.py",
            verbose=args.verbose
        )
        
        results["422错误专项测试"] = run_test_suite(
            "422_errors",
            "test_ticket_detail_422.py",
            verbose=args.verbose
        )
    
    # UI测试
    if not args.no_ui and args.suite in ["all", "ui"]:
        print("\n  💡 UI测试需要安装Playwright:")
        print("     pip install playwright && playwright install")
        
        results["前端UI测试"] = run_test_suite(
            "frontend_ui",
            "test_frontend_ui.py",
            verbose=args.verbose
        )
    
    # 只运行422测试
    elif args.suite == "422":
        results["422错误专项测试"] = run_test_suite(
            "422_errors",
            "test_ticket_detail_422.py",
            verbose=args.verbose
        )
    
    # 4. 总结
    print("\n" + "=" * 70)
    print("[4/4] 测试总结")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status}  {test_name}")
    
    print("-" * 70)
    print(f"  总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n  🎉 所有测试通过！")
        return_code = 0
    else:
        print(f"\n  ⚠️  有 {total - passed} 个测试失败")
        return_code = 1
    
    # 报告位置
    print(f"\n  📊 测试报告: {reports_dir.absolute()}")
    print("=" * 70)
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())

