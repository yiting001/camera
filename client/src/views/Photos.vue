<template>
  <div class="photos">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>照片管理</span>
          <el-button type="primary" :icon="Plus">上传照片</el-button>
        </div>
      </template>
      
      <!-- 搜索和筛选 -->
      <el-row :gutter="16" class="filter-row">
        <el-col :span="8">
          <el-input v-model="searchText" placeholder="搜索照片..." :prefix-icon="Search" clearable />
        </el-col>
        <el-col :span="4">
          <el-select v-model="selectedAlbum" placeholder="选择相册" clearable>
            <el-option label="全部" value="" />
            <el-option label="风景" value="landscape" />
            <el-option label="人物" value="portrait" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-col>
      </el-row>

      <!-- 照片列表占位 -->
      <el-empty description="照片列表将在这里展示" />
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'

const searchText = ref('')
const selectedAlbum = ref('')
</script>

<style scoped>
.photos {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-row {
  margin-bottom: 20px;
}
</style>
