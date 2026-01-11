/**
 * 个人中心页面
 */
const app = getApp()
const { profileApi } = require('../../utils/api')

Page({
  data: {
    isLoggedIn: false,
    workerInfo: null,
    stats: {
      totalTrainings: 0,
      completedTrainings: 0,
      totalWatchTime: 0
    },
    notifications: [],
    unreadCount: 0
  },

  onLoad() {
    this.checkLoginAndLoad()
  },

  onShow() {
    if (app.globalData.isLoggedIn) {
      this.loadProfile()
    }
  },

  /**
   * 检查登录状态并加载数据
   */
  checkLoginAndLoad() {
    if (!app.globalData.isLoggedIn) {
      this.setData({ isLoggedIn: false })
      return
    }

    this.setData({
      isLoggedIn: true,
      workerInfo: app.globalData.workerInfo
    })

    this.loadProfile()
  },

  /**
   * 加载个人信息
   */
  async loadProfile() {
    try {
      const res = await profileApi.getProfile()
      
      this.setData({
        stats: res.data.stats,
        notifications: res.data.recent_notifications || [],
        unreadCount: res.data.unread_count || 0
      })
    } catch (err) {
      console.error('Failed to load profile:', err)
    }
  },

  /**
   * 跳转登录
   */
  goLogin() {
    wx.navigateTo({ url: '/pages/auth/bind' })
  },

  /**
   * 查看培训历史
   */
  goHistory() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  /**
   * 查看通知
   */
  goNotifications() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  },

  /**
   * 退出登录
   */
  logout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.clearLoginStatus()
          this.setData({ isLoggedIn: false })
          wx.switchTab({ url: '/pages/index/index' })
        }
      }
    })
  }
})

