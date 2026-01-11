<template>
  <div class="users-page">
    <div class="page-header">
      <div class="header-left">
        <h1>用户管理</h1>
        <p>管理系统用户和权限</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增用户
        </el-button>
      </div>
    </div>
    
    <el-card>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="role" label="角色" width="150">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">{{ getRoleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contractor_name" label="所属施工单位" min-width="150">
          <template #default="{ row }">
            {{ row.contractor_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="160">
          <template #default="{ row }">
            {{ row.last_login_at ? new Date(row.last_login_at).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button text type="warning" size="small" @click="handleResetPwd(row)">重置密码</el-button>
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
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" :disabled="isEdit" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码（至少6位）" show-password />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%" @change="handleRoleChange">
            <el-option label="系统管理员" value="SysAdmin" />
            <el-option label="施工单位管理员" value="ContractorAdmin" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.role === 'ContractorAdmin'" label="所属施工单位" prop="contractor_id">
          <el-select
            v-model="form.contractor_id"
            placeholder="请选择施工单位"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="c in contractorOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
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
    
    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="resetPwdDialogVisible"
      title="重置密码"
      width="400px"
    >
      <el-form
        ref="resetPwdFormRef"
        :model="resetPwdForm"
        :rules="resetPwdRules"
        label-width="100px"
      >
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetPwdForm.new_password" type="password" placeholder="请输入新密码（至少6位）" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="resetPwdForm.confirm_password" type="password" placeholder="请再次输入密码" show-password />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="resetPwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitResetPwd" :loading="resetting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usersApi } from '@/api/users'
import { contractorsApi } from '@/api/contractors'

const loading = ref(false)
const submitting = ref(false)
const resetting = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const resetPwdDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const resetPwdFormRef = ref()
const contractorOptions = ref([])

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const form = reactive({
  username: '',
  password: '',
  name: '',
  email: '',
  phone: '',
  role: 'ContractorAdmin',
  contractor_id: '',
  is_active: true
})

const resetPwdForm = reactive({
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== resetPwdForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 72, message: '密码长度为6-72位', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const resetPwdRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 72, message: '密码长度为6-72位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '新增用户')

// 获取列表数据
async function fetchList() {
  loading.value = true
  try {
    const response = await usersApi.getList({
      page: pagination.page,
      page_size: pagination.page_size
    })
    
    if (response.data?.code === 0) {
      tableData.value = response.data.data.items || []
      pagination.total = response.data.data.total || 0
    }
  } catch (error) {
    console.error('Failed to fetch users:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
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
    console.error('Failed to fetch contractors:', error)
  }
}

// 新增
function handleAdd() {
  isEdit.value = false
  resetForm()
  fetchContractorOptions()
  dialogVisible.value = true
}

// 编辑
async function handleEdit(row) {
  isEdit.value = true
  resetForm()
  await fetchContractorOptions()
  
  Object.assign(form, {
    user_id: row.user_id,
    username: row.username,
    name: row.name,
    email: row.email || '',
    phone: row.phone || '',
    role: row.role,
    contractor_id: row.contractor_id || '',
    is_active: row.is_active
  })
  dialogVisible.value = true
}

const currentResetUserId = ref(null)

// 重置密码
function handleResetPwd(row) {
  currentResetUserId.value = row.user_id
  resetPwdForm.new_password = ''
  resetPwdForm.confirm_password = ''
  resetPwdDialogVisible.value = true
}

// 角色变化
function handleRoleChange() {
  if (form.role === 'SysAdmin') {
    form.contractor_id = ''
  }
}

// 重置表单
function resetForm() {
  Object.assign(form, {
    username: '',
    password: '',
    name: '',
    email: '',
    phone: '',
    role: 'ContractorAdmin',
    contractor_id: '',
    is_active: true
  })
  formRef.value?.resetFields()
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    // 验证施工单位管理员必须选择施工单位
    if (form.role === 'ContractorAdmin' && !form.contractor_id) {
      ElMessage.warning('施工单位管理员必须选择所属施工单位')
      return
    }
    
    submitting.value = true
    
    try {
      let response
      if (isEdit.value) {
        const updateData = { ...form }
        delete updateData.password
        delete updateData.username
        response = await usersApi.update(form.user_id, updateData)
      } else {
        response = await usersApi.create(form)
      }
      
      if (response.data?.code === 0) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        await fetchList()
      } else {
        ElMessage.error(response.data?.message || '操作失败')
      }
    } catch (error) {
      console.error('Failed to save user:', error)
      ElMessage.error('操作失败，请重试')
    } finally {
      submitting.value = false
    }
  })
}

// 提交重置密码
async function handleSubmitResetPwd() {
  if (!resetPwdFormRef.value) return
  
  await resetPwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    resetting.value = true
    
    try {
      const response = await usersApi.resetPassword(currentResetUserId.value, resetPwdForm.new_password)
      
      if (response.data?.code === 0) {
        ElMessage.success('密码重置成功')
        resetPwdDialogVisible.value = false
      } else {
        ElMessage.error(response.data?.message || '重置失败')
      }
    } catch (error) {
      console.error('Failed to reset password:', error)
      ElMessage.error('重置失败，请重试')
    } finally {
      resetting.value = false
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

function getRoleType(role) {
  const map = { SysAdmin: 'danger', ContractorAdmin: 'warning' }
  return map[role] || 'info'
}

function getRoleLabel(role) {
  const map = { SysAdmin: '系统管理员', ContractorAdmin: '施工单位管理员' }
  return map[role] || role
}

onMounted(() => {
  fetchList()
})
</script>

<style lang="scss" scoped>
.users-page {
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

