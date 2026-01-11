# API清单文档

**最后更新**: 2026-01-10  
**维护者**: 开发团队

> 本文档列出所有API端点，前后端开发必须参考此文档，确保接口一致性。

---

## 一、认证授权 API

### POST /api/admin/auth/login
**描述**: 用户登录

**请求**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "string",
    "token_type": "bearer"
  }
}
```

---

### GET /api/admin/auth/me
**描述**: 获取当前用户信息

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": "uuid",
    "username": "string",
    "role": "SysAdmin|ContractorAdmin",
    "contractor_id": "uuid|null"
  }
}
```

---

## 二、作业票管理 API

### GET /api/admin/work-tickets
**描述**: 获取作业票列表

**查询参数**:
- `page`: int (默认: 1)
- `page_size`: int (默认: 20)
- `contractor_id`: uuid (可选)
- `status`: string (可选: PUBLISHED, IN_PROGRESS, EXPIRED, CLOSED)
- `keyword`: string (可选)
- `start_date`: date (可选)
- `end_date`: date (可选)

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "ticket_id": "uuid",
        "title": "string",
        "contractor_name": "string",
        "contractor": {
          "contractor_id": "uuid",
          "name": "string"
        },
        "areas": [
          {
            "area_id": "uuid",
            "name": "string"
          }
        ],
        "start_date": "date",
        "end_date": "date",
        "status": "string",
        "total_workers": 0,
        "completed_workers": 0,
        "created_at": "datetime"
      }
    ],
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

---

### GET /api/admin/work-tickets/{ticket_id}
**描述**: 获取作业票详情

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "ticket_id": "uuid",
    "title": "string",
    "description": "string",
    "contractor_id": "uuid",
    "contractor_name": "string",
    "start_date": "date",
    "end_date": "date",
    "status": "string",
    "workers": [...],
    "areas": [...],
    "videos": [...]
  }
}
```

---

### POST /api/admin/work-tickets
**描述**: 创建作业票

**请求**:
```json
{
  "title": "string",
  "description": "string",
  "contractor_id": "uuid",
  "start_date": "date",
  "end_date": "date",
  "worker_ids": ["uuid"],
  "area_ids": ["uuid"],
  "video_ids": ["uuid"]
}
```

---

## 三、施工单位管理 API

### GET /api/admin/contractors
**描述**: 获取施工单位列表

**查询参数**:
- `page`: int
- `page_size`: int
- `keyword`: string (可选)
- `is_active`: bool (可选)

---

### GET /api/admin/contractors/options ⚠️
**描述**: 获取施工单位选项（用于下拉框）

**注意**: 此路由必须在 `/{contractor_id}` 之前定义！

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": "uuid",
      "name": "string",
      "contractor_id": "uuid"
    }
  ]
}
```

---

### GET /api/admin/contractors/{contractor_id}
**描述**: 获取施工单位详情

---

## 四、区域管理 API

### GET /api/admin/areas
**描述**: 获取区域列表

---

## 五、视频管理 API

### GET /api/admin/videos
**描述**: 获取视频列表

---

## 六、人员管理 API

### GET /api/admin/workers
**描述**: 获取人员列表

---

## 七、报表统计 API

### GET /api/admin/reports/dashboard
**描述**: 获取Dashboard数据

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "stats": {
      "todayTasks": 0,
      "activeTickets": 0,
      "todayTrainings": 0,
      "accessGrants": 0,
      "syncRate": 0
    },
    "pendingTickets": [
      {
        "id": "uuid",
        "title": "string",
        "contractor": "string",
        "workerCount": 0,
        "progress": 0,
        "status": "string"
      }
    ],
    "recentAlerts": []
  }
}
```

---

## 八、告警管理 API

### GET /api/admin/alerts/stats
**描述**: 获取告警统计

**查询参数**:
- `status`: string (可选: UNACKNOWLEDGED, ACKNOWLEDGED, RESOLVED)

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 0,
    "unacknowledged": 0,
    "acknowledged": 0,
    "resolved": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  }
}
```

---

### GET /api/admin/alerts
**描述**: 获取告警列表

**查询参数**:
- `page`: int
- `page_size`: int
- `status`: string (可选)
- `severity`: string (可选)

---

## 九、API命名规范

### 资源命名
- ✅ 使用复数形式: `/work-tickets`, `/contractors`, `/areas`
- ✅ 使用kebab-case: `work-tickets` (不是 `workTickets`)
- ✅ 避免缩写: `contractors` (不是 `ctors`)

### 路由顺序
- ✅ 具体路由在前: `/contractors/options`
- ✅ 动态路由在后: `/contractors/{contractor_id}`

### 响应格式
统一使用:
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

错误响应:
```json
{
  "code": 10000,
  "message": "错误信息",
  "data": null
}
```

---

## 十、更新日志

### 2026-01-10
- ✅ 添加告警管理API
- ✅ 修正Dashboard API响应格式
- ✅ 添加API命名规范

---

**维护说明**: 
- 每次新增API时，必须更新此文档
- 前后端开发前，必须参考此文档
- PR审查时，必须检查API是否与文档一致


