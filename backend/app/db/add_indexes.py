"""
数据库索引优化脚本 (P2-4)

为常用查询字段添加索引，提升查询性能
"""

# 索引创建 SQL 语句
INDEX_STATEMENTS = [
    # WorkTicket 表索引
    "CREATE INDEX IF NOT EXISTS idx_work_tickets_status ON work_tickets(status);",
    "CREATE INDEX IF NOT EXISTS idx_work_tickets_contractor_id ON work_tickets(contractor_id);",
    "CREATE INDEX IF NOT EXISTS idx_work_tickets_created_at ON work_tickets(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_work_tickets_date_range ON work_tickets(start_date, end_date);",
    "CREATE INDEX IF NOT EXISTS idx_work_tickets_site_status ON work_tickets(site_id, status);",
    
    # DailyTicket 表索引
    "CREATE INDEX IF NOT EXISTS idx_daily_tickets_date ON daily_tickets(date DESC);",
    "CREATE INDEX IF NOT EXISTS idx_daily_tickets_ticket_id ON daily_tickets(ticket_id);",
    "CREATE INDEX IF NOT EXISTS idx_daily_tickets_status ON daily_tickets(status);",
    "CREATE INDEX IF NOT EXISTS idx_daily_tickets_date_status ON daily_tickets(date, status);",
    
    # DailyTicketWorker 表索引
    "CREATE INDEX IF NOT EXISTS idx_daily_ticket_workers_daily_ticket_id ON daily_ticket_workers(daily_ticket_id);",
    "CREATE INDEX IF NOT EXISTS idx_daily_ticket_workers_worker_id ON daily_ticket_workers(worker_id);",
    "CREATE INDEX IF NOT EXISTS idx_daily_ticket_workers_training_status ON daily_ticket_workers(training_status);",
    "CREATE INDEX IF NOT EXISTS idx_daily_ticket_workers_status ON daily_ticket_workers(status);",
    
    # AccessGrant 表索引
    "CREATE INDEX IF NOT EXISTS idx_access_grants_worker_id ON access_grants(worker_id);",
    "CREATE INDEX IF NOT EXISTS idx_access_grants_area_id ON access_grants(area_id);",
    "CREATE INDEX IF NOT EXISTS idx_access_grants_status ON access_grants(status);",
    "CREATE INDEX IF NOT EXISTS idx_access_grants_daily_ticket_id ON access_grants(daily_ticket_id);",
    "CREATE INDEX IF NOT EXISTS idx_access_grants_created_at ON access_grants(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_access_grants_status_created ON access_grants(status, created_at);",
    
    # AccessEvent 表索引
    "CREATE INDEX IF NOT EXISTS idx_access_events_worker_id ON access_events(worker_id);",
    "CREATE INDEX IF NOT EXISTS idx_access_events_event_time ON access_events(event_time DESC);",
    "CREATE INDEX IF NOT EXISTS idx_access_events_result ON access_events(result);",
    "CREATE INDEX IF NOT EXISTS idx_access_events_time_result ON access_events(event_time DESC, result);",
    
    # TrainingSession 表索引
    "CREATE INDEX IF NOT EXISTS idx_training_sessions_daily_ticket_worker_id ON training_sessions(daily_ticket_worker_id);",
    "CREATE INDEX IF NOT EXISTS idx_training_sessions_status ON training_sessions(status);",
    "CREATE INDEX IF NOT EXISTS idx_training_sessions_started_at ON training_sessions(started_at DESC);",
    
    # Worker 表索引
    "CREATE INDEX IF NOT EXISTS idx_workers_contractor_id ON workers(contractor_id);",
    "CREATE INDEX IF NOT EXISTS idx_workers_phone ON workers(phone);",
    "CREATE INDEX IF NOT EXISTS idx_workers_id_no ON workers(id_no);",
    "CREATE INDEX IF NOT EXISTS idx_workers_status ON workers(status);",
    "CREATE INDEX IF NOT EXISTS idx_workers_site_status ON workers(site_id, status);",
    
    # AuditLog 表索引
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_id ON audit_logs(resource_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_type_id ON audit_logs(resource_type, resource_id);",
]


async def create_indexes(db_session):
    """
    创建所有索引
    
    Args:
        db_session: 数据库会话
    """
    success_count = 0
    failed_count = 0
    
    for sql in INDEX_STATEMENTS:
        try:
            await db_session.execute(sql)
            success_count += 1
            print(f"✅ 创建索引成功: {sql[:80]}...")
        except Exception as e:
            failed_count += 1
            print(f"❌ 创建索引失败: {sql[:80]}... - {str(e)}")
    
    await db_session.commit()
    
    print(f"\n索引创建完成: 成功 {success_count} 个，失败 {failed_count} 个")
    return success_count, failed_count


async def drop_indexes(db_session):
    """
    删除所有索引（用于回滚）
    
    Args:
        db_session: 数据库会话
    """
    index_names = [
        # 从 CREATE INDEX 语句中提取索引名
        sql.split("INDEX IF NOT EXISTS ")[1].split(" ON ")[0]
        for sql in INDEX_STATEMENTS
    ]
    
    success_count = 0
    failed_count = 0
    
    for index_name in index_names:
        try:
            sql = f"DROP INDEX IF EXISTS {index_name};"
            await db_session.execute(sql)
            success_count += 1
            print(f"✅ 删除索引成功: {index_name}")
        except Exception as e:
            failed_count += 1
            print(f"❌ 删除索引失败: {index_name} - {str(e)}")
    
    await db_session.commit()
    
    print(f"\n索引删除完成: 成功 {success_count} 个，失败 {failed_count} 个")
    return success_count, failed_count


if __name__ == "__main__":
    import asyncio
    from app.core.database import SessionLocal
    
    async def main():
        async with SessionLocal() as session:
            print("开始创建数据库索引...")
            await create_indexes(session)
    
    asyncio.run(main())

