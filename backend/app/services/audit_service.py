"""
审计服务
"""
import uuid
from typing import Any, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog
from app.middleware.tenant import get_tenant_context

logger = logging.getLogger(__name__)


class AuditService:
    """审计服务 - 记录所有关键操作"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record(
        self,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID = None,
        resource_name: str = None,
        operator_id: uuid.UUID = None,
        old_value: dict = None,
        new_value: dict = None,
        reason: str = None,
        ip_address: str = None,
        user_agent: str = None,
        request_id: str = None,
        is_success: bool = True,
        error_message: str = None
    ) -> AuditLog:
        """
        记录审计日志
        
        Args:
            action: 操作类型 (CREATE/UPDATE/DELETE/LOGIN等)
            resource_type: 资源类型
            resource_id: 资源ID
            resource_name: 资源名称
            operator_id: 操作人ID
            old_value: 变更前的值
            new_value: 变更后的值
            reason: 变更原因
            ip_address: IP地址
            user_agent: User-Agent
            request_id: 请求ID
            is_success: 是否成功
            error_message: 错误信息
        
        Returns:
            AuditLog: 审计日志记录
        """
        # 获取租户上下文
        ctx = get_tenant_context()
        site_id = None
        operator_role = None
        
        if ctx:
            site_id = ctx.site_id or (ctx.accessible_sites[0] if ctx.accessible_sites else None)
            operator_role = ctx.user_role
        
        # 创建审计日志
        log = AuditLog(
            site_id=site_id,
            operator_id=operator_id,
            operator_role=operator_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            is_success=is_success,
            error_message=error_message
        )
        
        self.db.add(log)
        
        logger.info(
            f"Audit log recorded: action={action}, "
            f"resource_type={resource_type}, resource_id={resource_id}, "
            f"operator={operator_id}"
        )
        
        return log
    
    async def record_login(
        self,
        user_id: uuid.UUID,
        username: str,
        success: bool,
        ip_address: str = None,
        user_agent: str = None,
        error_message: str = None
    ) -> AuditLog:
        """记录登录日志"""
        return await self.record(
            action="LOGIN",
            resource_type="SysUser",
            resource_id=user_id,
            resource_name=username,
            operator_id=user_id,
            is_success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message
        )
    
    async def record_ticket_change(
        self,
        ticket_id: uuid.UUID,
        ticket_title: str,
        operator_id: uuid.UUID,
        changes: dict,
        reason: str = None
    ) -> AuditLog:
        """记录作业票变更"""
        return await self.record(
            action="TICKET_CHANGE",
            resource_type="WorkTicket",
            resource_id=ticket_id,
            resource_name=ticket_title,
            operator_id=operator_id,
            new_value=changes,
            reason=reason
        )
    
    async def record_access_grant(
        self,
        grant_id: uuid.UUID,
        worker_id: uuid.UUID,
        area_id: uuid.UUID,
        action: str = "CREATE"
    ) -> AuditLog:
        """记录门禁授权"""
        return await self.record(
            action=f"ACCESS_GRANT_{action}",
            resource_type="AccessGrant",
            resource_id=grant_id,
            new_value={
                "worker_id": str(worker_id),
                "area_id": str(area_id)
            }
        )

