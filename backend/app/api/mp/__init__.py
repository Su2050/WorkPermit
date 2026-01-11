"""
小程序API
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .tasks import router as tasks_router
from .training import router as training_router
from .profile import router as profile_router

mp_router = APIRouter()

mp_router.include_router(auth_router, prefix="/auth", tags=["小程序-认证"])
mp_router.include_router(tasks_router, prefix="/tasks", tags=["小程序-待办"])
mp_router.include_router(training_router, prefix="/training", tags=["小程序-培训"])
mp_router.include_router(profile_router, prefix="/profile", tags=["小程序-我的"])

