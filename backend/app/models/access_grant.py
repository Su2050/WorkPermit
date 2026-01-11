"""
门禁授权模型 (P0-4调整: 时间窗强制)
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Text, ForeignKey, UniqueConstraint, Index, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .daily_ticket import DailyTicket
    from .worker import Worker
    from .work_area import WorkArea


class AccessGrant(Base, TimestampMixin):
    """
    门禁授权表 (P0-4: 时间窗强制字段)
    - 对某日、某人、某区域，在指定时间窗内授予"进入权限"
    - 状态机: PENDING_SYNC → SYNCED / SYNC_FAILED → REVOKED
    - 支持幂等推送 (P1-1)
    """
    __tablename__ = "access_grant"
    
    # 主键
    grant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    
    # 外键 - 日作业票
    daily_ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_ticket.daily_ticket_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 外键 - 人员
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worker.worker_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 外键 - 区域
    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_area.area_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 外键 - 所属工地 (P0-7: 多租户，冗余存储便于查询)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # P0-4: 时间窗强制字段
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="授权开始时间（精确到秒）"
    )
    valid_to: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="授权结束时间（精确到秒）"
    )
    
    # 同步状态
    status: Mapped[str] = mapped_column(
        String(20), 
        default="PENDING_SYNC",
        comment="状态: PENDING_SYNC/SYNCED/SYNC_FAILED/REVOKED"
    )
    
    # 同步重试信息
    sync_attempt_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="同步尝试次数"
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后同步时间"
    )
    sync_error_msg: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True,
        comment="同步错误信息"
    )
    
    # 门禁侧返回的ID (P1-1: 幂等键)
    vendor_ref: Mapped[str | None] = mapped_column(
        String(128), 
        nullable=True,
        comment="门禁系统返回的授权ID"
    )
    
    # 撤销信息
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="撤销时间"
    )
    revoke_reason: Mapped[str | None] = mapped_column(
        String(100), 
        nullable=True,
        comment="撤销原因: TICKET_CANCELLED/EXPIRED/WORKER_REMOVED/AREA_REMOVED"
    )
    
    # 关系
    daily_ticket: Mapped["DailyTicket"] = relationship(
        "DailyTicket", 
        back_populates="access_grants"
    )
    worker: Mapped["Worker"] = relationship(
        "Worker", 
        back_populates="access_grants"
    )
    area: Mapped["WorkArea"] = relationship(
        "WorkArea", 
        back_populates="access_grants"
    )
    
    # 约束和索引
    __table_args__ = (
        # 唯一约束
        UniqueConstraint(
            "daily_ticket_id", "worker_id", "area_id", 
            name="uq_grant_daily_worker_area"
        ),
        # P0-4: 时间窗约束
        CheckConstraint("valid_to > valid_from", name="ck_grant_time_window"),
        # 索引
        Index("idx_grant_site_status", "site_id", "status"),
        Index("idx_grant_sync_status", "status", "created_at"),
        Index("idx_grant_worker", "worker_id"),
        Index("idx_grant_valid_time", "valid_from", "valid_to"),
    )
    
    @property
    def is_valid_now(self) -> bool:
        """当前是否在有效时间窗内"""
        now = datetime.now(self.valid_from.tzinfo)
        return self.valid_from <= now <= self.valid_to and self.status == "SYNCED"
    
    def __repr__(self) -> str:
        return f"<AccessGrant(grant_id={self.grant_id}, status={self.status})>"

