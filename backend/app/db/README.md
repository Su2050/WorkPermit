# 数据库优化脚本

本目录包含数据库优化相关的脚本。

## 索引优化

### 创建索引

```bash
cd backend
python -m app.db.add_indexes
```

### 索引说明

已为以下表的常用查询字段添加索引：

1. **work_tickets** - 作业票表
   - status: 状态筛选
   - contractor_id: 施工单位筛选
   - created_at: 时间排序
   - date_range: 日期范围查询
   - site_id + status: 复合查询

2. **daily_tickets** - 每日票据表
   - date: 日期查询和排序
   - ticket_id: 关联查询
   - status: 状态筛选
   - date + status: 复合查询

3. **daily_ticket_workers** - 每日票据人员表
   - daily_ticket_id: 关联查询
   - worker_id: 人员查询
   - training_status: 培训状态筛选
   - status: 状态筛选

4. **access_grants** - 门禁授权表
   - worker_id: 人员查询
   - area_id: 区域查询
   - status: 状态筛选
   - daily_ticket_id: 关联查询
   - created_at: 时间排序
   - status + created_at: 复合查询

5. **access_events** - 门禁事件表
   - worker_id: 人员查询
   - event_time: 时间排序
   - result: 结果筛选
   - event_time + result: 复合查询

6. **training_sessions** - 培训会话表
   - daily_ticket_worker_id: 关联查询
   - status: 状态筛选
   - started_at: 时间排序

7. **workers** - 人员表
   - contractor_id: 施工单位查询
   - phone: 手机号查询
   - id_no: 身份证号查询
   - status: 状态筛选
   - site_id + status: 复合查询

8. **audit_logs** - 审计日志表
   - resource_type: 资源类型筛选
   - resource_id: 资源ID查询
   - action: 操作类型筛选
   - created_at: 时间排序
   - resource_type + resource_id: 复合查询

### 性能提升

添加索引后，预期性能提升：

- 列表查询: 50-80% 提升
- 状态筛选: 60-90% 提升
- 关联查询: 40-70% 提升
- 时间范围查询: 50-80% 提升

### 注意事项

1. 索引会占用额外的存储空间
2. 索引会略微降低写入性能
3. 定期维护索引（VACUUM、ANALYZE）
4. 监控索引使用情况

### 索引维护

```sql
-- 查看索引使用情况
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 查看未使用的索引
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexname NOT LIKE 'pg_%';

-- 重建索引
REINDEX TABLE table_name;

-- 分析表
ANALYZE table_name;
```

## 查询优化建议

1. **使用索引字段进行筛选**
2. **避免在索引字段上使用函数**
3. **使用 LIMIT 限制返回数量**
4. **使用 EXPLAIN ANALYZE 分析查询计划**
5. **定期更新统计信息**

## 监控

建议监控以下指标：

- 查询响应时间
- 索引命中率
- 表扫描次数
- 缓存命中率

