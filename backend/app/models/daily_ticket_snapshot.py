"""
每日快照模型 (P0-8)
避免历史数据被"篡改"
"""
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .daily_ticket import DailyTicket


class DailyTicketSnapshot(Base, TimestampMixin):
    """
    每日快照表 (P0-8: 避免历史"被篡改")
    - daily_ticket 生成时保存快照
    - 防止后续 ticket 变更影响历史记录
    - 记录当时的人员、区域、视频信息
    """
    __tablename__ = "daily_ticket_snapshot"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
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
    
    # 快照类型
    snapshot_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="快照类型: WORKER/AREA/VIDEO"
    )
    
    # 关联实体ID
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="关联实体ID（worker_id/area_id/video_id）"
    )
    
    # 冗余存储名称（便于展示历史记录）
    entity_name: Mapped[str | None] = mapped_column(
        String(255), 
        nullable=True,
        comment="实体名称"
    )
    
    # 额外元数据（如视频时长、区域门禁组ID等）
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, 
        nullable=True,
        comment="额外元数据"
    )
    
    # 关系
    daily_ticket: Mapped["DailyTicket"] = relationship(
        "DailyTicket", 
        back_populates="snapshots"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_snapshot_daily_type", "daily_ticket_id", "snapshot_type"),
        Index("idx_snapshot_entity", "entity_id"),
    )
    
    def __repr__(self) -> str:
        return f"<DailyTicketSnapshot(daily_ticket_id={self.daily_ticket_id}, type={self.snapshot_type})>"

