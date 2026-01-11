import request from './request'

export const workersApi = {
  // 获取人员列表
  getList(params) {
    return request.get('/admin/workers', { params })
  },
  
  // 获取人员详情
  getDetail(id) {
    return request.get(`/admin/workers/${id}`)
  },
  
  // 创建人员
  create(data) {
    return request.post('/admin/workers', data)
  },
  
  // 更新人员
  update(id, data) {
    return request.patch(`/admin/workers/${id}`, data)
  },
  
  // 删除人员
  delete(id) {
    return request.delete(`/admin/workers/${id}`)
  },
  
  // 获取人员选项（下拉框用）
  getOptions(params) {
    return request.get('/admin/workers/options', { params })
  },
  
  // 批量导入人员
  batchImport(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    return request.post('/admin/workers/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 导出人员模板
  exportTemplate() {
    return request.get('/admin/workers/template', {
      responseType: 'blob'
    })
  }
}

