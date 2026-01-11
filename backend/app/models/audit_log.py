"""
审计日志模型
"""
import uuid
from typing import Any

from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAtMixin, generate_uuid


class AuditLog(Base, CreatedAtMixin):
    """
    审计日志表
    - 记录所有关键操作（PRD要求可追溯）
    - 审计日志不可篡改（只追加写入）
    - 记录：who、when、what、before、after
    """
    __tablename__ = "audit_log"
    
    # 主键
    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    
    # 外键 - 所属工地 (P0-7: 多租户)
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("site.site_id", ondelete="SET NULL"),
        nullable=True,  # 系统级操作可能没有site
        comment="工地ID"
    )
    
    # 操作人信息 (who)
    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="操作人ID"
    )
    operator_name: Mapped[str | None] = mapped_column(
        String(64), 
        nullable=True,
        comment="操作人姓名"
    )
    operator_role: Mapped[str | None] = mapped_column(
        String(32), 
        nullable=True,
        comment="操作人角色: SysAdmin/ContractorAdmin/Worker/System"
    )
    
    # 操作信息 (what)
    action: Mapped[str] = mapped_column(
        String(64), 
        nullable=False,
        comment="操作类型: CREATE/UPDATE/DELETE/LOGIN/LOGOUT/TICKET_CHANGE/ACCESS_GRANT等"
    )
    resource_type: Mapped[str] = mapped_column(
        String(64), 
        nullable=False,
        comment="资源类型: WorkTicket/DailyTicket/Worker/AccessGrant等"
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="资源ID"
    )
    resource_name: Mapped[str | None] = mapped_column(
        String(255), 
        nullable=True,
        comment="资源名称（便于展示）"
    )
    
    # 变更内容 (before/after)
    old_value: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, 
        nullable=True,
        comment="变更前的值"
    )
    new_value: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, 
        nullable=True,
        comment="变更后的值"
    )
    
    # 变更原因
    reason: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True,
        comment="变更原因"
    )
    
    # 请求信息
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 最长45字符
        nullable=True,
        comment="IP地址"
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(512), 
        nullable=True,
        comment="User-Agent"
    )
    request_id: Mapped[str | None] = mapped_column(
        String(64), 
        nullable=True,
        comment="请求ID（用于链路追踪）"
    )
    
    # 结果
    is_success: Mapped[bool] = mapped_column(
        default=True,
        comment="是否成功"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True,
        comment="错误信息"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_audit_site_action", "site_id", "action"),
        Index("idx_audit_operator", "operator_id"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(log_id={self.log_id}, action={self.action})>"

