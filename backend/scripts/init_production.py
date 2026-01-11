"""
生产环境数据初始化脚本
仅在数据库为空时创建默认管理员账号
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.sys_user import SysUser
from app.core.security import get_password_hash


async def init_admin_user():
    """创建默认管理员账号"""
    async with SessionLocal() as session:
        # 检查是否已有管理员
        result = await session.execute(
            select(SysUser).where(SysUser.username == "admin")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("✅ 管理员账号已存在，跳过初始化")
            return
        
        # 创建管理员
        admin = SysUser(
            username="admin",
            name="系统管理员",
            password_hash=get_password_hash("admin123"),
            role="SysAdmin",
            is_active=True,
            is_locked=False
        )
        session.add(admin)
        await session.commit()
        print("✅ 管理员账号创建成功: admin / admin123")


async def main():
    """主函数"""
    print("🚀 开始初始化生产环境数据...")
    
    try:
        await init_admin_user()
        print("✅ 数据初始化完成")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

