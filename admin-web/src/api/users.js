import request from './request'

export const usersApi = {
  // 获取用户列表
  getList(params) {
    return request.get('/admin/users', { params })
  },
  
  // 获取用户详情
  getDetail(id) {
    return request.get(`/admin/users/${id}`)
  },
  
  // 创建用户
  create(data) {
    return request.post('/admin/users', data)
  },
  
  // 更新用户
  update(id, data) {
    return request.patch(`/admin/users/${id}`, data)
  },
  
  // 重置密码
  resetPassword(id, newPassword) {
    return request.post(`/admin/users/${id}/reset-password`, { new_password: newPassword })
  }
}


