/**
 * 网络请求封装
 */
const app = getApp()

/**
 * 发起HTTP请求
 */
function request(options) {
  return new Promise((resolve, reject) => {
    const { url, method = 'GET', data, header = {} } = options
    
    // 添加认证头
    if (app.globalData.token) {
      header['Authorization'] = `Bearer ${app.globalData.token}`
    }
    
    wx.request({
      url: `${app.globalData.baseUrl}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...header
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          const response = res.data
          
          // 业务错误处理
          if (response.code !== 0) {
            if (response.code === 401) {
              // Token过期，跳转登录
              app.clearLoginStatus()
              wx.redirectTo({ url: '/pages/auth/bind' })
              reject(new Error('登录已过期'))
              return
            }
            
            wx.showToast({
              title: response.message || '请求失败',
              icon: 'none'
            })
            reject(new Error(response.message))
            return
          }
          
          resolve(response)
        } else {
          // HTTP错误
          const errMsg = getHttpErrorMessage(res.statusCode)
          wx.showToast({ title: errMsg, icon: 'none' })
          reject(new Error(errMsg))
        }
      },
      fail(err) {
        wx.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      }
    })
  })
}

/**
 * GET请求
 */
function get(url, params = {}) {
  return request({ url, method: 'GET', data: params })
}

/**
 * POST请求
 */
function post(url, data = {}) {
  return request({ url, method: 'POST', data })
}

/**
 * PUT请求
 */
function put(url, data = {}) {
  return request({ url, method: 'PUT', data })
}

/**
 * DELETE请求
 */
function del(url, data = {}) {
  return request({ url, method: 'DELETE', data })
}

/**
 * 获取HTTP错误信息
 */
function getHttpErrorMessage(statusCode) {
  const messages = {
    400: '请求参数错误',
    401: '未授权',
    403: '无权限访问',
    404: '资源不存在',
    500: '服务器错误',
    502: '网关错误',
    503: '服务暂不可用'
  }
  return messages[statusCode] || `请求失败 (${statusCode})`
}

module.exports = {
  request,
  get,
  post,
  put,
  del
}

