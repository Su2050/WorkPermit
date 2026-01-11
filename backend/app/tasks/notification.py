"""
通知任务 (P1-2: 优先级队列)
- 发送当日提醒
- 截止时间提醒
- 支持优先级排序和时间段控制
"""
import logging
from datetime import date, datetime, timedelta
from typing import List
import uuid

from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.notification.send_daily_reminder")
def send_daily_reminder():
    """
    每日 05:30 - 当日提醒
    扫描今日未完成培训的人员，发送提醒通知
    """
    import asyncio
    from sqlalchemy import select
    from app.core.database import SessionLocal
    from app.models import DailyTicket, DailyTicketWorker, Worker
    
    async def _run():
        async with SessionLocal() as db:
            today = date.today()
            sent_count = 0
            failed_count = 0
            
            # 查找今日进行中的票据中未开始学习的人员
            result = await db.execute(
                select(DailyTicketWorker, Worker, DailyTicket)
                .join(Worker, DailyTicketWorker.worker_id == Worker.worker_id)
                .join(DailyTicket, DailyTicketWorker.daily_ticket_id == DailyTicket.daily_ticket_id)
                .where(
                    DailyTicket.date == today,
                    DailyTicket.status == "IN_PROGRESS",
                    DailyTicketWorker.training_status == "NOT_STARTED",
                    DailyTicketWorker.status == "ACTIVE",
                    Worker.is_bound == True  # 已绑定微信
                )
            )
            
            rows = result.all()
            
            for dtw, worker, daily_ticket in rows:
                # 检查24小时内是否已发送过提醒
                if dtw.last_notify_at:
                    if datetime.now() - dtw.last_notify_at < timedelta(hours=24):
                        continue
                
                # 发送通知（入队）
                try:
                    send_notification_task.delay(
                        worker_id=str(worker.worker_id),
                        notification_type="DAILY_REMINDER",
                        daily_ticket_id=str(daily_ticket.daily_ticket_id),
                        priority=2,  # 高优先级
                        data={
                            "title": "培训提醒",
                            "ticket_title": daily_ticket.ticket.title,
                            "deadline": str(daily_ticket.training_deadline_time),
                            "remaining_videos": dtw.total_video_count - dtw.completed_video_count
                        }
                    )
                    
                    # 更新通知时间
                    dtw.last_notify_at = datetime.now()
                    dtw.notify_count += 1
                    sent_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send daily reminder to {worker.worker_id}: {e}")
                    failed_count += 1
            
            await db.commit()
            
            logger.info(
                f"Daily reminder completed: date={today}, "
                f"sent={sent_count}, failed={failed_count}"
            )
            
            return {
                "date": str(today),
                "sent_count": sent_count,
                "failed_count": failed_count
            }
    
    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.notification.check_deadline_soon")
def check_deadline_soon():
    """
    每小时 - 检查截止时间提醒
    距离截止2小时仍未完成者发送提醒
    """
    import asyncio
    from sqlalchemy import select
    from app.core.database import SessionLocal
    from app.models import DailyTicket, DailyTicketWorker, Worker
    
    async def _run():
        async with SessionLocal() as db:
            today = date.today()
            now = datetime.now()
            sent_count = 0
            
            # 查找今日进行中的票据
            result = await db.execute(
                select(DailyTicketWorker, Worker, DailyTicket)
                .join(Worker, DailyTicketWorker.worker_id == Worker.worker_id)
                .join(DailyTicket, DailyTicketWorker.daily_ticket_id == DailyTicket.daily_ticket_id)
                .where(
                    DailyTicket.date == today,
                    DailyTicket.status == "IN_PROGRESS",
                    DailyTicketWorker.training_status.in_(["NOT_STARTED", "IN_LEARNING"]),
                    DailyTicketWorker.status == "ACTIVE",
                    Worker.is_bound == True
                )
            )
            
            rows = result.all()
            
            for dtw, worker, daily_ticket in rows:
                # 计算截止时间
                deadline = datetime.combine(today, daily_ticket.training_deadline_time)
                time_to_deadline = deadline - now
                
                # 距离截止2小时内
                if timedelta(hours=0) < time_to_deadline <= timedelta(hours=2):
                    # 检查是否已发送过截止提醒（通过类型判断）
                    # 这里简化处理，实际应该检查notification_log
                    
                    try:
                        send_notification_task.delay(
                            worker_id=str(worker.worker_id),
                            notification_type="DEADLINE_SOON",
                            daily_ticket_id=str(daily_ticket.daily_ticket_id),
                            priority=1,  # 紧急
                            data={
                                "title": "培训即将截止",
                                "ticket_title": daily_ticket.ticket.title,
                                "deadline": str(daily_ticket.training_deadline_time),
                                "time_left": str(time_to_deadline)
                            }
                        )
                        sent_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to send deadline reminder: {e}")
            
            logger.info(f"Deadline check completed: sent={sent_count}")
            
            return {"sent_count": sent_count}
    
    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(
    name="tasks.notification.send_notification",
    bind=True,
    max_retries=5,
    default_retry_delay=60
)
def send_notification_task(
    self,
    worker_id: str,
    notification_type: str,
    daily_ticket_id: str = None,
    priority: int = 3,
    data: dict = None
):
    """
    发送单条通知
    
    P1-2: 
    - 优先级排序
    - 时间段控制（只在07:00-21:00发送非紧急通知）
    - 指数退避重试
    """
    import asyncio
    from app.core.config import settings
    
    async def _run():
        now = datetime.now()
        current_hour = now.hour
        
        # P1-2: 时间段控制
        if priority > 1:  # 非紧急
            if not (settings.NOTIFICATION_ALLOWED_HOURS_START <= current_hour <= settings.NOTIFICATION_ALLOWED_HOURS_END):
                # 不在允许时间段，计算下次可发送时间并重试
                if current_hour < settings.NOTIFICATION_ALLOWED_HOURS_START:
                    delay = (settings.NOTIFICATION_ALLOWED_HOURS_START - current_hour) * 3600
                else:
                    delay = (24 - current_hour + settings.NOTIFICATION_ALLOWED_HOURS_START) * 3600
                
                logger.info(
                    f"Notification delayed due to time restriction: "
                    f"worker={worker_id}, delay={delay}s"
                )
                raise self.retry(countdown=delay)
        
        # 发送通知
        try:
            from app.adapters.wechat_adapter import WechatAdapter
            
            adapter = WechatAdapter()
            result = await adapter.send_subscribe_message(
                worker_id=uuid.UUID(worker_id),
                notification_type=notification_type,
                data=data
            )
            
            # 记录日志
            await _log_notification(
                worker_id=uuid.UUID(worker_id),
                daily_ticket_id=uuid.UUID(daily_ticket_id) if daily_ticket_id else None,
                notification_type=notification_type,
                priority=priority,
                status="SENT" if result["success"] else "FAILED",
                error_message=result.get("error")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            
            # 指数退避重试
            retry_delay = 60 * (2 ** self.request.retries)  # 1m/2m/4m/8m/16m
            raise self.retry(exc=e, countdown=retry_delay)
    
    return asyncio.get_event_loop().run_until_complete(_run())


async def _log_notification(
    worker_id: uuid.UUID,
    daily_ticket_id: uuid.UUID,
    notification_type: str,
    priority: int,
    status: str,
    error_message: str = None
):
    """记录通知日志"""
    from app.core.database import SessionLocal
    from app.models import NotificationLog, Worker
    from sqlalchemy import select
    
    async with SessionLocal() as db:
        # 获取worker的site_id
        worker_result = await db.execute(
            select(Worker).where(Worker.worker_id == worker_id)
        )
        worker = worker_result.scalar_one_or_none()
        
        if not worker:
            return
        
        log = NotificationLog(
            site_id=worker.site_id,
            worker_id=worker_id,
            daily_ticket_id=daily_ticket_id,
            notification_type=notification_type,
            priority=priority,
            status=status,
            sent_at=datetime.now() if status == "SENT" else None,
            error_message=error_message
        )
        
        db.add(log)
        await db.commit()


@celery_app.task(name="tasks.notification.process_notification_queue")
def process_notification_queue():
    """
    处理通知优先级队列 (P1-2)
    每30秒从Redis队列中取出通知并发送
    """
    import asyncio
    from app.services.notification_service import NotificationService
    from app.core.database import SessionLocal
    
    async def _run():
        async with SessionLocal() as db:
            service = NotificationService(db)
            result = await service.process_queue(batch_size=50)
            await db.commit()
            
            logger.info(f"Notification queue processed: {result}")
            return result
    
    return asyncio.get_event_loop().run_until_complete(_run())

