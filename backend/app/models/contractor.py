"""
施工单位模型
"""
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .site import Site
    from .worker import Worker
    from .work_ticket import WorkTicket


class Contractor(Base, TimestampMixin):
    """
    施工单位表
    - 施工单位管理员(ContractorAdmin)归属于施工单位
    - 可管理其下属的作业人员和作业票
    """
    __tablename__ = "contractor"
    
    # 主键
    contractor_id: Mapped[uuid.UUID] = mapped_column(
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
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="单位名称")
    code: Mapped[str] = mapped_column(String(64), nullable=False, comment="单位编码")
    contact_person: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="联系人")
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="联系电话")
    address: Mapped[str | None] = mapped_column(Text, nullable=True, comment="单位地址")
    
    # 资质信息
    license_no: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="营业执照号")
    qualification_level: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="资质等级")
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    
    # 关系
    site: Mapped["Site"] = relationship("Site", back_populates="contractors")
    workers: Mapped[List["Worker"]] = relationship(
        "Worker",
        back_populates="contractor",
        lazy="selectin"
    )
    work_tickets: Mapped[List["WorkTicket"]] = relationship(
        "WorkTicket",
        back_populates="contractor",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Contractor(contractor_id={self.contractor_id}, name={self.name})>"

