<template>
  <div class="logo-setting">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>品牌 Logo 管理</span>
        </div>
      </template>
      
      <div class="logo-content">
        <div class="current-logo">
          <h4>当前 Logo</h4>
          <div class="logo-preview" v-if="logoUrl">
            <img :src="fullLogoUrl" alt="品牌 Logo" />
          </div>
          <el-empty v-else description="暂未设置 Logo" />
        </div>
        
        <el-divider />
        
        <div class="upload-section">
          <h4>上传新 Logo</h4>
          <p class="tips">支持 PNG、JPG、GIF、SVG、WEBP 格式，建议使用透明背景的 PNG 图片</p>
          
          <el-upload
            class="logo-uploader"
            action="#"
            :show-file-list="false"
            :before-upload="beforeUpload"
            :http-request="uploadLogo"
            accept=".png,.jpg,.jpeg,.gif,.svg,.webp"
          >
            <el-button type="primary" :loading="uploading">
              <el-icon><Upload /></el-icon>
              选择图片上传
            </el-button>
          </el-upload>
        </div>
        
        <el-divider v-if="logoUrl" />
        
        <div class="actions" v-if="logoUrl">
          <el-popconfirm
            title="确定要删除当前 Logo 吗？"
            @confirm="deleteLogo"
          >
            <template #reference>
              <el-button type="danger" :loading="deleting">
                <el-icon><Delete /></el-icon>
                删除 Logo
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

const logoUrl = ref(null)
const uploading = ref(false)
const deleting = ref(false)

const fullLogoUrl = computed(() => {
  if (!logoUrl.value) return ''
  return logoUrl.value
})

// 获取当前 Logo
async function fetchLogo() {
  try {
    const res = await api.getLogo()
    if (res.code === 200) {
      logoUrl.value = res.data.url
    }
  } catch (error) {
    console.error('获取 Logo 失败:', error)
  }
}

// 上传前检查
function beforeUpload(file) {
  const isImage = /\.(png|jpe?g|gif|svg|webp)$/i.test(file.name)
  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB！')
    return false
  }
  
  return true
}

// 上传 Logo
async function uploadLogo(options) {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    
    const res = await api.uploadLogo(formData)
    if (res.code === 200) {
      logoUrl.value = res.data.url
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

// 删除 Logo
async function deleteLogo() {
  deleting.value = true
  try {
    const res = await api.deleteLogo()
    if (res.code === 200) {
      logoUrl.value = null
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
  fetchLogo()
})
</script>

<style scoped>
.logo-setting {
  padding: 20px;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
}

.logo-content {
  max-width: 600px;
}

.current-logo h4,
.upload-section h4 {
  margin-bottom: 16px;
  color: #303133;
}

.logo-preview {
  background: #f5f7fa;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.logo-preview img {
  max-width: 300px;
  max-height: 150px;
  object-fit: contain;
}

.tips {
  color: #909399;
  font-size: 13px;
  margin-bottom: 16px;
}

.logo-uploader {
  display: inline-block;
}

.actions {
  margin-top: 20px;
}
</style>
