"""
审计日志查询API
"""
import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import AuditLog, SysUser
from app.api.admin.auth import get_current_user
from app.middleware.tenant import get_tenant_context, TenantQueryFilter
from app.utils.response import success_response, error_response, ErrorCode
from app.utils.pagination import PaginationParams, paginate

router = APIRouter()


class AuditLogQuery(PaginationParams):
    """审计日志查询参数"""
    resource_type: Optional[str] = None
    resource_id: Optional[uuid.UUID] = None
    action: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    operator_id: Optional[uuid.UUID] = None


@router.get("")
async def list_audit_logs(
    query: AuditLogQuery = Depends(),
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询审计日志
    
    支持筛选：
    - resource_type: 资源类型 (WorkTicket/DailyTicket/Worker等)
    - action: 操作类型 (CREATE/UPDATE/DELETE/TICKET_CHANGE等)
    - start_date/end_date: 时间范围
    - operator_id: 操作人ID
    """
    ctx = get_tenant_context()
    
    # 构建查询
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    
    # 多租户过滤
    stmt = TenantQueryFilter.apply(stmt, ctx)
    
    # 资源类型过滤
    if query.resource_type:
        stmt = stmt.where(AuditLog.resource_type == query.resource_type)
    
    # 资源ID过滤
    if query.resource_id:
        stmt = stmt.where(AuditLog.resource_id == query.resource_id)
    
    # 操作类型过滤
    if query.action:
        stmt = stmt.where(AuditLog.action == query.action)
    
    # 时间范围过滤
    if query.start_date:
        stmt = stmt.where(AuditLog.created_at >= datetime.combine(query.start_date, datetime.min.time()))
    if query.end_date:
        stmt = stmt.where(AuditLog.created_at <= datetime.combine(query.end_date, datetime.max.time()))
    
    # 操作人过滤
    if query.operator_id:
        stmt = stmt.where(AuditLog.operator_id == query.operator_id)
    
    # 分页
    result = await paginate(db, stmt, query)
    
    # 格式化响应
    items = []
    for log in result.items:
        items.append({
            "log_id": str(log.log_id),
            "operator_id": str(log.operator_id) if log.operator_id else None,
            "operator_name": log.operator_name,
            "operator_role": log.operator_role,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "resource_name": log.resource_name,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "reason": log.reason,
            "ip_address": log.ip_address,
            "is_success": log.is_success,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat()
        })
    
    return success_response({
        "items": items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size
    })


@router.get("/{log_id}")
async def get_audit_log(
    log_id: uuid.UUID,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取审计日志详情"""
    result = await db.execute(
        select(AuditLog).where(AuditLog.log_id == log_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="审计日志不存在"
        )
    
    return success_response({
        "log_id": str(log.log_id),
        "operator_id": str(log.operator_id) if log.operator_id else None,
        "operator_name": log.operator_name,
        "operator_role": log.operator_role,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": str(log.resource_id) if log.resource_id else None,
        "resource_name": log.resource_name,
        "old_value": log.old_value,
        "new_value": log.new_value,
        "reason": log.reason,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "request_id": log.request_id,
        "is_success": log.is_success,
        "error_message": log.error_message,
        "created_at": log.created_at.isoformat()
    })


