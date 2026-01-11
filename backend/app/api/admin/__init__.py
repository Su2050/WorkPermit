"""
后台管理API
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .tickets import router as tickets_router
from .areas import router as areas_router
from .videos import router as videos_router
from .workers import router as workers_router
from .contractors import router as contractors_router
from .sites import router as sites_router
from .reports import router as reports_router
from .audit_logs import router as audit_logs_router
from .alerts import router as alerts_router
from .users import router as users_router
from .daily_tickets import router as daily_tickets_router

admin_router = APIRouter()

admin_router.include_router(auth_router, prefix="/auth", tags=["认证"])
admin_router.include_router(tickets_router, prefix="/work-tickets", tags=["作业票管理"])
admin_router.include_router(daily_tickets_router, tags=["每日票据管理"])
admin_router.include_router(areas_router, prefix="/areas", tags=["区域管理"])
admin_router.include_router(videos_router, prefix="/videos", tags=["视频管理"])
admin_router.include_router(workers_router, prefix="/workers", tags=["人员管理"])
admin_router.include_router(contractors_router, prefix="/contractors", tags=["施工单位管理"])
admin_router.include_router(sites_router, prefix="/sites", tags=["工地管理"])
admin_router.include_router(reports_router, prefix="/reports", tags=["报表统计"])
admin_router.include_router(alerts_router, prefix="/alerts", tags=["告警管理"])
admin_router.include_router(users_router, prefix="/users", tags=["用户管理"])
admin_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["审计日志"])

