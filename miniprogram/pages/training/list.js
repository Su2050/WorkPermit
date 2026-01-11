/**
 * 培训列表页面
 */
const app = getApp()
const { trainingApi } = require('../../utils/api')

Page({
  data: {
    dailyTicketId: '',
    ticketInfo: null,
    videos: [],
    loading: true
  },

  onLoad(options) {
    this.setData({ dailyTicketId: options.dailyTicketId })
    this.loadProgress()
  },

  onPullDownRefresh() {
    this.loadProgress().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 加载培训进度
   */
  async loadProgress() {
    const { dailyTicketId } = this.data
    this.setData({ loading: true })

    try {
      const res = await trainingApi.getProgress(dailyTicketId)
      
      this.setData({
        ticketInfo: res.data.ticket,
        videos: res.data.videos
      })
    } catch (err) {
      console.error('Failed to load progress:', err)
    } finally {
      this.setData({ loading: false })
    }
  },

  /**
   * 开始学习视频
   */
  startVideo(e) {
    const { videoId, status } = e.currentTarget.dataset
    
    if (status === 'COMPLETED') {
      wx.showToast({ title: '该视频已完成', icon: 'none' })
      return
    }

    wx.navigateTo({
      url: `/pages/training/video?dailyTicketId=${this.data.dailyTicketId}&videoId=${videoId}`
    })
  }
})

