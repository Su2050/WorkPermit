<template>
  <div class="access-events-page">
    <div class="page-header">
      <h1>门禁事件记录</h1>
      <p>查看所有进出记录和拒绝原因统计</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">总记录数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value success">{{ stats.pass }}</div>
            <div class="stat-label">通过</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value danger">{{ stats.deny }}</div>
            <div class="stat-label">拒绝</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ stats.passRate }}%</div>
            <div class="stat-label">通过率</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="日期">
          <el-date-picker
            v-model="searchForm.date"
            type="date"
            placeholder="选择日期"
            clearable
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <el-form-item label="结果">
          <el-select v-model="searchForm.result" placeholder="全部结果" clearable style="width: 150px">
            <el-option label="通过" value="PASS" />
            <el-option label="拒绝" value="DENY" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="方向">
          <el-select v-model="searchForm.direction" placeholder="全部方向" clearable style="width: 150px">
            <el-option label="进入" value="IN" />
            <el-option label="离开" value="OUT" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 拒绝原因统计 -->
    <el-card v-if="denyReasons.length > 0">
      <template #header>
        <span>拒绝原因统计</span>
      </template>
      <div ref="chartRef" style="height: 300px;"></div>
    </el-card>

    <!-- 事件列表 -->
    <el-card>
      <template #header>
        <span>事件记录</span>
      </template>
      
      <el-table
        :data="eventsList"
        v-loading="loading"
        stripe
      >
        <el-table-column prop="event_time" label="时间" width="180" />
        
        <el-table-column prop="worker_name" label="工人姓名" width="120">
          <template #default="{ row }">
            {{ row.worker_name || '未知' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="device_id" label="设备ID" width="150" />
        
        <el-table-column prop="direction" label="方向" width="100">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'IN' ? 'success' : 'info'" size="small">
              {{ row.direction === 'IN' ? '进入' : '离开' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="result" label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.result === 'PASS' ? 'success' : 'danger'" size="small">
              {{ row.result === 'PASS' ? '通过' : '拒绝' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="reason_code" label="原因代码" width="120" />
        
        <el-table-column prop="reason_message" label="原因说明" min-width="200" show-overflow-tooltip />
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSearch"
        @current-change="handleSearch"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import request from '@/api/request'

const loading = ref(false)
const eventsList = ref([])
const chartRef = ref()
let chart = null

const searchForm = reactive({
  date: '',
  result: '',
  direction: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const stats = reactive({
  total: 0,
  pass: 0,
  deny: 0,
  passRate: 0
})

const denyReasons = ref([])

// 获取事件列表
async function fetchEvents() {
  loading.value = true
  try {
    const params = {
      date_str: searchForm.date,
      result_filter: searchForm.result,
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    const response = await request.get('/admin/reports/access-events', { params })
    
    if (response.data?.code === 0) {
      const data = response.data.data
      eventsList.value = data.items || []
      pagination.total = data.total || 0
      
      // 更新统计
      updateStats()
    }
  } catch (error) {
    console.error('Failed to fetch events:', error)
    // 响应拦截器已处理错误显示，这里只记录日志
  } finally {
    loading.value = false
  }
}

// 更新统计
function updateStats() {
  stats.total = pagination.total
  stats.pass = eventsList.value.filter(e => e.result === 'PASS').length
  stats.deny = eventsList.value.filter(e => e.result === 'DENY').length
  stats.passRate = stats.total > 0 ? ((stats.pass / stats.total) * 100).toFixed(1) : 0
  
  // 统计拒绝原因
  const reasonMap = {}
  eventsList.value.filter(e => e.result === 'DENY').forEach(e => {
    const reason = e.reason_message || e.reason_code || '未知原因'
    reasonMap[reason] = (reasonMap[reason] || 0) + 1
  })
  
  denyReasons.value = Object.entries(reasonMap)
    .map(([reason, count]) => ({ reason, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
  
  // 更新图表
  nextTick(() => {
    updateChart()
  })
}

// 更新图表
function updateChart() {
  if (!chartRef.value || denyReasons.value.length === 0) return
  
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: denyReasons.value.map(r => r.reason)
    },
    series: [
      {
        name: '拒绝次数',
        type: 'bar',
        data: denyReasons.value.map(r => r.count),
        itemStyle: {
          color: '#f56c6c'
        }
      }
    ]
  }
  
  chart.setOption(option)
}

// 搜索
function handleSearch() {
  pagination.page = 1
  fetchEvents()
}

// 重置
function handleReset() {
  searchForm.date = ''
  searchForm.result = ''
  searchForm.direction = ''
  handleSearch()
}

// 导出
async function handleExport() {
  try {
    const params = {
      start_date: searchForm.date || undefined,
      end_date: searchForm.date || undefined
    }
    
    const response = await request.get('/admin/reports/export/access-events', {
      params,
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `门禁事件记录_${new Date().getTime()}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Failed to export:', error)
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  fetchEvents()
})
</script>

<style lang="scss" scoped>
.access-events-page {
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

.stats-row {
  margin: 0;
}

.stat-item {
  text-align: center;
  
  .stat-value {
    font-size: 32px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
    
    &.success {
      color: #67c23a;
    }
    
    &.danger {
      color: #f56c6c;
    }
  }
  
  .stat-label {
    font-size: 14px;
    color: var(--text-secondary);
  }
}

.filter-card {
  margin-bottom: 0;
}

.el-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>

