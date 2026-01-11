"""
作业票-人员关联模型 (P0-8)
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, UniqueConstraint, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .work_ticket import WorkTicket
    from .worker import Worker


class WorkTicketWorker(Base, TimestampMixin):
    """
    作业票-人员关联表 (P0-8: 多对多关系表)
    - 记录作业票关联的人员
    - 支持变更追溯（添加/移除时间、操作人）
    """
    __tablename__ = "work_ticket_worker"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    
    # 外键 - 作业票
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_ticket.ticket_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 外键 - 人员
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worker.worker_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 外键 - 所属工地 (P0-7: 多租户，冗余存储便于查询)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 操作追溯
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="添加时间"
    )
    added_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="添加人ID"
    )
    
    # 状态 (P0-5: 变更补偿)
    status: Mapped[str] = mapped_column(
        String(20), 
        default="ACTIVE",
        comment="状态: ACTIVE/REMOVED"
    )
    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="移除时间"
    )
    removed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="移除人ID"
    )
    
    # 关系
    ticket: Mapped["WorkTicket"] = relationship(
        "WorkTicket", 
        back_populates="work_ticket_workers"
    )
    worker: Mapped["Worker"] = relationship("Worker")
    
    # 约束和索引
    __table_args__ = (
        UniqueConstraint("ticket_id", "worker_id", name="uq_ticket_worker"),
        Index("idx_ticket_worker_ticket", "ticket_id", "status"),
        Index("idx_ticket_worker_worker", "worker_id"),
        Index("idx_ticket_worker_site", "site_id"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkTicketWorker(ticket_id={self.ticket_id}, worker_id={self.worker_id})>"

