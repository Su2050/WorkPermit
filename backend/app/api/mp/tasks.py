"""
小程序待办API (P0-1: 显示多视频进度)
"""
import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import (
    DailyTicket, DailyTicketWorker, TrainingSession, 
    WorkTicket, WorkTicketVideo, Worker
)
from app.api.mp.deps import get_current_worker
from app.utils.response import success_response, error_response, ErrorCode

router = APIRouter()


@router.get("/today")
async def get_today_tasks(
    current_worker: Worker = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    """
    获取今日待办任务 (P0-1)
    
    返回今日需要学习的作业票和视频列表
    包含多视频进度信息
    """
    today = date.today()
    
    # 查询今日的日票-工人记录
    result = await db.execute(
        select(DailyTicketWorker)
        .join(DailyTicket)
        .options(
            selectinload(DailyTicketWorker.daily_ticket)
            .selectinload(DailyTicket.ticket)
            .selectinload(WorkTicket.work_ticket_videos)
            .selectinload(WorkTicketVideo.video)
        )
        .where(
            DailyTicket.date == today,
            DailyTicket.status.in_(["PUBLISHED", "IN_PROGRESS"]),
            DailyTicketWorker.worker_id == current_worker.worker_id,
            DailyTicketWorker.status == "ACTIVE"
        )
    )
    
    daily_ticket_workers = result.scalars().all()
    
    tasks = []
    for dtw in daily_ticket_workers:
        dt = dtw.daily_ticket
        ticket = dt.ticket
        
        # 获取视频列表及学习状态
        videos = []
        for tv in ticket.work_ticket_videos:
            if tv.status != "ACTIVE":
                continue
            
            # 查询该视频的学习会话
            session_result = await db.execute(
                select(TrainingSession).where(
                    TrainingSession.daily_ticket_id == dt.daily_ticket_id,
                    TrainingSession.worker_id == current_worker.worker_id,
                    TrainingSession.video_id == tv.video_id
                )
            )
            session = session_result.scalar_one_or_none()
            
            video_status = "NOT_STARTED"
            if session:
                video_status = session.status
            
            videos.append({
                "video_id": str(tv.video_id),
                "title": tv.video.title,
                "duration": tv.video.duration_sec,
                "status": video_status,
                "thumbnail_url": tv.video.thumbnail_url
            })
        
        # P0-1: 多视频进度
        tasks.append({
            "daily_ticket_id": str(dt.daily_ticket_id),
            "ticket_title": ticket.title,
            "areas": [],  # TODO: 加载区域
            "deadline": str(dt.training_deadline_time),
            "videos": videos,
            "progress": {
                "total_videos": dtw.total_video_count,
                "completed_videos": dtw.completed_video_count,
                "remaining_videos": dtw.total_video_count - dtw.completed_video_count
            },
            "training_status": dtw.training_status,
            "authorized": dtw.authorized
        })
    
    return success_response({
        "date": str(today),
        "tasks": tasks
    })


@router.get("/history")
async def get_task_history(
    days: int = 7,
    current_worker: Worker = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    """
    获取历史任务
    
    返回最近N天的学习记录
    """
    from datetime import timedelta
    
    today = date.today()
    start_date = today - timedelta(days=days)
    
    result = await db.execute(
        select(DailyTicketWorker)
        .join(DailyTicket)
        .options(
            selectinload(DailyTicketWorker.daily_ticket)
            .selectinload(DailyTicket.ticket)
        )
        .where(
            DailyTicket.date >= start_date,
            DailyTicket.date < today,
            DailyTicketWorker.worker_id == current_worker.worker_id
        )
        .order_by(DailyTicket.date.desc())
    )
    
    daily_ticket_workers = result.scalars().all()
    
    history = []
    for dtw in daily_ticket_workers:
        dt = dtw.daily_ticket
        history.append({
            "date": str(dt.date),
            "daily_ticket_id": str(dt.daily_ticket_id),
            "ticket_title": dt.ticket.title,
            "training_status": dtw.training_status,
            "authorized": dtw.authorized,
            "completed_videos": dtw.completed_video_count,
            "total_videos": dtw.total_video_count
        })
    
    return success_response({
        "days": days,
        "history": history
    })


@router.get("/{daily_ticket_id}")
async def get_task_detail(
    daily_ticket_id: uuid.UUID,
    current_worker: Worker = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务详情
    
    返回作业票详细信息和视频学习状态
    """
    # 查询日票
    result = await db.execute(
        select(DailyTicket)
        .options(
            selectinload(DailyTicket.ticket)
            .selectinload(WorkTicket.work_ticket_videos)
            .selectinload(WorkTicketVideo.video),
            selectinload(DailyTicket.ticket)
            .selectinload(WorkTicket.work_ticket_areas)
        )
        .where(DailyTicket.daily_ticket_id == daily_ticket_id)
    )
    dt = result.scalar_one_or_none()
    
    if not dt:
        return error_response(
            code=ErrorCode.TICKET_NOT_FOUND,
            message="任务不存在"
        )
    
    # 查询工人状态
    dtw_result = await db.execute(
        select(DailyTicketWorker).where(
            DailyTicketWorker.daily_ticket_id == daily_ticket_id,
            DailyTicketWorker.worker_id == current_worker.worker_id
        )
    )
    dtw = dtw_result.scalar_one_or_none()
    
    if not dtw:
        return error_response(
            code=ErrorCode.WORKER_NOT_IN_TICKET,
            message="您不在此作业票名单中"
        )
    
    ticket = dt.ticket
    
    # 获取视频详细状态
    videos = []
    for tv in ticket.work_ticket_videos:
        if tv.status != "ACTIVE":
            continue
        
        session_result = await db.execute(
            select(TrainingSession).where(
                TrainingSession.daily_ticket_id == daily_ticket_id,
                TrainingSession.worker_id == current_worker.worker_id,
                TrainingSession.video_id == tv.video_id
            )
        )
        session = session_result.scalar_one_or_none()
        
        video_info = {
            "video_id": str(tv.video_id),
            "title": tv.video.title,
            "description": tv.video.description,
            "duration": tv.video.duration_sec,
            "file_url": tv.video.file_url,
            "thumbnail_url": tv.video.thumbnail_url,
            "status": "NOT_STARTED",
            "progress": 0
        }
        
        if session:
            video_info["status"] = session.status
            video_info["progress"] = round(
                session.valid_watch_sec / tv.video.duration_sec * 100, 1
            ) if tv.video.duration_sec > 0 else 0
            video_info["session_id"] = str(session.session_id)
        
        videos.append(video_info)
    
    # 获取区域信息
    areas = [
        {
            "area_id": str(ta.area_id),
            "name": ta.area.name
        }
        for ta in ticket.work_ticket_areas
        if ta.status == "ACTIVE"
    ]
    
    return success_response({
        "daily_ticket_id": str(dt.daily_ticket_id),
        "date": str(dt.date),
        "ticket": {
            "ticket_id": str(ticket.ticket_id),
            "title": ticket.title,
            "description": ticket.description
        },
        "areas": areas,
        "time_config": {
            "access_start_time": str(dt.access_start_time),
            "access_end_time": str(dt.access_end_time),
            "training_deadline": str(dt.training_deadline_time)
        },
        "videos": videos,
        "progress": {
            "total_videos": dtw.total_video_count,
            "completed_videos": dtw.completed_video_count,
            "remaining_videos": dtw.total_video_count - dtw.completed_video_count
        },
        "training_status": dtw.training_status,
        "authorized": dtw.authorized
    })

