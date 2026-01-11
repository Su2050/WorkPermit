"""
作业票-区域关联模型 (P0-8)
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
    from .work_area import WorkArea


class WorkTicketArea(Base, TimestampMixin):
    """
    作业票-区域关联表 (P0-8: 多对多关系表)
    - 记录作业票关联的施工区域
    - 支持变更追溯（添加/移除时间、操作人）
    """
    __tablename__ = "work_ticket_area"
    
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
        back_populates="work_ticket_areas"
    )
    area: Mapped["WorkArea"] = relationship(
        "WorkArea", 
        back_populates="work_ticket_areas"
    )
    
    # 约束和索引
    __table_args__ = (
        UniqueConstraint("ticket_id", "area_id", name="uq_ticket_area"),
        Index("idx_ticket_area_ticket", "ticket_id", "status"),
        Index("idx_ticket_area_area", "area_id"),
        Index("idx_ticket_area_site", "site_id"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkTicketArea(ticket_id={self.ticket_id}, area_id={self.area_id})>"

