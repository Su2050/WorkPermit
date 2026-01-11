<template>
  <div class="site-detail">
    <div class="page-header">
      <el-page-header @back="router.back()">
        <template #content>
          <div class="header-content">
            <span class="page-title">{{ site?.name || '工地详情' }}</span>
            <el-tag :type="site?.is_active ? 'success' : 'info'" size="large">
              {{ site?.is_active ? '启用' : '禁用' }}
            </el-tag>
          </div>
        </template>
        <template #extra>
          <el-button-group>
            <el-button @click="handleRefresh">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="primary" @click="handleEdit">
              <el-icon><Edit /></el-icon>
              编辑
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
          <el-descriptions-item label="工地名称">
            {{ site?.name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="工地编码">
            {{ site?.code || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="site?.is_active ? 'success' : 'info'" size="small">
              {{ site?.is_active ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="地址" :span="3">
            {{ site?.address || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="3">
            {{ site?.description || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="默认授权开始时间">
            {{ site?.default_access_start_time || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="默认授权结束时间">
            {{ site?.default_access_end_time || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="默认培训截止时间">
            {{ site?.default_training_deadline || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(site?.created_at) || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(site?.updated_at) || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Edit } from '@element-plus/icons-vue'
import { sitesApi } from '@/api/sites'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const site = reactive({
  site_id: '',
  name: '',
  code: '',
  address: '',
  description: '',
  default_access_start_time: '',
  default_access_end_time: '',
  default_training_deadline: '',
  is_active: true,
  created_at: '',
  updated_at: ''
})

// 获取工地详情
async function fetchDetail() {
  const siteId = route.params.id
  if (!siteId) {
    ElMessage.error('工地ID不存在')
    router.back()
    return
  }
  
  loading.value = true
  try {
    const response = await sitesApi.getDetail(siteId)
    if (response.data?.code === 0) {
      Object.assign(site, response.data.data)
    } else {
      ElMessage.error(response.data?.message || '获取工地详情失败')
      router.back()
    }
  } catch (error) {
    console.error('Failed to fetch site detail:', error)
    ElMessage.error('获取工地详情失败')
    router.back()
  } finally {
    loading.value = false
  }
}

// 刷新
function handleRefresh() {
  fetchDetail()
}

// 编辑
function handleEdit() {
  router.push({
    name: 'Sites',
    query: { edit: site.site_id }
  })
}

// 格式化日期时间
function formatDateTime(dateTime) {
  if (!dateTime) return '-'
  try {
    const date = new Date(dateTime)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return dateTime
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style lang="scss" scoped>
.site-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  .header-content {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .page-title {
      font-size: 18px;
      font-weight: 600;
    }
  }
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card {
  :deep(.el-descriptions__label) {
    font-weight: 500;
    width: 140px;
  }
}
</style>

