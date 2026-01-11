<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="grid-pattern"></div>
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
    </div>
    
    <!-- 登录卡片 -->
    <div class="login-card">
      <div class="login-header">
        <div class="logo">
          <el-icon :size="36"><Tickets /></el-icon>
        </div>
        <h1>作业票管理系统</h1>
        <p class="subtitle">Work Permit Management System</p>
      </div>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>演示账号</p>
        <div class="demo-accounts">
          <span @click="fillDemo('admin', 'admin123')">管理员</span>
          <span @click="fillDemo('contractor', 'contractor123')">施工单位</span>
        </div>
      </div>
    </div>
    
    <!-- 版权信息 -->
    <div class="copyright">
      © 2026 Work Permit System. All rights reserved.
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)
const rememberMe = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

// 填充演示账号
function fillDemo(username, password) {
  form.username = username
  form.password = password
}

// 登录
async function handleLogin() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    
    try {
      const result = await authStore.login({
        username: form.username,
        password: form.password
      })
      
      if (result.success) {
        ElMessage.success('登录成功')
        
        // 跳转到重定向页面或首页
        const redirect = route.query.redirect || '/dashboard'
        router.push(redirect)
      } else {
        ElMessage.error(result.message || '登录失败')
      }
    } finally {
      loading.value = false
    }
  })
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: var(--bg-dark);
  overflow: hidden;
}

.bg-decoration {
  position: absolute;
  inset: 0;
  overflow: hidden;
  
  .grid-pattern {
    position: absolute;
    inset: 0;
    background-image: 
      linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 60px 60px;
  }
  
  .gradient-orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.5;
    
    &.orb-1 {
      width: 500px;
      height: 500px;
      background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
      top: -200px;
      right: -100px;
    }
    
    &.orb-2 {
      width: 400px;
      height: 400px;
      background: linear-gradient(135deg, var(--accent-color), var(--accent-dark));
      bottom: -150px;
      left: -100px;
      opacity: 0.3;
    }
  }
}

.login-card {
  position: relative;
  width: 420px;
  padding: 48px 40px;
  background: rgba(22, 27, 34, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  animation: slideUp 0.5s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
  
  .logo {
    width: 72px;
    height: 72px;
    margin: 0 auto 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--accent-color), var(--accent-dark));
    border-radius: 16px;
    color: white;
    box-shadow: 0 8px 24px rgba(255, 107, 53, 0.3);
  }
  
  h1 {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }
  
  .subtitle {
    font-size: 14px;
    color: var(--text-muted);
    letter-spacing: 0.5px;
  }
}

.login-form {
  :deep(.el-form-item) {
    margin-bottom: 24px;
  }
  
  :deep(.el-input__wrapper) {
    padding: 0 15px;
    height: 48px;
    background: var(--bg-elevated);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    
    &:hover {
      border-color: var(--primary-light);
    }
    
    &.is-focus {
      border-color: var(--accent-color);
      box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.15);
    }
  }
  
  :deep(.el-checkbox__label) {
    color: var(--text-secondary);
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, var(--accent-color), var(--accent-dark));
  border: none;
  border-radius: var(--radius-md);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(255, 107, 53, 0.35);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.login-footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
  text-align: center;
  
  p {
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 12px;
  }
  
  .demo-accounts {
    display: flex;
    justify-content: center;
    gap: 24px;
    
    span {
      font-size: 13px;
      color: var(--primary-light);
      cursor: pointer;
      transition: color 0.2s;
      
      &:hover {
        color: var(--accent-color);
      }
    }
  }
}

.copyright {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  color: var(--text-muted);
}
</style>

