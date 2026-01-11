<template>
  <div class="access-grants-page">
    <div class="page-header">
      <h1>门禁授权管理</h1>
      <p>查看和管理所有门禁授权，支持手动重试同步失败的授权</p>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="待同步" value="PENDING_SYNC" />
            <el-option label="已同步" value="SYNCED" />
            <el-option label="同步失败" value="SYNC_FAILED" />
            <el-option label="已撤销" value="REVOKED" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="日期">
          <el-date-picker
            v-model="searchForm.date"
            type="date"
            placeholder="选择日期"
            clearable
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <el-form-item label="工人姓名">
          <el-input
            v-model="searchForm.worker_name"
            placeholder="输入工人姓名"
            clearable
            style="width: 200px"
          />
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
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">总授权数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value success">{{ stats.synced }}</div>
            <div class="stat-label">已同步</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value warning">{{ stats.pending }}</div>
            <div class="stat-label">待同步</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value danger">{{ stats.failed }}</div>
            <div class="stat-label">同步失败</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 授权列表 -->
    <el-card>
      <div class="table-header">
        <span class="table-title">授权列表</span>
        <el-button type="primary" @click="handleBatchRetry" :disabled="selectedGrants.length === 0">
          <el-icon><RefreshRight /></el-icon>
          批量重试
        </el-button>
      </div>
      
      <el-table
        :data="grantsList"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="worker_name" label="工人姓名" width="120" />
        
        <el-table-column prop="area_name" label="授权区域" width="150" />
        
        <el-table-column label="有效期" width="200">
          <template #default="{ row }">
            {{ row.valid_from }} ~ {{ row.valid_to }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="sync_attempt_count" label="重试次数" width="100" align="center" />
        
        <el-table-column prop="last_sync_at" label="最后同步时间" width="180">
          <template #default="{ row }">
            {{ row.last_sync_at || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="sync_error_msg" label="错误信息" min-width="200" show-overflow-tooltip />
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'SYNC_FAILED'"
              type="primary"
              size="small"
              @click="handleRetry(row)"
            >
              重试
            </el-button>
            <el-button
              v-if="row.status === 'SYNCED'"
              type="danger"
              size="small"
              @click="handleRevoke(row)"
            >
              撤销
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSearch"
        @current-change="handleSearch"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, RefreshRight } from '@element-plus/icons-vue'
import request from '@/api/request'

const loading = ref(false)
const grantsList = ref([])
const selectedGrants = ref([])

const searchForm = reactive({
  status: '',
  date: '',
  worker_name: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const stats = reactive({
  total: 0,
  synced: 0,
  pending: 0,
  failed: 0
})

// 获取授权列表
async function fetchGrants() {
  loading.value = true
  try {
    const params = {
      ...searchForm,
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    const response = await request.get('/admin/access-grants', { params })
    
    if (response.data?.code === 0) {
      const data = response.data.data
      grantsList.value = data.items || []
      pagination.total = data.total || 0
      
      // 更新统计
      stats.total = data.total || 0
      stats.synced = data.items?.filter(g => g.status === 'SYNCED').length || 0
      stats.pending = data.items?.filter(g => g.status === 'PENDING_SYNC').length || 0
      stats.failed = data.items?.filter(g => g.status === 'SYNC_FAILED').length || 0
    }
  } catch (error) {
    console.error('Failed to fetch grants:', error)
    // 响应拦截器已处理错误显示，这里只记录日志
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1
  fetchGrants()
}

// 重置
function handleReset() {
  searchForm.status = ''
  searchForm.date = ''
  searchForm.worker_name = ''
  handleSearch()
}

// 选择变更
function handleSelectionChange(selection) {
  selectedGrants.value = selection
}

// 重试单个授权
async function handleRetry(row) {
  try {
    const response = await request.post(`/admin/access-grants/${row.grant_id}/retry`)
    
    if (response.data?.code === 0) {
      ElMessage.success('重试成功')
      fetchGrants()
    }
  } catch (error) {
    console.error('Failed to retry grant:', error)
    ElMessage.error('重试失败')
  }
}

// 批量重试
async function handleBatchRetry() {
  if (selectedGrants.value.length === 0) {
    ElMessage.warning('请选择要重试的授权')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要重试选中的 ${selectedGrants.value.length} 个授权吗？`,
      '批量重试',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const grant_ids = selectedGrants.value.map(g => g.grant_id)
    const response = await request.post('/admin/access-grants/batch-retry', { grant_ids })
    
    if (response.data?.code === 0) {
      ElMessage.success('批量重试成功')
      fetchGrants()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to batch retry:', error)
      ElMessage.error('批量重试失败')
    }
  }
}

// 撤销授权
async function handleRevoke(row) {
  try {
    await ElMessageBox.confirm(
      `确定要撤销 ${row.worker_name} 在 ${row.area_name} 的授权吗？`,
      '撤销授权',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await request.post(`/admin/access-grants/${row.grant_id}/revoke`, {
      reason: '手动撤销'
    })
    
    if (response.data?.code === 0) {
      ElMessage.success('撤销成功')
      fetchGrants()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to revoke grant:', error)
      ElMessage.error('撤销失败')
    }
  }
}

// 获取状态类型
function getStatusType(status) {
  const typeMap = {
    'PENDING_SYNC': 'warning',
    'SYNCED': 'success',
    'SYNC_FAILED': 'danger',
    'REVOKED': 'info'
  }
  return typeMap[status] || ''
}

// 获取状态标签
function getStatusLabel(status) {
  const labelMap = {
    'PENDING_SYNC': '待同步',
    'SYNCED': '已同步',
    'SYNC_FAILED': '同步失败',
    'REVOKED': '已撤销'
  }
  return labelMap[status] || status
}

onMounted(() => {
  fetchGrants()
})
</script>

<style lang="scss" scoped>
.access-grants-page {
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

.filter-card {
  margin-bottom: 0;
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
    
    &.warning {
      color: #e6a23c;
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

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .table-title {
    font-size: 16px;
    font-weight: 500;
    color: var(--text-primary);
  }
}

.el-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>

