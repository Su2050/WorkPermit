"""Initial schema - P0硬规格落地

Revision ID: 0001
Revises: 
Create Date: 2026-01-09

包含15张核心表:
1. site - 工地项目
2. contractor - 施工单位
3. worker - 作业人员
4. work_area - 施工区域
5. training_video - 培训视频
6. work_ticket - 作业票
7. work_ticket_worker - 作业票-人员关联 (P0-8)
8. work_ticket_area - 作业票-区域关联 (P0-8)
9. work_ticket_video - 作业票-视频关联 (P0-8)
10. daily_ticket - 日作业票
11. daily_ticket_worker - 日票-人员状态 (P0-1)
12. daily_ticket_snapshot - 每日快照 (P0-8)
13. training_session - 学习会话 (P0-1, P0-2)
14. access_grant - 门禁授权 (P0-4)
15. access_event - 进出记录 (P1-1)

以及辅助表:
- notification_log - 通知日志
- audit_log - 审计日志
- sys_user - 系统用户
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. site表
    op.create_table(
        'site',
        sa.Column('site_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(64), unique=True, nullable=False),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('default_access_start_time', sa.String(8), default='06:00:00'),
        sa.Column('default_access_end_time', sa.String(8), default='20:00:00'),
        sa.Column('default_training_deadline', sa.String(8), default='07:30:00'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 2. contractor表
    op.create_table(
        'contractor',
        sa.Column('contractor_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('contact_person', sa.String(64), nullable=True),
        sa.Column('contact_phone', sa.String(32), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('license_no', sa.String(128), nullable=True),
        sa.Column('qualification_level', sa.String(64), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_contractor_site', 'contractor', ['site_id'])

    # 3. worker表
    op.create_table(
        'worker',
        sa.Column('worker_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('contractor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contractor.contractor_id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('id_no', sa.String(18), nullable=False),
        sa.Column('phone', sa.String(32), nullable=False),
        sa.Column('job_type', sa.String(64), nullable=True),
        sa.Column('team_name', sa.String(128), nullable=True),
        sa.Column('wechat_unionid', sa.String(64), unique=True, nullable=True),
        sa.Column('wechat_openid', sa.String(64), nullable=True),
        sa.Column('face_id', sa.String(128), nullable=True),
        sa.Column('face_photo_url', sa.String(512), nullable=True),
        sa.Column('status', sa.String(20), default='ACTIVE'),
        sa.Column('is_bound', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_worker_site_status', 'worker', ['site_id', 'status'])
    op.create_index('idx_worker_id_no', 'worker', ['id_no'])
    op.create_index('idx_worker_phone', 'worker', ['phone'])

    # 4. work_area表
    op.create_table(
        'work_area',
        sa.Column('area_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('access_group_id', sa.String(128), nullable=True),
        sa.Column('access_group_name', sa.String(255), nullable=True),
        sa.Column('building', sa.String(128), nullable=True),
        sa.Column('floor', sa.String(32), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_area_site_active', 'work_area', ['site_id', 'is_active'])

    # 5. training_video表
    op.create_table(
        'training_video',
        sa.Column('video_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('file_url', sa.String(512), nullable=False),
        sa.Column('thumbnail_url', sa.String(512), nullable=True),
        sa.Column('duration_sec', sa.Integer, default=0),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('category', sa.String(64), nullable=True),
        sa.Column('is_shared', sa.Boolean, default=False),
        sa.Column('status', sa.String(20), default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_video_site_status', 'training_video', ['site_id', 'status'])

    # 6. work_ticket表
    op.create_table(
        'work_ticket',
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('contractor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contractor.contractor_id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('default_access_start_time', sa.Time, nullable=False),
        sa.Column('default_access_end_time', sa.Time, nullable=False),
        sa.Column('default_training_deadline_time', sa.Time, nullable=False),
        sa.Column('notify_on_publish', sa.Boolean, default=True),
        sa.Column('daily_reminder_enabled', sa.Boolean, default=True),
        sa.Column('status', sa.String(20), default='DRAFT'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('remark', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_ticket_site_date', 'work_ticket', ['site_id', 'start_date', 'end_date'])

    # 7-9. 多对多关联表 (P0-8)
    op.create_table(
        'work_ticket_worker',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('work_ticket.ticket_id', ondelete='CASCADE'), nullable=False),
        sa.Column('worker_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('worker.worker_id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), default='ACTIVE'),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('removed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('ticket_id', 'worker_id', name='uq_ticket_worker'),
    )

    op.create_table(
        'work_ticket_area',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('work_ticket.ticket_id', ondelete='CASCADE'), nullable=False),
        sa.Column('area_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('work_area.area_id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), default='ACTIVE'),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('removed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('ticket_id', 'area_id', name='uq_ticket_area'),
    )

    op.create_table(
        'work_ticket_video',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('work_ticket.ticket_id', ondelete='CASCADE'), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('training_video.video_id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('required_watch_percent', sa.Numeric(3, 2), default=0.95),
        sa.Column('sequence_order', sa.Integer, nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), default='ACTIVE'),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('removed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('ticket_id', 'video_id', name='uq_ticket_video'),
    )

    # 10. daily_ticket表
    op.create_table(
        'daily_ticket',
        sa.Column('daily_ticket_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('work_ticket.ticket_id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('access_start_time', sa.Time, nullable=False),
        sa.Column('access_end_time', sa.Time, nullable=False),
        sa.Column('training_deadline_time', sa.Time, nullable=False),
        sa.Column('status', sa.String(20), default='DRAFT'),
        sa.Column('cancel_reason', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_daily_ticket_date_status', 'daily_ticket', ['date', 'status'])
    op.create_index('idx_daily_ticket_site_date', 'daily_ticket', ['site_id', 'date'])

    # 11. daily_ticket_worker表 (P0-1)
    op.create_table(
        'daily_ticket_worker',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_ticket.daily_ticket_id', ondelete='CASCADE'), nullable=False),
        sa.Column('worker_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('worker.worker_id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_video_count', sa.Integer, nullable=False),
        sa.Column('completed_video_count', sa.Integer, default=0),
        sa.Column('training_status', sa.String(20), default='NOT_STARTED'),
        sa.Column('authorized', sa.Boolean, default=False),
        sa.Column('last_notify_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notify_count', sa.Integer, default=0),
        sa.Column('status', sa.String(20), default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('daily_ticket_id', 'worker_id', name='uq_daily_ticket_worker'),
    )
    op.create_index('idx_dtw_daily_ticket_status', 'daily_ticket_worker', ['daily_ticket_id', 'training_status'])

    # 12. daily_ticket_snapshot表 (P0-8)
    op.create_table(
        'daily_ticket_snapshot',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_ticket.daily_ticket_id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_type', sa.String(20), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_name', sa.String(255), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_snapshot_daily_type', 'daily_ticket_snapshot', ['daily_ticket_id', 'snapshot_type'])

    # 13. training_session表 (P0-1, P0-2)
    op.create_table(
        'training_session',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_ticket.daily_ticket_id', ondelete='CASCADE'), nullable=False),
        sa.Column('worker_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('worker.worker_id', ondelete='CASCADE'), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('training_video.video_id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), default='NOT_STARTED'),
        sa.Column('session_token', sa.String(64), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_watch_sec', sa.Integer, default=0),
        sa.Column('total_watch_sec', sa.Integer, default=0),
        sa.Column('last_position', sa.Integer, default=0),
        sa.Column('last_heartbeat_ts', sa.Integer, nullable=True),
        sa.Column('random_check_passed', sa.Integer, default=0),
        sa.Column('random_check_failed', sa.Integer, default=0),
        sa.Column('consecutive_check_failures', sa.Integer, default=0),
        sa.Column('last_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('suspicious_event_count', sa.Integer, default=0),
        sa.Column('failure_reason', sa.String(100), nullable=True),
        sa.Column('video_state', sa.String(20), default='unknown'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('daily_ticket_id', 'worker_id', 'video_id', name='uq_session_daily_worker_video'),
    )
    op.create_index('idx_session_status', 'training_session', ['daily_ticket_id', 'worker_id', 'status'])

    # 14. access_grant表 (P0-4)
    op.create_table(
        'access_grant',
        sa.Column('grant_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('daily_ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_ticket.daily_ticket_id', ondelete='CASCADE'), nullable=False),
        sa.Column('worker_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('worker.worker_id', ondelete='CASCADE'), nullable=False),
        sa.Column('area_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('work_area.area_id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), default='PENDING_SYNC'),
        sa.Column('sync_attempt_count', sa.Integer, default=0),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_error_msg', sa.Text, nullable=True),
        sa.Column('vendor_ref', sa.String(128), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoke_reason', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('daily_ticket_id', 'worker_id', 'area_id', name='uq_grant_daily_worker_area'),
        sa.CheckConstraint('valid_to > valid_from', name='ck_grant_time_window'),
    )
    op.create_index('idx_grant_sync_status', 'access_grant', ['status', 'created_at'])
    op.create_index('idx_grant_site_status', 'access_grant', ['site_id', 'status'])

    # 15. access_event表 (P1-1)
    op.create_table(
        'access_event',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vendor_event_id', sa.String(128), unique=True, nullable=True),
        sa.Column('device_id', sa.String(64), nullable=False),
        sa.Column('device_name', sa.String(128), nullable=True),
        sa.Column('worker_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('worker.worker_id', ondelete='SET NULL'), nullable=True),
        sa.Column('area_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('work_area.area_id', ondelete='SET NULL'), nullable=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('direction', sa.String(10), nullable=True),
        sa.Column('result', sa.String(20), nullable=False),
        sa.Column('reason_code', sa.String(50), nullable=True),
        sa.Column('reason_message', sa.String(255), nullable=True),
        sa.Column('face_photo_url', sa.String(512), nullable=True),
        sa.Column('face_id', sa.String(128), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('device_id', 'worker_id', 'event_time', 'direction', name='uq_event_device_worker_time_direction'),
    )
    op.create_index('idx_event_site_time', 'access_event', ['site_id', 'event_time'])
    op.create_index('idx_event_worker_time', 'access_event', ['worker_id', 'event_time'])

    # 辅助表: notification_log
    op.create_table(
        'notification_log',
        sa.Column('log_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='CASCADE'), nullable=False),
        sa.Column('worker_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('worker.worker_id', ondelete='CASCADE'), nullable=False),
        sa.Column('daily_ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_ticket.daily_ticket_id', ondelete='SET NULL'), nullable=True),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('priority', sa.Integer, default=3),
        sa.Column('channel', sa.String(32), default='WECHAT_SUBSCRIBE'),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('template_id', sa.String(128), nullable=True),
        sa.Column('template_data', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(20), default='PENDING'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('max_retries', sa.Integer, default=5),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('vendor_response', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_notification_status', 'notification_log', ['status', 'scheduled_at'])

    # 辅助表: audit_log
    op.create_table(
        'audit_log',
        sa.Column('log_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.site_id', ondelete='SET NULL'), nullable=True),
        sa.Column('operator_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('operator_name', sa.String(64), nullable=True),
        sa.Column('operator_role', sa.String(32), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resource_name', sa.String(255), nullable=True),
        sa.Column('old_value', postgresql.JSONB, nullable=True),
        sa.Column('new_value', postgresql.JSONB, nullable=True),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('request_id', sa.String(64), nullable=True),
        sa.Column('is_success', sa.Boolean, default=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_audit_created', 'audit_log', ['created_at'])
    op.create_index('idx_audit_resource', 'audit_log', ['resource_type', 'resource_id'])

    # 辅助表: sys_user
    op.create_table(
        'sys_user',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(64), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(128), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('email', sa.String(128), nullable=True),
        sa.Column('phone', sa.String(32), nullable=True),
        sa.Column('avatar_url', sa.String(512), nullable=True),
        sa.Column('role', sa.String(32), default='ContractorAdmin'),
        sa.Column('contractor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contractor.contractor_id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_locked', sa.Boolean, default=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('login_fail_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_user_role', 'sys_user', ['role', 'is_active'])


def downgrade() -> None:
    # 按依赖顺序反向删除表
    op.drop_table('sys_user')
    op.drop_table('audit_log')
    op.drop_table('notification_log')
    op.drop_table('access_event')
    op.drop_table('access_grant')
    op.drop_table('training_session')
    op.drop_table('daily_ticket_snapshot')
    op.drop_table('daily_ticket_worker')
    op.drop_table('daily_ticket')
    op.drop_table('work_ticket_video')
    op.drop_table('work_ticket_area')
    op.drop_table('work_ticket_worker')
    op.drop_table('work_ticket')
    op.drop_table('training_video')
    op.drop_table('work_area')
    op.drop_table('worker')
    op.drop_table('contractor')
    op.drop_table('site')

