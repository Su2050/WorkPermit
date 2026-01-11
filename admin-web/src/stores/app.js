import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 侧边栏折叠状态
  const sidebarCollapsed = ref(false)
  
  // 当前站点（多租户）
  const currentSiteId = ref('')
  const currentSiteName = ref('')
  
  // 全局加载状态
  const globalLoading = ref(false)
  
  // 切换侧边栏
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  
  // 设置当前站点
  function setCurrentSite(siteId, siteName) {
    currentSiteId.value = siteId
    currentSiteName.value = siteName
  }
  
  // 设置全局加载
  function setGlobalLoading(loading) {
    globalLoading.value = loading
  }
  
  return {
    sidebarCollapsed,
    currentSiteId,
    currentSiteName,
    globalLoading,
    toggleSidebar,
    setCurrentSite,
    setGlobalLoading
  }
}, {
  persist: {
    paths: ['sidebarCollapsed', 'currentSiteId', 'currentSiteName']
  }
})

