<template>
  <div class="training-detail-page">
    <div class="page-header">
      <el-page-header @back="router.back()">
        <template #content>
          <span class="page-title">培训进度详情</span>
        </template>
        <template #extra>
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button type="primary" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
        </template>
      </el-page-header>
    </div>

    <!-- 工人基本信息 -->
    <el-card v-loading="loading">
      <template #header>
        <span>工人信息</span>
      </template>
      
      <el-descriptions :column="3" border>
        <el-descriptions-item label="姓名">{{ workerInfo.name }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ workerInfo.phone }}</el-descriptions-item>
        <el-descriptions-item label="身份证号">{{ workerInfo.id_no }}</el-descriptions-item>
        <el-descriptions-item label="施工单位">{{ workerInfo.contractor_name }}</el-descriptions-item>
        <el-descriptions-item label="工种">{{ workerInfo.job_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="workerInfo.status === 'ACTIVE' ? 'success' : 'info'" size="small">
            {{ workerInfo.status === 'ACTIVE' ? '在职' : '离职' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 培训统计 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ trainingStats.total_sessions }}</div>
            <div class="stat-label">总培训次数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value success">{{ trainingStats.completed_sessions }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ trainingStats.total_duration }}</div>
            <div class="stat-label">累计时长(分钟)</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value warning">{{ trainingStats.suspicious_count }}</div>
            <div class="stat-label">可疑事件</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 培训记录 -->
    <el-card>
      <template #header>
        <span>培训记录</span>
      </template>
      
      <el-table :data="trainingList" stripe>
        <el-table-column prop="video_title" label="视频标题" min-width="200" />
        
        <el-table-column prop="started_at" label="开始时间" width="180" />
        
        <el-table-column prop="ended_at" label="结束时间" width="180">
          <template #default="{ row }">
            {{ row.ended_at || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column label="学习时长" width="120">
          <template #default="{ row }">
            {{ row.duration_minutes }} 分钟
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="completion_rate" label="完成度" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.completion_rate"
              :status="row.completion_rate === 100 ? 'success' : ''"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleViewDetail(row)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 可疑事件 -->
    <el-card v-if="suspiciousEvents.length > 0">
      <template #header>
        <span>可疑事件记录</span>
      </template>
      
      <el-timeline>
        <el-timeline-item
          v-for="event in suspiciousEvents"
          :key="event.id"
          :timestamp="event.created_at"
          placement="top"
          :type="event.severity === 'HIGH' ? 'danger' : 'warning'"
        >
          <el-card>
            <h4>{{ event.event_type_label }}</h4>
            <p>{{ event.description }}</p>
            <el-tag :type="event.severity === 'HIGH' ? 'danger' : 'warning'" size="small">
              {{ event.severity === 'HIGH' ? '高风险' : '中风险' }}
            </el-tag>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 培训详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="培训详情"
      width="800px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="视频标题">{{ currentSession.video_title }}</el-descriptions-item>
        <el-descriptions-item label="视频时长">{{ currentSession.video_duration }} 秒</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ currentSession.started_at }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ currentSession.ended_at || '进行中' }}</el-descriptions-item>
        <el-descriptions-item label="学习时长">{{ currentSession.duration_minutes }} 分钟</el-descriptions-item>
        <el-descriptions-item label="完成度">{{ currentSession.completion_rate }}%</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentSession.status)" size="small">
            {{ getStatusLabel(currentSession.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="设备信息">{{ currentSession.device_info || '-' }}</el-descriptions-item>
      </el-descriptions>
      
      <div v-if="currentSession.suspicious_events && currentSession.suspicious_events.length > 0" style="margin-top: 20px">
        <h4>可疑事件</h4>
        <el-alert
          v-for="event in currentSession.suspicious_events"
          :key="event.id"
          :title="event.event_type_label"
          :type="event.severity === 'HIGH' ? 'error' : 'warning'"
          :description="event.description"
          style="margin-top: 10px"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'
import request from '@/api/request'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const detailDialogVisible = ref(false)

const workerInfo = reactive({
  name: '',
  phone: '',
  id_no: '',
  contractor_name: '',
  job_type: '',
  status: ''
})

const trainingStats = reactive({
  total_sessions: 0,
  completed_sessions: 0,
  total_duration: 0,
  suspicious_count: 0
})

const trainingList = ref([])
const suspiciousEvents = ref([])
const currentSession = reactive({})

// 获取工人信息
async function fetchWorkerInfo() {
  loading.value = true
  try {
    const response = await request.get(`/admin/workers/${route.params.id}`)
    
    if (response.data?.code === 0) {
      const data = response.data.data
      Object.assign(workerInfo, data)
    }
  } catch (error) {
    console.error('Failed to fetch worker info:', error)
    ElMessage.error('获取工人信息失败')
  } finally {
    loading.value = false
  }
}

// 获取培训统计
async function fetchTrainingStats() {
  try {
    const response = await request.get(`/admin/workers/${route.params.id}/training-stats`)
    
    if (response.data?.code === 0) {
      Object.assign(trainingStats, response.data.data)
    }
  } catch (error) {
    console.error('Failed to fetch training stats:', error)
  }
}

// 获取培训记录
async function fetchTrainingList() {
  try {
    const response = await request.get(`/admin/workers/${route.params.id}/training-sessions`)
    
    if (response.data?.code === 0) {
      trainingList.value = response.data.data.items || []
    }
  } catch (error) {
    console.error('Failed to fetch training list:', error)
  }
}

// 获取可疑事件
async function fetchSuspiciousEvents() {
  try {
    const response = await request.get(`/admin/workers/${route.params.id}/suspicious-events`)
    
    if (response.data?.code === 0) {
      suspiciousEvents.value = response.data.data.items || []
    }
  } catch (error) {
    console.error('Failed to fetch suspicious events:', error)
  }
}

// 刷新
function handleRefresh() {
  fetchWorkerInfo()
  fetchTrainingStats()
  fetchTrainingList()
  fetchSuspiciousEvents()
}

// 查看详情
function handleViewDetail(row) {
  Object.assign(currentSession, row)
  detailDialogVisible.value = true
}

// 导出报告
async function handleExport() {
  try {
    const response = await request.get(`/admin/workers/${route.params.id}/training-report`, {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `培训报告_${workerInfo.name}_${new Date().getTime()}.pdf`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Failed to export report:', error)
    ElMessage.error('导出失败')
  }
}

// 获取状态类型
function getStatusType(status) {
  const typeMap = {
    'IN_LEARNING': 'primary',
    'COMPLETED': 'success',
    'PAUSED': 'warning',
    'ABANDONED': 'info'
  }
  return typeMap[status] || ''
}

// 获取状态标签
function getStatusLabel(status) {
  const labelMap = {
    'IN_LEARNING': '学习中',
    'COMPLETED': '已完成',
    'PAUSED': '已暂停',
    'ABANDONED': '已放弃'
  }
  return labelMap[status] || status
}

onMounted(() => {
  handleRefresh()
})
</script>

<style lang="scss" scoped>
.training-detail-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  .page-title {
    font-size: 20px;
    font-weight: 600;
  }
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
    
    &.warning {
      color: #e6a23c;
    }
  }
  
  .stat-label {
    font-size: 14px;
    color: var(--text-secondary);
  }
}
</style>

