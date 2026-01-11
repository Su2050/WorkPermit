<template>
  <div class="reports-page">
    <div class="page-header">
      <h1>报表中心</h1>
      <p>查看系统运行数据和统计报表</p>
    </div>
    
    <el-tabs v-model="activeTab" class="reports-tabs">
      <el-tab-pane label="培训统计" name="training">
        <el-card>
          <div class="chart-header">
            <span>培训完成率趋势</span>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
            />
          </div>
          <div ref="trainingChartRef" style="height: 400px;"></div>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="门禁同步" name="access">
        <el-card>
          <div class="chart-header">
            <span>门禁同步状态</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="stat-block">
                <span class="stat-value success">{{ syncStats.sync_rate || 0 }}%</span>
                <span class="stat-label">同步成功率</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-block">
                <span class="stat-value">{{ syncStats.total_count || 0 }}</span>
                <span class="stat-label">总同步次数</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-block">
                <span class="stat-value warning">{{ syncStats.failed_count || 0 }}</span>
                <span class="stat-label">失败次数</span>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="对账报告" name="reconciliation">
        <el-card>
          <div class="chart-header">
            <span>每日对账报告</span>
            <el-button type="primary" size="small">导出报告</el-button>
          </div>
          <el-table :data="reconciliationData" stripe>
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column prop="expected" label="期望权限数" width="120" align="center" />
            <el-table-column prop="actual" label="实际权限数" width="120" align="center" />
            <el-table-column prop="mismatch" label="不一致数" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="row.mismatch > 0 ? 'danger' : 'success'" size="small">
                  {{ row.mismatch }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'PASS' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'PASS' ? '通过' : '异常' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { reportsApi } from '@/api/reports'
import dayjs from 'dayjs'

const activeTab = ref('training')
const dateRange = ref([
  dayjs().subtract(7, 'day').format('YYYY-MM-DD'),
  dayjs().format('YYYY-MM-DD')
])
const trainingChartRef = ref()
const loading = ref(false)

const reconciliationData = ref([])
const trainingStats = ref({
  completion_rate: 0,
  avg_duration_minutes: 0
})
const syncStats = ref({
  sync_rate: 0,
  failed_count: 0
})
const trendData = ref([])

// 获取培训统计
async function fetchTrainingStats() {
  loading.value = true
  try {
    const [startDate, endDate] = dateRange.value
    const response = await reportsApi.getTrainingStats({
      start_date: startDate,
      end_date: endDate
    })
    
    if (response.data?.code === 0) {
      trainingStats.value = response.data.data
    }
  } catch (error) {
    console.error('Failed to fetch training stats:', error)
  } finally {
    loading.value = false
  }
}

// 获取门禁同步统计
async function fetchSyncStats() {
  try {
    const [startDate, endDate] = dateRange.value
    const response = await reportsApi.getAccessSyncStats({
      start_date: startDate,
      end_date: endDate
    })
    
    if (response.data?.code === 0) {
      syncStats.value = response.data.data
    }
  } catch (error) {
    console.error('Failed to fetch sync stats:', error)
  }
}

// 获取趋势数据
async function fetchTrend() {
  try {
    const response = await reportsApi.getTrend({
      metric: 'completion_rate',
      days: 7
    })
    
    if (response.data?.code === 0) {
      trendData.value = response.data.data.data || []
      updateChart()
    }
  } catch (error) {
    console.error('Failed to fetch trend:', error)
  }
}

// 更新图表
function updateChart() {
  if (!trainingChartRef.value) return
  
  const chart = echarts.init(trainingChartRef.value)
  const dates = trendData.value.map(d => dayjs(d.date).format('MM/DD'))
  const values = trendData.value.map(d => d.value)
  
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { 
      type: 'category', 
      data: dates 
    },
    yAxis: { 
      type: 'value', 
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [{ 
      name: '完成率', 
      type: 'line', 
      smooth: true, 
      data: values,
      itemStyle: {
        color: '#409EFF'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ]
        }
      }
    }]
  })
}

// 获取对账报告
async function fetchReconciliation() {
  try {
    const response = await reportsApi.getReconciliationReport({
      date: dateRange.value[1]
    })
    
    if (response.data?.code === 0) {
      reconciliationData.value = response.data.data.items || []
    }
  } catch (error) {
    console.error('Failed to fetch reconciliation:', error)
  }
}

// 日期范围变化时重新加载数据
watch(dateRange, () => {
  if (activeTab.value === 'training') {
    fetchTrainingStats()
    fetchTrend()
  } else if (activeTab.value === 'access') {
    fetchSyncStats()
  } else if (activeTab.value === 'reconciliation') {
    fetchReconciliation()
  }
})

// Tab切换时加载对应数据
watch(activeTab, (newTab) => {
  if (newTab === 'training') {
    fetchTrainingStats()
    fetchTrend()
  } else if (newTab === 'access') {
    fetchSyncStats()
  } else if (newTab === 'reconciliation') {
    fetchReconciliation()
  }
})

onMounted(() => {
  fetchTrainingStats()
  fetchTrend()
  fetchSyncStats()
  fetchReconciliation()
})
</script>

<style lang="scss" scoped>
.reports-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  h1 {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 4px;
  }
  
  p {
    font-size: 14px;
    color: var(--text-secondary);
  }
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  span {
    font-size: 16px;
    font-weight: 500;
    color: var(--text-primary);
  }
}

.stat-block {
  text-align: center;
  padding: 24px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  
  .stat-value {
    display: block;
    font-size: 32px;
    font-weight: 600;
    color: var(--text-primary);
    
    &.success { color: var(--success-color); }
    &.warning { color: var(--warning-color); }
  }
  
  .stat-label {
    display: block;
    margin-top: 8px;
    color: var(--text-secondary);
  }
}
</style>

