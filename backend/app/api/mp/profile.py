"""
小程序个人中心API
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import (
    Worker, DailyTicketWorker, DailyTicket, TrainingSession
)
from app.api.mp.deps import get_current_worker
from app.utils.response import success_response

router = APIRouter()


@router.get("/me")
async def get_profile(
    current_worker: Worker = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    """获取个人信息"""
    return success_response({
        "worker_id": str(current_worker.worker_id),
        "name": current_worker.name,
        "phone": current_worker.phone[-4:] if current_worker.phone else None,
        "job_type": current_worker.job_type,
        "team_name": current_worker.team_name,
        "is_bound": current_worker.is_bound
    })


@router.get("/statistics")
async def get_statistics(
    current_worker: Worker = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    """
    获取学习统计
    
    返回总学习时长、完成任务数等
    """
    # 总学习时长
    total_watch_result = await db.execute(
        select(func.sum(TrainingSession.valid_watch_sec))
        .where(
            TrainingSession.worker_id == current_worker.worker_id,
            TrainingSession.status == "COMPLETED"
        )
    )
    total_watch_sec = total_watch_result.scalar() or 0
    
    # 完成任务数
    completed_tasks_result = await db.execute(
        select(func.count(DailyTicketWorker.id))
        .where(
            DailyTicketWorker.worker_id == current_worker.worker_id,
            DailyTicketWorker.training_status == "COMPLETED"
        )
    )
    completed_tasks = completed_tasks_result.scalar() or 0
    
    # 完成视频数
    completed_videos_result = await db.execute(
        select(func.count(TrainingSession.session_id))
        .where(
            TrainingSession.worker_id == current_worker.worker_id,
            TrainingSession.status == "COMPLETED"
        )
    )
    completed_videos = completed_videos_result.scalar() or 0
    
    # 通过校验次数
    passed_checks_result = await db.execute(
        select(func.sum(TrainingSession.random_check_passed))
        .where(
            TrainingSession.worker_id == current_worker.worker_id
        )
    )
    passed_checks = passed_checks_result.scalar() or 0
    
    return success_response({
        "total_watch_sec": total_watch_sec,
        "total_watch_hours": round(total_watch_sec / 3600, 1),
        "completed_tasks": completed_tasks,
        "completed_videos": completed_videos,
        "passed_checks": passed_checks
    })


@router.get("/certificates")
async def get_certificates(
    current_worker: Worker = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    """
    获取培训证书列表
    
    返回已完成的培训记录
    """
    result = await db.execute(
        select(DailyTicketWorker, DailyTicket)
        .join(DailyTicket)
        .where(
            DailyTicketWorker.worker_id == current_worker.worker_id,
            DailyTicketWorker.training_status == "COMPLETED"
        )
        .order_by(DailyTicket.date.desc())
        .limit(50)
    )
    
    rows = result.all()
    
    certificates = []
    for dtw, dt in rows:
        certificates.append({
            "daily_ticket_id": str(dt.daily_ticket_id),
            "date": str(dt.date),
            "ticket_title": dt.ticket.title if dt.ticket else "",
            "completed_videos": dtw.completed_video_count,
            "authorized": dtw.authorized
        })
    
    return success_response({
        "certificates": certificates
    })

