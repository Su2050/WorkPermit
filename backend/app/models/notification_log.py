"""
通知日志模型
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import String, Integer, Text, ForeignKey, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, generate_uuid


class NotificationLog(Base, TimestampMixin):
    """
    通知日志表
    - 记录所有通知发送记录
    - 支持去重、重试追溯
    - 记录发送结果和错误信息
    """
    __tablename__ = "notification_log"
    
    # 主键
    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    
    # 外键 - 所属工地 (P0-7: 多租户)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 关联信息
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worker.worker_id", ondelete="CASCADE"),
        nullable=False,
        comment="接收人ID"
    )
    daily_ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_ticket.daily_ticket_id", ondelete="SET NULL"),
        nullable=True,
        comment="关联日票ID"
    )
    
    # 通知类型 (P0-3: 未读替代指标)
    notification_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="通知类型: TICKET_PUBLISHED/DAILY_REMINDER/DEADLINE_SOON/BIND_REQUIRED"
    )
    
    # 优先级 (P1-2)
    priority: Mapped[int] = mapped_column(
        Integer, 
        default=3,
        comment="优先级: 1-紧急/2-高/3-普通/4-低"
    )
    
    # 发送渠道
    channel: Mapped[str] = mapped_column(
        String(32), 
        default="WECHAT_SUBSCRIBE",
        comment="发送渠道: WECHAT_SUBSCRIBE/SMS/APP_PUSH"
    )
    
    # 发送内容
    title: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="通知标题")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="通知内容")
    template_id: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="模板ID")
    template_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, 
        nullable=True,
        comment="模板数据"
    )
    
    # 发送状态
    status: Mapped[str] = mapped_column(
        String(20), 
        default="PENDING",
        comment="状态: PENDING/SENT/FAILED"
    )
    
    # 时间记录
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="计划发送时间"
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="实际发送时间"
    )
    
    # 重试信息
    retry_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="重试次数"
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, 
        default=5,
        comment="最大重试次数"
    )
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="下次重试时间"
    )
    
    # 错误信息
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="错误码")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    
    # 第三方响应
    vendor_response: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, 
        nullable=True,
        comment="第三方响应数据"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_notification_site_type", "site_id", "notification_type"),
        Index("idx_notification_worker", "worker_id", "notification_type"),
        Index("idx_notification_status", "status", "scheduled_at"),
        Index("idx_notification_daily_ticket", "daily_ticket_id"),
    )
    
    def __repr__(self) -> str:
        return f"<NotificationLog(log_id={self.log_id}, type={self.notification_type})>"

