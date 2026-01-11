import request from './request'

export const ticketsApi = {
  // 获取作业票列表
  getList(params) {
    return request.get('/admin/work-tickets', { params })
  },
  
  // 获取作业票详情
  getDetail(id) {
    return request.get(`/admin/work-tickets/${id}`)
  },
  
  // 创建作业票
  create(data) {
    return request.post('/admin/work-tickets', data)
  },
  
  // 更新作业票（变更）
  update(id, data) {
    return request.patch(`/admin/work-tickets/${id}`, data)
  },
  
  // 注意: 变更作业票请使用 update(id, data) 方法，通过 PATCH 请求
  // applyChanges 已废弃，后端没有 /changes 路由
  
  // 发布作业票
  publish(id) {
    return request.post(`/admin/work-tickets/${id}/publish`)
  },
  
  // 取消作业票
  cancel(id, reason) {
    return request.post(`/admin/work-tickets/${id}/cancel`, { reason })
  },
  
  // 关闭作业票
  close(id, reason) {
    return request.post(`/admin/work-tickets/${id}/close`, { reason })
  },
  
  // 获取每日票据列表
  getDailyTickets(ticketId, params) {
    return request.get(`/admin/work-tickets/${ticketId}/daily-tickets`, { params })
  },
  
  // 获取每日票据详情
  getDailyTicketDetail(dailyTicketId) {
    return request.get(`/admin/daily-tickets/${dailyTicketId}`)
  },
  
  // 获取作业票统计
  getStats(params) {
    return request.get('/admin/work-tickets/stats', { params })
  },
  
  // 导出作业票
  export(params) {
    return request.get('/admin/work-tickets/export', { 
      params,
      responseType: 'blob'
    })
  },
  
  // 批量关闭作业票
  batchClose(ticket_ids, reason) {
    return request.post('/admin/work-tickets/batch-close', { ticket_ids, reason })
  },
  
  // 批量取消作业票
  batchCancel(ticket_ids, reason) {
    return request.post('/admin/work-tickets/batch-cancel', { ticket_ids, reason })
  }
}

