import request from './request'

export const authApi = {
  // 登录
  login(data) {
    return request.post('/admin/auth/login', data)
  },
  
  // 获取当前用户信息
  getUserInfo() {
    return request.get('/admin/auth/me')
  },
  
  // 修改密码
  changePassword(data) {
    return request.post('/admin/auth/change-password', data)
  }
  
  // 注意: refreshToken 已移除，后端没有对应路由
}

