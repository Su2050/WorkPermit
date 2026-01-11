"""
施工区域模型
"""
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .site import Site
    from .work_ticket_area import WorkTicketArea
    from .access_grant import AccessGrant
    from .access_event import AccessEvent


class WorkArea(Base, TimestampMixin):
    """
    施工区域表
    - 与门禁权限组/设备组关联
    - 一个区域可关联多个门禁设备（同一权限组）
    """
    __tablename__ = "work_area"
    
    # 主键
    area_id: Mapped[uuid.UUID] = mapped_column(
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
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="区域名称")
    code: Mapped[str] = mapped_column(String(64), nullable=False, comment="区域编码")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="区域描述")
    
    # 门禁关联
    access_group_id: Mapped[str | None] = mapped_column(
        String(128), 
        nullable=True,
        comment="门禁系统权限组ID"
    )
    access_group_name: Mapped[str | None] = mapped_column(
        String(255), 
        nullable=True,
        comment="门禁系统权限组名称"
    )
    
    # 位置信息
    building: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="所属建筑")
    floor: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="楼层")
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    
    # 关系
    site: Mapped["Site"] = relationship("Site", back_populates="work_areas")
    work_ticket_areas: Mapped[List["WorkTicketArea"]] = relationship(
        "WorkTicketArea",
        back_populates="area",
        lazy="selectin"
    )
    access_grants: Mapped[List["AccessGrant"]] = relationship(
        "AccessGrant",
        back_populates="area",
        lazy="selectin"
    )
    access_events: Mapped[List["AccessEvent"]] = relationship(
        "AccessEvent",
        back_populates="area",
        lazy="selectin"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_area_site_active", "site_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkArea(area_id={self.area_id}, name={self.name})>"

