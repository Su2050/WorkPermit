# 作业票系统数据模型
# 包含15张核心表，符合P0硬规格要求

from .base import Base, TimestampMixin, CreatedAtMixin
from .site import Site
from .contractor import Contractor
from .worker import Worker
from .work_area import WorkArea
from .training_video import TrainingVideo
from .work_ticket import WorkTicket
from .work_ticket_worker import WorkTicketWorker
from .work_ticket_area import WorkTicketArea
from .work_ticket_video import WorkTicketVideo
from .daily_ticket import DailyTicket
from .daily_ticket_worker import DailyTicketWorker
from .daily_ticket_snapshot import DailyTicketSnapshot
from .training_session import TrainingSession
from .access_grant import AccessGrant
from .access_event import AccessEvent
from .notification_log import NotificationLog
from .audit_log import AuditLog
from .sys_user import SysUser
from .alert import Alert

__all__ = [
    "Base",
    "TimestampMixin",
    "CreatedAtMixin",
    "Site",
    "Contractor",
    "Worker",
    "WorkArea",
    "TrainingVideo",
    "WorkTicket",
    "WorkTicketWorker",
    "WorkTicketArea",
    "WorkTicketVideo",
    "DailyTicket",
    "DailyTicketWorker",
    "DailyTicketSnapshot",
    "TrainingSession",
    "AccessGrant",
    "AccessEvent",
    "NotificationLog",
    "AuditLog",
    "SysUser",
    "Alert",
]

