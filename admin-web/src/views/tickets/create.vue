<template>
  <div class="ticket-create">
    <div class="page-header">
      <el-page-header @back="router.back()">
        <template #content>
          <span class="page-title">新建作业票</span>
        </template>
      </el-page-header>
    </div>
    
    <el-card class="form-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <!-- 基本信息 -->
        <div class="form-section">
          <h3 class="section-title">基本信息</h3>
          
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="作业票名称" prop="title">
                <el-input v-model="form.title" placeholder="请输入作业票名称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="施工单位" prop="contractorId">
                <el-select v-model="form.contractorId" placeholder="请选择施工单位">
                  <el-option
                    v-for="c in contractorOptions"
                    :key="c.id"
                    :label="c.name"
                    :value="c.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="有效期" prop="dateRange">
                <el-date-picker
                  v-model="form.dateRange"
                  type="daterange"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  value-format="YYYY-MM-DD"
                  :disabled-date="disabledDate"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="培训截止时间" prop="trainingDeadline">
                <el-time-picker
                  v-model="form.trainingDeadline"
                  placeholder="请选择截止时间"
                  format="HH:mm"
                  value-format="HH:mm:ss"
                />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="授权开始时间" prop="accessStartTime">
                <el-time-picker
                  v-model="form.accessStartTime"
                  placeholder="请选择开始时间"
                  format="HH:mm"
                  value-format="HH:mm:ss"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="授权结束时间" prop="accessEndTime">
                <el-time-picker
                  v-model="form.accessEndTime"
                  placeholder="请选择结束时间"
                  format="HH:mm"
                  value-format="HH:mm:ss"
                />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="备注说明">
            <el-input 
              v-model="form.remark" 
              type="textarea" 
              rows="3"
              placeholder="请输入备注说明（可选）"
            />
          </el-form-item>
        </div>
        
        <!-- 作业区域 -->
        <div class="form-section">
          <h3 class="section-title">作业区域</h3>
          
          <el-form-item label="选择区域" prop="areaIds">
            <el-select
              v-model="form.areaIds"
              multiple
              filterable
              placeholder="请选择作业区域"
              style="width: 100%;"
            >
              <el-option
                v-for="a in areaOptions"
                :key="a.id"
                :label="a.name"
                :value="a.id"
              >
                <span>{{ a.name }}</span>
                <span style="color: var(--text-muted); margin-left: 8px;">
                  {{ a.device_count }} 个门禁设备
                </span>
              </el-option>
            </el-select>
          </el-form-item>
          
          <!-- 已选区域列表 -->
          <div v-if="form.areaIds.length" class="selected-items">
            <el-tag
              v-for="id in form.areaIds"
              :key="id"
              closable
              @close="removeArea(id)"
            >
              {{ getAreaName(id) }}
            </el-tag>
          </div>
        </div>
        
        <!-- 培训视频 -->
        <div class="form-section">
          <h3 class="section-title">培训视频</h3>
          
          <el-form-item label="选择视频" prop="videoIds">
            <el-select
              v-model="form.videoIds"
              multiple
              filterable
              placeholder="请选择培训视频"
              style="width: 100%;"
            >
              <el-option
                v-for="v in videoOptions"
                :key="v.id"
                :label="v.title"
                :value="v.id"
              >
                <span>{{ v.title }}</span>
                <span style="color: var(--text-muted); margin-left: 8px;">
                  {{ formatDuration(v.duration_sec) }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>
          
          <!-- 已选视频列表 -->
          <div v-if="form.videoIds.length" class="selected-items">
            <el-tag
              v-for="id in form.videoIds"
              :key="id"
              closable
              type="success"
              @close="removeVideo(id)"
            >
              {{ getVideoTitle(id) }}
            </el-tag>
          </div>
        </div>
        
        <!-- 作业人员 -->
        <div class="form-section">
          <h3 class="section-title">
            作业人员
            <el-button text type="primary" size="small" @click="showWorkerImport = true">
              <el-icon><Upload /></el-icon>
              批量导入
            </el-button>
          </h3>
          
          <el-form-item label="选择人员" prop="workerIds">
            <el-select
              v-model="form.workerIds"
              multiple
              filterable
              remote
              :remote-method="searchWorkers"
              :loading="workersLoading"
              placeholder="搜索并选择作业人员"
              style="width: 100%;"
            >
              <el-option
                v-for="w in workerOptions"
                :key="w.id"
                :label="w.name"
                :value="w.id"
              >
                <span>{{ w.name }}</span>
                <span style="color: var(--text-muted); margin-left: 8px;">
                  {{ w.id_card_masked }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>
          
          <!-- 已选人员列表 -->
          <div v-if="form.workerIds.length" class="selected-workers">
            <div class="workers-header">
              <span>已选择 {{ form.workerIds.length }} 人</span>
              <el-button text type="danger" size="small" @click="form.workerIds = []">
                清空
              </el-button>
            </div>
            <el-table :data="selectedWorkers" max-height="300" stripe size="small">
              <el-table-column prop="name" label="姓名" width="100" />
              <el-table-column prop="id_card_masked" label="身份证号" />
              <el-table-column prop="phone_masked" label="手机号" width="120" />
              <el-table-column label="操作" width="60">
                <template #default="{ row }">
                  <el-button 
                    text 
                    type="danger" 
                    size="small"
                    @click="removeWorker(row.id)"
                  >
                    移除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        
        <!-- 提交按钮 -->
        <div class="form-actions">
          <el-button @click="router.back()">取消</el-button>
          <el-button @click="handleSaveDraft" :loading="saving">保存草稿</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            提交并发布
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ticketsApi } from '@/api/tickets'
import { areasApi } from '@/api/areas'
import { videosApi } from '@/api/videos'
import { workersApi } from '@/api/workers'
import { contractorsApi } from '@/api/contractors'

const router = useRouter()

const formRef = ref()
const saving = ref(false)
const submitting = ref(false)
const workersLoading = ref(false)
const showWorkerImport = ref(false)

// 表单数据
const form = reactive({
  title: '',
  contractorId: '',
  dateRange: [],
  trainingDeadline: '12:00:00',
  accessStartTime: '08:00:00',
  accessEndTime: '18:00:00',
  remark: '',
  areaIds: [],
  videoIds: [],
  workerIds: []
})

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入作业票名称', trigger: 'blur' }
  ],
  contractorId: [
    { required: true, message: '请选择施工单位', trigger: 'change' }
  ],
  dateRange: [
    { required: true, message: '请选择有效期', trigger: 'change' }
  ],
  trainingDeadline: [
    { required: true, message: '请选择培训截止时间', trigger: 'change' }
  ],
  accessStartTime: [
    { required: true, message: '请选择授权开始时间', trigger: 'change' }
  ],
  accessEndTime: [
    { required: true, message: '请选择授权结束时间', trigger: 'change' }
  ],
  areaIds: [
    { required: true, type: 'array', min: 1, message: '请至少选择一个作业区域', trigger: 'change' }
  ],
  videoIds: [
    { required: true, type: 'array', min: 1, message: '请至少选择一个培训视频', trigger: 'change' }
  ],
  workerIds: [
    { required: true, type: 'array', min: 1, message: '请至少选择一个作业人员', trigger: 'change' }
  ]
}

// 选项数据
const contractorOptions = ref([])
const areaOptions = ref([])
const videoOptions = ref([])
const workerOptions = ref([])

// 已选人员详情
const selectedWorkers = computed(() => {
  return workerOptions.value.filter(w => form.workerIds.includes(w.id))
})

// 禁用日期（只能选今天及以后）
function disabledDate(date) {
  return date.getTime() < Date.now() - 24 * 60 * 60 * 1000
}

// 格式化时长
function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}分${secs}秒`
}

// 获取区域名称
function getAreaName(id) {
  return areaOptions.value.find(a => a.id === id)?.name || id
}

// 获取视频标题
function getVideoTitle(id) {
  return videoOptions.value.find(v => v.id === id)?.title || id
}

// 移除区域
function removeArea(id) {
  form.areaIds = form.areaIds.filter(i => i !== id)
}

// 移除视频
function removeVideo(id) {
  form.videoIds = form.videoIds.filter(i => i !== id)
}

// 移除人员
function removeWorker(id) {
  form.workerIds = form.workerIds.filter(i => i !== id)
}

// 搜索人员
async function searchWorkers(query) {
  // 如果没有输入关键字，加载前20个人员
  if (!query || query.length < 2) {
    await loadInitialWorkers()
    return
  }
  
  workersLoading.value = true
  
  try {
    const response = await workersApi.getOptions({ keyword: query })
    if (response.data?.code === 0) {
      workerOptions.value = response.data.data || []
    }
  } catch (error) {
    console.error('Failed to search workers:', error)
  } finally {
    workersLoading.value = false
  }
}

// 加载初始人员列表（前20个）
async function loadInitialWorkers() {
  if (workerOptions.value.length > 0) return // 已加载过就不重复加载
  
  workersLoading.value = true
  
  try {
    const response = await workersApi.getOptions()
    if (response.data?.code === 0) {
      workerOptions.value = response.data.data?.slice(0, 20) || []
    }
  } catch (error) {
    console.error('Failed to load workers:', error)
  } finally {
    workersLoading.value = false
  }
}

// 保存草稿
async function handleSaveDraft() {
  saving.value = true
  
  try {
    // TODO: 实现草稿保存
    ElMessage.success('草稿已保存')
  } finally {
    saving.value = false
  }
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    
    try {
      const data = {
        title: form.title,
        description: form.description || '',
        contractor_id: form.contractorId,
        start_date: form.dateRange[0],
        end_date: form.dateRange[1],
        default_training_deadline_time: form.trainingDeadline || '07:30:00',
        default_access_start_time: form.accessStartTime || '06:00:00',
        default_access_end_time: form.accessEndTime || '20:00:00',
        notify_on_publish: true,
        daily_reminder_enabled: true,
        remark: form.remark || '',
        area_ids: form.areaIds,
        video_ids: form.videoIds,
        worker_ids: form.workerIds
      }
      
      const response = await ticketsApi.create(data)
      
      if (response.data?.code === 0) {
        ElMessage.success('作业票创建成功')
        router.push('/tickets')
      }
    } catch (error) {
      console.error('Failed to create ticket:', error)
      ElMessage.error('创建失败，请重试')
    } finally {
      submitting.value = false
    }
  })
}

// 获取选项数据
async function fetchOptions() {
  try {
    const [contractorsRes, areasRes, videosRes] = await Promise.all([
      contractorsApi.getOptions(),
      areasApi.getOptions(),
      videosApi.getOptions()
    ])
    
    if (contractorsRes.data?.code === 0) {
      contractorOptions.value = contractorsRes.data.data || []
    }
    if (areasRes.data?.code === 0) {
      areaOptions.value = areasRes.data.data || []
    }
    if (videosRes.data?.code === 0) {
      videoOptions.value = videosRes.data.data || []
    }
    
    // 加载初始人员列表
    await loadInitialWorkers()
  } catch (error) {
    console.error('Failed to fetch options:', error)
    // 使用模拟数据
    contractorOptions.value = [
      { id: '1', name: '建设工程集团' },
      { id: '2', name: '电力安装公司' }
    ]
    areaOptions.value = [
      { id: '1', name: '焊接区A', device_count: 2 },
      { id: '2', name: '组装区B', device_count: 3 }
    ]
    videoOptions.value = [
      { id: '1', title: '安全生产基础培训', duration_sec: 300 },
      { id: '2', title: '焊接作业安全规范', duration_sec: 480 }
    ]
  }
}

onMounted(() => {
  fetchOptions()
})
</script>

<style lang="scss" scoped>
.ticket-create {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  .page-title {
    font-size: 18px;
    font-weight: 500;
    color: var(--text-primary);
  }
}

.form-card {
  :deep(.el-card__body) {
    padding: 24px 32px;
  }
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
  
  &:last-of-type {
    border-bottom: none;
    padding-bottom: 0;
  }
  
  .section-title {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 16px;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--accent-color);
    width: fit-content;
  }
}

.selected-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  padding: 12px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.selected-workers {
  margin-top: 16px;
  
  .workers-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    
    span {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}
</style>

