"""
每日票据管理API
"""
import uuid
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import (
    DailyTicket, DailyTicketWorker, DailyTicketSnapshot,
    WorkTicket, Worker, SysUser
)
from app.api.admin.auth import get_current_user
from app.middleware.tenant import get_tenant_context, TenantQueryFilter
from app.utils.response import success_response, error_response, ErrorCode
from app.utils.pagination import PaginationParams, paginate

router = APIRouter()


class DailyTicketQuery(PaginationParams):
    """查询每日票据参数"""
    ticket_id: Optional[uuid.UUID] = None
    date: Optional[date] = None
    status: Optional[str] = None


@router.get("/work-tickets/{ticket_id}/daily-tickets")
async def list_daily_tickets_by_ticket(
    ticket_id: uuid.UUID,
    date: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取作业票的每日票据列表"""
    ctx = get_tenant_context()
    
    # 验证作业票存在
    ticket_result = await db.execute(
        select(WorkTicket).where(WorkTicket.ticket_id == ticket_id)
    )
    ticket = ticket_result.scalar_one_or_none()
    if not ticket:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="作业票不存在"
        )
    
    # 查询每日票据
    stmt = select(DailyTicket).where(
        DailyTicket.ticket_id == ticket_id
    ).order_by(DailyTicket.date.desc())
    
    # 状态过滤
    if status:
        stmt = stmt.where(DailyTicket.status == status)
    
    # 日期过滤
    if date:
        from datetime import datetime
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            stmt = stmt.where(DailyTicket.date == parsed_date)
        except ValueError:
            return error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message="日期格式错误，请使用 YYYY-MM-DD 格式"
            )
    
    # 创建分页参数对象
    from app.utils.pagination import PaginationParams
    query = PaginationParams(page=page, page_size=page_size)
    result = await paginate(db, stmt, query)
    
    # 计算每个每日票据的培训完成率
    items = []
    for dt in result.items:
        # 查询该日票的工人状态
        workers_result = await db.execute(
            select(
                func.count(DailyTicketWorker.id),
                func.sum(cast(DailyTicketWorker.completed_video_count, Integer)),
                func.sum(cast(DailyTicketWorker.total_video_count, Integer))
            ).where(
                DailyTicketWorker.daily_ticket_id == dt.daily_ticket_id,
                DailyTicketWorker.status == "ACTIVE"
            )
        )
        stats = workers_result.first()
        total_workers = stats[0] or 0
        total_completed = stats[1] or 0
        total_videos = stats[2] or 0
        
        # 计算完成率
        completion_rate = 0
        if total_workers > 0 and total_videos > 0:
            completion_rate = int((total_completed / total_videos) * 100)
        
        items.append({
            "daily_ticket_id": str(dt.daily_ticket_id),
            "ticket_id": str(dt.ticket_id),
            "date": str(dt.date),
            "status": dt.status,
            "access_start_time": str(dt.access_start_time),
            "access_end_time": str(dt.access_end_time),
            "training_deadline_time": str(dt.training_deadline_time),
            "total_workers": total_workers,
            "completion_rate": completion_rate,
            "created_at": dt.created_at.isoformat()
        })
    
    return success_response({
        "items": items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size
    })


@router.get("/daily-tickets/{daily_ticket_id}")
async def get_daily_ticket_detail(
    daily_ticket_id: uuid.UUID,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取每日票据详情"""
    result = await db.execute(
        select(DailyTicket)
        .options(
            selectinload(DailyTicket.ticket),
            selectinload(DailyTicket.daily_ticket_workers)
            .selectinload(DailyTicketWorker.worker)
        )
        .where(DailyTicket.daily_ticket_id == daily_ticket_id)
    )
    daily_ticket = result.scalar_one_or_none()
    
    if not daily_ticket:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="每日票据不存在"
        )
    
    # 计算培训完成率
    total_workers = len([w for w in daily_ticket.daily_ticket_workers if w.status == "ACTIVE"])
    completed_workers = len([
        w for w in daily_ticket.daily_ticket_workers 
        if w.status == "ACTIVE" and w.training_status == "COMPLETED"
    ])
    
    completion_rate = 0
    if total_workers > 0:
        completion_rate = int((completed_workers / total_workers) * 100)
    
    # 构建工人列表
    workers = []
    for dtw in daily_ticket.daily_ticket_workers:
        if dtw.status == "ACTIVE":
            workers.append({
                "worker_id": str(dtw.worker_id),
                "name": dtw.worker.name if dtw.worker else "",
                "phone": dtw.worker.phone if dtw.worker else "",
                "training_status": dtw.training_status,
                "completed_video_count": dtw.completed_video_count,
                "total_video_count": dtw.total_video_count,
                "authorized": dtw.authorized,
                "last_notify_at": dtw.last_notify_at.isoformat() if dtw.last_notify_at else None
            })
    
    return success_response({
        "daily_ticket_id": str(daily_ticket.daily_ticket_id),
        "ticket_id": str(daily_ticket.ticket_id),
        "ticket_title": daily_ticket.ticket.title if daily_ticket.ticket else "",
        "date": str(daily_ticket.date),
        "status": daily_ticket.status,
        "access_start_time": str(daily_ticket.access_start_time),
        "access_end_time": str(daily_ticket.access_end_time),
        "training_deadline_time": str(daily_ticket.training_deadline_time),
        "cancel_reason": daily_ticket.cancel_reason,
        "total_workers": total_workers,
        "completed_workers": completed_workers,
        "completion_rate": completion_rate,
        "workers": workers,
        "created_at": daily_ticket.created_at.isoformat(),
        "updated_at": daily_ticket.updated_at.isoformat()
    })


@router.post("/daily-tickets/{daily_ticket_id}/cancel")
async def cancel_daily_ticket(
    daily_ticket_id: uuid.UUID,
    reason: str,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消每日票据 (P1-3)
    
    1. 更新每日票据状态为 CANCELLED
    2. 撤销所有相关的门禁授权
    3. 记录审计日志
    """
    from app.models import AccessGrant
    from app.services.access_service import AccessService
    from app.services.audit_service import AuditService
    
    # 获取每日票据
    result = await db.execute(
        select(DailyTicket).where(DailyTicket.daily_ticket_id == daily_ticket_id)
    )
    daily_ticket = result.scalar_one_or_none()
    
    if not daily_ticket:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="每日票据不存在"
        )
    
    if daily_ticket.status == "CANCELLED":
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="每日票据已取消"
        )
    
    if daily_ticket.status == "CLOSED":
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="每日票据已关闭，无法取消"
        )
    
    # 更新状态
    daily_ticket.status = "CANCELLED"
    daily_ticket.cancel_reason = reason
    
    # 撤销所有相关授权
    access_service = AccessService(db)
    
    grants_result = await db.execute(
        select(AccessGrant).where(
            AccessGrant.daily_ticket_id == daily_ticket_id,
            AccessGrant.status.in_(["SYNCED", "PENDING_SYNC", "SYNC_FAILED"])
        )
    )
    grants = grants_result.scalars().all()
    
    revoked_count = 0
    for grant in grants:
        success = await access_service.revoke_grant(
            grant.grant_id,
            reason="DAILY_TICKET_CANCELLED"
        )
        if success:
            revoked_count += 1
    
    # 记录审计日志
    try:
        audit_service = AuditService(db)
        await audit_service.record(
            action="DAILY_TICKET_CANCEL",
            resource_type="DailyTicket",
            resource_id=daily_ticket.daily_ticket_id,
            resource_name=f"{daily_ticket.date} 每日票据",
            operator_id=current_user.user_id,
            reason=reason,
            new_value={
                "status": "CANCELLED",
                "revoked_grants_count": revoked_count
            }
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to record audit log: {e}")
    
    await db.commit()
    
    return success_response({
        "daily_ticket_id": str(daily_ticket.daily_ticket_id),
        "status": daily_ticket.status,
        "revoked_grants_count": revoked_count
    }, message=f"每日票据已取消，已撤销 {revoked_count} 个授权")

