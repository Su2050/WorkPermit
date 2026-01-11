"""
生产环境数据初始化脚本
仅在数据库为空时创建默认管理员账号和默认工地
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.sys_user import SysUser
from app.models.site import Site
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


async def init_default_site():
    """创建默认工地"""
    async with SessionLocal() as session:
        # 检查是否已有工地
        result = await session.execute(select(Site).limit(1))
        existing_site = result.scalar_one_or_none()
        
        if existing_site:
            print("✅ 工地已存在，跳过创建默认工地")
            return
        
        # 创建默认工地
        default_site = Site(
            name="默认工地",
            code="DEFAULT",
            address="",
            description="系统默认工地",
            default_access_start_time="06:00:00",
            default_access_end_time="20:00:00",
            default_training_deadline="07:30:00",
            is_active=True
        )
        session.add(default_site)
        await session.commit()
        print("✅ 默认工地创建成功: 默认工地 (DEFAULT)")


async def main():
    """主函数"""
    print("🚀 开始初始化生产环境数据...")
    
    try:
        await init_admin_user()
        await init_default_site()
        print("✅ 数据初始化完成")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

