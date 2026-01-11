"""
告警管理API
"""
from typing import Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import SysUser, Alert
from app.api.admin.auth import get_current_user
from app.middleware.tenant import get_tenant_context, TenantQueryFilter
from app.utils.response import success_response, error_response, ErrorCode
from app.utils.pagination import PaginationParams, paginate

router = APIRouter()


class AlertQuery(PaginationParams):
    """告警查询参数"""
    status: Optional[str] = None
    priority: Optional[str] = None
    type: Optional[str] = None
    keyword: Optional[str] = None


class ResolveRequest(BaseModel):
    """解决告警请求"""
    resolution_note: Optional[str] = None


@router.get("/stats")
async def get_alert_stats(
    status: Optional[str] = None,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取告警统计
    
    返回各状态告警数量
    """
    ctx = get_tenant_context()
    
    # 基础查询
    base_stmt = select(Alert)
    base_stmt = TenantQueryFilter.apply(base_stmt, ctx)
    
    # 总数
    total_result = await db.execute(select(func.count()).select_from(base_stmt.subquery()))
    total = total_result.scalar() or 0
    
    # 各状态数量
    stats = {
        "total": total,
        "unacknowledged": 0,
        "acknowledged": 0,
        "resolved": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    # 按状态统计
    for s in ["UNACKNOWLEDGED", "ACKNOWLEDGED", "RESOLVED"]:
        stmt = select(func.count()).select_from(
            base_stmt.where(Alert.status == s).subquery()
        )
        result = await db.execute(stmt)
        stats[s.lower()] = result.scalar() or 0
    
    # 按优先级统计
    for p in ["HIGH", "MEDIUM", "LOW"]:
        stmt = select(func.count()).select_from(
            base_stmt.where(Alert.priority == p).subquery()
        )
        result = await db.execute(stmt)
        stats[p.lower()] = result.scalar() or 0
    
    return success_response(stats)


@router.get("")
async def list_alerts(
    query: AlertQuery = Depends(),
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取告警列表
    
    支持分页、状态和严重程度筛选
    """
    ctx = get_tenant_context()
    
    stmt = select(Alert).order_by(Alert.created_at.desc())
    stmt = TenantQueryFilter.apply(stmt, ctx)
    
    if query.status:
        stmt = stmt.where(Alert.status == query.status)
    
    if query.priority:
        stmt = stmt.where(Alert.priority == query.priority)
    
    if query.type:
        stmt = stmt.where(Alert.type == query.type)
    
    if query.keyword:
        stmt = stmt.where(
            Alert.title.ilike(f"%{query.keyword}%") |
            Alert.message.ilike(f"%{query.keyword}%")
        )
    
    result = await paginate(db, stmt, query)
    
    items = [
        {
            "alert_id": str(alert.alert_id),
            "type": alert.type,
            "priority": alert.priority,
            "status": alert.status,
            "title": alert.title,
            "message": alert.message,
            "source": alert.source,
            "created_at": alert.created_at.isoformat(),
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
        }
        for alert in result.items
    ]
    
    return success_response({
        "items": items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size
    })


@router.get("/{alert_id}")
async def get_alert_detail(
    alert_id: uuid.UUID,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取告警详情
    """
    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="告警不存在"
        )
    
    return success_response({
        "alert_id": str(alert.alert_id),
        "site_id": str(alert.site_id),
        "type": alert.type,
        "priority": alert.priority,
        "status": alert.status,
        "title": alert.title,
        "message": alert.message,
        "source": alert.source,
        "related_id": str(alert.related_id) if alert.related_id else None,
        "acknowledged_by": str(alert.acknowledged_by) if alert.acknowledged_by else None,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "resolved_by": str(alert.resolved_by) if alert.resolved_by else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "resolution_note": alert.resolution_note,
        "created_at": alert.created_at.isoformat()
    })


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: uuid.UUID,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    确认告警
    """
    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="告警不存在"
        )
    
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_by = current_user.user_id
    alert.acknowledged_at = datetime.now()
    
    await db.commit()
    
    return success_response(message="告警已确认")


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: uuid.UUID,
    request: ResolveRequest,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    解决告警
    """
    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="告警不存在"
        )
    
    alert.status = "RESOLVED"
    alert.resolved_by = current_user.user_id
    alert.resolved_at = datetime.now()
    alert.resolution_note = request.resolution_note
    
    await db.commit()
    
    return success_response(message="告警已解决")


@router.post("/batch-acknowledge")
async def batch_acknowledge_alerts(
    alert_ids: list[uuid.UUID],
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量确认告警
    """
    result = await db.execute(
        select(Alert).where(Alert.alert_id.in_(alert_ids))
    )
    alerts = result.scalars().all()
    
    count = 0
    for alert in alerts:
        if alert.status != "ACKNOWLEDGED":
            alert.status = "ACKNOWLEDGED"
            alert.acknowledged_by = current_user.user_id
            alert.acknowledged_at = datetime.now()
            count += 1
    
    await db.commit()
    
    return success_response(message=f"已确认 {count} 条告警")


@router.post("/batch-resolve")
async def batch_resolve_alerts(
    alert_ids: list[uuid.UUID],
    resolution_note: Optional[str] = None,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量解决告警
    """
    result = await db.execute(
        select(Alert).where(Alert.alert_id.in_(alert_ids))
    )
    alerts = result.scalars().all()
    
    count = 0
    for alert in alerts:
        if alert.status != "RESOLVED":
            alert.status = "RESOLVED"
            alert.resolved_by = current_user.user_id
            alert.resolved_at = datetime.now()
            alert.resolution_note = resolution_note
            count += 1
    
    await db.commit()
    
    return success_response(message=f"已解决 {count} 条告警")


@router.get("/rules")
async def get_alert_rules(
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取告警规则列表
    """
    # TODO: 实现告警规则表后，从数据库查询真实数据
    return success_response([])


@router.put("/rules/{rule_id}")
async def update_alert_rule(
    rule_id: uuid.UUID,
    data: dict,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新告警规则
    """
    # TODO: 实现告警规则表后，更新规则
    return success_response(message="规则已更新")
