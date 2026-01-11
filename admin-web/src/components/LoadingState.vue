<template>
  <div class="loading-state">
    <!-- 骨架屏加载 -->
    <template v-if="type === 'skeleton'">
      <el-skeleton :rows="rows" animated />
    </template>
    
    <!-- 卡片骨架屏 -->
    <template v-else-if="type === 'card'">
      <el-card v-for="i in count" :key="i" class="skeleton-card">
        <el-skeleton :rows="3" animated />
      </el-card>
    </template>
    
    <!-- 表格骨架屏 -->
    <template v-else-if="type === 'table'">
      <el-skeleton :rows="rows" animated>
        <template #template>
          <el-skeleton-item variant="text" style="width: 100%; height: 40px; margin-bottom: 10px;" />
          <el-skeleton-item 
            v-for="i in rows" 
            :key="i" 
            variant="text" 
            style="width: 100%; height: 50px; margin-bottom: 5px;" 
          />
        </template>
      </el-skeleton>
    </template>
    
    <!-- 加载动画 -->
    <template v-else-if="type === 'spinner'">
      <div class="spinner-container">
        <el-icon class="is-loading" :size="size">
          <Loading />
        </el-icon>
        <p v-if="text" class="loading-text">{{ text }}</p>
      </div>
    </template>
    
    <!-- 默认加载 -->
    <template v-else>
      <div class="default-loading">
        <el-icon class="is-loading">
          <Loading />
        </el-icon>
      </div>
    </template>
  </div>
</template>

<script setup>
import { Loading } from '@element-plus/icons-vue'

defineProps({
  type: {
    type: String,
    default: 'skeleton',
    validator: (value) => ['skeleton', 'card', 'table', 'spinner', 'default'].includes(value)
  },
  rows: {
    type: Number,
    default: 5
  },
  count: {
    type: Number,
    default: 3
  },
  size: {
    type: Number,
    default: 40
  },
  text: {
    type: String,
    default: ''
  }
})
</script>

<style lang="scss" scoped>
.loading-state {
  width: 100%;
}

.skeleton-card {
  margin-bottom: 20px;
}

.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  
  .loading-text {
    margin-top: 16px;
    font-size: 14px;
    color: var(--text-secondary);
  }
}

.default-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}
</style>

