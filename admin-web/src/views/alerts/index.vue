<template>
  <div class="alerts-page">
    <div class="page-header">
      <div class="header-left">
        <h1>告警中心</h1>
        <p>系统告警监控和处理</p>
      </div>
      <div class="header-right">
        <el-badge :value="unacknowledgedCount" :hidden="!unacknowledgedCount">
          <el-button type="primary" @click="handleBatchAck" :disabled="!selectedAlerts.length">
            批量确认
          </el-button>
        </el-badge>
      </div>
    </div>
    
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="告警级别">
          <el-select v-model="filters.severity" placeholder="全部" clearable>
            <el-option label="紧急" value="HIGH" />
            <el-option label="警告" value="MEDIUM" />
            <el-option label="提示" value="LOW" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable>
            <el-option label="未确认" value="UNACKNOWLEDGED" />
            <el-option label="已确认" value="ACKNOWLEDGED" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card>
      <el-table 
        :data="tableData" 
        v-loading="loading" 
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="severity" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ getSeverityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column prop="message" label="告警内容" min-width="300" />
        <el-table-column prop="site_name" label="站点" width="120" />
        <el-table-column prop="created_at" label="时间" width="160" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ACKNOWLEDGED' ? 'success' : 'warning'" size="small">
              {{ row.status === 'ACKNOWLEDGED' ? '已确认' : '未确认' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button 
              text 
              type="primary" 
              size="small" 
              @click="handleAck(row)"
              :disabled="row.status === 'ACKNOWLEDGED'"
            >
              确认
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const unacknowledgedCount = ref(5)
const selectedAlerts = ref([])

const filters = reactive({
  severity: '',
  status: ''
})

const tableData = ref([
  { id: '1', severity: 'HIGH', type: 'SYNC_STUCK', message: '5个门禁授权同步卡住超过10分钟', site_name: 'A工地', created_at: '2026-01-09 10:30:00', status: 'UNACKNOWLEDGED' },
  { id: '2', severity: 'MEDIUM', type: 'TRAINING_TIMEOUT', message: '张三培训超时未完成', site_name: 'A工地', created_at: '2026-01-09 09:45:00', status: 'UNACKNOWLEDGED' },
  { id: '3', severity: 'LOW', type: 'ACCESS_MISMATCH', message: '权限对账发现2条不一致', site_name: 'B工地', created_at: '2026-01-09 03:00:00', status: 'ACKNOWLEDGED' }
])

function getSeverityType(severity) {
  const map = { HIGH: 'danger', MEDIUM: 'warning', LOW: 'info' }
  return map[severity] || 'info'
}

function getSeverityLabel(severity) {
  const map = { HIGH: '紧急', MEDIUM: '警告', LOW: '提示' }
  return map[severity] || severity
}

function handleSelectionChange(val) {
  selectedAlerts.value = val
}

function handleSearch() {
  ElMessage.info('搜索功能开发中')
}

function handleAck(row) {
  row.status = 'ACKNOWLEDGED'
  unacknowledgedCount.value--
  ElMessage.success('已确认')
}

function handleBatchAck() {
  selectedAlerts.value.forEach(row => {
    row.status = 'ACKNOWLEDGED'
  })
  unacknowledgedCount.value -= selectedAlerts.value.length
  selectedAlerts.value = []
  ElMessage.success('批量确认成功')
}
</script>

<style lang="scss" scoped>
.alerts-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  
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
  :deep(.el-card__body) {
    padding: 16px 20px;
  }
  
  :deep(.el-form-item) {
    margin-bottom: 0;
  }
}
</style>

