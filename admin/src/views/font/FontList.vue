<template>
  <div class="font-list">
    <div class="page-header">
      <h2>字体管理</h2>
      <el-upload
        :show-file-list="false"
        :before-upload="beforeUpload"
        :http-request="handleUpload"
        accept=".ttf,.otf,.woff,.woff2"
      >
        <el-button type="primary" :loading="uploading">
          <el-icon><Upload /></el-icon>
          上传字体
        </el-button>
      </el-upload>
    </div>

    <el-table :data="fontList" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="字体名称">
        <template #default="{ row }">
          <span :style="{ fontFamily: row.fontFamily }">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column label="预览" width="200">
        <template #default="{ row }">
          <span :style="{ fontFamily: row.fontFamily, fontSize: '18px' }">
            摄影 Photo ABC
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="file_size" label="文件大小" width="120">
        <template #default="{ row }">
          {{ formatSize(row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="上传时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button 
            size="small" 
            :type="row.is_active ? 'warning' : 'success'"
            @click="handleToggle(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchFonts"
      />
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑字体" width="400px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="字体名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="editLoading">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import api from '@/api'

const fontList = ref([])
const loading = ref(false)
const uploading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const editDialogVisible = ref(false)
const editLoading = ref(false)
const editForm = reactive({
  id: null,
  name: ''
})

// 加载字体到页面
const loadedFonts = new Set()

const loadFont = (font) => {
  if (loadedFonts.has(font.id)) return font.filename.replace(/\.[^.]+$/, '')
  
  const fontFamily = `font_${font.id}`
  const style = document.createElement('style')
  style.textContent = `
    @font-face {
      font-family: '${fontFamily}';
      src: url('${font.url}');
    }
  `
  document.head.appendChild(style)
  loadedFonts.add(font.id)
  return fontFamily
}

const fetchFonts = async () => {
  loading.value = true
  try {
    const res = await api.getFonts({ page: page.value, page_size: pageSize.value })
    if (res.code === 200) {
      fontList.value = res.data.list.map(font => ({
        ...font,
        fontFamily: loadFont(font)
      }))
      total.value = res.data.total
    }
  } catch (error) {
    ElMessage.error('获取字体列表失败')
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file) => {
  const validExts = ['.ttf', '.otf', '.woff', '.woff2']
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  if (!validExts.includes(ext)) {
    ElMessage.error('只支持 TTF, OTF, WOFF, WOFF2 格式')
    return false
  }
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error('字体文件不能超过 20MB')
    return false
  }
  return true
}

const handleUpload = async ({ file }) => {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', file.name.replace(/\.[^.]+$/, ''))
    
    const res = await api.uploadFont(formData)
    if (res.code === 200) {
      ElMessage.success('上传成功')
      fetchFonts()
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const handleEdit = (row) => {
  editForm.id = row.id
  editForm.name = row.name
  editDialogVisible.value = true
}

const submitEdit = async () => {
  editLoading.value = true
  try {
    const res = await api.updateFont(editForm.id, { name: editForm.name })
    if (res.code === 200) {
      ElMessage.success('更新成功')
      editDialogVisible.value = false
      fetchFonts()
    } else {
      ElMessage.error(res.message || '更新失败')
    }
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}

const handleToggle = async (row) => {
  try {
    const res = await api.toggleFont(row.id)
    if (res.code === 200) {
      ElMessage.success(res.message)
      fetchFonts()
    } else {
      ElMessage.error(res.message || '操作失败')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该字体吗？', '提示', {
      type: 'warning'
    })
    const res = await api.deleteFont(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchFonts()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const formatSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchFonts()
})
</script>

<style scoped>
.font-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
