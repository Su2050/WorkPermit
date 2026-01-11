/**
 * 小程序入口文件
 */
App({
  globalData: {
    userInfo: null,
    token: '',
    baseUrl: 'https://api.workpermit.example.com', // 后端API地址
    isLoggedIn: false,
    workerInfo: null
  },

  onLaunch() {
    // 检查登录状态
    this.checkLoginStatus()
    
    // 获取系统信息
    const systemInfo = wx.getSystemInfoSync()
    this.globalData.systemInfo = systemInfo
    this.globalData.statusBarHeight = systemInfo.statusBarHeight
  },

  /**
   * 检查登录状态
   */
  checkLoginStatus() {
    const token = wx.getStorageSync('token')
    const workerInfo = wx.getStorageSync('workerInfo')
    
    if (token && workerInfo) {
      this.globalData.token = token
      this.globalData.workerInfo = workerInfo
      this.globalData.isLoggedIn = true
    }
  },

  /**
   * 设置登录状态
   */
  setLoginStatus(token, workerInfo) {
    this.globalData.token = token
    this.globalData.workerInfo = workerInfo
    this.globalData.isLoggedIn = true
    
    wx.setStorageSync('token', token)
    wx.setStorageSync('workerInfo', workerInfo)
  },

  /**
   * 清除登录状态
   */
  clearLoginStatus() {
    this.globalData.token = ''
    this.globalData.workerInfo = null
    this.globalData.isLoggedIn = false
    
    wx.removeStorageSync('token')
    wx.removeStorageSync('workerInfo')
  },

  /**
   * 全局错误处理
   */
  onError(err) {
    console.error('Global error:', err)
  }
})

