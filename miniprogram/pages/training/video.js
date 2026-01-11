/**
 * 视频播放页面
 * P0-2: 防作弊实现
 */
const app = getApp()
const { trainingApi } = require('../../utils/api')

Page({
  data: {
    dailyTicketId: '',
    videoId: '',
    videoInfo: null,
    sessionId: '',
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    progressPercent: 0,
    showFaceCheck: false,
    faceCheckCountdown: 10,
    loading: true
  },

  // 心跳定时器
  heartbeatTimer: null,
  // 随机校验定时器
  randomCheckTimer: null,
  // 最后上报时间
  lastReportTime: 0,

  onLoad(options) {
    this.setData({
      dailyTicketId: options.dailyTicketId,
      videoId: options.videoId
    })
    this.initSession()
  },

  onUnload() {
    this.stopTimers()
  },

  onHide() {
    // 进入后台，暂停视频
    this.pauseVideo()
  },

  /**
   * 初始化学习会话
   */
  async initSession() {
    const { dailyTicketId, videoId } = this.data

    try {
      const res = await trainingApi.startSession({
        daily_ticket_id: dailyTicketId,
        video_id: videoId
      })

      this.setData({
        sessionId: res.data.session_id,
        videoInfo: res.data.video,
        loading: false
      })

      // 启动心跳
      this.startHeartbeat()
      // 启动随机校验调度
      this.startRandomCheckScheduler()
    } catch (err) {
      console.error('Failed to init session:', err)
      wx.showToast({ title: '初始化失败', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
    }
  },

  /**
   * 视频播放事件
   */
  onVideoPlay() {
    this.setData({ isPlaying: true })
  },

  /**
   * 视频暂停事件
   */
  onVideoPause() {
    this.setData({ isPlaying: false })
  },

  /**
   * 视频进度更新
   */
  onVideoTimeUpdate(e) {
    const { currentTime, duration } = e.detail
    const progressPercent = duration ? Math.round(currentTime / duration * 100) : 0

    this.setData({
      currentTime,
      duration,
      progressPercent
    })
  },

  /**
   * 视频播放结束
   */
  async onVideoEnded() {
    this.setData({ isPlaying: false })
    
    try {
      await trainingApi.completeSession(this.data.sessionId)
      
      wx.showToast({ title: '学习完成！', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 1500)
    } catch (err) {
      console.error('Failed to complete session:', err)
    }
  },

  /**
   * 视频错误
   */
  onVideoError(e) {
    console.error('Video error:', e.detail)
    wx.showToast({ title: '视频加载失败', icon: 'none' })
  },

  /**
   * 暂停视频
   */
  pauseVideo() {
    const videoContext = wx.createVideoContext('trainingVideo')
    videoContext.pause()
  },

  /**
   * 启动心跳上报
   */
  startHeartbeat() {
    // 每5秒上报一次
    this.heartbeatTimer = setInterval(() => {
      this.reportProgress()
    }, 5000)
  },

  /**
   * 上报进度
   */
  async reportProgress() {
    const { sessionId, currentTime, isPlaying } = this.data
    
    if (!sessionId) return

    const now = Date.now()
    const delta = Math.round((now - this.lastReportTime) / 1000)
    this.lastReportTime = now

    try {
      await trainingApi.reportProgress(sessionId, {
        position: Math.round(currentTime),
        played_seconds_delta: isPlaying ? delta : 0,
        video_state: isPlaying ? 'playing' : 'paused',
        client_ts: Math.round(now / 1000)
      })
    } catch (err) {
      console.error('Failed to report progress:', err)
    }
  },

  /**
   * 启动随机校验调度
   */
  startRandomCheckScheduler() {
    // 3-7分钟随机触发
    const scheduleNext = () => {
      const delay = (Math.random() * 4 + 3) * 60 * 1000 // 3-7分钟
      
      this.randomCheckTimer = setTimeout(() => {
        if (this.data.isPlaying) {
          this.triggerFaceCheck()
        }
        scheduleNext()
      }, delay)
    }
    
    scheduleNext()
  },

  /**
   * 触发人脸校验
   */
  triggerFaceCheck() {
    this.pauseVideo()
    this.setData({
      showFaceCheck: true,
      faceCheckCountdown: 10
    })

    // 倒计时
    const countdownTimer = setInterval(() => {
      const count = this.data.faceCheckCountdown - 1
      
      if (count <= 0) {
        clearInterval(countdownTimer)
        this.handleFaceCheckTimeout()
      } else {
        this.setData({ faceCheckCountdown: count })
      }
    }, 1000)
  },

  /**
   * 开始人脸校验
   */
  startFaceCheck() {
    // 调用微信人脸核身（需要开通资质）
    // 这里简化为模拟
    wx.showLoading({ title: '验证中...' })

    setTimeout(async () => {
      wx.hideLoading()
      
      // 模拟通过
      try {
        await trainingApi.submitFaceCheck(this.data.sessionId, {
          passed: true
        })
        
        wx.showToast({ title: '验证通过', icon: 'success' })
        this.setData({ showFaceCheck: false })
        
        // 继续播放
        const videoContext = wx.createVideoContext('trainingVideo')
        videoContext.play()
      } catch (err) {
        console.error('Face check failed:', err)
      }
    }, 2000)
  },

  /**
   * 人脸校验超时
   */
  async handleFaceCheckTimeout() {
    try {
      await trainingApi.submitFaceCheck(this.data.sessionId, {
        passed: false,
        reason: 'TIMEOUT'
      })
    } catch (err) {
      console.error('Face check timeout report failed:', err)
    }

    this.setData({ showFaceCheck: false })
    wx.showToast({ title: '校验超时，请重试', icon: 'none' })
  },

  /**
   * 停止所有定时器
   */
  stopTimers() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
    if (this.randomCheckTimer) {
      clearTimeout(this.randomCheckTimer)
      this.randomCheckTimer = null
    }
  }
})

