import request from './request'

export const sitesApi = {
  // 获取工地列表
  getList(params) {
    return request.get('/admin/sites', { params })
  },
  
  // 获取工地详情
  getDetail(id) {
    return request.get(`/admin/sites/${id}`)
  },
  
  // 获取工地选项（下拉框用）
  getOptions() {
    return request.get('/admin/sites/options')
  },
  
  // 创建工地
  create(data) {
    return request.post('/admin/sites', data)
  },
  
  // 更新工地
  update(id, data) {
    return request.patch(`/admin/sites/${id}`, data)
  }
}

