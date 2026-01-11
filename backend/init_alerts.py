"""
初始化告警表并插入测试数据
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 数据库连接
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/work_permit"

async def init_alerts():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        # 创建alert表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alert (
                alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                site_id UUID NOT NULL REFERENCES site(site_id),
                type VARCHAR(50) NOT NULL,
                priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
                status VARCHAR(20) NOT NULL DEFAULT 'UNACKNOWLEDGED',
                title VARCHAR(255) NOT NULL,
                message TEXT,
                source VARCHAR(100),
                related_id UUID,
                acknowledged_by UUID REFERENCES sys_user(user_id),
                acknowledged_at TIMESTAMP WITH TIME ZONE,
                resolved_by UUID REFERENCES sys_user(user_id),
                resolved_at TIMESTAMP WITH TIME ZONE,
                resolution_note TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """))
        print("✓ 告警表创建成功")
    
    async with async_session() as session:
        # 获取一个site_id
        result = await session.execute(text("SELECT site_id FROM site LIMIT 1"))
        row = result.fetchone()
        if not row:
            print("✗ 没有找到工地数据，请先创建工地")
            return
        
        site_id = row[0]
        print(f"✓ 使用工地ID: {site_id}")
        
        # 检查是否已有告警数据
        result = await session.execute(text("SELECT COUNT(*) FROM alert"))
        count = result.scalar()
        if count > 0:
            print(f"✓ 已存在 {count} 条告警数据，跳过创建")
            return
        
        # 插入测试告警数据
        now = datetime.now()
        alerts = [
            {
                "site_id": site_id,
                "type": "ACCESS_DENIED",
                "priority": "HIGH",
                "status": "UNACKNOWLEDGED",
                "title": "未授权人员尝试进入",
                "message": "检测到未授权人员在A区门禁尝试刷卡进入，已被系统拒绝。",
                "source": "门禁系统",
                "created_at": now - timedelta(hours=1)
            },
            {
                "site_id": site_id,
                "type": "FACE_MISMATCH",
                "priority": "HIGH",
                "status": "UNACKNOWLEDGED",
                "title": "人脸识别不匹配",
                "message": "工人张三的人脸识别与系统记录不匹配，请核实身份。",
                "source": "人脸识别系统",
                "created_at": now - timedelta(hours=2)
            },
            {
                "site_id": site_id,
                "type": "TICKET_EXPIRED",
                "priority": "MEDIUM",
                "status": "UNACKNOWLEDGED",
                "title": "作业票即将过期",
                "message": "作业票TK-2026-001将在2小时后过期，请及时处理。",
                "source": "作业票系统",
                "created_at": now - timedelta(hours=3)
            },
            {
                "site_id": site_id,
                "type": "TRAINING_OVERDUE",
                "priority": "MEDIUM",
                "status": "ACKNOWLEDGED",
                "title": "培训视频未完成",
                "message": "工人李四有3个必修培训视频未完成观看。",
                "source": "培训系统",
                "created_at": now - timedelta(days=1)
            },
            {
                "site_id": site_id,
                "type": "DEVICE_OFFLINE",
                "priority": "LOW",
                "status": "RESOLVED",
                "title": "设备离线",
                "message": "B区门禁设备已离线超过30分钟。",
                "source": "设备监控",
                "created_at": now - timedelta(days=2),
                "resolution_note": "设备已恢复正常"
            },
            {
                "site_id": site_id,
                "type": "ACCESS_DENIED",
                "priority": "MEDIUM",
                "status": "UNACKNOWLEDGED",
                "title": "非工作时间访问",
                "message": "检测到非工作时间（22:30）有人尝试进入施工区域。",
                "source": "门禁系统",
                "created_at": now - timedelta(hours=5)
            },
            {
                "site_id": site_id,
                "type": "SAFETY_VIOLATION",
                "priority": "HIGH",
                "status": "UNACKNOWLEDGED",
                "title": "安全违规行为",
                "message": "检测到施工人员未佩戴安全帽进入危险区域。",
                "source": "视频监控",
                "created_at": now - timedelta(minutes=30)
            },
            {
                "site_id": site_id,
                "type": "TICKET_EXPIRED",
                "priority": "LOW",
                "status": "RESOLVED",
                "title": "作业票已过期",
                "message": "作业票TK-2025-099已过期。",
                "source": "作业票系统",
                "created_at": now - timedelta(days=3),
                "resolution_note": "已创建新的作业票"
            }
        ]
        
        for alert in alerts:
            alert_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO alert (alert_id, site_id, type, priority, status, title, message, source, created_at, resolution_note)
                    VALUES (:alert_id, :site_id, :type, :priority, :status, :title, :message, :source, :created_at, :resolution_note)
                """),
                {
                    "alert_id": alert_id,
                    "site_id": alert["site_id"],
                    "type": alert["type"],
                    "priority": alert["priority"],
                    "status": alert["status"],
                    "title": alert["title"],
                    "message": alert["message"],
                    "source": alert["source"],
                    "created_at": alert["created_at"],
                    "resolution_note": alert.get("resolution_note")
                }
            )
        
        await session.commit()
        print(f"✓ 成功插入 {len(alerts)} 条测试告警数据")
        
        # 验证数据
        result = await session.execute(text("SELECT COUNT(*) FROM alert"))
        count = result.scalar()
        print(f"✓ 告警表当前共有 {count} 条数据")

if __name__ == "__main__":
    asyncio.run(init_alerts())

