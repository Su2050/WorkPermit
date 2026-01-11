"""
系统用户模型
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, ForeignKey, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .site import Site
    from .contractor import Contractor


class SysUser(Base, TimestampMixin):
    """
    系统用户表
    - 后台管理系统的用户
    - 支持RBAC角色: SysAdmin / ContractorAdmin
    - 支持多租户访问控制
    """
    __tablename__ = "sys_user"
    
    # 主键
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    
    # 登录信息
    username: Mapped[str] = mapped_column(
        String(64), 
        unique=True,
        nullable=False,
        comment="用户名"
    )
    password_hash: Mapped[str] = mapped_column(
        String(128), 
        nullable=False,
        comment="密码哈希"
    )
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    email: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="手机号")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="头像URL")
    
    # 角色 (RBAC)
    role: Mapped[str] = mapped_column(
        String(32), 
        nullable=False,
        default="ContractorAdmin",
        comment="角色: SysAdmin/ContractorAdmin"
    )
    
    # 关联 - 施工单位（ContractorAdmin 必须关联）
    contractor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contractor.contractor_id", ondelete="SET NULL"),
        nullable=True,
        comment="所属施工单位ID"
    )
    
    # P0-7: 多租户 - 可访问的工地（SysAdmin 可访问所有，ContractorAdmin 按绑定访问）
    # 这里简化处理，通过 contractor -> site 关联
    # 如果需要更灵活的权限，可以单独建一张 user_site 关联表
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否锁定")
    
    # 登录信息
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后登录时间"
    )
    last_login_ip: Mapped[str | None] = mapped_column(
        String(45), 
        nullable=True,
        comment="最后登录IP"
    )
    login_fail_count: Mapped[int] = mapped_column(
        default=0,
        comment="登录失败次数"
    )
    
    # 关系
    contractor: Mapped["Contractor"] = relationship("Contractor")
    
    # 索引
    __table_args__ = (
        Index("idx_user_role", "role", "is_active"),
        Index("idx_user_contractor", "contractor_id"),
    )
    
    @property
    def is_sys_admin(self) -> bool:
        """是否为系统管理员"""
        return self.role == "SysAdmin"
    
    @property
    def is_contractor_admin(self) -> bool:
        """是否为施工单位管理员"""
        return self.role == "ContractorAdmin"
    
    def __repr__(self) -> str:
        return f"<SysUser(user_id={self.user_id}, username={self.username})>"

