"""
调度任务 (P1-3)
- 每日状态切换
- 过期处理
- 健康检查
"""
import logging
from datetime import date, datetime

from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.scheduler.daily_ticket_status_transition")
def daily_ticket_status_transition():
    """
    每日 00:05 - 状态切换任务
    将当天 DailyTicket 状态从 PUBLISHED 切换到 IN_PROGRESS
    """
    import asyncio
    from sqlalchemy import update
    from app.core.database import SessionLocal
    from app.models import DailyTicket
    
    async def _run():
        async with SessionLocal() as db:
            today = date.today()
            
            result = await db.execute(
                update(DailyTicket)
                .where(
                    DailyTicket.date == today,
                    DailyTicket.status == "PUBLISHED"
                )
                .values(status="IN_PROGRESS", updated_at=datetime.now())
            )
            
            await db.commit()
            
            logger.info(
                f"Daily ticket status transition completed: "
                f"date={today}, updated={result.rowcount}"
            )
            
            return {"date": str(today), "updated_count": result.rowcount}
    
    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.scheduler.expire_daily_tickets")
def expire_daily_tickets():
    """
    每日 23:59 - 过期处理
    将当天 DailyTicket 状态切换到 EXPIRED 并撤销门禁权限
    """
    import asyncio
    from sqlalchemy import select, update
    from app.core.database import SessionLocal
    from app.models import DailyTicket, AccessGrant
    
    async def _run():
        async with SessionLocal() as db:
            today = date.today()
            
            # 1. 获取当天进行中的日票
            result = await db.execute(
                select(DailyTicket)
                .where(
                    DailyTicket.date == today,
                    DailyTicket.status == "IN_PROGRESS"
                )
            )
            daily_tickets = result.scalars().all()
            
            expired_count = 0
            revoked_count = 0
            
            for dt in daily_tickets:
                # 更新状态为过期
                dt.status = "EXPIRED"
                dt.updated_at = datetime.now()
                expired_count += 1
                
                # 撤销相关授权
                grants_result = await db.execute(
                    select(AccessGrant)
                    .where(
                        AccessGrant.daily_ticket_id == dt.daily_ticket_id,
                        AccessGrant.status.in_(["SYNCED", "PENDING_SYNC"])
                    )
                )
                grants = grants_result.scalars().all()
                
                for grant in grants:
                    grant.status = "REVOKED"
                    grant.revoked_at = datetime.now()
                    grant.revoke_reason = "EXPIRED"
                    revoked_count += 1
            
            await db.commit()
            
            logger.info(
                f"Daily ticket expiration completed: "
                f"date={today}, expired={expired_count}, revoked={revoked_count}"
            )
            
            return {
                "date": str(today),
                "expired_count": expired_count,
                "revoked_count": revoked_count
            }
    
    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.scheduler.health_check")
def health_check():
    """
    每10分钟 - 健康检查
    检查第三方服务可用性，生成告警
    """
    import asyncio
    import httpx
    from app.core.config import settings
    
    async def _run():
        results = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # 检查数据库连接
        try:
            from app.core.database import engine
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            results["services"]["database"] = {"status": "healthy"}
        except Exception as e:
            results["services"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            logger.error(f"Database health check failed: {e}")
        
        # 检查Redis连接
        try:
            import redis.asyncio as redis
            r = redis.from_url(settings.REDIS_URL)
            await r.ping()
            await r.close()
            results["services"]["redis"] = {"status": "healthy"}
        except Exception as e:
            results["services"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            logger.error(f"Redis health check failed: {e}")
        
        # 检查门禁系统（如果配置了）
        if settings.ACCESS_CONTROL_API_URL:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{settings.ACCESS_CONTROL_API_URL}/health"
                    )
                    if response.status_code == 200:
                        results["services"]["access_control"] = {"status": "healthy"}
                    else:
                        results["services"]["access_control"] = {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status_code}"
                        }
            except Exception as e:
                results["services"]["access_control"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                logger.error(f"Access control health check failed: {e}")
        
        # 检查人脸识别服务（如果配置了）
        if settings.FACE_VERIFY_API_URL:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{settings.FACE_VERIFY_API_URL}/health"
                    )
                    if response.status_code == 200:
                        results["services"]["face_verify"] = {"status": "healthy"}
                    else:
                        results["services"]["face_verify"] = {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status_code}"
                        }
            except Exception as e:
                results["services"]["face_verify"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                logger.error(f"Face verify health check failed: {e}")
        
        # 如果有服务不健康，生成告警
        unhealthy_services = [
            name for name, info in results["services"].items()
            if info.get("status") != "healthy"
        ]
        
        if unhealthy_services:
            logger.warning(
                f"Health check found unhealthy services: {unhealthy_services}"
            )
            # TODO: 调用告警服务发送告警
        
        logger.info(f"Health check completed: {results}")
        return results
    
    return asyncio.get_event_loop().run_until_complete(_run())

