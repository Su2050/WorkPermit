"""
作业票服务
"""
import uuid
from datetime import date, datetime, timedelta
from typing import List, Any
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    WorkTicket, WorkTicketWorker, WorkTicketArea, WorkTicketVideo,
    DailyTicket, DailyTicketWorker, DailyTicketSnapshot
)

logger = logging.getLogger(__name__)


class TicketService:
    """作业票服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_daily_tickets(
        self, 
        ticket: WorkTicket
    ) -> List[DailyTicket]:
        """
        生成每日票据 (P0-8: 含快照)
        
        Args:
            ticket: 作业票对象
        
        Returns:
            List[DailyTicket]: 生成的每日票据列表
        """
        # 获取关联数据
        workers_result = await self.db.execute(
            select(WorkTicketWorker)
            .where(
                WorkTicketWorker.ticket_id == ticket.ticket_id,
                WorkTicketWorker.status == "ACTIVE"
            )
        )
        workers = workers_result.scalars().all()
        
        areas_result = await self.db.execute(
            select(WorkTicketArea)
            .where(
                WorkTicketArea.ticket_id == ticket.ticket_id,
                WorkTicketArea.status == "ACTIVE"
            )
        )
        areas = areas_result.scalars().all()
        
        videos_result = await self.db.execute(
            select(WorkTicketVideo)
            .where(
                WorkTicketVideo.ticket_id == ticket.ticket_id,
                WorkTicketVideo.status == "ACTIVE"
            )
        )
        videos = videos_result.scalars().all()
        
        video_count = len(videos)
        
        # 生成日期范围
        dates = self._get_date_range(ticket.start_date, ticket.end_date)
        
        daily_tickets = []
        
        for d in dates:
            # 创建日票
            daily_ticket = DailyTicket(
                ticket_id=ticket.ticket_id,
                site_id=ticket.site_id,
                date=d,
                access_start_time=ticket.default_access_start_time,
                access_end_time=ticket.default_access_end_time,
                training_deadline_time=ticket.default_training_deadline_time,
                status="PUBLISHED"
            )
            self.db.add(daily_ticket)
            await self.db.flush()  # 获取ID
            
            # P0-8: 保存快照
            for tw in workers:
                # 工人快照
                worker = tw.worker
                snapshot = DailyTicketSnapshot(
                    daily_ticket_id=daily_ticket.daily_ticket_id,
                    snapshot_type="WORKER",
                    entity_id=tw.worker_id,
                    entity_name=worker.name if worker else None,
                    metadata={
                        "id_no": worker.id_no if worker else None,
                        "phone": worker.phone if worker else None,
                        "job_type": worker.job_type if worker else None
                    }
                )
                self.db.add(snapshot)
                
                # 创建日票-工人状态
                dtw = DailyTicketWorker(
                    daily_ticket_id=daily_ticket.daily_ticket_id,
                    worker_id=tw.worker_id,
                    site_id=ticket.site_id,
                    total_video_count=video_count,
                    completed_video_count=0,
                    training_status="NOT_STARTED",
                    authorized=False,
                    status="ACTIVE"
                )
                self.db.add(dtw)
            
            for ta in areas:
                # 区域快照
                area = ta.area
                snapshot = DailyTicketSnapshot(
                    daily_ticket_id=daily_ticket.daily_ticket_id,
                    snapshot_type="AREA",
                    entity_id=ta.area_id,
                    entity_name=area.name if area else None,
                    metadata={
                        "access_group_id": area.access_group_id if area else None
                    }
                )
                self.db.add(snapshot)
            
            for tv in videos:
                # 视频快照
                video = tv.video
                snapshot = DailyTicketSnapshot(
                    daily_ticket_id=daily_ticket.daily_ticket_id,
                    snapshot_type="VIDEO",
                    entity_id=tv.video_id,
                    entity_name=video.title if video else None,
                    metadata={
                        "duration": video.duration_sec if video else None,
                        "required_percent": float(tv.required_watch_percent)
                    }
                )
                self.db.add(snapshot)
            
            daily_tickets.append(daily_ticket)
        
        logger.info(
            f"Generated {len(daily_tickets)} daily tickets for ticket {ticket.ticket_id}"
        )
        
        return daily_tickets
    
    def _get_date_range(self, start: date, end: date) -> List[date]:
        """生成日期范围"""
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        return dates
    
    async def get_ticket_statistics(
        self, 
        ticket_id: uuid.UUID
    ) -> dict:
        """获取作业票统计信息"""
        # 获取所有日票
        result = await self.db.execute(
            select(DailyTicket).where(DailyTicket.ticket_id == ticket_id)
        )
        daily_tickets = result.scalars().all()
        
        total_daily_tickets = len(daily_tickets)
        in_progress = sum(1 for dt in daily_tickets if dt.status == "IN_PROGRESS")
        completed = sum(1 for dt in daily_tickets if dt.status == "EXPIRED")
        
        # 获取培训完成统计
        dtw_result = await self.db.execute(
            select(DailyTicketWorker)
            .join(DailyTicket)
            .where(DailyTicket.ticket_id == ticket_id)
        )
        daily_ticket_workers = dtw_result.scalars().all()
        
        total_training = len(daily_ticket_workers)
        completed_training = sum(
            1 for dtw in daily_ticket_workers 
            if dtw.training_status == "COMPLETED"
        )
        
        return {
            "total_daily_tickets": total_daily_tickets,
            "in_progress": in_progress,
            "completed": completed,
            "total_training": total_training,
            "completed_training": completed_training,
            "training_completion_rate": round(
                completed_training / total_training * 100, 1
            ) if total_training > 0 else 0
        }

