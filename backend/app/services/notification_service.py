"""
通知服务 (P1-2: 优先级队列)
- Redis Sorted Set 实现优先级队列
- 时间段控制（07:00-21:00）
- 去重机制
- 未读指标统计
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

import redis.asyncio as redis
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import NotificationLog, Worker
from app.adapters.wechat_adapter import WechatAdapter

logger = logging.getLogger(__name__)


class NotificationPriorityQueue:
    """
    通知优先级队列 (P1-2)
    
    使用 Redis Sorted Set 实现:
    - score = priority * 1_000_000_000 + timestamp
    - 优先级越小越优先（1=紧急, 2=高, 3=普通）
    - 同优先级按时间先后
    """
    
    QUEUE_KEY = "notification:priority_queue"
    DEDUP_KEY_PREFIX = "notification:dedup:"
    DEDUP_TTL = 3600  # 1小时去重
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis = redis_client
    
    async def _get_redis(self) -> redis.Redis:
        """获取Redis连接"""
        if self.redis is None:
            self.redis = redis.from_url(settings.REDIS_URL)
        return self.redis
    
    async def enqueue(
        self,
        worker_id: uuid.UUID,
        notification_type: str,
        priority: int = 3,
        data: Dict[str, Any] = None,
        daily_ticket_id: uuid.UUID = None,
        dedup_key: str = None
    ) -> bool:
        """
        将通知加入优先级队列
        
        Args:
            worker_id: 工人ID
            notification_type: 通知类型
            priority: 优先级 (1=紧急, 2=高, 3=普通)
            data: 通知数据
            daily_ticket_id: 日票ID
            dedup_key: 去重键（可选）
        
        Returns:
            bool: 是否成功入队
        """
        r = await self._get_redis()
        
        # 去重检查
        if dedup_key:
            actual_dedup_key = f"{self.DEDUP_KEY_PREFIX}{dedup_key}"
            exists = await r.exists(actual_dedup_key)
            if exists:
                logger.info(f"Notification deduplicated: {dedup_key}")
                return False
            
            # 设置去重标记
            await r.setex(actual_dedup_key, self.DEDUP_TTL, "1")
        
        # 构造通知消息
        notification = {
            "id": str(uuid.uuid4()),
            "worker_id": str(worker_id),
            "notification_type": notification_type,
            "priority": priority,
            "data": data or {},
            "daily_ticket_id": str(daily_ticket_id) if daily_ticket_id else None,
            "enqueued_at": datetime.now().isoformat()
        }
        
        # 计算 score: priority * 10^9 + timestamp
        # 这样优先级小的排前面，同优先级按时间先后
        timestamp = int(datetime.now().timestamp())
        score = priority * 1_000_000_000 + timestamp
        
        # 入队
        await r.zadd(self.QUEUE_KEY, {json.dumps(notification): score})
        
        logger.info(
            f"Notification enqueued: worker={worker_id}, "
            f"type={notification_type}, priority={priority}"
        )
        
        return True
    
    async def dequeue(self, batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        从队列中取出通知（按优先级）
        
        Args:
            batch_size: 批量大小
        
        Returns:
            List[Dict]: 通知列表
        """
        r = await self._get_redis()
        
        # 获取优先级最高的通知
        items = await r.zrange(
            self.QUEUE_KEY, 
            0, 
            batch_size - 1, 
            withscores=True
        )
        
        if not items:
            return []
        
        notifications = []
        members_to_remove = []
        
        for item, score in items:
            try:
                notification = json.loads(item)
                notifications.append(notification)
                members_to_remove.append(item)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode notification: {item}")
                members_to_remove.append(item)
        
        # 移除已取出的通知
        if members_to_remove:
            await r.zrem(self.QUEUE_KEY, *members_to_remove)
        
        return notifications
    
    async def get_queue_size(self) -> int:
        """获取队列大小"""
        r = await self._get_redis()
        return await r.zcard(self.QUEUE_KEY)
    
    async def get_queue_stats(self) -> Dict[str, int]:
        """获取队列统计"""
        r = await self._get_redis()
        
        total = await r.zcard(self.QUEUE_KEY)
        
        # 按优先级统计
        stats = {"total": total}
        
        for priority in [1, 2, 3]:
            min_score = priority * 1_000_000_000
            max_score = (priority + 1) * 1_000_000_000 - 1
            count = await r.zcount(self.QUEUE_KEY, min_score, max_score)
            stats[f"priority_{priority}"] = count
        
        return stats


class NotificationService:
    """
    通知服务
    
    功能:
    - 入队通知（带去重）
    - 处理队列中的通知
    - 时间段控制
    - 未读指标统计
    """
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.queue = NotificationPriorityQueue()
        self.adapter = WechatAdapter()
    
    async def send_notification(
        self,
        worker_id: uuid.UUID,
        notification_type: str,
        priority: int = 3,
        data: Dict[str, Any] = None,
        daily_ticket_id: uuid.UUID = None,
        dedup_key: str = None
    ) -> bool:
        """
        发送通知（入队）
        
        Args:
            worker_id: 工人ID
            notification_type: 通知类型
            priority: 优先级
            data: 通知数据
            daily_ticket_id: 日票ID
            dedup_key: 去重键
        
        Returns:
            bool: 是否成功入队
        """
        # 生成默认去重键
        if dedup_key is None:
            dedup_key = f"{worker_id}:{notification_type}:{daily_ticket_id}:{datetime.now().date()}"
        
        return await self.queue.enqueue(
            worker_id=worker_id,
            notification_type=notification_type,
            priority=priority,
            data=data,
            daily_ticket_id=daily_ticket_id,
            dedup_key=dedup_key
        )
    
    async def process_queue(self, batch_size: int = 10) -> Dict[str, int]:
        """
        处理队列中的通知
        
        P1-2: 时间段控制
        - 紧急通知（priority=1）随时发送
        - 非紧急通知只在 07:00-21:00 发送
        
        Args:
            batch_size: 批量大小
        
        Returns:
            Dict: 处理结果统计
        """
        now = datetime.now()
        current_hour = now.hour
        
        # 检查时间段
        in_allowed_hours = (
            settings.NOTIFICATION_ALLOWED_HOURS_START <= current_hour <= 
            settings.NOTIFICATION_ALLOWED_HOURS_END
        )
        
        notifications = await self.queue.dequeue(batch_size)
        
        result = {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "delayed": 0
        }
        
        for notification in notifications:
            result["processed"] += 1
            priority = notification.get("priority", 3)
            
            # 时间段控制：非紧急且不在允许时间段，重新入队
            if priority > 1 and not in_allowed_hours:
                # 重新入队（延迟到允许时间）
                await self.queue.enqueue(
                    worker_id=uuid.UUID(notification["worker_id"]),
                    notification_type=notification["notification_type"],
                    priority=priority,
                    data=notification.get("data"),
                    daily_ticket_id=uuid.UUID(notification["daily_ticket_id"]) 
                        if notification.get("daily_ticket_id") else None,
                    dedup_key=None  # 不再去重
                )
                result["delayed"] += 1
                continue
            
            # 发送通知
            try:
                send_result = await self.adapter.send_subscribe_message(
                    worker_id=uuid.UUID(notification["worker_id"]),
                    notification_type=notification["notification_type"],
                    data=notification.get("data")
                )
                
                if send_result["success"]:
                    result["sent"] += 1
                else:
                    result["failed"] += 1
                
                # 记录日志
                await self._log_notification(notification, send_result)
                
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
                result["failed"] += 1
        
        return result
    
    async def _log_notification(
        self, 
        notification: Dict[str, Any], 
        send_result: Dict[str, Any]
    ) -> None:
        """记录通知日志"""
        if self.db is None:
            return
        
        # 获取worker的site_id
        worker_result = await self.db.execute(
            select(Worker).where(
                Worker.worker_id == uuid.UUID(notification["worker_id"])
            )
        )
        worker = worker_result.scalar_one_or_none()
        
        if not worker:
            return
        
        log = NotificationLog(
            site_id=worker.site_id,
            worker_id=uuid.UUID(notification["worker_id"]),
            daily_ticket_id=uuid.UUID(notification["daily_ticket_id"]) 
                if notification.get("daily_ticket_id") else None,
            notification_type=notification["notification_type"],
            priority=notification.get("priority", 3),
            status="SENT" if send_result["success"] else "FAILED",
            sent_at=datetime.now() if send_result["success"] else None,
            error_message=send_result.get("error")
        )
        
        self.db.add(log)
        await self.db.flush()
    
    async def get_unread_count(self, worker_id: uuid.UUID) -> int:
        """
        获取未读通知数量
        
        Args:
            worker_id: 工人ID
        
        Returns:
            int: 未读数量
        """
        if self.db is None:
            return 0
        
        # 查询最近7天未读通知
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        result = await self.db.execute(
            select(func.count(NotificationLog.log_id))
            .where(
                NotificationLog.worker_id == worker_id,
                NotificationLog.status == "SENT",
                NotificationLog.read_at.is_(None),
                NotificationLog.sent_at >= seven_days_ago
            )
        )
        
        return result.scalar() or 0
    
    async def mark_as_read(
        self, 
        worker_id: uuid.UUID, 
        log_ids: List[uuid.UUID] = None
    ) -> int:
        """
        标记通知为已读
        
        Args:
            worker_id: 工人ID
            log_ids: 通知日志ID列表（为空则标记全部）
        
        Returns:
            int: 标记数量
        """
        if self.db is None:
            return 0
        
        from sqlalchemy import update
        
        query = (
            update(NotificationLog)
            .where(
                NotificationLog.worker_id == worker_id,
                NotificationLog.read_at.is_(None)
            )
            .values(read_at=datetime.now())
        )
        
        if log_ids:
            query = query.where(NotificationLog.log_id.in_(log_ids))
        
        result = await self.db.execute(query)
        
        return result.rowcount
    
    async def get_notification_history(
        self,
        worker_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取通知历史
        
        Args:
            worker_id: 工人ID
            page: 页码
            page_size: 每页数量
        
        Returns:
            Dict: 分页结果
        """
        if self.db is None:
            return {"items": [], "total": 0}
        
        # 查询总数
        total_result = await self.db.execute(
            select(func.count(NotificationLog.log_id))
            .where(NotificationLog.worker_id == worker_id)
        )
        total = total_result.scalar() or 0
        
        # 查询列表
        result = await self.db.execute(
            select(NotificationLog)
            .where(NotificationLog.worker_id == worker_id)
            .order_by(NotificationLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        items = result.scalars().all()
        
        return {
            "items": [
                {
                    "log_id": str(item.log_id),
                    "notification_type": item.notification_type,
                    "priority": item.priority,
                    "status": item.status,
                    "sent_at": item.sent_at.isoformat() if item.sent_at else None,
                    "read_at": item.read_at.isoformat() if item.read_at else None,
                    "created_at": item.created_at.isoformat()
                }
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }


# Celery 任务：处理通知队列
def process_notification_queue():
    """处理通知队列（供 Celery 调用）"""
    import asyncio
    from app.core.database import SessionLocal
    
    async def _run():
        async with SessionLocal() as db:
            service = NotificationService(db)
            result = await service.process_queue(batch_size=50)
            await db.commit()
            
            logger.info(f"Notification queue processed: {result}")
            return result
    
    return asyncio.get_event_loop().run_until_complete(_run())

