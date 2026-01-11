"""
Celery应用配置 (P1-3: 统一任务调度)
- 替代APScheduler，统一使用Celery Beat + Worker
- 支持定时任务和异步任务
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# 创建Celery应用
celery_app = Celery(
    "work_permit_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.scheduler",
        "app.tasks.notification",
        "app.tasks.access",
    ]
)

# Celery配置
celery_app.conf.update(
    # 序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务路由
    task_routes={
        "tasks.notification.*": {"queue": "notification"},
        "tasks.access.*": {"queue": "access"},
        "tasks.scheduler.*": {"queue": "scheduler"},
    },
    
    # 任务结果
    result_expires=3600,  # 结果1小时后过期
    
    # 并发
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    
    # 任务追踪
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
    task_soft_time_limit=240,  # 4分钟软超时
)

# 定时任务配置（Celery Beat）
celery_app.conf.beat_schedule = {
    # 每日 00:05 - 状态切换任务
    "daily-ticket-status-transition": {
        "task": "tasks.scheduler.daily_ticket_status_transition",
        "schedule": crontab(hour=0, minute=5),
        "options": {"queue": "scheduler"},
    },
    
    # 每日 05:30 - 当日提醒
    "daily-reminder": {
        "task": "tasks.notification.send_daily_reminder",
        "schedule": crontab(hour=5, minute=30),
        "options": {"queue": "notification"},
    },
    
    # 截止前2小时提醒 - 每小时检查一次
    "deadline-soon-check": {
        "task": "tasks.notification.check_deadline_soon",
        "schedule": crontab(minute=0),  # 每小时整点
        "options": {"queue": "notification"},
    },
    
    # 每1分钟 - 授权同步重试
    "access-grant-sync-retry": {
        "task": "tasks.access.retry_failed_sync",
        "schedule": 60.0,
        "options": {"queue": "access"},
    },
    
    # 每10分钟 - 健康检查
    "health-check": {
        "task": "tasks.scheduler.health_check",
        "schedule": 600.0,
        "options": {"queue": "scheduler"},
    },
    
    # 每日 23:59 - 过期处理
    "daily-ticket-expiration": {
        "task": "tasks.scheduler.expire_daily_tickets",
        "schedule": crontab(hour=23, minute=59),
        "options": {"queue": "scheduler"},
    },
    
    # 每日 02:00 - 一级对账（同步状态）
    "reconcile-sync-status": {
        "task": "tasks.access.reconcile_sync_status",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "access"},
    },
    
    # 每日 03:00 - 二级对账（权限对账，可选）
    "reconcile-with-vendor": {
        "task": "tasks.access.reconcile_with_vendor",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "access"},
    },
    
    # 每30秒 - 处理通知优先级队列 (P1-2)
    "process-notification-queue": {
        "task": "tasks.notification.process_notification_queue",
        "schedule": 30.0,
        "options": {"queue": "notification"},
    },
}

# 任务优先级配置
celery_app.conf.task_queue_max_priority = 10
celery_app.conf.task_default_priority = 5

