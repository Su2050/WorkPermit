"""
培训视频模型
"""
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .site import Site
    from .work_ticket_video import WorkTicketVideo
    from .training_session import TrainingSession


class TrainingVideo(Base, TimestampMixin):
    """
    培训视频表
    - 视频存储到对象存储（MinIO/OSS），这里存元数据与播放URL
    - 支持按工地归属，也可跨工地共享（通过配置）
    """
    __tablename__ = "training_video"
    
    # 主键
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    
    # 外键 - 所属工地 (P0-7: 多租户，视频可跨site共享但归属某site)
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 基本信息
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="视频标题")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="视频描述")
    
    # 视频文件信息
    file_url: Mapped[str] = mapped_column(String(512), nullable=False, comment="视频文件URL")
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="缩略图URL")
    duration_sec: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        default=0,
        comment="视频时长（秒）"
    )
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="文件大小（字节）")
    
    # 分类
    category: Mapped[str | None] = mapped_column(
        String(64), 
        nullable=True,
        comment="视频分类: 高处作业/用电安全/消防安全等"
    )
    
    # 配置
    is_shared: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="是否可跨工地共享"
    )
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(20), 
        default="ACTIVE",
        comment="状态: DRAFT/ACTIVE/ARCHIVED"
    )
    
    # 关系
    work_ticket_videos: Mapped[List["WorkTicketVideo"]] = relationship(
        "WorkTicketVideo",
        back_populates="video",
        lazy="selectin"
    )
    training_sessions: Mapped[List["TrainingSession"]] = relationship(
        "TrainingSession",
        back_populates="video",
        lazy="selectin"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_video_site_status", "site_id", "status"),
        Index("idx_video_category", "category"),
    )
    
    def __repr__(self) -> str:
        return f"<TrainingVideo(video_id={self.video_id}, title={self.title})>"

