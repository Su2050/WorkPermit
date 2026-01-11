"""
进出记录模型 (P1-1调整: 去重约束)
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, UniqueConstraint, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .worker import Worker
    from .work_area import WorkArea


class AccessEvent(Base, TimestampMixin):
    """
    进出记录表 (P1-1: 去重约束)
    - 门禁设备上报的进出事件
    - 支持事件去重（避免重复记录）
    - 记录拒绝原因码（用于追溯）
    """
    __tablename__ = "access_event"
    
    # 主键
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    
    # 门禁侧事件ID (P1-1: 优先用于去重)
    vendor_event_id: Mapped[str | None] = mapped_column(
        String(128), 
        nullable=True,
        unique=True,
        comment="门禁系统事件ID"
    )
    
    # 设备信息
    device_id: Mapped[str] = mapped_column(
        String(64), 
        nullable=False,
        comment="设备ID"
    )
    device_name: Mapped[str | None] = mapped_column(
        String(128), 
        nullable=True,
        comment="设备名称"
    )
    
    # 外键 - 人员
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worker.worker_id", ondelete="SET NULL"),
        nullable=True,  # 可能是未识别的人员
        comment="人员ID"
    )
    
    # 外键 - 区域
    area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_area.area_id", ondelete="SET NULL"),
        nullable=True,
        comment="区域ID"
    )
    
    # 外键 - 所属工地 (P0-7: 多租户)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 事件信息
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="事件时间"
    )
    direction: Mapped[str | None] = mapped_column(
        String(10), 
        nullable=True,
        comment="方向: IN/OUT"
    )
    result: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="结果: PASS/DENY"
    )
    
    # 拒绝原因码（PRD要求100%可解释）
    reason_code: Mapped[str | None] = mapped_column(
        String(50), 
        nullable=True,
        comment="原因码: NOT_IN_TICKET/TRAINING_INCOMPLETE/OUT_OF_TIME_WINDOW/AREA_NOT_ALLOWED/SYNC_PENDING/IDENTITY_NOT_BOUND/DEVICE_ERROR"
    )
    reason_message: Mapped[str | None] = mapped_column(
        String(255), 
        nullable=True,
        comment="原因描述"
    )
    
    # 抓拍图（可选）
    face_photo_url: Mapped[str | None] = mapped_column(
        String(512), 
        nullable=True,
        comment="抓拍图URL"
    )
    
    # 识别信息
    face_id: Mapped[str | None] = mapped_column(
        String(128), 
        nullable=True,
        comment="人脸ID"
    )
    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="识别置信度"
    )
    
    # 关系
    worker: Mapped["Worker"] = relationship(
        "Worker", 
        back_populates="access_events"
    )
    area: Mapped["WorkArea"] = relationship(
        "WorkArea", 
        back_populates="access_events"
    )
    
    # 约束和索引 (P1-1: 去重)
    __table_args__ = (
        # 兜底去重约束（device_id + worker_id + event_time + direction）
        UniqueConstraint(
            "device_id", "worker_id", "event_time", "direction",
            name="uq_event_device_worker_time_direction"
        ),
        # 索引
        Index("idx_event_site_time", "site_id", "event_time"),
        Index("idx_event_worker_time", "worker_id", "event_time"),
        Index("idx_event_result", "result", "event_time"),
        Index("idx_event_reason", "reason_code"),
    )
    
    def __repr__(self) -> str:
        return f"<AccessEvent(event_id={self.event_id}, result={self.result})>"

