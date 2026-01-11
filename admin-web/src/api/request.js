import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    
    // 添加 token
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data
    
    // 业务错误处理
    if (res.code !== 0) {
      // 特殊错误码处理
      if (res.code === 401) {
        // Token 过期
        ElMessageBox.confirm(
          '登录已过期，请重新登录',
          '提示',
          {
            confirmButtonText: '重新登录',
            cancelButtonText: '取消',
            type: 'warning'
          }
        ).then(() => {
          const authStore = useAuthStore()
          authStore.logout()
        })
        return Promise.reject(new Error(res.message || '未授权'))
      }
      
      if (res.code === 403) {
        ElMessage.error('没有权限执行此操作')
        return Promise.reject(new Error(res.message || '无权限'))
      }
      
      // 其他错误 - 优先显示详细错误信息（如果有）
      let errorMessage = res.message || '请求失败'
      if (res.data && Array.isArray(res.data) && res.data.length > 0) {
        // 如果有详细错误列表，显示第一个错误的具体信息
        const firstError = res.data[0]
        if (firstError.message) {
          errorMessage = firstError.message
        }
      }
      ElMessage.error(errorMessage)
      return Promise.reject(new Error(res.message))
    }
    
    return response
  },
  (error) => {
    // HTTP 错误处理
    if (error.response) {
      const status = error.response.status
      const res = error.response.data
      
      // 优先显示后端返回的详细错误信息（如果有）
      let errorMessage = null
      if (res && res.data && Array.isArray(res.data) && res.data.length > 0) {
        const firstError = res.data[0]
        if (firstError.message) {
          errorMessage = firstError.message
        }
      } else if (res && res.message) {
        errorMessage = res.message
      }
      
      switch (status) {
        case 401:
          const authStore = useAuthStore()
          authStore.logout()
          router.push({ name: 'Login' })
          break
        case 403:
          ElMessage.error(errorMessage || '没有权限访问')
          break
        case 404:
          ElMessage.error(errorMessage || '请求的资源不存在')
          break
        case 500:
          ElMessage.error(errorMessage || '服务器内部错误')
          break
        default:
          ElMessage.error(errorMessage || `请求失败: ${status}`)
      }
    } else if (error.message.includes('timeout')) {
      ElMessage.error('请求超时，请稍后重试')
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default request

