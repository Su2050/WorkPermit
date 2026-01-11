import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 布局
import MainLayout from '@/layouts/MainLayout.vue'

// 路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台', icon: 'Odometer' }
      },
      // 作业票管理
      {
        path: 'tickets',
        name: 'Tickets',
        component: () => import('@/views/tickets/index.vue'),
        meta: { title: '作业票管理', icon: 'Tickets' }
      },
      {
        path: 'tickets/create',
        name: 'TicketCreate',
        component: () => import('@/views/tickets/create.vue'),
        meta: { title: '新建作业票', hidden: true, activeMenu: '/tickets' }
      },
      {
        path: 'tickets/:id',
        name: 'TicketDetail',
        component: () => import('@/views/tickets/detail.vue'),
        meta: { title: '作业票详情', hidden: true, activeMenu: '/tickets' }
      },
      // 基础数据
      {
        path: 'sites',
        name: 'Sites',
        component: () => import('@/views/sites/index.vue'),
        meta: { title: '工地管理', icon: 'Office' }
      },
      {
        path: 'sites/:id',
        name: 'SiteDetail',
        component: () => import('@/views/sites/detail.vue'),
        meta: { title: '工地详情', hidden: true, activeMenu: '/sites' }
      },
      {
        path: 'areas',
        name: 'Areas',
        component: () => import('@/views/areas/index.vue'),
        meta: { title: '作业区域', icon: 'Location' }
      },
      {
        path: 'videos',
        name: 'Videos',
        component: () => import('@/views/videos/index.vue'),
        meta: { title: '培训视频', icon: 'VideoCamera' }
      },
      {
        path: 'contractors',
        name: 'Contractors',
        component: () => import('@/views/contractors/index.vue'),
        meta: { title: '施工单位', icon: 'OfficeBuilding' }
      },
      {
        path: 'workers',
        name: 'Workers',
        component: () => import('@/views/workers/index.vue'),
        meta: { title: '人员管理', icon: 'User' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/index.vue'),
        meta: { title: '用户管理', icon: 'UserFilled' }
      },
      // 监控与报表
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/views/reports/index.vue'),
        meta: { title: '报表中心', icon: 'TrendCharts' }
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: () => import('@/views/alerts/index.vue'),
        meta: { title: '告警中心', icon: 'Bell' }
      },
      // 系统设置
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/index.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      }
    ]
  },
  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 设置页面标题
  document.title = `${to.meta.title || '作业票管理系统'} - WorkPermit`
  
  // 公开页面直接放行
  if (to.meta.public) {
    next()
    return
  }
  
  // 检查登录状态
  if (!authStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }
  
  next()
})

export default router

