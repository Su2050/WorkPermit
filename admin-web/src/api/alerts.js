import request from './request'

export const alertsApi = {
  // 获取告警列表
  getList(params) {
    return request.get('/admin/alerts', { params })
  },
  
  // 获取告警详情
  getDetail(id) {
    return request.get(`/admin/alerts/${id}`)
  },
  
  // 确认告警
  acknowledge(id) {
    return request.post(`/admin/alerts/${id}/acknowledge`)
  },
  
  // 批量确认告警
  batchAcknowledge(ids) {
    return request.post('/admin/alerts/batch-acknowledge', { ids })
  },
  
  // 获取告警统计
  getStats(params) {
    return request.get('/admin/alerts/stats', { params })
  },
  
  // 获取告警规则列表
  getRules() {
    return request.get('/admin/alerts/rules')
  },
  
  // 更新告警规则
  updateRule(id, data) {
    return request.put(`/admin/alerts/rules/${id}`, data)
  }
}

