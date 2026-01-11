"""
作业人员模型
"""
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .site import Site
    from .contractor import Contractor
    from .daily_ticket_worker import DailyTicketWorker
    from .training_session import TrainingSession
    from .access_grant import AccessGrant
    from .access_event import AccessEvent


class Worker(Base, TimestampMixin):
    """
    作业人员表
    - 与实名制系统对接，存储人员基本信息
    - 微信小程序绑定信息
    - 门禁人脸ID
    """
    __tablename__ = "worker"
    
    # 主键
    worker_id: Mapped[uuid.UUID] = mapped_column(
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
    
    # 外键 - 所属施工单位（可为空，可能是临时工）
    contractor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contractor.contractor_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    id_no: Mapped[str] = mapped_column(String(18), nullable=False, comment="身份证号")
    phone: Mapped[str] = mapped_column(String(32), nullable=False, comment="手机号")
    
    # 工种信息
    job_type: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="工种")
    team_name: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="班组名称")
    
    # 微信绑定信息
    wechat_unionid: Mapped[str | None] = mapped_column(
        String(64), 
        nullable=True, 
        unique=True,
        comment="微信unionid"
    )
    wechat_openid: Mapped[str | None] = mapped_column(
        String(64), 
        nullable=True,
        comment="微信openid"
    )
    
    # 门禁/人脸信息
    face_id: Mapped[str | None] = mapped_column(
        String(128), 
        nullable=True,
        comment="门禁系统人脸ID"
    )
    face_photo_url: Mapped[str | None] = mapped_column(
        String(512), 
        nullable=True,
        comment="人脸照片URL"
    )
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(20), 
        default="ACTIVE",
        comment="状态: ACTIVE/INACTIVE/BLACKLISTED"
    )
    is_bound: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="是否已绑定微信"
    )
    
    # 关系
    site: Mapped["Site"] = relationship("Site", back_populates="workers")
    contractor: Mapped["Contractor"] = relationship("Contractor", back_populates="workers")
    daily_ticket_workers: Mapped[List["DailyTicketWorker"]] = relationship(
        "DailyTicketWorker",
        back_populates="worker",
        lazy="selectin"
    )
    training_sessions: Mapped[List["TrainingSession"]] = relationship(
        "TrainingSession",
        back_populates="worker",
        lazy="selectin"
    )
    access_grants: Mapped[List["AccessGrant"]] = relationship(
        "AccessGrant",
        back_populates="worker",
        lazy="selectin"
    )
    access_events: Mapped[List["AccessEvent"]] = relationship(
        "AccessEvent",
        back_populates="worker",
        lazy="selectin"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_worker_id_no", "id_no"),
        Index("idx_worker_phone", "phone"),
        Index("idx_worker_site_status", "site_id", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Worker(worker_id={self.worker_id}, name={self.name})>"

