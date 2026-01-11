<template>
  <div class="videos-page">
    <div class="page-header">
      <div class="header-left">
        <h1>培训视频管理</h1>
        <p>管理安全培训视频资源</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleUpload">
          <el-icon><Upload /></el-icon>
          上传视频
        </el-button>
      </div>
    </div>
    
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column label="视频" min-width="300">
          <template #default="{ row }">
            <div class="video-cell">
              <div class="video-thumb">
                <el-icon :size="24"><VideoCamera /></el-icon>
              </div>
              <div class="video-info">
                <span class="video-title">{{ row.title }}</span>
                <span class="video-desc">{{ row.description }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration_sec) }}
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="handlePreview(row)">预览</el-button>
            <el-button text type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除此视频？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button text type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </el-card>
    
    <!-- 新增/编辑视频对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑视频' : '新增视频'"
      width="600px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="视频标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入视频标题" />
        </el-form-item>
        <el-form-item label="视频URL" prop="file_url" v-if="!isEdit">
          <el-input v-model="form.file_url" placeholder="请输入视频文件URL" />
        </el-form-item>
        <el-form-item label="缩略图URL">
          <el-input v-model="form.thumbnail_url" placeholder="请输入缩略图URL（可选）" />
        </el-form-item>
        <el-form-item label="视频时长（秒）" prop="duration_sec" v-if="!isEdit">
          <el-input-number v-model="form.duration_sec" :min="1" placeholder="请输入视频时长" style="width: 100%" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="请输入分类（可选）" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入视频描述（可选）" />
        </el-form-item>
        <el-form-item label="是否共享">
          <el-switch v-model="form.is_shared" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { videosApi } from '@/api/videos'
import { sitesApi } from '@/api/sites'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const submitting = ref(false)

const tableData = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const form = reactive({
  video_id: '', // For edit
  site_id: '', // 所属工地
  title: '',
  description: '',
  file_url: '',
  thumbnail_url: '',
  duration_sec: 0,
  category: '',
  is_shared: false
})

const rules = {
  title: [{ required: true, message: '请输入视频标题', trigger: 'blur' }],
  file_url: [{ required: true, message: '请输入视频URL', trigger: 'blur' }],
  duration_sec: [{ required: true, message: '请输入视频时长', trigger: 'blur' }]
}

// 获取列表
async function fetchList() {
  loading.value = true
  try {
    const response = await videosApi.getList({
      page: pagination.page,
      page_size: pagination.page_size
    })
    if (response.data?.code === 0) {
      tableData.value = response.data.data.items || []
      pagination.total = response.data.data.total || 0
    }
  } catch (error) {
    console.error('Failed to fetch videos:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

function formatDuration(seconds) {
  if (!seconds) return '0:00'
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${String(secs).padStart(2, '0')}`
}

function formatSize(bytes) {
  if (!bytes) return '-'
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(1)} MB`
}

function handleUpload() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function handlePreview(row) {
  if (row.file_url) {
    window.open(row.file_url, '_blank')
  } else {
    ElMessage.warning('视频URL不存在')
  }
}

function handleEdit(row) {
  isEdit.value = true
  resetForm()
  Object.assign(form, {
    video_id: row.video_id,
    title: row.title,
    description: row.description || '',
    file_url: row.file_url || '',
    thumbnail_url: row.thumbnail_url || '',
    duration_sec: row.duration_sec || 0,
    category: row.category || '',
    is_shared: row.is_shared || false
  })
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(form, {
    video_id: '',
    site_id: '',
    title: '',
    description: '',
    file_url: '',
    thumbnail_url: '',
    duration_sec: 0,
    category: '',
    is_shared: false
  })
  formRef.value?.resetFields()
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    
    try {
      let response
      if (isEdit.value) {
        response = await videosApi.update(form.video_id, {
          title: form.title,
          description: form.description,
          thumbnail_url: form.thumbnail_url,
          category: form.category,
          is_shared: form.is_shared,
          status: 'ACTIVE'
        })
      } else {
        // 获取site_id（从app store或从第一个可用site）
        let siteId = appStore.currentSiteId
        
        // 如果app store中没有site_id，从sites/options获取第一个
        if (!siteId) {
          try {
            const sitesResponse = await sitesApi.getOptions()
            if (sitesResponse.data?.code === 0 && sitesResponse.data.data?.length > 0) {
              siteId = sitesResponse.data.data[0].site_id || sitesResponse.data.data[0].id
            }
          } catch (error) {
            console.error('Failed to fetch sites:', error)
          }
        }
        
        if (!siteId) {
          ElMessage.error('无法确定工地，请先创建工地')
          return
        }
        
        response = await videosApi.create({
          site_id: siteId,
          title: form.title,
          description: form.description,
          file_url: form.file_url,
          thumbnail_url: form.thumbnail_url,
          duration_sec: form.duration_sec,
          category: form.category,
          is_shared: form.is_shared
        })
      }
      
      if (response.data?.code === 0) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        await fetchList()
      } else {
        ElMessage.error(response.data?.message || '操作失败')
      }
    } catch (error) {
      console.error('Failed to save video:', error)
      ElMessage.error('操作失败，请重试')
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除此视频？', '确认删除', {
      type: 'warning'
    })
    
    const response = await videosApi.delete(row.video_id)
    if (response.data?.code === 0) {
      ElMessage.success('删除成功')
      await fetchList()
    } else {
      ElMessage.error(response.data?.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete video:', error)
      ElMessage.error('删除失败，请重试')
    }
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style lang="scss" scoped>
.videos-page {
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

.video-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .video-thumb {
    width: 48px;
    height: 36px;
    background: var(--bg-elevated);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
  }
  
  .video-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    
    .video-title {
      font-size: 14px;
      color: var(--text-primary);
    }
    
    .video-desc {
      font-size: 12px;
      color: var(--text-muted);
    }
  }
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>

