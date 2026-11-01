<template>
  <div class="home">
    <el-card class="welcome-card">
      <template #header>
        <div class="card-header">
          <span>欢迎使用 Photo App</span>
        </div>
      </template>
      <div class="welcome-content">
        <el-icon :size="64" color="#409eff"><Camera /></el-icon>
        <h2>Windows PC 照片应用</h2>
        <p>基于 Vue 3 + Element Plus + Electron 构建</p>
      </div>
    </el-card>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="照片总数" :value="128" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="相册数量" :value="12" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="存储空间" :value="2.5" suffix="GB" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { Camera } from '@element-plus/icons-vue'
</script>

<style scoped>
.home {
  padding: 20px;
}

.welcome-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.welcome-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  gap: 16px;
}

.welcome-content h2 {
  margin: 0;
  color: #303133;
}

.welcome-content p {
  color: #909399;
}

.stats-row {
  margin-top: 20px;
}
</style>
