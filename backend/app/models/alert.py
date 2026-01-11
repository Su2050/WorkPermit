"""
告警模型
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin, generate_uuid


class Alert(Base, TimestampMixin):
    """
    告警表
    存储系统告警信息
    """
    __tablename__ = "alert"
    
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
        comment="告警ID"
    )
    
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id"),
        nullable=False,
        comment="工地ID"
    )
    
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="告警类型: ACCESS_DENIED/FACE_MISMATCH/TICKET_EXPIRED/TRAINING_OVERDUE/DEVICE_OFFLINE等"
    )
    
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MEDIUM",
        comment="优先级: HIGH/MEDIUM/LOW"
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="UNACKNOWLEDGED",
        comment="状态: UNACKNOWLEDGED/ACKNOWLEDGED/RESOLVED"
    )
    
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="告警标题"
    )
    
    message: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="告警详情"
    )
    
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment="告警来源"
    )
    
    related_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="关联对象ID（如工人ID、设备ID等）"
    )
    
    acknowledged_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_user.user_id"),
        nullable=True,
        comment="确认人ID"
    )
    
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="确认时间"
    )
    
    resolved_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_user.user_id"),
        nullable=True,
        comment="解决人ID"
    )
    
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="解决时间"
    )
    
    resolution_note: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="解决说明"
    )

