<template>
  <div class="background-manage">
    <!-- 操作栏 -->
    <div class="action-bar">
      <el-upload
        ref="uploadRef"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        :show-file-list="false"
        accept="image/*"
        multiple
      >
        <el-button type="primary" :icon="Upload">上传背景图</el-button>
      </el-upload>
      <el-button :icon="Refresh" @click="fetchBackgrounds">刷新</el-button>
    </div>

    <!-- 背景图列表 -->
    <div class="background-grid" v-loading="loading">
      <div
        v-for="item in backgrounds"
        :key="item.id"
        class="background-item"
      >
        <div class="image-wrapper">
          <el-image
            :src="item.url"
            fit="cover"
            class="bg-image"
            :preview-src-list="[item.url]"
          />
          <div class="overlay">
            <el-button
              type="danger"
              :icon="Delete"
              circle
              size="small"
              @click="handleDelete(item)"
            />
          </div>
        </div>
        <div class="info">
          <span class="name" :title="item.name">{{ item.name }}</span>
          <span class="date">{{ formatDate(item.created_at) }}</span>
        </div>
      </div>
      
      <el-empty v-if="!loading && backgrounds.length === 0" description="暂无背景图" />
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchBackgrounds"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Refresh, Delete } from '@element-plus/icons-vue'

const BASE_URL = '/api'

const backgrounds = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const uploadUrl = `${BASE_URL}/admin/backgrounds/upload`
const uploadHeaders = {
  Authorization: `Bearer ${localStorage.getItem('admin_token')}`
}

const fetchBackgrounds = async () => {
  loading.value = true
  try {
    const response = await fetch(
      `${BASE_URL}/admin/backgrounds?page=${page.value}&page_size=${pageSize.value}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('admin_token')}`
        }
      }
    )
    const data = await response.json()
    if (data.code === 200) {
      backgrounds.value = data.data.list || []
      total.value = data.data.total || 0
    }
  } catch (error) {
    ElMessage.error('获取背景图列表失败')
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过10MB!')
    return false
  }
  return true
}

const handleUploadSuccess = (response) => {
  if (response.code === 200) {
    ElMessage.success('上传成功')
    fetchBackgrounds()
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleUploadError = () => {
  ElMessage.error('上传失败，请重试')
}

const handleDelete = async (item) => {
  try {
    await ElMessageBox.confirm('确定要删除此背景图吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const response = await fetch(`${BASE_URL}/admin/backgrounds/${item.id}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('admin_token')}`
      }
    })
    const data = await response.json()
    if (data.code === 200) {
      ElMessage.success('删除成功')
      fetchBackgrounds()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchBackgrounds()
})
</script>

<style scoped>
.background-manage {
  padding: 20px;
}

.action-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.background-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  min-height: 300px;
}

.background-item {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.background-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.image-wrapper {
  position: relative;
  padding-top: 75%;
}

.bg-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-wrapper:hover .overlay {
  opacity: 1;
}

.info {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.name {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.date {
  font-size: 12px;
  color: #909399;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
