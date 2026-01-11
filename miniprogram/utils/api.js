/**
 * API接口定义
 */
const { get, post, put } = require('./request')

// 认证相关
const authApi = {
  // 微信登录
  wxLogin(code) {
    return post('/mp/auth/wx-login', { code })
  },
  
  // 绑定身份
  bind(data) {
    return post('/mp/auth/bind', data)
  },
  
  // 获取用户信息
  getUserInfo() {
    return get('/mp/auth/me')
  }
}

// 培训相关
const trainingApi = {
  // 获取待办任务列表
  getTasks() {
    return get('/mp/tasks')
  },
  
  // 获取培训进度
  getProgress(dailyTicketId) {
    return get(`/mp/training/progress/${dailyTicketId}`)
  },
  
  // 开始学习（创建session）
  startSession(data) {
    return post('/mp/training/session/start', data)
  },
  
  // 上报进度（心跳）
  reportProgress(sessionId, data) {
    return post(`/mp/training/session/${sessionId}/progress`, data)
  },
  
  // 完成学习
  completeSession(sessionId) {
    return post(`/mp/training/session/${sessionId}/complete`)
  },
  
  // 提交人脸校验结果
  submitFaceCheck(sessionId, data) {
    return post(`/mp/training/session/${sessionId}/face-check`, data)
  }
}

// 个人中心
const profileApi = {
  // 获取个人信息
  getProfile() {
    return get('/mp/profile')
  },
  
  // 获取培训历史
  getHistory(params) {
    return get('/mp/profile/history', params)
  },
  
  // 获取通知列表
  getNotifications(params) {
    return get('/mp/profile/notifications', params)
  },
  
  // 标记通知已读
  markNotificationRead(logId) {
    return post(`/mp/profile/notifications/${logId}/read`)
  }
}

module.exports = {
  authApi,
  trainingApi,
  profileApi
}

