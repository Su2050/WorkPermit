<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>系统设置</h1>
      <p>配置系统参数和个人偏好</p>
    </div>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="基本设置" name="basic">
        <el-card>
          <el-form label-width="150px">
            <el-form-item label="系统名称">
              <el-input v-model="settings.systemName" style="width: 300px;" />
            </el-form-item>
            <el-form-item label="培训截止时间">
              <el-time-picker v-model="settings.trainingDeadline" format="HH:mm" />
            </el-form-item>
            <el-form-item label="授权时间窗">
              <el-time-picker
                v-model="settings.accessTimeRange"
                is-range
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                format="HH:mm"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="通知设置" name="notification">
        <el-card>
          <el-form label-width="150px">
            <el-form-item label="发送时间段">
              <el-time-picker
                v-model="settings.notifyTimeRange"
                is-range
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                format="HH:mm"
              />
            </el-form-item>
            <el-form-item label="培训提醒">
              <el-switch v-model="settings.trainingReminder" />
            </el-form-item>
            <el-form-item label="截止提醒">
              <el-switch v-model="settings.deadlineReminder" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="安全设置" name="security">
        <el-card>
          <el-form label-width="150px">
            <el-form-item label="修改密码">
              <el-button>修改密码</el-button>
            </el-form-item>
            <el-form-item label="登录日志">
              <el-button>查看日志</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const activeTab = ref('basic')

const settings = reactive({
  systemName: '作业票管理系统',
  trainingDeadline: new Date(2026, 0, 1, 12, 0),
  accessTimeRange: [new Date(2026, 0, 1, 8, 0), new Date(2026, 0, 1, 18, 0)],
  notifyTimeRange: [new Date(2026, 0, 1, 7, 0), new Date(2026, 0, 1, 21, 0)],
  trainingReminder: true,
  deadlineReminder: true
})
</script>

<style lang="scss" scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
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

