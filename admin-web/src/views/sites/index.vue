<template>
  <div class="sites-page">
    <div class="page-header">
      <div class="header-left">
        <h1>工地管理</h1>
        <p>管理系统中的工地信息</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增工地
        </el-button>
      </div>
    </div>
    
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="工地名称" min-width="200" />
        <el-table-column prop="code" label="工地编码" width="120" />
        <el-table-column prop="address" label="地址" min-width="200" />
        <el-table-column prop="is_active" label="状态" width="120">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              inline-prompt
              :active-text="'启用'"
              :inactive-text="'禁用'"
              :loading="togglingSiteId === row.site_id"
              @change="(val) => handleToggleActive(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button text type="primary" size="small" @click="handleView(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
      >
        <el-form-item label="工地名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入工地名称" />
        </el-form-item>
        <el-form-item label="工地编码" prop="code">
          <el-input 
            v-model="form.code" 
            :placeholder="isEdit ? '工地编码不可修改' : '请输入工地编码（唯一）'" 
            :disabled="isEdit"
          />
          <div v-if="isEdit" style="color: #909399; font-size: 12px; margin-top: 4px;">
            工地编码创建后不可修改
          </div>
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" type="textarea" rows="2" placeholder="请输入地址" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入工地描述（可选）" />
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态" prop="is_active">
          <el-switch
            v-model="form.is_active"
            inline-prompt
            :active-text="'启用'"
            :inactive-text="'禁用'"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            禁用后，该工地下的下拉选项将不可选（但历史数据仍保留）
          </div>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="默认授权开始时间" prop="default_access_start_time">
              <el-time-picker
                v-model="form.default_access_start_time"
                format="HH:mm:ss"
                value-format="HH:mm:ss"
                placeholder="选择时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="默认授权结束时间" prop="default_access_end_time">
              <el-time-picker
                v-model="form.default_access_end_time"
                format="HH:mm:ss"
                value-format="HH:mm:ss"
                placeholder="选择时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="默认培训截止时间" prop="default_training_deadline">
          <el-time-picker
            v-model="form.default_training_deadline"
            format="HH:mm:ss"
            value-format="HH:mm:ss"
            placeholder="选择时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { sitesApi } from '@/api/sites'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const togglingSiteId = ref('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const form = reactive({
  name: '',
  code: '',
  address: '',
  description: '',
  default_access_start_time: '06:00:00',
  default_access_end_time: '20:00:00',
  default_training_deadline: '07:30:00',
  is_active: true
})

const rules = {
  name: [
    { required: true, message: '请输入工地名称', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入工地编码', trigger: 'blur' }
  ],
  default_access_start_time: [
    { required: true, message: '请选择默认授权开始时间', trigger: 'change' }
  ],
  default_access_end_time: [
    { required: true, message: '请选择默认授权结束时间', trigger: 'change' }
  ],
  default_training_deadline: [
    { required: true, message: '请选择默认培训截止时间', trigger: 'change' }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑工地' : '新增工地')

// 获取列表数据
async function fetchList() {
  loading.value = true
  try {
    const response = await sitesApi.getList({
      page: pagination.page,
      page_size: pagination.page_size
    })
    
    if (response.data?.code === 0) {
      tableData.value = response.data.data.items || []
      pagination.total = response.data.data.total || 0
    }
  } catch (error) {
    console.error('Failed to fetch sites:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 快速启用/禁用（列表内切换）
async function handleToggleActive(row, val) {
  const prev = !val
  try {
    togglingSiteId.value = row.site_id
    await ElMessageBox.confirm(
      `确定要将工地「${row.name}」设置为${val ? '启用' : '禁用'}吗？`,
      '确认操作',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
    const resp = await sitesApi.update(row.site_id, { is_active: val })
    if (resp.data?.code === 0) {
      ElMessage.success('状态已更新')
    } else {
      row.is_active = prev
      ElMessage.error(resp.data?.message || '状态更新失败')
    }
  } catch (e) {
    // 取消/失败都回滚 UI 状态
    row.is_active = prev
  } finally {
    togglingSiteId.value = ''
  }
}

// 新增
function handleAdd() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑
function handleEdit(row) {
  isEdit.value = true
  resetForm()
  // 获取详情
  sitesApi.getDetail(row.site_id).then(response => {
    if (response.data?.code === 0) {
      const detail = response.data.data
      Object.assign(form, {
        site_id: detail.site_id,
        name: detail.name,
        code: detail.code,
        address: detail.address || '',
        description: detail.description || '',
        default_access_start_time: detail.default_access_start_time || '06:00:00',
        default_access_end_time: detail.default_access_end_time || '20:00:00',
        default_training_deadline: detail.default_training_deadline || '07:30:00',
        is_active: detail.is_active
      })
      dialogVisible.value = true
    }
  }).catch(error => {
    console.error('Failed to fetch site detail:', error)
    ElMessage.error('获取工地详情失败')
  })
}

// 查看详情
function handleView(row) {
  router.push(`/sites/${row.site_id}`)
}

// 重置表单
function resetForm() {
  Object.assign(form, {
    name: '',
    code: '',
    address: '',
    description: '',
    default_access_start_time: '06:00:00',
    default_access_end_time: '20:00:00',
    default_training_deadline: '07:30:00',
    is_active: true
  })
  formRef.value?.resetFields()
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    
    try {
      let response
      if (isEdit.value) {
        // 只提交后端允许的更新字段，避免 422（例如 code/site_id 这类后端不接收）
        const payload = {
          name: form.name,
          address: form.address,
          description: form.description,
          default_access_start_time: form.default_access_start_time,
          default_access_end_time: form.default_access_end_time,
          default_training_deadline: form.default_training_deadline,
          is_active: form.is_active
        }
        response = await sitesApi.update(form.site_id, payload)
      } else {
        // 创建接口不支持 is_active（默认启用），只提交创建所需字段
        const payload = {
          name: form.name,
          code: form.code,
          address: form.address,
          description: form.description,
          default_access_start_time: form.default_access_start_time,
          default_access_end_time: form.default_access_end_time,
          default_training_deadline: form.default_training_deadline
        }
        response = await sitesApi.create(payload)
      }
      
      if (response.data?.code === 0) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        await fetchList()
      } else {
        ElMessage.error(response.data?.message || '操作失败')
      }
    } catch (error) {
      console.error('Failed to save site:', error)
      ElMessage.error('操作失败，请重试')
    } finally {
      submitting.value = false
    }
  })
}

// 分页变化
function handleSizeChange() {
  fetchList()
}

function handlePageChange() {
  fetchList()
}

// 监听路由参数，如果有点击编辑的site_id，自动打开编辑对话框
watch(() => route.query.edit, (siteId) => {
  if (siteId) {
    // 从列表中找到对应的工地并打开编辑对话框
    const site = tableData.value.find(s => s.site_id === siteId)
    if (site) {
      handleEdit(site)
      // 清除查询参数
      router.replace({ query: {} })
    }
  }
}, { immediate: true })

onMounted(() => {
  fetchList()
})
</script>

<style lang="scss" scoped>
.sites-page {
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

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>

