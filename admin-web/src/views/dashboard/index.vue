<template>
  <div class="dashboard">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1>早上好，{{ authStore.userName }} 👋</h1>
        <p>{{ currentDate }} · 今日有 {{ stats.todayTasks }} 项待处理任务</p>
      </div>
      <div class="quick-actions">
        <el-button type="primary" @click="router.push('/tickets/create')">
          <el-icon><Plus /></el-icon>
          新建作业票
        </el-button>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card" v-for="card in statCards" :key="card.key">
        <div class="stat-icon" :style="{ background: card.iconBg }">
          <el-icon :size="24"><component :is="card.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-label">{{ card.label }}</span>
          <span class="stat-value">{{ card.value }}</span>
          <span 
            class="stat-trend" 
            :class="card.trendType"
            v-if="card.trend"
          >
            <el-icon>
              <component :is="card.trendType === 'up' ? 'Top' : 'Bottom'" />
            </el-icon>
            {{ card.trend }}
          </span>
        </div>
      </div>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- 培训完成率趋势 -->
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <span>培训完成率趋势</span>
            <el-radio-group v-model="chartRange" size="small">
              <el-radio-button label="7d">近7天</el-radio-button>
              <el-radio-button label="30d">近30天</el-radio-button>
            </el-radio-group>
          </div>
        </template>
        <div ref="trendChartRef" class="chart-container"></div>
      </el-card>
      
      <!-- 实时状态 -->
      <el-card class="status-card">
        <template #header>
          <div class="card-header">
            <span>今日作业状态</span>
            <el-tag type="success" size="small">实时</el-tag>
          </div>
        </template>
        <div class="status-list">
          <div 
            class="status-item" 
            v-for="item in statusItems" 
            :key="item.key"
          >
            <div class="status-dot" :class="item.status"></div>
            <span class="status-label">{{ item.label }}</span>
            <span class="status-count">{{ item.count }}</span>
          </div>
        </div>
        <div ref="statusChartRef" class="status-chart"></div>
      </el-card>
    </div>
    
    <!-- 列表区域 -->
    <div class="list-section">
      <!-- 待处理作业票 -->
      <el-card class="list-card">
        <template #header>
          <div class="card-header">
            <span>待处理作业票</span>
            <el-button text type="primary" @click="router.push('/tickets')">
              查看全部
            </el-button>
          </div>
        </template>
        <el-table :data="pendingTickets" stripe>
          <el-table-column prop="title" label="作业票名称" min-width="200">
            <template #default="{ row }">
              <el-link 
                type="primary" 
                @click="router.push(`/tickets/${row.id}`)"
              >
                {{ row.title }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="contractor" label="施工单位" width="150" />
          <el-table-column prop="workerCount" label="人员" width="80" align="center" />
          <el-table-column prop="progress" label="培训进度" width="120">
            <template #default="{ row }">
              <el-progress 
                :percentage="row.progress" 
                :stroke-width="6"
                :color="getProgressColor(row.progress)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
      
      <!-- 最近告警 -->
      <el-card class="list-card">
        <template #header>
          <div class="card-header">
            <span>最近告警</span>
            <el-button text type="primary" @click="router.push('/alerts')">
              查看全部
            </el-button>
          </div>
        </template>
        <div class="alert-list">
          <div 
            class="alert-item" 
            v-for="alert in recentAlerts" 
            :key="alert.id"
            @click="router.push(`/alerts?id=${alert.id}`)"
          >
            <div class="alert-icon" :class="alert.severity">
              <el-icon><WarningFilled /></el-icon>
            </div>
            <div class="alert-content">
              <span class="alert-title">{{ alert.title }}</span>
              <span class="alert-time">{{ alert.time }}</span>
            </div>
          </div>
          <el-empty 
            v-if="!recentAlerts.length" 
            description="暂无告警"
            :image-size="80"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { useAuthStore } from '@/stores/auth'
import { reportsApi } from '@/api/reports'
import { ticketsApi } from '@/api/tickets'
import { alertsApi } from '@/api/alerts'

const router = useRouter()
const authStore = useAuthStore()

// 当前日期
const currentDate = computed(() => dayjs().format('YYYY年MM月DD日 dddd'))

// 图表范围
const chartRange = ref('7d')

// 统计数据
const stats = ref({
  todayTasks: 0,
  activeTickets: 0,
  todayTrainings: 0,
  accessGrants: 0,
  syncRate: 0
})

// 统计卡片
const statCards = computed(() => [
  {
    key: 'activeTickets',
    label: '进行中的作业票',
    value: stats.value.activeTickets,
    icon: 'Tickets',
    iconBg: 'linear-gradient(135deg, #1e3a5f, #2d5a8a)',
    trend: '+3',
    trendType: 'up'
  },
  {
    key: 'todayTrainings',
    label: '今日培训人次',
    value: stats.value.todayTrainings,
    icon: 'User',
    iconBg: 'linear-gradient(135deg, #2ea043, #46d160)',
    trend: '+12%',
    trendType: 'up'
  },
  {
    key: 'accessGrants',
    label: '今日门禁授权',
    value: stats.value.accessGrants,
    icon: 'Key',
    iconBg: 'linear-gradient(135deg, #d29922, #f0b429)',
    trend: null
  },
  {
    key: 'syncRate',
    label: '门禁同步率',
    value: `${stats.value.syncRate}%`,
    icon: 'Connection',
    iconBg: 'linear-gradient(135deg, #58a6ff, #79c0ff)',
    trend: null
  }
])

// 今日作业状态
const statusItems = ref([
  { key: 'notStarted', label: '未开始', count: 0, status: 'pending' },
  { key: 'inProgress', label: '进行中', count: 0, status: 'active' },
  { key: 'completed', label: '已完成', count: 0, status: 'success' },
  { key: 'failed', label: '异常', count: 0, status: 'danger' }
])

// 待处理作业票
const pendingTickets = ref([])

// 最近告警
const recentAlerts = ref([])

// 图表引用
const trendChartRef = ref()
const statusChartRef = ref()
let trendChart = null
let statusChart = null

// 获取进度颜色
function getProgressColor(progress) {
  if (progress >= 80) return '#2ea043'
  if (progress >= 50) return '#d29922'
  return '#f85149'
}

// 获取状态类型
function getStatusType(status) {
  const map = {
    'PUBLISHED': 'info',
    'IN_PROGRESS': 'primary',
    'EXPIRED': 'warning',
    'CLOSED': 'info'
  }
  return map[status] || 'info'
}

// 获取状态标签
function getStatusLabel(status) {
  const map = {
    'PUBLISHED': '已发布',
    'IN_PROGRESS': '进行中',
    'EXPIRED': '已过期',
    'CLOSED': '已关闭'
  }
  return map[status] || status
}

// 初始化趋势图
function initTrendChart() {
  if (!trendChartRef.value) return
  
  trendChart = echarts.init(trendChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(22, 27, 34, 0.95)',
      borderColor: '#30363d',
      textStyle: { color: '#e6edf3' }
    },
    grid: {
      left: 40,
      right: 20,
      top: 20,
      bottom: 30
    },
    xAxis: {
      type: 'category',
      data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      axisLine: { lineStyle: { color: '#30363d' } },
      axisLabel: { color: '#8b949e' }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#21262d' } },
      axisLabel: { 
        color: '#8b949e',
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '完成率',
        type: 'line',
        smooth: true,
        data: [85, 88, 92, 89, 95, 90, 93],
        lineStyle: { color: '#ff6b35', width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(255, 107, 53, 0.3)' },
              { offset: 1, color: 'rgba(255, 107, 53, 0)' }
            ]
          }
        },
        itemStyle: { color: '#ff6b35' }
      }
    ]
  }
  
  trendChart.setOption(option)
}

// 初始化状态图
function initStatusChart() {
  if (!statusChartRef.value) return
  
  statusChart = echarts.init(statusChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(22, 27, 34, 0.95)',
      borderColor: '#30363d',
      textStyle: { color: '#e6edf3' }
    },
    series: [
      {
        type: 'pie',
        radius: ['50%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        label: { show: false },
        data: [
          { value: 10, name: '未开始', itemStyle: { color: '#6e7681' } },
          { value: 25, name: '进行中', itemStyle: { color: '#58a6ff' } },
          { value: 60, name: '已完成', itemStyle: { color: '#2ea043' } },
          { value: 5, name: '异常', itemStyle: { color: '#f85149' } }
        ]
      }
    ]
  }
  
  statusChart.setOption(option)
}

// 获取看板数据
async function fetchDashboardStats() {
  try {
    const response = await reportsApi.getDashboardStats()
    if (response.data?.code === 0) {
      const data = response.data.data
      stats.value = data.stats || stats.value
    }
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', error)
    // 使用模拟数据
    stats.value = {
      todayTasks: 5,
      activeTickets: 12,
      todayTrainings: 86,
      accessGrants: 145,
      syncRate: 98.5
    }
  }
}

// 获取看板详情（列表/告警等，异步加载，不阻塞首屏）
async function fetchDashboardDetails() {
  try {
    const response = await reportsApi.getDashboard()
    if (response.data?.code === 0) {
      const data = response.data.data
      pendingTickets.value = data.pendingTickets || []
      recentAlerts.value = data.recentAlerts || []
    }
  } catch (error) {
    console.error('Failed to fetch dashboard details:', error)
    // 使用模拟数据（仅列表/告警），避免首屏空白
    pendingTickets.value = [
      { id: '1', title: 'A区焊接作业', contractor: '建设集团', workerCount: 15, progress: 60, status: 'IN_PROGRESS' },
      { id: '2', title: 'B区电气施工', contractor: '电力公司', workerCount: 8, progress: 30, status: 'IN_PROGRESS' },
      { id: '3', title: 'C区管道安装', contractor: '管道工程', workerCount: 12, progress: 85, status: 'IN_PROGRESS' }
    ]
    recentAlerts.value = [
      { id: '1', title: '门禁同步失败', severity: 'high', time: '10分钟前' },
      { id: '2', title: '培训超时未完成', severity: 'medium', time: '30分钟前' }
    ]
  }
}

// 异步加载趋势数据（不阻塞首屏）
async function fetchTrendData() {
  try {
    const days = chartRange.value === '30d' ? 30 : 7
    const response = await reportsApi.getTrend({ metric: 'completion_rate', days })
    if (response.data?.code !== 0) return
    const list = response.data.data || []
    const x = list.map(i => (i.date || '').slice(5)) // MM-DD
    const y = list.map(i => i.value || 0)

    if (trendChart) {
      trendChart.setOption({
        xAxis: { data: x },
        series: [{ data: y }]
      })
    }
  } catch (error) {
    console.error('Failed to fetch trend data:', error)
  }
}

// 窗口大小变化处理
function handleResize() {
  trendChart?.resize()
  statusChart?.resize()
}

onMounted(() => {
  // 首屏只拉 stats（更快）
  fetchDashboardStats()

  initTrendChart()
  initStatusChart()
  window.addEventListener('resize', handleResize)

  // 列表/趋势异步加载（不阻塞首屏渲染）
  setTimeout(() => {
    fetchDashboardDetails()
    fetchTrendData()
  }, 0)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  statusChart?.dispose()
})

// 切换近7天/近30天时，异步刷新趋势数据
watch(chartRange, () => {
  fetchTrendData()
})
</script>

<style lang="scss" scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  border-radius: var(--radius-lg);
  
  h1 {
    font-size: 24px;
    font-weight: 600;
    color: white;
    margin-bottom: 8px;
  }
  
  p {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  
  @media (max-width: 1200px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }
  
  .stat-icon {
    width: 56px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-md);
    color: white;
    flex-shrink: 0;
  }
  
  .stat-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .stat-label {
    font-size: 13px;
    color: var(--text-secondary);
  }
  
  .stat-value {
    font-size: 28px;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  .stat-trend {
    display: flex;
    align-items: center;
    gap: 2px;
    font-size: 12px;
    
    &.up {
      color: var(--success-color);
    }
    
    &.down {
      color: var(--danger-color);
    }
  }
}

.charts-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
}

.chart-card,
.status-card {
  :deep(.el-card__header) {
    padding: 16px 20px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    span {
      font-size: 15px;
      font-weight: 500;
      color: var(--text-primary);
    }
  }
}

.chart-container {
  height: 280px;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
  
  .status-item {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      
      &.pending { background: #6e7681; }
      &.active { background: #58a6ff; }
      &.success { background: #2ea043; }
      &.danger { background: #f85149; }
    }
    
    .status-label {
      flex: 1;
      font-size: 14px;
      color: var(--text-secondary);
    }
    
    .status-count {
      font-size: 16px;
      font-weight: 500;
      color: var(--text-primary);
    }
  }
}

.status-chart {
  height: 180px;
}

.list-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
}

.list-card {
  :deep(.el-card__header) {
    padding: 16px 20px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    span {
      font-size: 15px;
      font-weight: 500;
      color: var(--text-primary);
    }
  }
  
  :deep(.el-table) {
    --el-table-header-bg-color: transparent;
  }
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .alert-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background: var(--bg-hover);
    }
    
    .alert-icon {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: var(--radius-sm);
      
      &.high {
        background: rgba(248, 81, 73, 0.2);
        color: var(--danger-color);
      }
      
      &.medium {
        background: rgba(210, 153, 34, 0.2);
        color: var(--warning-color);
      }
      
      &.low {
        background: rgba(88, 166, 255, 0.2);
        color: var(--info-color);
      }
    }
    
    .alert-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;
      
      .alert-title {
        font-size: 14px;
        color: var(--text-primary);
      }
      
      .alert-time {
        font-size: 12px;
        color: var(--text-muted);
      }
    }
  }
}
</style>

