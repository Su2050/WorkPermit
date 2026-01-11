<template>
  <div class="workers-page">
    <div class="page-header">
      <div class="header-left">
        <h1>人员管理</h1>
        <p>管理作业人员信息</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增人员
        </el-button>
      </div>
    </div>
    
    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="关键词">
          <el-input 
            v-model="filters.keyword"
            placeholder="搜索姓名或手机号"
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
            <el-option label="活跃" value="ACTIVE" />
            <el-option label="已离职" value="INACTIVE" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table 
        :data="tableData" 
        v-loading="loading"
        stripe
      >
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="id_no" label="身份证号" width="180">
          <template #default="{ row }">
            {{ row.id_no || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="job_type" label="工种" width="120" />
        <el-table-column prop="team_name" label="班组" width="120" />
        <el-table-column prop="contractor_name" label="施工单位" min-width="150" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ACTIVE' || !row.status ? 'success' : 'info'" size="small">
              {{ row.status === 'ACTIVE' || !row.status ? '活跃' : '已离职' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_bound" label="绑定状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_bound ? 'success' : 'warning'" size="small">
              {{ row.is_bound ? '已绑定' : '未绑定' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除此人员？" @confirm="handleDelete(row)">
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
    
    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑人员' : '新增人员'"
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
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="身份证号" prop="id_no">
          <el-input v-model="form.id_no" placeholder="请输入身份证号" />
        </el-form-item>
        <el-form-item label="工种">
          <el-input v-model="form.job_type" placeholder="请输入工种（可选）" />
        </el-form-item>
        <el-form-item label="班组">
          <el-input v-model="form.team_name" placeholder="请输入班组（可选）" />
        </el-form-item>
        <el-form-item label="施工单位" prop="contractor_id">
          <el-select v-model="form.contractor_id" placeholder="请选择施工单位" filterable style="width: 100%">
            <el-option
              v-for="c in contractorOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" v-if="isEdit">
          <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="活跃" value="ACTIVE" />
            <el-option label="已离职" value="INACTIVE" />
          </el-select>
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
import { workersApi } from '@/api/workers'
import { contractorsApi } from '@/api/contractors'
import { sitesApi } from '@/api/sites'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const submitting = ref(false)

const tableData = ref([])
const contractorOptions = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const filters = reactive({
  keyword: '',
  contractorId: null,
  status: null
})

const form = reactive({
  worker_id: '', // For edit
  name: '',
  phone: '',
  id_no: '',
  job_type: '',
  team_name: '',
  contractor_id: null,
  status: 'ACTIVE'
})

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  id_no: [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    { pattern: /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/, message: '请输入正确的身份证号', trigger: 'blur' }
  ],
  contractor_id: [{ required: true, message: '请选择施工单位', trigger: 'change' }]
}

// 获取施工单位选项
async function fetchContractorOptions() {
  try {
    const response = await contractorsApi.getOptions()
    if (response.data?.code === 0) {
      contractorOptions.value = response.data.data || []
    }
  } catch (error) {
    console.error('Failed to fetch contractors:', error)
  }
}

// 获取列表
async function fetchList() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    if (filters.keyword) {
      params.keyword = filters.keyword
    }
    if (filters.contractorId) {
      params.contractor_id = filters.contractorId
    }
    if (filters.status) {
      params.status = filters.status
    }
    
    const response = await workersApi.getList(params)
    if (response.data?.code === 0) {
      tableData.value = response.data.data.items || []
      pagination.total = response.data.data.total || 0
    }
  } catch (error) {
    console.error('Failed to fetch workers:', error)
    // 响应拦截器已处理错误显示，这里只记录日志
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

async function handleEdit(row) {
  isEdit.value = true
  resetForm()
  
  // 获取完整的人员信息（包含完整身份证号）
  try {
    const response = await workersApi.getDetail(row.worker_id)
    if (response.data?.code === 0) {
      const detail = response.data.data
      Object.assign(form, {
        worker_id: detail.worker_id,
        name: detail.name,
        phone: detail.phone,
        id_no: detail.id_no || '', // 使用完整身份证号
        job_type: detail.job_type || '',
        team_name: detail.team_name || '',
        contractor_id: detail.contractor_id || null,
        status: detail.status || 'ACTIVE'
      })
    } else {
      // 如果获取详情失败，使用列表数据（身份证号是脱敏的）
      Object.assign(form, {
        worker_id: row.worker_id,
        name: row.name,
        phone: row.phone.replace(/\*+/g, ''), // 尝试恢复手机号（如果可能）
        id_no: '', // 列表中的身份证号是脱敏的，需要用户重新输入
        job_type: row.job_type || '',
        team_name: row.team_name || '',
        contractor_id: row.contractor_id || null,
        status: row.status || 'ACTIVE'
      })
    }
  } catch (error) {
    console.error('Failed to fetch worker detail:', error)
    // 使用列表数据
    Object.assign(form, {
      worker_id: row.worker_id,
      name: row.name,
      phone: row.phone.replace(/\*+/g, ''),
      id_no: '',
      job_type: row.job_type || '',
      team_name: row.team_name || '',
      contractor_id: row.contractor_id || null,
      status: row.status || 'ACTIVE'
    })
  }
  
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(form, {
    worker_id: '',
    name: '',
    phone: '',
    id_no: '',
    job_type: '',
    team_name: '',
    contractor_id: null,
    status: 'ACTIVE'
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
        response = await workersApi.update(form.worker_id, {
          name: form.name,
          phone: form.phone,
          id_no: form.id_no,
          job_type: form.job_type,
          team_name: form.team_name,
          contractor_id: form.contractor_id,
          status: form.status
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
        
        response = await workersApi.create({
          site_id: siteId,
          name: form.name,
          phone: form.phone,
          id_no: form.id_no,
          job_type: form.job_type,
          team_name: form.team_name,
          contractor_id: form.contractor_id
        })
      }
      
      if (response.data?.code === 0) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        await fetchList()
      }
      // 注意: 如果 code !== 0，响应拦截器会自动显示错误信息
    } catch (error) {
      console.error('Failed to save worker:', error)
      // 响应拦截器已处理错误显示，这里只记录日志
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除此人员？', '确认删除', {
      type: 'warning'
    })
    
    const response = await workersApi.delete(row.worker_id)
    if (response.data?.code === 0) {
      ElMessage.success('删除成功')
      await fetchList()
    }
    // 注意: 如果 code !== 0，响应拦截器会自动显示错误信息
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete worker:', error)
      // 响应拦截器已处理错误显示，这里只记录日志
    }
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function handleReset() {
  Object.assign(filters, {
    keyword: '',
    contractorId: null,
    status: null
  })
  handleSearch()
}

onMounted(() => {
  fetchContractorOptions()
  fetchList()
})
</script>

<style lang="scss" scoped>
.workers-page {
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
  margin-bottom: 0;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>

