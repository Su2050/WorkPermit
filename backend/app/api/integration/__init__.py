"""
系统集成API - 门禁事件回调等
"""
from fastapi import APIRouter

from .access_events import router as access_events_router

integration_router = APIRouter()

integration_router.include_router(
    access_events_router, 
    prefix="/access-events", 
    tags=["门禁事件"]
)

