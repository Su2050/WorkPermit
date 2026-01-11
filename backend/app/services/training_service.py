"""
培训服务
"""
import uuid
from datetime import datetime
from typing import List, Optional, Any
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DailyTicket, DailyTicketWorker, TrainingSession, TrainingVideo
)
from app.utils.progress_validator import TrainingProgressValidator

logger = logging.getLogger(__name__)


class TrainingService:
    """
    培训服务
    
    P0-1: 多视频学习完成判定
    P0-2: 防作弊支持
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.validator = TrainingProgressValidator()
    
    async def check_and_trigger_access_grant(
        self, 
        daily_ticket_id: uuid.UUID, 
        worker_id: uuid.UUID
    ) -> bool:
        """
        检查当日所有视频是否完成，若完成则触发授权 (P0-1)
        
        Args:
            daily_ticket_id: 日票ID
            worker_id: 工人ID
        
        Returns:
            bool: 是否触发了授权
        """
        # 获取所有学习会话
        result = await self.db.execute(
            select(TrainingSession).where(
                TrainingSession.daily_ticket_id == daily_ticket_id,
                TrainingSession.worker_id == worker_id
            )
        )
        sessions = result.scalars().all()
        
        # 检查是否所有视频都完成
        if not sessions:
            return False
        
        all_completed = all(s.status == "COMPLETED" for s in sessions)
        
        if all_completed:
            # 更新 daily_ticket_worker
            dtw_result = await self.db.execute(
                select(DailyTicketWorker).where(
                    DailyTicketWorker.daily_ticket_id == daily_ticket_id,
                    DailyTicketWorker.worker_id == worker_id
                )
            )
            dtw = dtw_result.scalar_one_or_none()
            
            if dtw:
                dtw.training_status = "COMPLETED"
                dtw.completed_video_count = len(sessions)
                
                # 触发门禁授权
                from app.services.access_service import AccessService
                access_service = AccessService(self.db)
                await access_service.create_grants_for_worker(
                    daily_ticket_id, 
                    worker_id
                )
                dtw.authorized = True
                
                logger.info(
                    f"Training completed and access granted: "
                    f"daily_ticket={daily_ticket_id}, worker={worker_id}"
                )
                
                return True
        
        return False
    
    async def get_worker_progress(
        self, 
        daily_ticket_id: uuid.UUID, 
        worker_id: uuid.UUID
    ) -> dict:
        """
        获取工人的学习进度
        
        Args:
            daily_ticket_id: 日票ID
            worker_id: 工人ID
        
        Returns:
            dict: 进度信息
        """
        # 获取日票工人记录
        dtw_result = await self.db.execute(
            select(DailyTicketWorker).where(
                DailyTicketWorker.daily_ticket_id == daily_ticket_id,
                DailyTicketWorker.worker_id == worker_id
            )
        )
        dtw = dtw_result.scalar_one_or_none()
        
        if not dtw:
            return None
        
        # 获取各视频学习进度
        sessions_result = await self.db.execute(
            select(TrainingSession).where(
                TrainingSession.daily_ticket_id == daily_ticket_id,
                TrainingSession.worker_id == worker_id
            )
        )
        sessions = sessions_result.scalars().all()
        
        videos_progress = []
        for session in sessions:
            video_result = await self.db.execute(
                select(TrainingVideo).where(
                    TrainingVideo.video_id == session.video_id
                )
            )
            video = video_result.scalar_one_or_none()
            
            progress_percent = 0
            if video and video.duration_sec > 0:
                progress_percent = round(
                    session.valid_watch_sec / video.duration_sec * 100, 1
                )
            
            videos_progress.append({
                "video_id": str(session.video_id),
                "title": video.title if video else None,
                "status": session.status,
                "valid_watch_sec": session.valid_watch_sec,
                "progress_percent": progress_percent,
                "suspicious_events": session.suspicious_event_count,
                "random_checks_passed": session.random_check_passed,
                "random_checks_failed": session.random_check_failed
            })
        
        return {
            "total_videos": dtw.total_video_count,
            "completed_videos": dtw.completed_video_count,
            "remaining_videos": dtw.total_video_count - dtw.completed_video_count,
            "training_status": dtw.training_status,
            "authorized": dtw.authorized,
            "videos": videos_progress
        }
    
    async def mark_session_failed(
        self, 
        session_id: uuid.UUID, 
        reason: str
    ) -> bool:
        """
        标记学习会话为失败
        
        Args:
            session_id: 会话ID
            reason: 失败原因
        
        Returns:
            bool: 是否成功
        """
        result = await self.db.execute(
            select(TrainingSession).where(
                TrainingSession.session_id == session_id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return False
        
        session.status = "FAILED"
        session.failure_reason = reason
        session.ended_at = datetime.now()
        
        # 更新日票工人状态
        dtw_result = await self.db.execute(
            select(DailyTicketWorker).where(
                DailyTicketWorker.daily_ticket_id == session.daily_ticket_id,
                DailyTicketWorker.worker_id == session.worker_id
            )
        )
        dtw = dtw_result.scalar_one_or_none()
        
        if dtw:
            dtw.training_status = "FAILED"
        
        logger.warning(
            f"Training session marked as failed: "
            f"session={session_id}, reason={reason}"
        )
        
        return True

