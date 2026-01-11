#!/usr/bin/env python3
"""
开发环境快速启动脚本
"""
import os
import sys
import subprocess
import time

def check_docker():
    """检查Docker是否运行"""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def check_services():
    """检查必要服务是否运行"""
    services = {
        "postgres": "5432",
        "redis": "6379"
    }
    
    import socket
    running = {}
    
    for service, port in services.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', int(port)))
            sock.close()
            running[service] = result == 0
        except:
            running[service] = False
    
    return running

def main():
    print("=" * 60)
    print("作业票管理系统 - 开发环境启动")
    print("=" * 60)
    
    # 检查Docker
    if not check_docker():
        print("\n⚠️  Docker未运行")
        print("请先启动Docker Desktop，然后运行:")
        print("  docker-compose up -d postgres redis minio")
        print("\n或者使用启动脚本:")
        print("  ./scripts/start_dev.sh")
        return 1
    
    # 检查服务
    print("\n检查服务状态...")
    services = check_services()
    
    if not services.get("postgres"):
        print("⚠️  PostgreSQL未运行")
        print("启动命令: docker-compose up -d postgres")
    else:
        print("✅ PostgreSQL运行中")
    
    if not services.get("redis"):
        print("⚠️  Redis未运行")
        print("启动命令: docker-compose up -d redis")
    else:
        print("✅ Redis运行中")
    
    if not all(services.values()):
        print("\n请先启动必要的服务:")
        print("  docker-compose up -d postgres redis")
        return 1
    
    # 检查环境变量
    if not os.path.exists(".env"):
        print("\n⚠️  未找到.env文件")
        print("请创建.env文件（参考.env.example）")
        return 1
    
    print("\n✅ 环境检查通过")
    print("\n启动FastAPI服务...")
    print("访问地址: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务\n")
    
    # 启动uvicorn
    try:
        os.execvp("uvicorn", [
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\n服务已停止")
        return 0
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

