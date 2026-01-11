import request from './request'

export const auditApi = {
  // 获取审计日志列表
  getList(params) {
    return request.get('/admin/audit-logs', { params })
  },
  
  // 获取审计日志详情
  getDetail(id) {
    return request.get(`/admin/audit-logs/${id}`)
  }
}


