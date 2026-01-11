import request from './request'

export const areasApi = {
  // 获取区域列表
  getList(params) {
    return request.get('/admin/areas', { params })
  },
  
  // 获取区域详情
  getDetail(id) {
    return request.get(`/admin/areas/${id}`)
  },
  
  // 创建区域
  create(data) {
    return request.post('/admin/areas', data)
  },
  
  // 更新区域
  update(id, data) {
    return request.patch(`/admin/areas/${id}`, data)
  },
  
  // 删除区域
  delete(id) {
    return request.delete(`/admin/areas/${id}`)
  },
  
  // 获取区域选项（下拉框用）
  getOptions(params) {
    return request.get('/admin/areas/options', { params })
  }
}

