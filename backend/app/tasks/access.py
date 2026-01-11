"""
门禁任务 (P0-6: 两级对账, P1-1: 幂等)
- 授权同步重试
- 同步对账（一级）
- 权限对账（二级，可选）
"""
import logging
from datetime import datetime, timedelta
from typing import List
import uuid

from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.access.retry_failed_sync")
def retry_failed_sync():
    """
    每1分钟 - 授权同步重试
    扫描 PENDING_SYNC 和 SYNC_FAILED 的授权，调用门禁适配器推送
    """
    import asyncio
    from sqlalchemy import select
    from app.core.database import SessionLocal
    from app.core.config import settings
    from app.models import AccessGrant
    
    async def _run():
        async with SessionLocal() as db:
            now = datetime.now()
            synced_count = 0
            failed_count = 0
            
            # 查找需要重试的授权
            result = await db.execute(
                select(AccessGrant)
                .where(
                    AccessGrant.status.in_(["PENDING_SYNC", "SYNC_FAILED"]),
                    AccessGrant.valid_to > now  # 未过期
                )
                .order_by(AccessGrant.created_at)
                .limit(100)  # 每次最多处理100条
            )
            
            grants = result.scalars().all()
            
            for grant in grants:
                # 检查是否需要等待（指数退避）
                if grant.last_sync_at:
                    retry_intervals = settings.ACCESS_SYNC_RETRY_INTERVALS
                    retry_index = min(
                        grant.sync_attempt_count, 
                        len(retry_intervals) - 1
                    )
                    wait_time = timedelta(seconds=retry_intervals[retry_index])
                    
                    if now - grant.last_sync_at < wait_time:
                        continue  # 还需要等待
                
                # 尝试同步
                try:
                    from app.adapters.access_control_adapter import AccessControlAdapter
                    
                    adapter = AccessControlAdapter()
                    result = await adapter.push_grant(grant)
                    
                    if result["success"]:
                        grant.status = "SYNCED"
                        grant.vendor_ref = result.get("vendor_ref")
                        synced_count += 1
                    else:
                        grant.status = "SYNC_FAILED"
                        grant.sync_error_msg = result.get("error")
                        failed_count += 1
                    
                    grant.last_sync_at = now
                    grant.sync_attempt_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync grant {grant.grant_id}: {e}")
                    grant.status = "SYNC_FAILED"
                    grant.sync_error_msg = str(e)
                    grant.last_sync_at = now
                    grant.sync_attempt_count += 1
                    failed_count += 1
            
            await db.commit()
            
            logger.info(
                f"Access grant sync retry completed: "
                f"synced={synced_count}, failed={failed_count}"
            )
            
            return {
                "synced_count": synced_count,
                "failed_count": failed_count
            }
    
    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.access.reconcile_sync_status")
def reconcile_sync_status():
    """
    每日 02:00 - 一级对账（同步状态）
    P0-6: 对账本系统期望权限 vs 同步状态
    无需门禁拉取，必做
    """
    import asyncio
    from sqlalchemy import select
    from app.core.database import SessionLocal
    from app.models import AccessGrant
    
    async def _run():
        async with SessionLocal() as db:
            now = datetime.now()
            
            # 找出"应该 SYNCED 但实际 PENDING/FAILED"的授权
            # 超过10分钟仍未同步 且 未过期
            result = await db.execute(
                select(AccessGrant)
                .where(
                    AccessGrant.status.in_(["PENDING_SYNC", "SYNC_FAILED"]),
                    AccessGrant.created_at < now - timedelta(minutes=10),
                    AccessGrant.valid_to > now
                )
            )
            
            stuck_grants = result.scalars().all()
            
            report = {
                "timestamp": now.isoformat(),
                "total_stuck": len(stuck_grants),
                "by_site": {},
                "by_area": {},
                "stuck_grants": []
            }
            
            for grant in stuck_grants:
                report["stuck_grants"].append({
                    "grant_id": str(grant.grant_id),
                    "worker_id": str(grant.worker_id),
                    "area_id": str(grant.area_id),
                    "status": grant.status,
                    "sync_attempt_count": grant.sync_attempt_count,
                    "last_error": grant.sync_error_msg
                })
                
                # 聚合统计
                site_id = str(grant.site_id)
                area_id = str(grant.area_id)
                
                report["by_site"][site_id] = report["by_site"].get(site_id, 0) + 1
                report["by_area"][area_id] = report["by_area"].get(area_id, 0) + 1
            
            # 生成告警
            if report["total_stuck"] > 0:
                await _create_alert(
                    alert_type="SYNC_STUCK",
                    severity="HIGH" if report["total_stuck"] > 10 else "MEDIUM",
                    message=f'{report["total_stuck"]} 个授权同步卡住',
                    details=report
                )
            
            logger.info(f"Sync status reconciliation completed: {report}")
            
            return report
    
    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.access.reconcile_with_vendor")
def reconcile_with_vendor():
    """
    每日 03:00 - 二级对账（权限对账）
    P0-6: 与门禁系统对账，需要门禁提供查询接口
    可选，根据门禁系统能力决定是否启用
    """
    import asyncio
    from sqlalchemy import select
    from app.core.database import SessionLocal
    from app.core.config import settings
    from app.models import AccessGrant, Site
    
    async def _run():
        # 检查门禁系统是否支持查询
        if not settings.ACCESS_CONTROL_SUPPORTS_QUERY:
            logger.info(
                "Access control system does not support query grants, "
                "skipping vendor reconciliation"
            )
            return {
                "status": "UNSUPPORTED",
                "message": "门禁系统不支持权限查询，跳过二级对账"
            }
        
        async with SessionLocal() as db:
            now = datetime.now()
            
            # 获取所有活跃的工地
            sites_result = await db.execute(
                select(Site).where(Site.is_active == True)
            )
            sites = sites_result.scalars().all()
            
            all_reports = []
            
            for site in sites:
                try:
                    report = await _reconcile_site(db, site.site_id, now)
                    all_reports.append(report)
                except Exception as e:
                    logger.error(f"Failed to reconcile site {site.site_id}: {e}")
                    all_reports.append({
                        "site_id": str(site.site_id),
                        "status": "ERROR",
                        "error": str(e)
                    })
            
            logger.info(f"Vendor reconciliation completed: {len(all_reports)} sites")
            
            return {
                "timestamp": now.isoformat(),
                "reports": all_reports
            }
    
    return asyncio.get_event_loop().run_until_complete(_run())


async def _reconcile_site(db, site_id: uuid.UUID, now: datetime) -> dict:
    """对账单个工地"""
    from sqlalchemy import select
    from app.models import AccessGrant
    from app.adapters.access_control_adapter import AccessControlAdapter
    
    # 1. 查询本系统期望权限
    expected_result = await db.execute(
        select(AccessGrant)
        .where(
            AccessGrant.site_id == site_id,
            AccessGrant.status == "SYNCED",
            AccessGrant.valid_to > now
        )
    )
    expected_grants = expected_result.scalars().all()
    
    # 2. 拉取门禁侧实际权限
    adapter = AccessControlAdapter()
    actual_grants = await adapter.query_effective_grants(site_id)
    
    # 3. 比对
    expected_set = {
        (str(g.worker_id), str(g.area_id), g.vendor_ref) 
        for g in expected_grants
    }
    actual_set = {
        (g['worker_id'], g['area_id'], g['vendor_ref']) 
        for g in actual_grants
    }
    
    missing_in_vendor = expected_set - actual_set  # 本系统有、门禁没有
    extra_in_vendor = actual_set - expected_set    # 门禁有、本系统没有
    
    report = {
        "site_id": str(site_id),
        "expected_count": len(expected_set),
        "actual_count": len(actual_set),
        "missing_in_vendor": [list(x) for x in missing_in_vendor],
        "extra_in_vendor": [list(x) for x in extra_in_vendor],
        "mismatch_count": len(missing_in_vendor) + len(extra_in_vendor)
    }
    
    # 4. 生成告警
    if report["mismatch_count"] > 0:
        await _create_alert(
            alert_type="ACCESS_MISMATCH",
            severity="HIGH" if report["mismatch_count"] > 20 else "MEDIUM",
            message=f'工地 {site_id} 权限不一致: {report["mismatch_count"]} 条',
            details=report
        )
    
    return report


async def _create_alert(
    alert_type: str,
    severity: str,
    message: str,
    details: dict
):
    """创建告警记录"""
    # TODO: 实现告警服务
    logger.warning(
        f"Alert created: type={alert_type}, severity={severity}, "
        f"message={message}"
    )


@celery_app.task(
    name="tasks.access.push_grant",
    bind=True,
    max_retries=5
)
def push_grant_task(
    self,
    grant_id: str
):
    """
    推送单个授权到门禁系统
    P1-1: 幂等推送
    """
    import asyncio
    from sqlalchemy import select
    from app.core.database import SessionLocal
    from app.models import AccessGrant
    from app.adapters.access_control_adapter import AccessControlAdapter
    
    async def _run():
        async with SessionLocal() as db:
            # 获取授权记录
            result = await db.execute(
                select(AccessGrant)
                .where(AccessGrant.grant_id == uuid.UUID(grant_id))
            )
            grant = result.scalar_one_or_none()
            
            if not grant:
                logger.error(f"Grant not found: {grant_id}")
                return {"success": False, "error": "Grant not found"}
            
            # 检查是否已过期
            if grant.valid_to < datetime.now():
                grant.status = "REVOKED"
                grant.revoke_reason = "EXPIRED"
                await db.commit()
                return {"success": False, "error": "Grant expired"}
            
            # 推送到门禁系统
            try:
                adapter = AccessControlAdapter()
                result = await adapter.push_grant(grant)
                
                if result["success"]:
                    grant.status = "SYNCED"
                    grant.vendor_ref = result.get("vendor_ref")
                else:
                    grant.status = "SYNC_FAILED"
                    grant.sync_error_msg = result.get("error")
                
                grant.last_sync_at = datetime.now()
                grant.sync_attempt_count += 1
                
                await db.commit()
                
                return result
                
            except Exception as e:
                logger.error(f"Failed to push grant: {e}")
                grant.sync_attempt_count += 1
                await db.commit()
                
                # 重试
                retry_delay = 60 * (2 ** self.request.retries)
                raise self.retry(exc=e, countdown=retry_delay)
    
    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.access.revoke_grant")
def revoke_grant_task(grant_id: str, reason: str = "MANUAL"):
    """撤销单个授权"""
    import asyncio
    from sqlalchemy import select
    from app.core.database import SessionLocal
    from app.models import AccessGrant
    from app.adapters.access_control_adapter import AccessControlAdapter
    
    async def _run():
        async with SessionLocal() as db:
            result = await db.execute(
                select(AccessGrant)
                .where(AccessGrant.grant_id == uuid.UUID(grant_id))
            )
            grant = result.scalar_one_or_none()
            
            if not grant:
                return {"success": False, "error": "Grant not found"}
            
            # 如果已同步，需要通知门禁系统撤销
            if grant.status == "SYNCED" and grant.vendor_ref:
                try:
                    adapter = AccessControlAdapter()
                    await adapter.revoke_grant(grant)
                except Exception as e:
                    logger.error(f"Failed to revoke grant from vendor: {e}")
            
            # 更新状态
            grant.status = "REVOKED"
            grant.revoked_at = datetime.now()
            grant.revoke_reason = reason
            
            await db.commit()
            
            logger.info(f"Grant revoked: {grant_id}, reason={reason}")
            
            return {"success": True}
    
    return asyncio.get_event_loop().run_until_complete(_run())

