"""
日作业票模型
"""
import uuid
from datetime import date, time
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Date, Time, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .work_ticket import WorkTicket
    from .daily_ticket_worker import DailyTicketWorker
    from .daily_ticket_snapshot import DailyTicketSnapshot
    from .training_session import TrainingSession
    from .access_grant import AccessGrant


class DailyTicket(Base, TimestampMixin):
    """
    日作业票表
    - 系统把"多日范围"的作业票拆成按天的记录
    - 用于"当日培训→当日授权"的逻辑控制
    - 状态机: DRAFT → PUBLISHED → IN_PROGRESS → EXPIRED / CANCELLED
    """
    __tablename__ = "daily_ticket"
    
    # 主键
    daily_ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    
    # 外键 - 父作业票
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_ticket.ticket_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 外键 - 所属工地 (P0-7: 多租户，冗余存储便于查询)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 日期
    date: Mapped[date] = mapped_column(Date, nullable=False, comment="日期")
    
    # 时间配置（从父作业票继承，可单独修改）
    access_start_time: Mapped[time] = mapped_column(
        Time, 
        nullable=False,
        comment="授权开始时间"
    )
    access_end_time: Mapped[time] = mapped_column(
        Time, 
        nullable=False,
        comment="授权结束时间"
    )
    training_deadline_time: Mapped[time] = mapped_column(
        Time, 
        nullable=False,
        comment="培训截止时间"
    )
    
    # 状态机
    status: Mapped[str] = mapped_column(
        String(20), 
        default="DRAFT",
        comment="状态: DRAFT/PUBLISHED/IN_PROGRESS/EXPIRED/CANCELLED"
    )
    
    # 取消原因（如果状态为CANCELLED）
    cancel_reason: Mapped[str | None] = mapped_column(
        String(500), 
        nullable=True,
        comment="取消原因"
    )
    
    # 关系
    ticket: Mapped["WorkTicket"] = relationship(
        "WorkTicket", 
        back_populates="daily_tickets"
    )
    
    # 日票-人员状态
    daily_ticket_workers: Mapped[List["DailyTicketWorker"]] = relationship(
        "DailyTicketWorker",
        back_populates="daily_ticket",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    # 每日快照 (P0-8)
    snapshots: Mapped[List["DailyTicketSnapshot"]] = relationship(
        "DailyTicketSnapshot",
        back_populates="daily_ticket",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    # 学习会话
    training_sessions: Mapped[List["TrainingSession"]] = relationship(
        "TrainingSession",
        back_populates="daily_ticket",
        lazy="selectin"
    )
    
    # 门禁授权
    access_grants: Mapped[List["AccessGrant"]] = relationship(
        "AccessGrant",
        back_populates="daily_ticket",
        lazy="selectin"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_daily_ticket_date_status", "date", "status"),
        Index("idx_daily_ticket_site_date", "site_id", "date"),
        Index("idx_daily_ticket_ticket", "ticket_id", "date"),
    )
    
    def __repr__(self) -> str:
        return f"<DailyTicket(daily_ticket_id={self.daily_ticket_id}, date={self.date})>"

