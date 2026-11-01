<template>
  <div class="reference-setting">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>合成参考图管理</span>
        </div>
      </template>
      
      <div class="reference-content">
        <el-alert 
          type="info" 
          :closable="false"
          style="margin-bottom: 20px"
        >
          参考图用于 AI 合成时的风格参考，上传后将在图片合成 API 中使用
        </el-alert>
        
        <div class="current-reference">
          <h4>当前参考图</h4>
          <div class="reference-preview" v-if="referenceUrl">
            <img :src="fullReferenceUrl" alt="参考图" />
          </div>
          <el-empty v-else description="暂未设置参考图" />
        </div>
        
        <el-divider />
        
        <div class="upload-section">
          <h4>上传新参考图</h4>
          <p class="tips">支持 PNG、JPG、WEBP 格式，建议使用高质量的参考图片</p>
          
          <el-upload
            class="reference-uploader"
            action="#"
            :show-file-list="false"
            :before-upload="beforeUpload"
            :http-request="uploadReference"
            accept=".png,.jpg,.jpeg,.webp"
          >
            <el-button type="primary" :loading="uploading">
              <el-icon><Upload /></el-icon>
              选择图片上传
            </el-button>
          </el-upload>
        </div>
        
        <el-divider v-if="referenceUrl" />
        
        <div class="actions" v-if="referenceUrl">
          <el-popconfirm
            title="确定要删除当前参考图吗？"
            @confirm="deleteReference"
          >
            <template #reference>
              <el-button type="danger" :loading="deleting">
                <el-icon><Delete /></el-icon>
                删除参考图
              </el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Delete } from '@element-plus/icons-vue'
import api from '@/api'

const referenceUrl = ref(null)
const uploading = ref(false)
const deleting = ref(false)

const fullReferenceUrl = computed(() => {
  if (!referenceUrl.value) return ''
  return referenceUrl.value
})

// 获取当前参考图
async function fetchReference() {
  try {
    const res = await api.getReference()
    if (res.code === 200) {
      referenceUrl.value = res.data.url
    }
  } catch (error) {
    console.error('获取参考图失败:', error)
  }
}

// 上传前检查
function beforeUpload(file) {
  const isImage = /\.(png|jpe?g|webp)$/i.test(file.name)
  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB！')
    return false
  }
  
  return true
}

// 上传参考图
async function uploadReference(options) {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    
    const res = await api.uploadReference(formData)
    if (res.code === 200) {
      referenceUrl.value = res.data.url
      ElMessage.success('上传成功')
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

// 删除参考图
async function deleteReference() {
  deleting.value = true
  try {
    const res = await api.deleteReference()
    if (res.code === 200) {
      referenceUrl.value = null
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  fetchReference()
})
</script>

<style scoped>
.reference-setting {
  padding: 20px;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
}

.reference-content {
  max-width: 800px;
}

.current-reference h4,
.upload-section h4 {
  margin-bottom: 16px;
  color: #303133;
}

.reference-preview {
  background: #f5f7fa;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.reference-preview img {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
}

.tips {
  color: #909399;
  font-size: 13px;
  margin-bottom: 16px;
}

.reference-uploader {
  display: inline-block;
}

.actions {
  margin-top: 20px;
}
</style>
