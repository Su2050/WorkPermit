"""
学习会话模型 (P0-1调整: 绑定单个视频)
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .daily_ticket import DailyTicket
    from .worker import Worker
    from .training_video import TrainingVideo


class TrainingSession(Base, TimestampMixin):
    """
    学习会话表 (P0-1: session 按视频拆分)
    - 一人一天一视频一session
    - 记录学习进度、校验结果、可疑事件
    - 支持防作弊逻辑 (P0-2)
    """
    __tablename__ = "training_session"
    
    # 主键
    session_id: Mapped[uuid.UUID] = mapped_column(
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
    
    # 外键 - 视频 (P0-1: 关键 - 绑定到单个视频)
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("training_video.video_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 外键 - 所属工地 (P0-7: 多租户，冗余存储便于查询)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 会话状态
    status: Mapped[str] = mapped_column(
        String(20), 
        default="NOT_STARTED",
        comment="状态: NOT_STARTED/IN_LEARNING/WAITING_VERIFY/COMPLETED/FAILED"
    )
    
    # 会话Token（用于验证请求合法性）
    session_token: Mapped[str | None] = mapped_column(
        String(64), 
        nullable=True,
        comment="会话Token"
    )
    
    # 时间记录
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始时间"
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="结束时间"
    )
    
    # 观看时长 (P0-2: 防作弊)
    valid_watch_sec: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="有效观看时长（秒）"
    )
    total_watch_sec: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="总观看时长（秒）"
    )
    
    # 播放进度 (P0-2: 用于防作弊验证)
    last_position: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="最后播放位置（秒）"
    )
    last_heartbeat_ts: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="最后心跳时间戳"
    )
    
    # 随机校验结果 (P0-2)
    random_check_passed: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="随机校验通过次数"
    )
    random_check_failed: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="随机校验失败次数"
    )
    consecutive_check_failures: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="连续校验失败次数"
    )
    last_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后校验时间"
    )
    
    # 可疑事件计数 (P0-2: 防作弊)
    suspicious_event_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="可疑事件计数（快进/跳跃）"
    )
    
    # 失败原因
    failure_reason: Mapped[str | None] = mapped_column(
        String(100), 
        nullable=True,
        comment="失败原因: TOO_MANY_SUSPICIOUS_EVENTS/CHECK_FAILED/HEARTBEAT_TIMEOUT"
    )
    
    # 视频状态 (P0-2: 网络容错)
    video_state: Mapped[str] = mapped_column(
        String(20), 
        default="unknown",
        comment="视频状态: playing/paused/background/unknown"
    )
    
    # 关系
    daily_ticket: Mapped["DailyTicket"] = relationship(
        "DailyTicket", 
        back_populates="training_sessions"
    )
    worker: Mapped["Worker"] = relationship(
        "Worker", 
        back_populates="training_sessions"
    )
    video: Mapped["TrainingVideo"] = relationship(
        "TrainingVideo", 
        back_populates="training_sessions"
    )
    
    # 约束和索引 (P0-1: 一人一天一视频一session)
    __table_args__ = (
        UniqueConstraint(
            "daily_ticket_id", "worker_id", "video_id", 
            name="uq_session_daily_worker_video"
        ),
        Index("idx_session_status", "daily_ticket_id", "worker_id", "status"),
        Index("idx_session_site", "site_id"),
        Index("idx_session_worker", "worker_id"),
    )
    
    def __repr__(self) -> str:
        return f"<TrainingSession(session_id={self.session_id}, status={self.status})>"

