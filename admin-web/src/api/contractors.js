import request from './request'

export const contractorsApi = {
  // 获取施工单位列表
  getList(params) {
    return request.get('/admin/contractors', { params })
  },
  
  // 获取施工单位详情
  getDetail(id) {
    return request.get(`/admin/contractors/${id}`)
  },
  
  // 创建施工单位
  create(data) {
    return request.post('/admin/contractors', data)
  },
  
  // 更新施工单位
  update(id, data) {
    return request.patch(`/admin/contractors/${id}`, data)
  },
  
  // 删除施工单位
  delete(id) {
    return request.delete(`/admin/contractors/${id}`)
  },
  
  // 获取施工单位选项
  getOptions(params) {
    return request.get('/admin/contractors/options', { params })
  },
  
  // 获取施工单位下的人员
  getWorkers(id, params) {
    return request.get(`/admin/contractors/${id}/workers`, { params })
  }
}

