<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6" v-for="stat in stats" :key="stat.title">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon :size="40" :color="stat.color">
              <component :is="stat.icon" />
            </el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-title">{{ stat.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>数据概览</span>
          </template>
          <el-empty description="图表区域" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>最近活动</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(activity, index) in activities"
              :key="index"
              :timestamp="activity.time"
            >
              {{ activity.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { User, Picture, FolderOpened, TrendCharts } from '@element-plus/icons-vue'

const stats = ref([
  { title: '用户总数', value: 0, icon: 'User', color: '#409eff' },
  { title: '照片数量', value: 0, icon: 'Picture', color: '#67c23a' },
  { title: '相册数量', value: 0, icon: 'FolderOpened', color: '#e6a23c' },
  { title: '本周新增', value: 0, icon: 'TrendCharts', color: '#f56c6c' }
])

const activities = ref([
  { time: '2024-01-01 10:00', content: '用户 admin 登录系统' },
  { time: '2024-01-01 09:30', content: '新用户注册' },
  { time: '2024-01-01 09:00', content: '上传了 5 张照片' }
])

onMounted(async () => {
  // TODO: 从后端获取统计数据
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-row {
  margin-top: 20px;
}
</style>
