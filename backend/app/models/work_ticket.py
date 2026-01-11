"""
作业票模型
"""
import uuid
from datetime import date, time
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text, Date, Time, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .site import Site
    from .contractor import Contractor
    from .work_ticket_worker import WorkTicketWorker
    from .work_ticket_area import WorkTicketArea
    from .work_ticket_video import WorkTicketVideo
    from .daily_ticket import DailyTicket


class WorkTicket(Base, TimestampMixin):
    """
    作业票表
    - 描述一个施工任务的日期范围、区域、参与人员、培训视频与截止规则
    - 创建后会拆分生成每日的 DailyTicket
    """
    __tablename__ = "work_ticket"
    
    # 主键
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    
    # 外键 - 所属工地 (P0-7: 多租户)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 外键 - 所属施工单位
    contractor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contractor.contractor_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 基本信息
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="作业票名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="作业描述")
    
    # 日期范围
    start_date: Mapped[date] = mapped_column(Date, nullable=False, comment="开始日期")
    end_date: Mapped[date] = mapped_column(Date, nullable=False, comment="结束日期")
    
    # 默认时间配置（可被每日覆盖）
    default_access_start_time: Mapped[time] = mapped_column(
        Time, 
        nullable=False,
        default=time(6, 0, 0),
        comment="默认授权开始时间"
    )
    default_access_end_time: Mapped[time] = mapped_column(
        Time, 
        nullable=False,
        default=time(20, 0, 0),
        comment="默认授权结束时间"
    )
    default_training_deadline_time: Mapped[time] = mapped_column(
        Time, 
        nullable=False,
        default=time(7, 30, 0),
        comment="默认培训截止时间"
    )
    
    # 通知配置
    notify_on_publish: Mapped[bool] = mapped_column(
        default=True,
        comment="发布时立即通知"
    )
    daily_reminder_enabled: Mapped[bool] = mapped_column(
        default=True,
        comment="启用每日提醒"
    )
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(20), 
        default="DRAFT",
        comment="状态: DRAFT/ACTIVE/CANCELLED"
    )
    
    # 创建人
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="创建人ID"
    )
    
    # 备注
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")
    
    # 关系
    site: Mapped["Site"] = relationship("Site", back_populates="work_tickets")
    contractor: Mapped["Contractor"] = relationship("Contractor", back_populates="work_tickets")
    
    # P0-8: 多对多关系表
    work_ticket_workers: Mapped[List["WorkTicketWorker"]] = relationship(
        "WorkTicketWorker",
        back_populates="ticket",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    work_ticket_areas: Mapped[List["WorkTicketArea"]] = relationship(
        "WorkTicketArea",
        back_populates="ticket",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    work_ticket_videos: Mapped[List["WorkTicketVideo"]] = relationship(
        "WorkTicketVideo",
        back_populates="ticket",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    # 每日票据
    daily_tickets: Mapped[List["DailyTicket"]] = relationship(
        "DailyTicket",
        back_populates="ticket",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_ticket_site_date", "site_id", "start_date", "end_date"),
        Index("idx_ticket_contractor", "contractor_id", "status"),
        Index("idx_ticket_status_date", "status", "start_date"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkTicket(ticket_id={self.ticket_id}, title={self.title})>"

