<template>
  <div class="ticket-detail">
    <div class="page-header">
      <el-page-header @back="router.back()">
        <template #content>
          <div class="header-content">
            <span class="page-title">{{ ticket?.title || '作业票详情' }}</span>
            <el-tag :type="getStatusType(ticket?.status)" size="large">
              {{ getStatusLabel(ticket?.status) }}
            </el-tag>
          </div>
        </template>
        <template #extra>
          <el-button-group>
            <el-button @click="handleRefresh">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button 
              v-if="ticket?.status === 'DRAFT'" 
              type="success" 
              @click="handlePublish"
            >
              <el-icon><Promotion /></el-icon>
              发布
            </el-button>
            <el-button 
              v-if="ticket?.status !== 'CLOSED' && ticket?.status !== 'CANCELLED'" 
              type="primary" 
              @click="handleEdit"
            >
              <el-icon><Edit /></el-icon>
              变更
            </el-button>
            <el-button 
              v-if="ticket?.status !== 'CLOSED' && ticket?.status !== 'CANCELLED'" 
              type="danger" 
              @click="handleCancel"
            >
              <el-icon><Close /></el-icon>
              取消
            </el-button>
          </el-button-group>
        </template>
      </el-page-header>
    </div>
    
    <div class="detail-content" v-loading="loading">
      <!-- 基本信息 -->
      <el-card class="info-card">
        <template #header>
          <span>基本信息</span>
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="作业票编号">
            {{ ticket?.ticket_no || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="施工单位">
            {{ ticket?.contractor_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建人">
            {{ ticket?.created_by_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="有效期">
            {{ ticket?.start_date }} ~ {{ ticket?.end_date }}
          </el-descriptions-item>
          <el-descriptions-item label="培训截止时间">
            {{ ticket?.default_training_deadline_time || ticket?.training_deadline_time || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="授权时段">
            {{ (ticket?.default_access_start_time || ticket?.access_start_time || '-') }} - {{ (ticket?.default_access_end_time || ticket?.access_end_time || '-') }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ ticket?.created_at || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">
            {{ ticket?.remark || '无' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
      
      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-icon blue">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ totalWorkers }}</span>
            <span class="stat-label">总人数</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon green">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ ticket?.completed_workers || 0 }}</span>
            <span class="stat-label">已完成培训</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon orange">
            <el-icon><Key /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ ticket?.authorized_workers || 0 }}</span>
            <span class="stat-label">已授权</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon purple">
            <el-icon><Location /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ ticket?.areas?.length || 0 }}</span>
            <span class="stat-label">作业区域</span>
          </div>
        </div>
      </div>
      
      <!-- 每日票据 -->
      <el-card class="daily-card">
        <template #header>
          <div class="card-header">
            <div class="daily-header-left">
              <span class="daily-title">每日票据</span>
              <el-tag v-if="!dailyTicket" type="info" size="small">暂无数据</el-tag>
            </div>
            <el-date-picker
              v-model="selectedDate"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
              :disabled-date="date => date < new Date(ticket?.start_date) || date > new Date(ticket?.end_date)"
              @change="handleDateChange"
            />
          </div>
        </template>

        <!-- 无数据时默认折叠；有数据时自动展开 -->
        <div class="daily-collapse-bar" v-if="!dailyTicket">
          <el-button text type="primary" @click="dailyExpanded = !dailyExpanded">
            {{ dailyExpanded ? '收起' : '展开' }}
          </el-button>
        </div>

        <el-collapse-transition>
          <div v-show="dailyExpanded">
            <div v-if="dailyTicket" class="daily-content">
              <div class="daily-header">
                <div class="daily-status">
                  <el-tag :type="getDailyStatusType(dailyTicket.status)" size="large">
                    {{ getDailyStatusLabel(dailyTicket.status) }}
                  </el-tag>
                  <span class="daily-date">{{ dailyTicket.date }}</span>
                </div>
                <div class="daily-progress">
                  <span>培训完成率</span>
                  <el-progress 
                    :percentage="dailyTicket.completion_rate || 0" 
                    :stroke-width="8"
                    :color="getProgressColor(dailyTicket.completion_rate)"
                  />
                </div>
              </div>
              
              <!-- 人员列表 -->
              <el-table :data="dailyWorkers" stripe max-height="400">
                <el-table-column prop="name" label="姓名" width="100" />
                <el-table-column prop="phone_masked" label="手机号" width="130" />
                <el-table-column label="培训状态" width="120">
                  <template #default="{ row }">
                    <el-tag :type="getTrainingStatusType(row.training_status)" size="small">
                      {{ getTrainingStatusLabel(row.training_status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="学习进度" width="180">
                  <template #default="{ row }">
                    <div class="progress-cell">
                      <span>{{ row.completed_videos }}/{{ row.total_videos }} 视频</span>
                      <el-progress 
                        :percentage="row.total_videos ? (row.completed_videos / row.total_videos * 100) : 0" 
                        :stroke-width="4"
                        :show-text="false"
                      />
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="门禁授权" width="100">
                  <template #default="{ row }">
                    <el-icon v-if="row.authorized" :size="20" color="#2ea043">
                      <CircleCheckFilled />
                    </el-icon>
                    <el-icon v-else :size="20" color="#6e7681">
                      <CircleClose />
                    </el-icon>
                  </template>
                </el-table-column>
                <el-table-column label="异常事件" width="100">
                  <template #default="{ row }">
                    <el-badge 
                      :value="row.suspicious_events" 
                      :hidden="!row.suspicious_events"
                      type="danger"
                    >
                      <span>{{ row.suspicious_events || 0 }}</span>
                    </el-badge>
                  </template>
                </el-table-column>
                <el-table-column prop="last_activity" label="最近活动" width="160" />
              </el-table>
            </div>
            
            <el-empty v-else description="暂无数据" />
          </div>
        </el-collapse-transition>
      </el-card>
      
      <!-- 作业区域 & 培训视频 -->
      <div class="detail-row">
        <el-card>
          <template #header>
            <span>作业人员</span>
          </template>
          <el-table
            :data="ticket?.workers || []"
            stripe
            size="small"
            max-height="260"
          >
            <el-table-column prop="name" label="姓名" width="120" />
            <el-table-column label="手机号" width="140">
              <template #default="{ row }">
                {{ maskPhone(row.phone) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'ACTIVE' ? 'success' : 'info'" size="small">
                  {{ row.status === 'ACTIVE' ? '在票' : '已移除' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!(ticket?.workers && ticket.workers.length)" description="暂无人员" />
        </el-card>

        <el-card>
          <template #header>
            <span>作业区域</span>
          </template>
          <div class="tag-list">
            <el-tag 
              v-for="area in ticket?.areas" 
              :key="area.area_id || area.id"
              type="info"
              size="large"
            >
              <el-icon><Location /></el-icon>
              {{ area.name }}
            </el-tag>
          </div>
        </el-card>
        
        <el-card>
          <template #header>
            <span>培训视频</span>
          </template>
          <div class="video-list">
            <div 
              v-for="video in ticket?.videos" 
              :key="video.video_id || video.id"
              class="video-item"
            >
              <el-icon :size="20"><VideoCamera /></el-icon>
              <span class="video-title">{{ video.title }}</span>
              <span class="video-duration">{{ formatDuration(video.duration_sec) }}</span>
            </div>
          </div>
        </el-card>
      </div>
      
      <!-- 变更历史 -->
      <el-card class="history-card">
        <template #header>
          <span>变更历史</span>
        </template>
        <el-timeline>
          <el-timeline-item
            v-for="log in changeHistory"
            :key="log.id"
            :timestamp="log.created_at"
            placement="top"
            :type="log.type === 'CREATE' ? 'primary' : 'warning'"
          >
            <div class="timeline-content">
              <div class="timeline-header">
                <span class="action-type">{{ getActionLabel(log.type) }}</span>
                <span class="operator">{{ log.operator_name }}</span>
              </div>
              <div class="timeline-detail">{{ log.description }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-if="!changeHistory.length" description="暂无变更记录" />
      </el-card>
    </div>
    
    <!-- 变更对话框 -->
    <el-dialog
      v-model="changeDialogVisible"
      title="变更作业票"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form :model="changeForm" label-width="120px">
        <el-form-item label="变更原因" required>
          <el-input
            v-model="changeForm.reason"
            type="textarea"
            rows="3"
            placeholder="请填写变更原因"
          />
        </el-form-item>
        
        <el-divider>人员变更</el-divider>
        
        <el-form-item label="增加人员">
          <el-select
            v-model="changeForm.add_workers"
            multiple
            filterable
            placeholder="选择要增加的人员"
            style="width: 100%"
          >
            <el-option
              v-for="w in workerOptions"
              :key="w.id"
              :label="w.name"
              :value="w.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="移除人员">
          <el-select
            v-model="changeForm.remove_workers"
            multiple
            filterable
            placeholder="选择要移除的人员"
            style="width: 100%"
          >
            <el-option
              v-for="w in ticket?.workers || []"
              :key="w.worker_id"
              :label="w.name"
              :value="w.worker_id"
            />
          </el-select>
        </el-form-item>
        
        <el-divider>区域变更</el-divider>
        
        <el-form-item label="增加区域">
          <el-select
            v-model="changeForm.add_areas"
            multiple
            filterable
            placeholder="选择要增加的区域"
            style="width: 100%"
          >
            <el-option
              v-for="a in areaOptions"
              :key="a.id"
              :label="a.name"
              :value="a.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="移除区域">
          <el-select
            v-model="changeForm.remove_areas"
            multiple
            filterable
            placeholder="选择要移除的区域"
            style="width: 100%"
          >
            <el-option
              v-for="a in ticket?.areas || []"
              :key="a.area_id"
              :label="a.name"
              :value="a.area_id"
            />
          </el-select>
        </el-form-item>
        
        <el-divider>视频变更</el-divider>
        
        <el-form-item label="增加视频">
          <el-select
            v-model="changeForm.add_videos"
            multiple
            filterable
            placeholder="选择要增加的视频"
            style="width: 100%"
          >
            <el-option
              v-for="v in videoOptions"
              :key="v.id"
              :label="v.title"
              :value="v.id"
            />
          </el-select>
        </el-form-item>
        
        <el-divider>时间变更</el-divider>
        
        <el-form-item label="授权开始时间">
          <el-time-picker
            v-model="changeForm.access_start_time"
            placeholder="选择开始时间"
            format="HH:mm"
            value-format="HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="授权结束时间">
          <el-time-picker
            v-model="changeForm.access_end_time"
            placeholder="选择结束时间"
            format="HH:mm"
            value-format="HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="培训截止时间">
          <el-time-picker
            v-model="changeForm.training_deadline_time"
            placeholder="选择截止时间"
            format="HH:mm"
            value-format="HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input
            v-model="changeForm.remark"
            type="textarea"
            rows="2"
            placeholder="可选"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="changeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitChange">确认变更</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ticketsApi } from '@/api/tickets'
import { areasApi } from '@/api/areas'
import { videosApi } from '@/api/videos'
import { workersApi } from '@/api/workers'
import { auditApi } from '@/api/audit'
import dayjs from 'dayjs'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const ticket = ref(null)
const dailyTicket = ref(null)
const dailyWorkers = ref([])
const changeHistory = ref([])
const selectedDate = ref(dayjs().format('YYYY-MM-DD'))
// 无数据时默认折叠；当拉到有数据时自动展开
const dailyExpanded = ref(false)

// 统计：后端详情接口返回的是 workers 数组（不一定有 total_workers 字段）
const totalWorkers = computed(() => {
  const workers = ticket.value?.workers || []
  // 只统计 ACTIVE，避免历史移除的人也算进去
  return workers.filter(w => (w?.status || 'ACTIVE') === 'ACTIVE').length
})

// 变更对话框
const changeDialogVisible = ref(false)
const changeForm = ref({
  reason: '',
  add_workers: [],
  remove_workers: [],
  add_areas: [],
  remove_areas: [],
  add_videos: [],
  access_start_time: '',
  access_end_time: '',
  training_deadline_time: '',
  remark: ''
})

// 选项数据
const workerOptions = ref([])
const areaOptions = ref([])
const videoOptions = ref([])

// 状态相关函数
function getStatusType(status) {
  const map = {
    'PUBLISHED': 'info',
    'IN_PROGRESS': 'primary',
    'EXPIRED': 'warning',
    'CLOSED': 'info'
  }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = {
    'PUBLISHED': '已发布',
    'IN_PROGRESS': '进行中',
    'EXPIRED': '已过期',
    'CLOSED': '已关闭'
  }
  return map[status] || status
}

function getDailyStatusType(status) {
  const map = {
    'PUBLISHED': 'info',
    'IN_PROGRESS': 'primary',
    'EXPIRED': 'warning'
  }
  return map[status] || 'info'
}

function getDailyStatusLabel(status) {
  const map = {
    'PUBLISHED': '未开始',
    'IN_PROGRESS': '进行中',
    'EXPIRED': '已结束'
  }
  return map[status] || status
}

function getTrainingStatusType(status) {
  const map = {
    'NOT_STARTED': 'info',
    'IN_LEARNING': 'warning',
    'COMPLETED': 'success',
    'FAILED': 'danger'
  }
  return map[status] || 'info'
}

function getTrainingStatusLabel(status) {
  const map = {
    'NOT_STARTED': '未开始',
    'IN_LEARNING': '学习中',
    'COMPLETED': '已完成',
    'FAILED': '失败'
  }
  return map[status] || status
}

function getProgressColor(rate) {
  if (rate >= 80) return '#2ea043'
  if (rate >= 50) return '#d29922'
  return '#f85149'
}

function maskPhone(phone) {
  if (!phone) return '-'
  const s = String(phone)
  if (s.length < 7) return s
  return s.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

function getActionLabel(type) {
  const map = {
    'CREATE': '创建',
    'CHANGE': '变更',
    'CLOSE': '关闭'
  }
  return map[type] || type
}

function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}分${secs}秒`
}

// 获取作业票详情
async function fetchTicketDetail() {
  loading.value = true
  
  try {
    const response = await ticketsApi.getDetail(route.params.id)
    
    if (response.data?.code === 0) {
      ticket.value = response.data.data
      // 确保workers和areas数组存在
      if (!ticket.value.workers) ticket.value.workers = []
      if (!ticket.value.areas) ticket.value.areas = []
      if (!ticket.value.videos) ticket.value.videos = []
    }
  } catch (error) {
    console.error('Failed to fetch ticket:', error)
    // 模拟数据
    ticket.value = {
      ticket_id: route.params.id,
      ticket_no: 'WP-2026-0001',
      title: 'A区焊接作业许可',
      contractor_name: '建设工程集团',
      status: 'IN_PROGRESS',
      start_date: '2026-01-09',
      end_date: '2026-01-15',
      training_deadline_time: '12:00:00',
      access_start_time: '08:00:00',
      access_end_time: '18:00:00',
      remark: '特殊作业，注意安全防护',
      total_workers: 20,
      completed_workers: 15,
      authorized_workers: 12,
      areas: [
        { id: '1', name: '焊接区A' },
        { id: '2', name: '组装区B' }
      ],
      videos: [
        { id: '1', title: '安全生产基础培训', duration_sec: 300 },
        { id: '2', title: '焊接作业安全规范', duration_sec: 480 }
      ],
      created_at: '2026-01-08 10:30:00',
      created_by_name: '管理员'
    }
  } finally {
    loading.value = false
  }
}

// 获取每日票据详情
async function fetchDailyTicket() {
  if (!ticket.value) return
  
  try {
    // 先获取该作业票的每日票据列表
    const listRes = await ticketsApi.getDailyTickets(route.params.id, {
      date: selectedDate.value
    })
    
    if (listRes.data?.code === 0 && listRes.data.data?.items?.length > 0) {
      const dailyTicketId = listRes.data.data.items[0].daily_ticket_id
      
      // 获取每日票据详情
      const detailRes = await ticketsApi.getDailyTicketDetail(dailyTicketId)
      
      if (detailRes.data?.code === 0) {
        const data = detailRes.data.data
        dailyTicket.value = {
          date: data.date,
          status: data.status,
          completion_rate: data.completion_rate || 0
        }
        dailyExpanded.value = true
        
        // 格式化工人数据
        dailyWorkers.value = (data.workers || []).map(w => ({
          id: w.worker_id,
          name: w.name,
          phone_masked: w.phone ? w.phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') : '',
          training_status: w.training_status,
          completed_videos: w.completed_video_count,
          total_videos: w.total_video_count,
          authorized: w.authorized,
          suspicious_events: 0, // TODO: 从后端获取
          last_activity: w.last_notify_at ? dayjs(w.last_notify_at).format('HH:mm') : '-'
        }))
      }
    } else {
      // 没有找到该日期的每日票据
      dailyTicket.value = null
      dailyWorkers.value = []
      dailyExpanded.value = false
    }
  } catch (error) {
    console.error('Failed to fetch daily ticket:', error)
    ElMessage.error('获取每日票据失败')
    dailyTicket.value = null
    dailyWorkers.value = []
    dailyExpanded.value = false
  }
}

// 日期变化
function handleDateChange() {
  fetchDailyTicket()
}

// 刷新
function handleRefresh() {
  fetchTicketDetail()
  fetchDailyTicket()
}

// 编辑 - 打开变更对话框
async function handleEdit() {
  if (!ticket.value) return
  
  // 重置表单
  changeForm.value = {
    reason: '',
    add_workers: [],
    remove_workers: [],
    add_areas: [],
    remove_areas: [],
    add_videos: [],
    access_start_time: ticket.value.default_access_start_time || '',
    access_end_time: ticket.value.default_access_end_time || '',
    training_deadline_time: ticket.value.default_training_deadline_time || '',
    remark: ticket.value.remark || ''
  }
  
  // 加载选项数据
  await loadChangeOptions()
  
  changeDialogVisible.value = true
}

// 加载变更选项数据
async function loadChangeOptions() {
  try {
    const [workersRes, areasRes, videosRes] = await Promise.all([
      workersApi.getOptions(),
      areasApi.getOptions(),
      videosApi.getOptions()
    ])
    
    if (workersRes.data?.code === 0) {
      workerOptions.value = workersRes.data.data || []
    }
    if (areasRes.data?.code === 0) {
      areaOptions.value = areasRes.data.data || []
    }
    if (videosRes.data?.code === 0) {
      videoOptions.value = videosRes.data.data || []
    }
  } catch (error) {
    console.error('Failed to load options:', error)
  }
}

// 提交变更
async function handleSubmitChange() {
  if (!changeForm.value.reason) {
    ElMessage.warning('请填写变更原因')
    return
  }
  
  try {
    const data = {
      reason: changeForm.value.reason,
      add_workers: changeForm.value.add_workers,
      remove_workers: changeForm.value.remove_workers,
      add_areas: changeForm.value.add_areas,
      remove_areas: changeForm.value.remove_areas,
      add_videos: changeForm.value.add_videos,
      access_start_time: changeForm.value.access_start_time || null,
      access_end_time: changeForm.value.access_end_time || null,
      training_deadline_time: changeForm.value.training_deadline_time || null,
      remark: changeForm.value.remark || null
    }
    
    // 移除空数组
    if (data.add_workers.length === 0) delete data.add_workers
    if (data.remove_workers.length === 0) delete data.remove_workers
    if (data.add_areas.length === 0) delete data.add_areas
    if (data.remove_areas.length === 0) delete data.remove_areas
    if (data.add_videos.length === 0) delete data.add_videos
    
    const response = await ticketsApi.update(route.params.id, data)
    
    if (response.data?.code === 0) {
      ElMessage.success('变更成功')
      changeDialogVisible.value = false
      // 刷新详情
      await fetchTicketDetail()
    }
    // 注意: 如果 code !== 0，响应拦截器会自动显示错误信息
  } catch (error) {
    console.error('Failed to update ticket:', error)
    // 响应拦截器已处理错误显示，这里只记录日志
  }
}

// 发布作业票
async function handlePublish() {
  if (!ticket.value) return
  
  try {
    await ElMessageBox.confirm(
      '发布后将生成每日票据并发送通知给相关人员，确定要发布吗？',
      '确认发布',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await ticketsApi.publish(route.params.id)
    
    if (response.data?.code === 0) {
      ElMessage.success('发布成功')
      await fetchTicketDetail()
    } else {
      ElMessage.error(response.data?.message || '发布失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to publish ticket:', error)
      ElMessage.error('发布失败，请重试')
    }
  }
}

// 取消作业票
async function handleCancel() {
  if (!ticket.value) return
  
  try {
    const { value: reason } = await ElMessageBox.prompt(
      '请输入取消原因',
      '取消作业票',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputType: 'textarea',
        inputPlaceholder: '请填写取消原因',
        inputValidator: (value) => {
          if (!value || value.trim().length === 0) {
            return '请输入取消原因'
          }
          return true
        }
      }
    )
    
    const response = await ticketsApi.cancel(route.params.id, reason)
    
    if (response.data?.code === 0) {
      ElMessage.success('取消成功')
      await fetchTicketDetail()
    } else {
      ElMessage.error(response.data?.message || '取消失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to cancel ticket:', error)
      ElMessage.error('取消失败，请重试')
    }
  }
}

// 获取变更历史
async function fetchChangeHistory() {
  try {
    const response = await auditApi.getList({
      resource_type: 'WorkTicket',
      resource_id: route.params.id,
      page: 1,
      page_size: 20
    })
    
    if (response.data?.code === 0) {
      const logs = response.data.data.items || []
      changeHistory.value = logs.map(log => ({
        id: log.log_id,
        type: log.action,
        operator_name: log.operator_name || '系统',
        description: getLogDescription(log),
        created_at: log.created_at
      }))
    }
  } catch (error) {
    console.error('Failed to fetch change history:', error)
    // 如果API调用失败，使用空数组
    changeHistory.value = []
  }
}

// 生成日志描述
function getLogDescription(log) {
  const actionMap = {
    'CREATE': '创建',
    'UPDATE': '更新',
    'DELETE': '删除',
    'TICKET_CHANGE': '变更',
    'TICKET_CANCEL': '取消',
    'TICKET_PUBLISH': '发布'
  }
  
  const action = actionMap[log.action] || log.action
  
  if (log.new_value) {
    if (log.new_value.revoked_grants_count) {
      return `${action}，撤销了 ${log.new_value.revoked_grants_count} 个授权`
    }
    if (log.new_value.add_workers) {
      return `${action}，新增 ${log.new_value.add_workers.length} 个人员`
    }
    if (log.new_value.remove_workers) {
      return `${action}，移除 ${log.new_value.remove_workers.length} 个人员`
    }
  }
  
  return action
}

onMounted(() => {
  fetchTicketDetail()
  fetchDailyTicket()
  fetchChangeHistory()
})
</script>

<style lang="scss" scoped>
.ticket-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .page-title {
    font-size: 18px;
    font-weight: 500;
    color: var(--text-primary);
  }
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;

  /* 统一增强本页卡片标题可读性（基本信息/每日票据/作业人员/作业区域/培训视频/变更历史等） */
  :deep(.el-card__header) {
    color: var(--el-text-color-primary) !important;
  }

  :deep(.el-card__header span) {
    color: var(--el-text-color-primary) !important;
    font-weight: 700;
  }
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  
  .stat-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    
    .stat-icon {
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: var(--radius-md);
      color: white;
      
      &.blue { background: linear-gradient(135deg, #1e3a5f, #2d5a8a); }
      &.green { background: linear-gradient(135deg, #2ea043, #46d160); }
      &.orange { background: linear-gradient(135deg, #d29922, #f0b429); }
      &.purple { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }
    }
    
    .stat-info {
      display: flex;
      flex-direction: column;
      
      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--text-primary);
      }
      
      .stat-label {
        font-size: 13px;
        color: var(--text-secondary);
      }
    }
  }
}

.daily-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;

    .daily-header-left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 120px;
    }

    .daily-title {
      font-size: 16px;
      font-weight: 700;
      color: var(--el-text-color-primary);
    }
  }

  .daily-collapse-bar {
    display: flex;
    justify-content: flex-end;
    padding: 4px 0 8px;
  }
  
  .daily-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-color);
    
    .daily-status {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .daily-date {
        color: var(--el-text-color-primary);
        font-weight: 500;
      }
    }
    
    .daily-progress {
      display: flex;
      align-items: center;
      gap: 12px;
      width: 200px;
      
      span {
        white-space: nowrap;
        color: var(--el-text-color-primary);
        font-size: 14px;
        font-weight: 500;
      }
    }
  }
}

.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  
  span {
    font-size: 12px;
    color: var(--text-secondary);
  }
}

.detail-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  
  .el-tag {
    display: flex;
    align-items: center;
    gap: 6px;
  }
}

.video-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .video-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    
    .video-title {
      flex: 1;
      color: var(--text-primary);
    }
    
    .video-duration {
      color: var(--text-muted);
      font-size: 13px;
    }
  }
}

.history-card {
  .timeline-content {
    .timeline-header {
      display: flex;
      gap: 12px;
      margin-bottom: 4px;
      
      .action-type {
        font-weight: 500;
        color: var(--text-primary);
      }
      
      .operator {
        color: var(--text-secondary);
      }
    }
    
    .timeline-detail {
      color: var(--text-secondary);
      font-size: 14px;
    }
  }
}
</style>

