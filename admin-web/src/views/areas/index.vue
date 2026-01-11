<template>
  <div class="areas-page">
    <div class="page-header">
      <div class="header-left">
        <h1>作业区域管理</h1>
        <p>管理工地作业区域和门禁设备关联</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增区域
        </el-button>
      </div>
    </div>
    
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="区域名称" min-width="150" />
        <el-table-column prop="code" label="区域编码" width="120" />
        <el-table-column prop="device_count" label="门禁设备" width="100" align="center">
          <template #default="{ row }">
            <el-tag>{{ row.device_count || 0 }} 个</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除此区域？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button text type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑区域' : '新增区域'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="所属工地" prop="site_id" v-if="!isEdit">
          <el-select 
            v-model="form.site_id" 
            placeholder="请选择工地" 
            filterable 
            style="width: 100%"
          >
            <el-option
              v-for="site in siteOptions"
              :key="site.site_id"
              :label="site.name"
              :value="site.site_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="区域名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入区域名称" />
        </el-form-item>
        <el-form-item label="区域编码" prop="code">
          <el-input v-model="form.code" placeholder="请输入区域编码" />
        </el-form-item>
        <el-form-item label="门禁组ID">
          <el-input v-model="form.access_group_id" placeholder="请输入门禁组ID（可选）" />
        </el-form-item>
        <el-form-item label="门禁组名称">
          <el-input v-model="form.access_group_name" placeholder="请输入门禁组名称（可选）" />
        </el-form-item>
        <el-form-item label="楼栋">
          <el-input v-model="form.building" placeholder="请输入楼栋（可选）" />
        </el-form-item>
        <el-form-item label="楼层">
          <el-input v-model="form.floor" placeholder="请输入楼层（可选）" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入区域描述（可选）" />
        </el-form-item>
        <el-form-item label="状态" v-if="isEdit">
          <el-switch v-model="form.is_active" />
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
import { ElMessage } from 'element-plus'
import { areasApi } from '@/api/areas'
import { sitesApi } from '@/api/sites'

const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const submitting = ref(false)

const tableData = ref([])
const siteOptions = ref([])
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const form = reactive({
  area_id: '', // For edit
  site_id: '', // 新增：所属工地
  name: '',
  code: '',
  description: '',
  access_group_id: '',
  access_group_name: '',
  building: '',
  floor: '',
  is_active: true
})

const rules = {
  site_id: [{ required: true, message: '请选择所属工地', trigger: 'change' }],
  name: [{ required: true, message: '请输入区域名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入区域编码', trigger: 'blur' }]
}

// 获取列表
async function fetchList() {
  loading.value = true
  try {
    const response = await areasApi.getList({
      page: pagination.page,
      page_size: pagination.page_size
    })
    if (response.data?.code === 0) {
      tableData.value = response.data.data.items || []
      pagination.total = response.data.data.total || 0
    }
  } catch (error) {
    console.error('Failed to fetch areas:', error)
    // 响应拦截器已处理错误显示，这里只记录日志
  } finally {
    loading.value = false
  }
}

// 获取工地选项
async function fetchSiteOptions() {
  try {
    const response = await sitesApi.getOptions()
    if (response.data?.code === 0) {
      siteOptions.value = response.data.data || []
    }
  } catch (error) {
    console.error('Failed to fetch site options:', error)
    // 响应拦截器已处理错误显示，这里只记录日志
  }
}

function handleAdd() {
  isEdit.value = false
  resetForm()
  fetchSiteOptions()
  dialogVisible.value = true
}

async function handleEdit(row) {
  isEdit.value = true
  resetForm()
  await fetchSiteOptions()  // 加载工地选项
  Object.assign(form, {
    area_id: row.area_id,
    site_id: row.site_id || '',  // 回填工地
    name: row.name,
    code: row.code,
    description: row.description || '',
    access_group_id: row.access_group_id || '',
    access_group_name: row.access_group_name || '',
    building: row.building || '',
    floor: row.floor || '',
    is_active: row.is_active
  })
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(form, {
    area_id: '',
    site_id: '',
    name: '',
    code: '',
    description: '',
    access_group_id: '',
    access_group_name: '',
    building: '',
    floor: '',
    is_active: true
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
        response = await areasApi.update(form.area_id, {
          name: form.name,
          description: form.description,
          access_group_id: form.access_group_id,
          access_group_name: form.access_group_name,
          building: form.building,
          floor: form.floor,
          is_active: form.is_active
        })
      } else {
        response = await areasApi.create({
          site_id: form.site_id, // 新增：传递工地ID
          name: form.name,
          code: form.code,
          description: form.description,
          access_group_id: form.access_group_id,
          access_group_name: form.access_group_name,
          building: form.building,
          floor: form.floor
        })
      }
      
      if (response.data?.code === 0) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        await fetchList()
      }
      // 注意: 如果 code !== 0，响应拦截器会自动显示错误信息
    } catch (error) {
      console.error('Failed to save area:', error)
      // 响应拦截器已处理错误显示，这里只记录日志
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(row) {
  try {
    const response = await areasApi.delete(row.area_id)
    if (response.data?.code === 0) {
      ElMessage.success('删除成功')
      await fetchList()
    }
    // 注意: 如果 code !== 0，响应拦截器会自动显示错误信息
  } catch (error) {
    console.error('Failed to delete area:', error)
    // 响应拦截器已处理错误显示，这里只记录日志
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style lang="scss" scoped>
.areas-page {
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
</style>

