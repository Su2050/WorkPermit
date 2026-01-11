"""
门禁授权服务 (P0-4, P0-6, P1-1)
"""
import uuid
from datetime import datetime, date, time, timedelta
from typing import List, Optional
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DailyTicket, DailyTicketWorker, WorkTicketArea, 
    AccessGrant, WorkArea
)
from app.adapters.access_control_adapter import AccessControlAdapter

logger = logging.getLogger(__name__)


class AccessService:
    """
    门禁授权服务
    
    P0-4: 时间窗强制
    P0-6: 两级对账
    P1-1: 幂等推送
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.adapter = AccessControlAdapter()
    
    async def create_grants_for_worker(
        self, 
        daily_ticket_id: uuid.UUID, 
        worker_id: uuid.UUID
    ) -> List[AccessGrant]:
        """
        为完成培训的工人创建门禁授权 (P0-4)
        
        Args:
            daily_ticket_id: 日票ID
            worker_id: 工人ID
        
        Returns:
            List[AccessGrant]: 创建的授权列表
        """
        # 获取日票
        dt_result = await self.db.execute(
            select(DailyTicket).where(
                DailyTicket.daily_ticket_id == daily_ticket_id
            )
        )
        daily_ticket = dt_result.scalar_one_or_none()
        
        if not daily_ticket:
            logger.error(f"Daily ticket not found: {daily_ticket_id}")
            return []
        
        # 获取关联区域
        areas_result = await self.db.execute(
            select(WorkTicketArea)
            .where(
                WorkTicketArea.ticket_id == daily_ticket.ticket_id,
                WorkTicketArea.status == "ACTIVE"
            )
        )
        areas = areas_result.scalars().all()
        
        grants = []
        
        for ta in areas:
            # P0-4: 计算时间窗
            valid_from = datetime.combine(
                daily_ticket.date,
                daily_ticket.access_start_time
            )
            valid_to = datetime.combine(
                daily_ticket.date,
                daily_ticket.access_end_time
            )
            
            # 确保不跨天
            if valid_to.date() != daily_ticket.date:
                valid_to = datetime.combine(
                    daily_ticket.date,
                    time(23, 59, 59)
                )
            
            # 检查是否已存在
            existing_result = await self.db.execute(
                select(AccessGrant).where(
                    AccessGrant.daily_ticket_id == daily_ticket_id,
                    AccessGrant.worker_id == worker_id,
                    AccessGrant.area_id == ta.area_id
                )
            )
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                logger.info(f"Grant already exists: {existing.grant_id}")
                grants.append(existing)
                continue
            
            # 创建授权
            grant = AccessGrant(
                daily_ticket_id=daily_ticket_id,
                worker_id=worker_id,
                area_id=ta.area_id,
                site_id=daily_ticket.site_id,
                valid_from=valid_from,
                valid_to=valid_to,
                status="PENDING_SYNC"
            )
            self.db.add(grant)
            await self.db.flush()
            
            grants.append(grant)
            
            logger.info(
                f"Access grant created: grant={grant.grant_id}, "
                f"worker={worker_id}, area={ta.area_id}, "
                f"valid_from={valid_from}, valid_to={valid_to}"
            )
            
            # 推送至门禁（异步任务）
            from app.tasks.access import push_grant_task
            push_grant_task.delay(str(grant.grant_id))
        
        return grants
    
    async def create_grant(
        self, 
        daily_ticket_id: uuid.UUID, 
        worker_id: uuid.UUID,
        area_id: uuid.UUID
    ) -> Optional[AccessGrant]:
        """
        创建单个门禁授权
        
        Args:
            daily_ticket_id: 日票ID
            worker_id: 工人ID
            area_id: 区域ID
        
        Returns:
            AccessGrant: 创建的授权
        """
        dt_result = await self.db.execute(
            select(DailyTicket).where(
                DailyTicket.daily_ticket_id == daily_ticket_id
            )
        )
        daily_ticket = dt_result.scalar_one_or_none()
        
        if not daily_ticket:
            return None
        
        # P0-4: 计算时间窗
        valid_from = datetime.combine(
            daily_ticket.date,
            daily_ticket.access_start_time
        )
        valid_to = datetime.combine(
            daily_ticket.date,
            daily_ticket.access_end_time
        )
        
        # 检查是否已存在
        existing_result = await self.db.execute(
            select(AccessGrant).where(
                AccessGrant.daily_ticket_id == daily_ticket_id,
                AccessGrant.worker_id == worker_id,
                AccessGrant.area_id == area_id
            )
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            return existing
        
        grant = AccessGrant(
            daily_ticket_id=daily_ticket_id,
            worker_id=worker_id,
            area_id=area_id,
            site_id=daily_ticket.site_id,
            valid_from=valid_from,
            valid_to=valid_to,
            status="PENDING_SYNC"
        )
        self.db.add(grant)
        await self.db.flush()
        
        # 推送
        from app.tasks.access import push_grant_task
        push_grant_task.delay(str(grant.grant_id))
        
        return grant
    
    async def revoke_grant(
        self, 
        grant_id: uuid.UUID, 
        reason: str = "MANUAL"
    ) -> bool:
        """
        撤销门禁授权
        
        Args:
            grant_id: 授权ID
            reason: 撤销原因
        
        Returns:
            bool: 是否成功
        """
        result = await self.db.execute(
            select(AccessGrant).where(AccessGrant.grant_id == grant_id)
        )
        grant = result.scalar_one_or_none()
        
        if not grant:
            return False
        
        # 如果已同步，撤销门禁侧权限
        if grant.status == "SYNCED" and grant.vendor_ref:
            try:
                await self.adapter.revoke_grant(grant)
            except Exception as e:
                logger.error(f"Failed to revoke grant from vendor: {e}")
        
        grant.status = "REVOKED"
        grant.revoked_at = datetime.now()
        grant.revoke_reason = reason
        
        logger.info(f"Access grant revoked: {grant_id}, reason={reason}")
        
        return True
    
    async def check_access(
        self, 
        worker_id: uuid.UUID, 
        area_id: uuid.UUID,
        check_time: datetime = None
    ) -> dict:
        """
        检查访问权限
        
        Args:
            worker_id: 工人ID
            area_id: 区域ID
            check_time: 检查时间（默认当前）
        
        Returns:
            dict: {"allowed": bool, "reason_code": str, "grant": AccessGrant}
        """
        if check_time is None:
            check_time = datetime.now()
        
        check_date = check_time.date()
        
        # 查找有效授权
        result = await self.db.execute(
            select(AccessGrant)
            .join(DailyTicket)
            .where(
                DailyTicket.date == check_date,
                AccessGrant.worker_id == worker_id,
                AccessGrant.area_id == area_id,
                AccessGrant.status == "SYNCED"
            )
        )
        grant = result.scalar_one_or_none()
        
        if not grant:
            # 查找是否有未同步的授权
            pending_result = await self.db.execute(
                select(AccessGrant)
                .join(DailyTicket)
                .where(
                    DailyTicket.date == check_date,
                    AccessGrant.worker_id == worker_id,
                    AccessGrant.area_id == area_id,
                    AccessGrant.status.in_(["PENDING_SYNC", "SYNC_FAILED"])
                )
            )
            pending_grant = pending_result.scalar_one_or_none()
            
            if pending_grant:
                return {
                    "allowed": False,
                    "reason_code": "SYNC_PENDING",
                    "reason_message": "权限同步中，请稍后重试"
                }
            
            # 查找是否在作业票中
            from app.models import DailyTicketWorker, WorkTicketArea
            
            dtw_result = await self.db.execute(
                select(DailyTicketWorker)
                .join(DailyTicket)
                .where(
                    DailyTicket.date == check_date,
                    DailyTicketWorker.worker_id == worker_id,
                    DailyTicketWorker.status == "ACTIVE"
                )
            )
            dtw = dtw_result.scalar_one_or_none()
            
            if not dtw:
                return {
                    "allowed": False,
                    "reason_code": "NOT_IN_TICKET",
                    "reason_message": "不在当日作业票名单中"
                }
            
            if dtw.training_status != "COMPLETED":
                return {
                    "allowed": False,
                    "reason_code": "TRAINING_INCOMPLETE",
                    "reason_message": "培训未完成"
                }
            
            return {
                "allowed": False,
                "reason_code": "AREA_NOT_ALLOWED",
                "reason_message": "该区域未授权"
            }
        
        # 检查时间窗
        if not (grant.valid_from <= check_time <= grant.valid_to):
            return {
                "allowed": False,
                "reason_code": "OUT_OF_TIME_WINDOW",
                "reason_message": f"不在授权时间段内（{grant.valid_from.time()} - {grant.valid_to.time()}）",
                "grant": grant
            }
        
        return {
            "allowed": True,
            "reason_code": None,
            "grant": grant
        }

