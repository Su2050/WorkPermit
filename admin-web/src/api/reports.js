import request from './request'

export const reportsApi = {
  // 获取看板数据
  getDashboard(params) {
    return request.get('/admin/reports/dashboard', { params })
  },

  // 获取看板首屏统计（仅stats，用于首屏快速渲染）
  getDashboardStats(params) {
    return request.get('/admin/reports/dashboard/stats', { params })
  },
  
  // 获取培训统计
  getTrainingStats(params) {
    return request.get('/admin/reports/training-stats', { params })
  },
  
  // 获取门禁同步统计
  getAccessSyncStats(params) {
    return request.get('/admin/reports/access-sync-stats', { params })
  },
  
  // 获取对账报告
  getReconciliationReport(params) {
    return request.get('/admin/reports/reconciliation', { params })
  },
  
  // 获取趋势数据
  getTrend(params) {
    return request.get('/admin/reports/trend', { params })
  },
  
  // 导出报表
  exportReport(reportType, params) {
    return request.get(`/admin/reports/export/${reportType}`, {
      params,
      responseType: 'blob'
    })
  }
}
