"""
作业票变更补偿器 (P0-5: 变更补偿矩阵)
- 变更校验器
- 变更补偿执行器
"""
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class TicketChanges:
    """作业票变更数据"""
    # 允许变更的字段
    remark: Optional[str] = None
    access_start_time: Optional[str] = None  # HH:MM:SS
    access_end_time: Optional[str] = None
    training_deadline_time: Optional[str] = None
    
    # 人员变更
    add_workers: List[uuid.UUID] = field(default_factory=list)
    remove_workers: List[uuid.UUID] = field(default_factory=list)
    
    # 区域变更
    add_areas: List[uuid.UUID] = field(default_factory=list)
    remove_areas: List[uuid.UUID] = field(default_factory=list)
    
    # 视频变更
    add_videos: List[uuid.UUID] = field(default_factory=list)
    # 注意: remove_videos 被禁止
    
    # 变更原因（审计用）
    reason: Optional[str] = None


@dataclass
class ValidationError:
    """校验错误"""
    field: str
    message: str
    code: str


class TicketChangeValidator:
    """
    作业票变更校验器 (P0-5)
    
    变更补偿矩阵规则:
    - 允许改: 备注、授权时间窗、截止时间、增加人员/区域、增加视频(当天未开始)
    - 禁止改: 日期范围、移除视频、移除已完成人员/区域
    """
    
    # 禁止变更的字段
    FORBIDDEN_FIELDS = ["start_date", "end_date", "site_id", "contractor_id"]
    
    async def validate_change(
        self, 
        ticket: Any,  # WorkTicket model
        changes: TicketChanges,
        db_session: Any
    ) -> List[ValidationError]:
        """
        校验变更合法性
        
        Args:
            ticket: 作业票对象
            changes: 变更数据
            db_session: 数据库会话
        
        Returns:
            List[ValidationError]: 错误列表，空列表表示校验通过
        """
        errors: List[ValidationError] = []
        today = date.today()
        
        # 1. 禁止移除视频（全面禁止）
        if hasattr(changes, 'remove_videos') and changes.remove_videos:
            errors.append(ValidationError(
                field="remove_videos",
                message="不允许移除视频，避免'学完又被删'争议",
                code="VIDEO_REMOVAL_FORBIDDEN"
            ))
        
        # 2. 移除人员检查（当天已完成禁止）
        if changes.remove_workers:
            for worker_id in changes.remove_workers:
                completed_today = await self._check_worker_completed_today(
                    db_session, ticket.ticket_id, worker_id, today
                )
                if completed_today:
                    errors.append(ValidationError(
                        field="remove_workers",
                        message=f"工人 {worker_id} 今日已完成培训，不允许移除",
                        code="WORKER_COMPLETED_TODAY"
                    ))
        
        # 3. 移除区域检查（当天已有授权禁止）
        if changes.remove_areas:
            for area_id in changes.remove_areas:
                has_grant_today = await self._check_area_has_grant_today(
                    db_session, ticket.ticket_id, area_id, today
                )
                if has_grant_today:
                    errors.append(ValidationError(
                        field="remove_areas",
                        message=f"区域 {area_id} 今日已有授权，不允许移除",
                        code="AREA_HAS_GRANT_TODAY"
                    ))
        
        # 4. 增加视频检查（当天已开始学习禁止）
        if changes.add_videos:
            today_started = await self._check_ticket_started_today(
                db_session, ticket.ticket_id, today
            )
            if today_started:
                errors.append(ValidationError(
                    field="add_videos",
                    message="今日已有人开始学习，不允许增加视频",
                    code="TRAINING_ALREADY_STARTED"
                ))
        
        # 5. 日期范围变更检查（建议新建票）
        # 由于日期范围在 TicketChanges 中没有定义，这个检查在 API 层处理
        
        return errors
    
    async def _check_worker_completed_today(
        self, 
        db_session: Any, 
        ticket_id: uuid.UUID,
        worker_id: uuid.UUID,
        today: date
    ) -> bool:
        """检查工人今天是否已完成培训"""
        from sqlalchemy import select
        from app.models import DailyTicket, DailyTicketWorker
        
        result = await db_session.execute(
            select(DailyTicketWorker)
            .join(DailyTicket)
            .where(
                DailyTicket.ticket_id == ticket_id,
                DailyTicket.date == today,
                DailyTicketWorker.worker_id == worker_id,
                DailyTicketWorker.training_status == "COMPLETED"
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def _check_area_has_grant_today(
        self, 
        db_session: Any, 
        ticket_id: uuid.UUID,
        area_id: uuid.UUID,
        today: date
    ) -> bool:
        """检查区域今天是否已有授权"""
        from sqlalchemy import select
        from app.models import DailyTicket, AccessGrant
        
        result = await db_session.execute(
            select(AccessGrant)
            .join(DailyTicket)
            .where(
                DailyTicket.ticket_id == ticket_id,
                DailyTicket.date == today,
                AccessGrant.area_id == area_id,
                AccessGrant.status.in_(["SYNCED", "PENDING_SYNC"])
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def _check_ticket_started_today(
        self, 
        db_session: Any, 
        ticket_id: uuid.UUID,
        today: date
    ) -> bool:
        """检查今天是否有人已开始学习"""
        from sqlalchemy import select
        from app.models import DailyTicket, TrainingSession
        
        result = await db_session.execute(
            select(TrainingSession)
            .join(DailyTicket)
            .where(
                DailyTicket.ticket_id == ticket_id,
                DailyTicket.date == today
            )
        )
        return result.scalar_one_or_none() is not None


class TicketChangeCompensator:
    """
    作业票变更补偿执行器 (P0-5)
    
    补偿规则:
    - 增加人员: 生成 daily_ticket_worker
    - 移除人员: 撤销权限, 标记 REMOVED
    - 增加区域: 已完成者立即授权新区域
    - 移除区域: 撤销该区域权限
    - 改时间窗: 更新 grant 的 valid_from/to
    """
    
    def __init__(self, db_session: Any, access_service: Any, audit_service: Any):
        """
        初始化补偿器
        
        Args:
            db_session: 数据库会话
            access_service: 门禁授权服务
            audit_service: 审计服务
        """
        self.db = db_session
        self.access_service = access_service
        self.audit_service = audit_service
    
    async def execute_change(
        self, 
        ticket: Any,  # WorkTicket model
        changes: TicketChanges,
        operator_id: uuid.UUID
    ) -> dict:
        """
        执行变更并补偿
        
        Args:
            ticket: 作业票对象
            changes: 变更数据
            operator_id: 操作人ID
        
        Returns:
            dict: 补偿执行结果
        """
        result = {
            "workers_added": 0,
            "workers_removed": 0,
            "areas_added": 0,
            "areas_removed": 0,
            "grants_created": 0,
            "grants_revoked": 0,
            "grants_updated": 0,
        }
        
        # 1. 记录审计日志
        await self.audit_service.record(
            action="TICKET_CHANGE",
            resource_type="WorkTicket",
            resource_id=ticket.ticket_id,
            operator_id=operator_id,
            new_value={k: str(v) if isinstance(v, (uuid.UUID, list)) else v for k, v in changes.__dict__.items() if v},
            reason=changes.reason
        )
        
        # 2. 增加人员 → 生成 daily_ticket_worker
        if changes.add_workers:
            count = await self._add_workers(ticket, changes.add_workers, operator_id)
            result["workers_added"] = count
        
        # 3. 移除人员 → 撤销权限
        if changes.remove_workers:
            removed, revoked = await self._remove_workers(
                ticket, changes.remove_workers, operator_id
            )
            result["workers_removed"] = removed
            result["grants_revoked"] += revoked
        
        # 4. 增加区域 → 已完成者立即授权
        if changes.add_areas:
            added, granted = await self._add_areas(
                ticket, changes.add_areas, operator_id
            )
            result["areas_added"] = added
            result["grants_created"] = granted
        
        # 5. 移除区域 → 撤销权限
        if changes.remove_areas:
            removed, revoked = await self._remove_areas(
                ticket, changes.remove_areas, operator_id
            )
            result["areas_removed"] = removed
            result["grants_revoked"] += revoked
        
        # 6. 改授权时间窗 → 更新 grant
        if changes.access_start_time or changes.access_end_time:
            updated = await self._update_time_window(
                ticket, 
                changes.access_start_time, 
                changes.access_end_time
            )
            result["grants_updated"] = updated
        
        logger.info(
            f"Ticket change compensation completed: ticket={ticket.ticket_id}, "
            f"result={result}"
        )
        
        return result
    
    async def _add_workers(
        self, 
        ticket: Any, 
        worker_ids: List[uuid.UUID],
        operator_id: uuid.UUID
    ) -> int:
        """增加人员"""
        from sqlalchemy import select
        from app.models import (
            WorkTicketWorker, DailyTicket, DailyTicketWorker, 
            WorkTicketVideo
        )
        
        count = 0
        now = datetime.now()
        
        # 获取视频数量
        video_count_result = await self.db.execute(
            select(WorkTicketVideo)
            .where(
                WorkTicketVideo.ticket_id == ticket.ticket_id,
                WorkTicketVideo.status == "ACTIVE"
            )
        )
        video_count = len(video_count_result.scalars().all())
        
        for worker_id in worker_ids:
            # 添加到 work_ticket_worker
            ticket_worker = WorkTicketWorker(
                ticket_id=ticket.ticket_id,
                worker_id=worker_id,
                site_id=ticket.site_id,
                added_at=now,
                added_by=operator_id,
                status="ACTIVE"
            )
            self.db.add(ticket_worker)
            
            # 为未来的每日票据添加 daily_ticket_worker
            daily_tickets_result = await self.db.execute(
                select(DailyTicket)
                .where(
                    DailyTicket.ticket_id == ticket.ticket_id,
                    DailyTicket.date >= date.today(),
                    DailyTicket.status.in_(["PUBLISHED", "IN_PROGRESS"])
                )
            )
            daily_tickets = daily_tickets_result.scalars().all()
            
            for dt in daily_tickets:
                dtw = DailyTicketWorker(
                    daily_ticket_id=dt.daily_ticket_id,
                    worker_id=worker_id,
                    site_id=ticket.site_id,
                    total_video_count=video_count,
                    completed_video_count=0,
                    training_status="NOT_STARTED",
                    authorized=False,
                    status="ACTIVE"
                )
                self.db.add(dtw)
            
            count += 1
        
        await self.db.flush()
        logger.info(f"Added {count} workers to ticket {ticket.ticket_id}")
        return count
    
    async def _remove_workers(
        self, 
        ticket: Any, 
        worker_ids: List[uuid.UUID],
        operator_id: uuid.UUID
    ) -> tuple[int, int]:
        """移除人员并撤销权限"""
        from sqlalchemy import select, update
        from app.models import (
            WorkTicketWorker, DailyTicket, DailyTicketWorker, AccessGrant
        )
        
        now = datetime.now()
        removed_count = 0
        revoked_count = 0
        
        for worker_id in worker_ids:
            # 更新 work_ticket_worker 状态
            await self.db.execute(
                update(WorkTicketWorker)
                .where(
                    WorkTicketWorker.ticket_id == ticket.ticket_id,
                    WorkTicketWorker.worker_id == worker_id
                )
                .values(status="REMOVED", removed_at=now, removed_by=operator_id)
            )
            
            # 更新 daily_ticket_worker 状态
            await self.db.execute(
                update(DailyTicketWorker)
                .where(
                    DailyTicketWorker.daily_ticket_id.in_(
                        select(DailyTicket.daily_ticket_id)
                        .where(DailyTicket.ticket_id == ticket.ticket_id)
                    ),
                    DailyTicketWorker.worker_id == worker_id
                )
                .values(status="REMOVED")
            )
            
            # 撤销所有相关授权
            grants_result = await self.db.execute(
                select(AccessGrant)
                .join(DailyTicket)
                .where(
                    DailyTicket.ticket_id == ticket.ticket_id,
                    AccessGrant.worker_id == worker_id,
                    AccessGrant.status.in_(["SYNCED", "PENDING_SYNC"])
                )
            )
            grants = grants_result.scalars().all()
            
            for grant in grants:
                await self.access_service.revoke_grant(
                    grant.grant_id, 
                    reason="WORKER_REMOVED"
                )
                revoked_count += 1
            
            removed_count += 1
        
        await self.db.flush()
        logger.info(
            f"Removed {removed_count} workers from ticket {ticket.ticket_id}, "
            f"revoked {revoked_count} grants"
        )
        return removed_count, revoked_count
    
    async def _add_areas(
        self, 
        ticket: Any, 
        area_ids: List[uuid.UUID],
        operator_id: uuid.UUID
    ) -> tuple[int, int]:
        """增加区域并为已完成者立即授权"""
        from sqlalchemy import select
        from app.models import (
            WorkTicketArea, DailyTicket, DailyTicketWorker
        )
        
        now = datetime.now()
        added_count = 0
        granted_count = 0
        
        for area_id in area_ids:
            # 添加到 work_ticket_area
            ticket_area = WorkTicketArea(
                ticket_id=ticket.ticket_id,
                area_id=area_id,
                site_id=ticket.site_id,
                added_at=now,
                added_by=operator_id,
                status="ACTIVE"
            )
            self.db.add(ticket_area)
            added_count += 1
            
            # 找出所有已完成培训的人，为其立即授权新区域
            completed_workers_result = await self.db.execute(
                select(DailyTicketWorker)
                .join(DailyTicket)
                .where(
                    DailyTicket.ticket_id == ticket.ticket_id,
                    DailyTicketWorker.training_status == "COMPLETED",
                    DailyTicketWorker.status == "ACTIVE"
                )
            )
            completed_workers = completed_workers_result.scalars().all()
            
            for dtw in completed_workers:
                await self.access_service.create_grant(
                    dtw.daily_ticket_id,
                    dtw.worker_id,
                    area_id
                )
                granted_count += 1
        
        await self.db.flush()
        logger.info(
            f"Added {added_count} areas to ticket {ticket.ticket_id}, "
            f"created {granted_count} grants"
        )
        return added_count, granted_count
    
    async def _remove_areas(
        self, 
        ticket: Any, 
        area_ids: List[uuid.UUID],
        operator_id: uuid.UUID
    ) -> tuple[int, int]:
        """移除区域并撤销权限"""
        from sqlalchemy import select, update
        from app.models import WorkTicketArea, DailyTicket, AccessGrant
        
        now = datetime.now()
        removed_count = 0
        revoked_count = 0
        
        for area_id in area_ids:
            # 更新 work_ticket_area 状态
            await self.db.execute(
                update(WorkTicketArea)
                .where(
                    WorkTicketArea.ticket_id == ticket.ticket_id,
                    WorkTicketArea.area_id == area_id
                )
                .values(status="REMOVED", removed_at=now, removed_by=operator_id)
            )
            
            # 撤销该区域的所有授权
            grants_result = await self.db.execute(
                select(AccessGrant)
                .join(DailyTicket)
                .where(
                    DailyTicket.ticket_id == ticket.ticket_id,
                    AccessGrant.area_id == area_id,
                    AccessGrant.status.in_(["SYNCED", "PENDING_SYNC"])
                )
            )
            grants = grants_result.scalars().all()
            
            for grant in grants:
                await self.access_service.revoke_grant(
                    grant.grant_id, 
                    reason="AREA_REMOVED"
                )
                revoked_count += 1
            
            removed_count += 1
        
        await self.db.flush()
        logger.info(
            f"Removed {removed_count} areas from ticket {ticket.ticket_id}, "
            f"revoked {revoked_count} grants"
        )
        return removed_count, revoked_count
    
    async def _update_time_window(
        self, 
        ticket: Any,
        new_start_time: Optional[str],
        new_end_time: Optional[str]
    ) -> int:
        """更新授权时间窗"""
        from sqlalchemy import select
        from app.models import DailyTicket, AccessGrant
        from datetime import time
        
        updated_count = 0
        today = date.today()
        
        # 获取未来的已同步授权
        grants_result = await self.db.execute(
            select(AccessGrant)
            .join(DailyTicket)
            .where(
                DailyTicket.ticket_id == ticket.ticket_id,
                DailyTicket.date >= today,
                AccessGrant.status == "SYNCED"
            )
        )
        grants = grants_result.scalars().all()
        
        for grant in grants:
            dt = grant.daily_ticket
            
            if new_start_time:
                h, m, s = map(int, new_start_time.split(":"))
                new_from = datetime.combine(dt.date, time(h, m, s))
                grant.valid_from = new_from
            
            if new_end_time:
                h, m, s = map(int, new_end_time.split(":"))
                new_to = datetime.combine(dt.date, time(h, m, s))
                grant.valid_to = new_to
            
            # 标记需要重新同步
            grant.status = "PENDING_SYNC"
            updated_count += 1
        
        await self.db.flush()
        logger.info(
            f"Updated time window for {updated_count} grants of ticket {ticket.ticket_id}"
        )
        return updated_count

