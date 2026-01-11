import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || '')
  const userName = computed(() => user.value?.username || '')
  const siteName = computed(() => user.value?.site?.name || '')
  
  // 是否系统管理员
  const isSysAdmin = computed(() => userRole.value === 'SysAdmin')
  // 是否施工单位管理员
  const isContractorAdmin = computed(() => userRole.value === 'ContractorAdmin')
  
  // 登录
  async function login(credentials) {
    try {
      const response = await authApi.login(credentials)
      
      if (response.data?.code === 0) {
        const data = response.data.data
        
        token.value = data.access_token
        user.value = data.user
        
        localStorage.setItem('token', data.access_token)
        
        return { success: true }
      } else {
        return { 
          success: false, 
          message: response.data?.message || '登录失败' 
        }
      }
    } catch (error) {
      console.error('Login failed:', error)
      return { 
        success: false, 
        message: error.response?.data?.message || '网络错误' 
      }
    }
  }
  
  // 登出
  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    router.push({ name: 'Login' })
  }
  
  // 获取用户信息
  async function fetchUserInfo() {
    try {
      const response = await authApi.getUserInfo()
      
      if (response.data?.code === 0) {
        user.value = response.data.data
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error)
      // Token 无效，登出
      if (error.response?.status === 401) {
        logout()
      }
    }
  }
  
  return {
    token,
    user,
    isLoggedIn,
    userRole,
    userName,
    siteName,
    isSysAdmin,
    isContractorAdmin,
    login,
    logout,
    fetchUserInfo
  }
}, {
  persist: {
    paths: ['token']
  }
})

