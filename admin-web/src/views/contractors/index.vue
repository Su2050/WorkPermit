<template>
  <div class="contractors-page">
    <div class="page-header">
      <div class="header-left">
        <h1>施工单位管理</h1>
        <p>管理合作的施工单位信息</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增施工单位
        </el-button>
      </div>
    </div>
    
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="单位名称" min-width="200" />
        <el-table-column prop="code" label="单位编码" width="120" />
        <el-table-column prop="contact_person" label="联系人" width="100" />
        <el-table-column prop="contact_phone" label="联系电话" width="130" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button text type="primary" size="small" @click="handleViewWorkers(row)">人员</el-button>
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
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="单位名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入单位名称" />
        </el-form-item>
        <el-form-item label="单位编码" prop="code">
          <el-input v-model="form.code" placeholder="请输入单位编码（唯一）" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact_person">
          <el-input v-model="form.contact_person" placeholder="请输入联系人姓名" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contact_phone">
          <el-input v-model="form.contact_phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" type="textarea" rows="2" placeholder="请输入地址" />
        </el-form-item>
        <el-form-item label="营业执照号" prop="license_no">
          <el-input v-model="form.license_no" placeholder="请输入营业执照号" />
        </el-form-item>
        <el-form-item label="资质等级" prop="qualification_level">
          <el-input v-model="form.qualification_level" placeholder="请输入资质等级" />
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态" prop="is_active">
          <el-switch v-model="form.is_active" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { contractorsApi } from '@/api/contractors'

const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const form = reactive({
  name: '',
  code: '',
  contact_person: '',
  contact_phone: '',
  address: '',
  license_no: '',
  qualification_level: '',
  is_active: true
})

const rules = {
  name: [
    { required: true, message: '请输入单位名称', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入单位编码', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑施工单位' : '新增施工单位')

// 获取列表数据
async function fetchList() {
  loading.value = true
  try {
    const response = await contractorsApi.getList({
      page: pagination.page,
      page_size: pagination.page_size
    })
    
    if (response.data?.code === 0) {
      tableData.value = response.data.data.items || []
      pagination.total = response.data.data.total || 0
    }
  } catch (error) {
    console.error('Failed to fetch contractors:', error)
    // 响应拦截器已处理错误显示，这里只记录日志
  } finally {
    loading.value = false
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
  Object.assign(form, {
    contractor_id: row.contractor_id,
    name: row.name,
    code: row.code,
    contact_person: row.contact_person || '',
    contact_phone: row.contact_phone || '',
    address: row.address || '',
    license_no: row.license_no || '',
    qualification_level: row.qualification_level || '',
    is_active: row.is_active
  })
  dialogVisible.value = true
}

// 查看人员
function handleViewWorkers(row) {
  ElMessage.info('查看人员功能开发中')
}

// 重置表单
function resetForm() {
  Object.assign(form, {
    name: '',
    code: '',
    contact_person: '',
    contact_phone: '',
    address: '',
    license_no: '',
    qualification_level: '',
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
        response = await contractorsApi.update(form.contractor_id, form)
      } else {
        response = await contractorsApi.create(form)
      }
      
      if (response.data?.code === 0) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        await fetchList()
      } else {
        // 特殊处理：检查是否是"没有工地"的错误，需要引导用户创建工地
        const errorMessage = response.data?.message || '操作失败'
        const errorDetails = response.data?.data || []
        let finalMessage = errorMessage
        
        // 优先使用详细错误信息
        if (errorDetails.length > 0 && errorDetails[0].message) {
          finalMessage = errorDetails[0].message
        }
        
        // 检查是否是"没有工地"的错误
        if (finalMessage.includes('没有工地') || finalMessage.includes('请先创建工地')) {
          ElMessageBox.confirm(
            finalMessage + '，是否前往创建工地？',
            '提示',
            {
              confirmButtonText: '去创建工地',
              cancelButtonText: '取消',
              type: 'warning'
            }
          ).then(() => {
            router.push('/sites')
          }).catch(() => {
            // 用户取消，不做任何操作
          })
        }
        // 注意: 其他错误由响应拦截器统一显示
      }
    } catch (error) {
      console.error('Failed to save contractor:', error)
      // 响应拦截器已处理错误显示，这里只记录日志
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

onMounted(() => {
  fetchList()
})
</script>

<style lang="scss" scoped>
.contractors-page {
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

