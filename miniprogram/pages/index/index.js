/**
 * 首页
 */
const app = getApp()
const { trainingApi } = require('../../utils/api')

Page({
  data: {
    isLoggedIn: false,
    workerInfo: null,
    todayTasks: [],
    taskStats: {
      total: 0,
      completed: 0,
      remaining: 0
    },
    loading: true
  },

  onLoad() {
    this.checkLoginAndLoad()
  },

  onShow() {
    if (app.globalData.isLoggedIn) {
      this.loadTasks()
    }
  },

  onPullDownRefresh() {
    this.loadTasks().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 检查登录状态并加载数据
   */
  checkLoginAndLoad() {
    if (!app.globalData.isLoggedIn) {
      this.setData({
        isLoggedIn: false,
        loading: false
      })
      return
    }

    this.setData({
      isLoggedIn: true,
      workerInfo: app.globalData.workerInfo
    })

    this.loadTasks()
  },

  /**
   * 加载今日任务
   */
  async loadTasks() {
    this.setData({ loading: true })

    try {
      const res = await trainingApi.getTasks()
      const tasks = res.data.tasks || []
      
      // 统计
      const completed = tasks.filter(t => t.training_status === 'COMPLETED').length
      
      this.setData({
        todayTasks: tasks,
        taskStats: {
          total: tasks.length,
          completed: completed,
          remaining: tasks.length - completed
        }
      })
    } catch (err) {
      console.error('Failed to load tasks:', err)
    } finally {
      this.setData({ loading: false })
    }
  },

  /**
   * 跳转登录
   */
  goLogin() {
    wx.navigateTo({ url: '/pages/auth/bind' })
  },

  /**
   * 跳转任务详情
   */
  goTaskDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/training/list?dailyTicketId=${id}`
    })
  },

  /**
   * 开始培训
   */
  startTraining(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/training/video?dailyTicketId=${id}`
    })
  }
})

