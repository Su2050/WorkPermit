"""
日票-人员状态模型 (P0-1调整)
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, ForeignKey, UniqueConstraint, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .daily_ticket import DailyTicket
    from .worker import Worker


class DailyTicketWorker(Base, TimestampMixin):
    """
    日票-人员状态表 (P0-1: 多视频学习完成判定)
    - 记录每个工人在每日作业票中的培训状态
    - 包含视频完成进度统计
    - 记录授权状态
    """
    __tablename__ = "daily_ticket_worker"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
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
    
    # 外键 - 所属工地 (P0-7: 多租户，冗余存储便于查询)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # P0-1: 多视频学习进度
    total_video_count: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment="需要学习的视频总数"
    )
    completed_video_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="已完成的视频数"
    )
    
    # 培训状态
    training_status: Mapped[str] = mapped_column(
        String(20), 
        default="NOT_STARTED",
        comment="培训状态: NOT_STARTED/IN_LEARNING/COMPLETED/FAILED"
    )
    
    # 授权状态
    authorized: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="是否已授权门禁"
    )
    
    # 通知记录
    last_notify_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后通知时间"
    )
    notify_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="通知次数"
    )
    
    # 变更状态 (P0-5: 变更补偿)
    status: Mapped[str] = mapped_column(
        String(20), 
        default="ACTIVE",
        comment="状态: ACTIVE/REMOVED"
    )
    
    # 关系
    daily_ticket: Mapped["DailyTicket"] = relationship(
        "DailyTicket", 
        back_populates="daily_ticket_workers"
    )
    worker: Mapped["Worker"] = relationship(
        "Worker", 
        back_populates="daily_ticket_workers"
    )
    
    # 约束和索引
    __table_args__ = (
        UniqueConstraint("daily_ticket_id", "worker_id", name="uq_daily_ticket_worker"),
        Index("idx_dtw_daily_ticket_status", "daily_ticket_id", "training_status"),
        Index("idx_dtw_worker", "worker_id"),
        Index("idx_dtw_site_status", "site_id", "training_status"),
    )
    
    @property
    def remaining_videos(self) -> int:
        """剩余需要学习的视频数"""
        return max(0, self.total_video_count - self.completed_video_count)
    
    @property
    def is_training_complete(self) -> bool:
        """培训是否完成"""
        return self.training_status == "COMPLETED"
    
    def __repr__(self) -> str:
        return f"<DailyTicketWorker(daily_ticket_id={self.daily_ticket_id}, worker_id={self.worker_id})>"

