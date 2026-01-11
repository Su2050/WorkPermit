<template>
  <div class="empty-state">
    <el-empty :description="description" :image-size="imageSize">
      <template v-if="$slots.default">
        <slot></slot>
      </template>
      <template v-else-if="showAction">
        <el-button type="primary" @click="handleAction">
          {{ actionText }}
        </el-button>
      </template>
    </el-empty>
  </div>
</template>

<script setup>
const props = defineProps({
  description: {
    type: String,
    default: '暂无数据'
  },
  imageSize: {
    type: Number,
    default: 200
  },
  showAction: {
    type: Boolean,
    default: false
  },
  actionText: {
    type: String,
    default: '立即创建'
  }
})

const emit = defineEmits(['action'])

function handleAction() {
  emit('action')
}
</script>

<style lang="scss" scoped>
.empty-state {
  padding: 40px 20px;
}
</style>

