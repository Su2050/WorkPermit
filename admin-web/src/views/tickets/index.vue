<template>
  <div class="tickets-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>作业票管理</h1>
        <p>管理和查看所有作业票信息</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="router.push('/tickets/create')">
          <el-icon><Plus /></el-icon>
          新建作业票
        </el-button>
      </div>
    </div>
    
    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="关键词">
          <el-input 
            v-model="filters.keyword"
            placeholder="搜索作业票名称"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="施工单位">
          <el-select 
            v-model="filters.contractorId" 
            placeholder="全部"
            clearable
            @change="handleSearch"
          >
            <el-option
              v-for="c in contractorOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select 
            v-model="filters.status" 
            placeholder="全部" 
            clearable
            @change="handleSearch"
          >
            <el-option label="已发布" value="PUBLISHED" />
            <el-option label="进行中" value="IN_PROGRESS" />
            <el-option label="已过期" value="EXPIRED" />
            <el-option label="已关闭" value="CLOSED" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="handleSearch"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 数据表格 -->
    <el-card class="table-card">
      <div class="table-header" v-if="selectedTickets.length > 0">
        <span>已选择 {{ selectedTickets.length }} 项</span>
        <el-button-group>
          <el-button type="primary" @click="handleBatchClose">
            批量关闭
          </el-button>
          <el-button type="danger" @click="handleBatchCancel">
            批量取消
          </el-button>
          <el-button @click="handleBatchExport">
            批量导出
          </el-button>
        </el-button-group>
      </div>
      
      <el-table 
        :data="tableData" 
        v-loading="loading"
        stripe
        @sort-change="handleSortChange"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="作业票名称" min-width="200">
          <template #default="{ row }">
            <el-link 
              type="primary" 
              @click="router.push(`/tickets/${row.ticket_id}`)"
            >
              {{ row.title }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="contractor_name" label="施工单位" width="150" />
        
        <el-table-column label="作业区域" width="150">
          <template #default="{ row }">
            <el-tooltip 
              :content="row.areas?.map(a => a.name).join(', ')" 
              placement="top"
              :disabled="!row.areas?.length"
            >
              <span>{{ row.areas?.length || 0 }} 个区域</span>
            </el-tooltip>
          </template>
        </el-table-column>
        
        <el-table-column label="有效期" width="200">
          <template #default="{ row }">
            {{ row.start_date }} ~ {{ row.end_date }}
          </template>
        </el-table-column>
        
        <el-table-column label="人员/培训" width="120" align="center">
          <template #default="{ row }">
            <div class="worker-stats">
              <span>{{ row.completed_workers || 0 }}/{{ row.total_workers || 0 }}</span>
              <el-progress 
                :percentage="getCompletionRate(row)" 
                :stroke-width="4"
                :show-text="false"
                :color="getProgressColor(getCompletionRate(row))"
              />
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160" sortable="custom" />
        
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button 
              text 
              type="primary" 
              size="small"
              @click="router.push(`/tickets/${row.ticket_id}`)"
            >
              查看
            </el-button>
            <el-button 
              text 
              type="warning" 
              size="small"
              @click="handleEdit(row)"
              :disabled="row.status === 'CLOSED'"
            >
              变更
            </el-button>
            <el-popconfirm
              title="确定关闭此作业票？"
              @confirm="handleClose(row)"
            >
              <template #reference>
                <el-button 
                  text 
                  type="danger" 
                  size="small"
                  :disabled="row.status === 'CLOSED'"
                >
                  关闭
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>
    
    <!-- 变更对话框 -->
    <el-dialog
      v-model="changeDialogVisible"
      title="作业票变更"
      width="600px"
    >
      <el-form 
        ref="changeFormRef"
        :model="changeForm"
        :rules="changeRules"
        label-width="100px"
      >
        <el-alert
          title="变更提示"
          type="warning"
          :closable="false"
          class="mb-4"
        >
          <template #default>
            <ul style="margin: 0; padding-left: 20px;">
              <li>移除视频：禁止（避免"学完又被删"争议）</li>
              <li>移除人员：当天已完成培训者禁止移除</li>
              <li>增加视频：当天已开始学习时禁止</li>
            </ul>
          </template>
        </el-alert>
        
        <el-form-item label="变更类型" prop="changeType">
          <el-radio-group v-model="changeForm.changeType">
            <el-radio label="workers">人员变更</el-radio>
            <el-radio label="areas">区域变更</el-radio>
            <el-radio label="time">时间变更</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 人员变更 -->
        <template v-if="changeForm.changeType === 'workers'">
          <el-form-item label="增加人员">
            <el-select 
              v-model="changeForm.addWorkers" 
              multiple 
              placeholder="选择要添加的人员"
              filterable
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
              v-model="changeForm.removeWorkers" 
              multiple 
              placeholder="选择要移除的人员"
              filterable
            >
              <el-option
                v-for="w in currentTicket?.workers || []"
                :key="w.id"
                :label="w.name"
                :value="w.id"
                :disabled="w.completedToday"
              >
                {{ w.name }}
                <el-tag v-if="w.completedToday" type="success" size="small">
                  今日已完成
                </el-tag>
              </el-option>
            </el-select>
          </el-form-item>
        </template>
        
        <!-- 区域变更 -->
        <template v-if="changeForm.changeType === 'areas'">
          <el-form-item label="增加区域">
            <el-select 
              v-model="changeForm.addAreas" 
              multiple 
              placeholder="选择要添加的区域"
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
              v-model="changeForm.removeAreas" 
              multiple 
              placeholder="选择要移除的区域"
            >
              <el-option
                v-for="a in currentTicket?.areas || []"
                :key="a.id"
                :label="a.name"
                :value="a.id"
                :disabled="a.hasGrantToday"
              >
                {{ a.name }}
                <el-tag v-if="a.hasGrantToday" type="warning" size="small">
                  今日有授权
                </el-tag>
              </el-option>
            </el-select>
          </el-form-item>
        </template>
        
        <!-- 时间变更 -->
        <template v-if="changeForm.changeType === 'time'">
          <el-form-item label="授权开始时间">
            <el-time-picker
              v-model="changeForm.accessStartTime"
              placeholder="选择开始时间"
              format="HH:mm"
              value-format="HH:mm:ss"
            />
          </el-form-item>
          <el-form-item label="授权结束时间">
            <el-time-picker
              v-model="changeForm.accessEndTime"
              placeholder="选择结束时间"
              format="HH:mm"
              value-format="HH:mm:ss"
            />
          </el-form-item>
        </template>
        
        <el-form-item label="变更原因" prop="reason">
          <el-input 
            v-model="changeForm.reason" 
            type="textarea" 
            rows="3"
            placeholder="请填写变更原因"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="changeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitChange" :loading="changing">
          提交变更
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ticketsApi } from '@/api/tickets'
import { contractorsApi } from '@/api/contractors'

const router = useRouter()

// 加载状态
const loading = ref(false)
const changing = ref(false)

// 表格数据
const tableData = ref([])
const selectedTickets = ref([])

// 筛选条件
const filters = reactive({
  keyword: '',
  contractorId: '',
  status: '',
  dateRange: []
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 排序
const sortParams = reactive({
  sortBy: 'created_at',
  sortOrder: 'desc'
})

// 下拉选项
const contractorOptions = ref([])
const workerOptions = ref([])
const areaOptions = ref([])

// 变更对话框
const changeDialogVisible = ref(false)
const changeFormRef = ref()
const currentTicket = ref(null)

const changeForm = reactive({
  changeType: 'workers',
  addWorkers: [],
  removeWorkers: [],
  addAreas: [],
  removeAreas: [],
  accessStartTime: null,
  accessEndTime: null,
  reason: ''
})

const changeRules = {
  reason: [
    { required: true, message: '请填写变更原因', trigger: 'blur' }
  ]
}

// 获取完成率
function getCompletionRate(row) {
  if (!row.total_workers) return 0
  return Math.round((row.completed_workers / row.total_workers) * 100)
}

// 获取进度颜色
function getProgressColor(rate) {
  if (rate >= 80) return '#2ea043'
  if (rate >= 50) return '#d29922'
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

// 搜索
async function handleSearch() {
  loading.value = true
  
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      contractor_id: filters.contractorId || undefined,
      status: filters.status || undefined,
      start_date: filters.dateRange?.[0] || undefined,
      end_date: filters.dateRange?.[1] || undefined,
      sort_by: sortParams.sortBy,
      sort_order: sortParams.sortOrder
    }
    
    const response = await ticketsApi.getList(params)
    
    if (response.data?.code === 0) {
      tableData.value = response.data.data.items || []
      pagination.total = response.data.data.total || 0
    } else {
      // API返回错误
      ElMessage.error(response.data?.message || '获取作业票列表失败')
      tableData.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('Failed to fetch tickets:', error)
    ElMessage.error('网络错误，请稍后重试')
    tableData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 重置筛选
function handleReset() {
  filters.keyword = ''
  filters.contractorId = ''
  filters.status = ''
  filters.dateRange = []
  pagination.page = 1
  handleSearch()
}

// 排序变化
function handleSortChange({ prop, order }) {
  sortParams.sortBy = prop
  sortParams.sortOrder = order === 'ascending' ? 'asc' : 'desc'
  handleSearch()
}

// 编辑/变更
function handleEdit(row) {
  currentTicket.value = row
  changeForm.changeType = 'workers'
  changeForm.addWorkers = []
  changeForm.removeWorkers = []
  changeForm.addAreas = []
  changeForm.removeAreas = []
  changeForm.accessStartTime = null
  changeForm.accessEndTime = null
  changeForm.reason = ''
  changeDialogVisible.value = true
}

// 提交变更
async function handleSubmitChange() {
  if (!changeFormRef.value) return
  
  await changeFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    changing.value = true
    
    try {
      const changes = {
        reason: changeForm.reason
      }
      
      if (changeForm.changeType === 'workers') {
        if (changeForm.addWorkers.length) {
          changes.add_workers = changeForm.addWorkers
        }
        if (changeForm.removeWorkers.length) {
          changes.remove_workers = changeForm.removeWorkers
        }
      } else if (changeForm.changeType === 'areas') {
        if (changeForm.addAreas.length) {
          changes.add_areas = changeForm.addAreas
        }
        if (changeForm.removeAreas.length) {
          changes.remove_areas = changeForm.removeAreas
        }
      } else if (changeForm.changeType === 'time') {
        if (changeForm.accessStartTime) {
          changes.access_start_time = changeForm.accessStartTime
        }
        if (changeForm.accessEndTime) {
          changes.access_end_time = changeForm.accessEndTime
        }
      }
      
      const response = await ticketsApi.applyChanges(currentTicket.value.ticket_id, changes)
      
      if (response.data?.code === 0) {
        ElMessage.success('变更申请已提交')
        changeDialogVisible.value = false
        handleSearch()
      }
    } catch (error) {
      console.error('Failed to apply changes:', error)
      ElMessage.error('变更失败，请重试')
    } finally {
      changing.value = false
    }
  })
}

// 选择变更
function handleSelectionChange(selection) {
  selectedTickets.value = selection
}

// 关闭作业票
async function handleClose(row) {
  try {
    const response = await ticketsApi.close(row.ticket_id, '手动关闭')
    
    if (response.data?.code === 0) {
      ElMessage.success('作业票已关闭')
      handleSearch()
    }
  } catch (error) {
    console.error('Failed to close ticket:', error)
    ElMessage.error('关闭失败，请重试')
  }
}

// 批量关闭
async function handleBatchClose() {
  if (selectedTickets.value.length === 0) {
    ElMessage.warning('请选择要关闭的作业票')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要关闭选中的 ${selectedTickets.value.length} 个作业票吗？`,
      '批量关闭',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const ticket_ids = selectedTickets.value.map(t => t.ticket_id)
    const response = await ticketsApi.batchClose(ticket_ids, '批量关闭')
    
    if (response.data?.code === 0) {
      const data = response.data.data
      ElMessage.success(`批量关闭完成：成功 ${data.success_count} 个，失败 ${data.failed_count} 个`)
      handleSearch()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to batch close:', error)
      ElMessage.error('批量关闭失败')
    }
  }
}

// 批量取消
async function handleBatchCancel() {
  if (selectedTickets.value.length === 0) {
    ElMessage.warning('请选择要取消的作业票')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要取消选中的 ${selectedTickets.value.length} 个作业票吗？`,
      '批量取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const ticket_ids = selectedTickets.value.map(t => t.ticket_id)
    const response = await ticketsApi.batchCancel(ticket_ids, '批量取消')
    
    if (response.data?.code === 0) {
      const data = response.data.data
      ElMessage.success(`批量取消完成：成功 ${data.success_count} 个，失败 ${data.failed_count} 个`)
      handleSearch()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to batch cancel:', error)
      ElMessage.error('批量取消失败')
    }
  }
}

// 批量导出
async function handleBatchExport() {
  if (selectedTickets.value.length === 0) {
    ElMessage.warning('请选择要导出的作业票')
    return
  }
  
  try {
    const ticket_ids = selectedTickets.value.map(t => t.ticket_id).join(',')
    const response = await ticketsApi.export({ ticket_ids })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `作业票列表_${new Date().getTime()}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Failed to export:', error)
    ElMessage.error('导出失败')
  }
}

// 获取施工单位选项
async function fetchContractorOptions() {
  try {
    const response = await contractorsApi.getOptions()
    if (response.data?.code === 0) {
      contractorOptions.value = response.data.data || []
    }
  } catch (error) {
    console.error('Failed to fetch contractor options:', error)
  }
}

onMounted(() => {
  handleSearch()
  fetchContractorOptions()
})
</script>

<style lang="scss" scoped>
.tickets-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  
  .header-left {
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
}

.filter-card {
  :deep(.el-card__body) {
    padding: 16px 20px;
  }
  
  :deep(.el-form-item) {
    margin-bottom: 0;
    margin-right: 16px;
  }
}

.table-card {
  :deep(.el-card__body) {
    padding: 0;
  }
}

.worker-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  
  span {
    font-size: 13px;
    color: var(--text-secondary);
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.mb-4 {
  margin-bottom: 16px;
}
</style>

