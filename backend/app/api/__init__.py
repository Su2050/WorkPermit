"""
API路由汇总
"""
from fastapi import APIRouter

from .admin import admin_router
from .mp import mp_router
from .integration import integration_router

api_router = APIRouter()

# 后台管理API
api_router.include_router(admin_router, prefix="/admin", tags=["后台管理"])

# 小程序API
api_router.include_router(mp_router, prefix="/mp", tags=["小程序"])

# 集成API（门禁事件回调等）
api_router.include_router(integration_router, prefix="/integration", tags=["系统集成"])

