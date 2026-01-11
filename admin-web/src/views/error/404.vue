<template>
  <div class="error-page">
    <div class="error-content">
      <h1>404</h1>
      <p>页面不存在</p>
      <el-button type="primary" @click="router.push('/dashboard')">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style lang="scss" scoped>
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-dark);
}

.error-content {
  text-align: center;
  
  h1 {
    font-size: 120px;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 16px;
  }
  
  p {
    font-size: 20px;
    color: var(--text-secondary);
    margin-bottom: 24px;
  }
}
</style>

