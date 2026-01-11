<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <aside 
      class="sidebar"
      :class="{ collapsed: appStore.sidebarCollapsed }"
    >
      <!-- Logo区域 -->
      <div class="sidebar-logo">
        <div class="logo-icon">
          <el-icon :size="28"><Tickets /></el-icon>
        </div>
        <span v-if="!appStore.sidebarCollapsed" class="logo-text">
          作业票系统
        </span>
      </div>
      
      <!-- 导航菜单 -->
      <el-scrollbar class="sidebar-scroll">
        <el-menu
          :default-active="activeMenu"
          :collapse="appStore.sidebarCollapsed"
          :collapse-transition="false"
          router
          class="sidebar-menu"
        >
          <template v-for="route in menuRoutes" :key="route.path">
            <el-menu-item :index="route.path">
              <el-icon>
                <component :is="route.meta.icon" />
              </el-icon>
              <template #title>{{ route.meta.title }}</template>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>
      
      <!-- 侧边栏底部 -->
      <div class="sidebar-footer">
        <el-button 
          text 
          class="collapse-btn"
          @click="appStore.toggleSidebar"
        >
          <el-icon :size="18">
            <component :is="appStore.sidebarCollapsed ? 'Expand' : 'Fold'" />
          </el-icon>
        </el-button>
      </div>
    </aside>
    
    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 顶部导航 -->
      <header class="header">
        <div class="header-left">
          <!-- 面包屑 -->
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">
              首页
            </el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute.meta.title">
              {{ currentRoute.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 站点选择（多租户） -->
          <el-dropdown v-if="authStore.isSysAdmin" class="site-dropdown">
            <span class="site-selector">
              <el-icon><Location /></el-icon>
              {{ appStore.currentSiteName || '全部站点' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="selectSite('', '全部站点')">
                  全部站点
                </el-dropdown-item>
                <!-- 实际站点列表从后端获取 -->
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <!-- 告警 -->
          <el-badge :value="alertCount" :hidden="!alertCount" class="alert-badge">
            <el-button text circle @click="router.push('/alerts')">
              <el-icon :size="20"><Bell /></el-icon>
            </el-button>
          </el-badge>
          
          <!-- 用户信息 -->
          <el-dropdown @command="handleUserCommand">
            <div class="user-info">
              <el-avatar :size="32" class="user-avatar">
                {{ authStore.userName?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="user-name">{{ authStore.userName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <span class="role-tag">{{ roleLabel }}</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="settings">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <!-- 页面内容 -->
      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { alertsApi } from '@/api/alerts'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

// 告警数量
const alertCount = ref(0)

// 当前路由
const currentRoute = computed(() => route)

// 当前激活的菜单
const activeMenu = computed(() => {
  const { meta, path } = route
  return meta.activeMenu || path
})

// 角色标签
const roleLabel = computed(() => {
  const roleMap = {
    SysAdmin: '系统管理员',
    ContractorAdmin: '施工单位管理员'
  }
  return roleMap[authStore.userRole] || '用户'
})

// 菜单路由
const menuRoutes = computed(() => {
  const allRoutes = router.options.routes.find(r => r.path === '/')?.children || []
  return allRoutes.filter(r => !r.meta?.hidden)
})

// 缓存的视图
const cachedViews = ref(['Dashboard'])

// 选择站点
function selectSite(siteId, siteName) {
  appStore.setCurrentSite(siteId, siteName)
}

// 处理用户命令
function handleUserCommand(command) {
  switch (command) {
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      authStore.logout()
      break
  }
}

// 获取告警数量
async function fetchAlertCount() {
  try {
    const response = await alertsApi.getStats({ status: 'UNACKNOWLEDGED' })
    if (response.data?.code === 0) {
      alertCount.value = response.data.data.count || 0
    }
  } catch (error) {
    console.error('Failed to fetch alert count:', error)
  }
}

onMounted(() => {
  // 获取用户信息
  if (authStore.isLoggedIn && !authStore.user) {
    authStore.fetchUserInfo()
  }
  
  // 获取告警数量
  fetchAlertCount()
  
  // 定时刷新告警数量
  setInterval(fetchAlertCount, 60000)
})
</script>

<style lang="scss" scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-dark);
}

.sidebar {
  width: 240px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, var(--bg-card) 0%, var(--bg-dark) 100%);
  border-right: 1px solid var(--border-color);
  transition: width 0.3s ease;
  
  &.collapsed {
    width: 64px;
    
    .logo-text {
      display: none;
    }
  }
}

.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-color);
  
  .logo-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--accent-color), var(--accent-dark));
    border-radius: var(--radius-md);
    color: white;
    flex-shrink: 0;
  }
  
  .logo-text {
    margin-left: 12px;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
  }
}

.sidebar-scroll {
  flex: 1;
  padding: 12px 0;
}

.sidebar-menu {
  border: none;
  
  :deep(.el-menu-item) {
    height: 44px;
    margin: 4px 8px;
    border-radius: var(--radius-md);
    
    &.is-active {
      background: rgba(255, 107, 53, 0.15);
      color: var(--accent-color);
      border-right: none;
      
      &::after {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 20px;
        background: var(--accent-color);
        border-radius: 0 2px 2px 0;
      }
    }
  }
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid var(--border-color);
  
  .collapse-btn {
    width: 100%;
    color: var(--text-secondary);
    
    &:hover {
      color: var(--text-primary);
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  
  &-left {
    display: flex;
    align-items: center;
    
    :deep(.el-breadcrumb) {
      .el-breadcrumb__item {
        .el-breadcrumb__inner {
          color: var(--text-secondary);
          
          &.is-link:hover {
            color: var(--accent-color);
          }
        }
        
        &:last-child .el-breadcrumb__inner {
          color: var(--text-primary);
        }
      }
      
      .el-breadcrumb__separator {
        color: var(--text-muted);
      }
    }
  }
  
  &-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
}

.site-dropdown {
  .site-selector {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 6px 12px;
    border-radius: var(--radius-md);
    transition: all 0.2s;
    
    &:hover {
      background: var(--bg-hover);
      color: var(--text-primary);
    }
  }
}

.alert-badge {
  :deep(.el-badge__content) {
    background: var(--danger-color);
    border: none;
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  transition: all 0.2s;
  
  &:hover {
    background: var(--bg-hover);
  }
  
  .user-avatar {
    background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
    color: white;
    font-weight: 500;
  }
  
  .user-name {
    color: var(--text-primary);
    font-size: 14px;
  }
  
  .el-icon {
    color: var(--text-muted);
    font-size: 12px;
  }
}

.role-tag {
  font-size: 12px;
  color: var(--text-muted);
}

.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--bg-dark);
}
</style>

