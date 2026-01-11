/**
 * 身份绑定页面
 */
const app = getApp()
const { authApi } = require('../../utils/api')

Page({
  data: {
    step: 1, // 1: 微信授权, 2: 身份验证
    loading: false,
    wxCode: '',
    form: {
      name: '',
      idCard: '',
      phone: ''
    },
    agreed: false
  },

  onLoad() {
    // 如果已登录，跳转首页
    if (app.globalData.isLoggedIn) {
      wx.switchTab({ url: '/pages/index/index' })
    }
  },

  /**
   * 微信登录
   */
  wxLogin() {
    this.setData({ loading: true })

    wx.login({
      success: (res) => {
        if (res.code) {
          this.setData({
            wxCode: res.code,
            step: 2,
            loading: false
          })
        } else {
          wx.showToast({ title: '登录失败', icon: 'none' })
          this.setData({ loading: false })
        }
      },
      fail: () => {
        wx.showToast({ title: '登录失败', icon: 'none' })
        this.setData({ loading: false })
      }
    })
  },

  /**
   * 获取手机号
   */
  getPhoneNumber(e) {
    if (e.detail.errMsg === 'getPhoneNumber:ok') {
      // 实际项目中需要发送 e.detail.code 到后端解密
      // 这里简化处理
      wx.showToast({ title: '获取成功', icon: 'success' })
    }
  },

  /**
   * 输入变化
   */
  onInputChange(e) {
    const { field } = e.currentTarget.dataset
    this.setData({
      [`form.${field}`]: e.detail.value
    })
  },

  /**
   * 协议勾选
   */
  onAgreeChange(e) {
    this.setData({ agreed: e.detail.value.length > 0 })
  },

  /**
   * 提交绑定
   */
  async submitBind() {
    const { form, agreed, wxCode } = this.data

    // 验证
    if (!form.name) {
      wx.showToast({ title: '请输入姓名', icon: 'none' })
      return
    }
    if (!form.idCard || form.idCard.length !== 18) {
      wx.showToast({ title: '请输入正确的身份证号', icon: 'none' })
      return
    }
    if (!form.phone || form.phone.length !== 11) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }
    if (!agreed) {
      wx.showToast({ title: '请阅读并同意用户协议', icon: 'none' })
      return
    }

    this.setData({ loading: true })

    try {
      const res = await authApi.bind({
        wx_code: wxCode,
        name: form.name,
        id_card_no: form.idCard,
        phone: form.phone
      })

      // 保存登录状态
      app.setLoginStatus(res.data.token, res.data.worker)

      wx.showToast({ title: '绑定成功', icon: 'success' })

      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
      }, 1500)
    } catch (err) {
      console.error('Bind failed:', err)
    } finally {
      this.setData({ loading: false })
    }
  }
})

