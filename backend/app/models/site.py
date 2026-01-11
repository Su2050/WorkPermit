"""
工地项目模型 - 租户主表 (P0-7)
所有业务数据都按site_id隔离
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .contractor import Contractor
    from .worker import Worker
    from .work_area import WorkArea
    from .work_ticket import WorkTicket


class Site(Base, TimestampMixin):
    """
    工地项目表 - 多租户隔离的核心实体
    
    P0-7: 租户 = 工地项目（site）
    - 最符合现实：一个工地一套门禁/规则/视频
    - ContractorAdmin 可访问其绑定的多个 site
    """
    __tablename__ = "site"
    
    # 主键
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="工地名称")
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="工地编码")
    address: Mapped[str | None] = mapped_column(Text, nullable=True, comment="工地地址")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="工地描述")
    
    # 配置项
    default_access_start_time: Mapped[str] = mapped_column(
        String(8), 
        default="06:00:00",
        comment="默认授权开始时间 HH:MM:SS"
    )
    default_access_end_time: Mapped[str] = mapped_column(
        String(8), 
        default="20:00:00",
        comment="默认授权结束时间 HH:MM:SS"
    )
    default_training_deadline: Mapped[str] = mapped_column(
        String(8), 
        default="07:30:00",
        comment="默认培训截止时间 HH:MM:SS"
    )
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    
    # 关系
    contractors: Mapped[List["Contractor"]] = relationship(
        "Contractor",
        back_populates="site",
        lazy="selectin"
    )
    workers: Mapped[List["Worker"]] = relationship(
        "Worker",
        back_populates="site",
        lazy="selectin"
    )
    work_areas: Mapped[List["WorkArea"]] = relationship(
        "WorkArea",
        back_populates="site",
        lazy="selectin"
    )
    work_tickets: Mapped[List["WorkTicket"]] = relationship(
        "WorkTicket",
        back_populates="site",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Site(site_id={self.site_id}, name={self.name})>"

