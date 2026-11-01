<template>
  <div class="user-list">
    <el-card>
      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="用户名">
          <el-input v-model="searchForm.keyword" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Plus" @click="handleAdd">新增用户</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="handleStatusChange(row)" />
          </template>
        </el-table-column>
        <el-table-column label="AI配额" width="180">
          <template #default="{ row }">
            <div v-if="row.role !== 'admin'">
              <el-progress 
                :percentage="row.ai_quota > 0 ? Math.round((row.ai_used || 0) / row.ai_quota * 100) : 0"
                :status="row.ai_remaining <= 0 ? 'exception' : ''"
                :stroke-width="10"
              />
              <span class="quota-text">{{ row.ai_used || 0 }} / {{ row.ai_quota || 0 }}</span>
            </div>
            <el-tag v-else type="success">无限制</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="warning" @click="handleQuota(row)" v-if="row.role !== 'admin'">配额</el-button>
            <el-popconfirm title="确定删除该用户?" @confirm="handleDelete(row)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        class="pagination"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @change="fetchData"
      />
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="500px">
      <el-form :model="editForm" :rules="formRules" ref="formRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" :disabled="isEdit" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="editForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- AI配额管理弹窗 -->
    <el-dialog v-model="quotaDialogVisible" title="AI配额管理" width="450px">
      <el-form :model="quotaForm" label-width="100px">
        <el-form-item label="用户">
          <span>{{ quotaForm.username }}</span>
        </el-form-item>
        <el-form-item label="当前配额">
          <el-input-number v-model="quotaForm.ai_quota" :min="0" :max="99999" />
          <span class="form-tip">次</span>
        </el-form-item>
        <el-form-item label="已使用">
          <span>{{ quotaForm.ai_used }} 次</span>
        </el-form-item>
        <el-form-item label="剩余次数">
          <el-tag :type="quotaForm.ai_remaining > 0 ? 'success' : 'danger'">
            {{ quotaForm.ai_remaining }} 次
          </el-tag>
        </el-form-item>
        <el-form-item label="重置已使用">
          <el-switch v-model="quotaForm.reset_used" />
          <span class="form-tip">开启后将重置已使用次数为0</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="quotaDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="quotaLoading" @click="handleSaveQuota">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { Search, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const BASE_URL = '/api'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const quotaDialogVisible = ref(false)
const quotaLoading = ref(false)
const tableData = ref([])
const formRef = ref(null)

const searchForm = reactive({
  keyword: ''
})

const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0
})

const editForm = reactive({
  id: null,
  username: '',
  password: '',
  email: '',
  role: 'user'
})

const quotaForm = reactive({
  id: null,
  username: '',
  ai_quota: 200,
  ai_used: 0,
  ai_remaining: 200,
  reset_used: false
})

const isEdit = computed(() => !!editForm.id)

const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: pagination.page,
      per_page: pagination.per_page
    })
    if (searchForm.keyword) params.append('keyword', searchForm.keyword)
    
    const response = await fetch(`${BASE_URL}/admin/users?${params}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('admin_token')}` }
    })
    const data = await response.json()
    if (data.code === 200) {
      tableData.value = data.data.list || []
      pagination.total = data.data.total || 0
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.keyword = ''
  handleSearch()
}

const handleAdd = () => {
  Object.assign(editForm, { id: null, username: '', password: '', email: '', role: 'user' })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  Object.assign(editForm, { ...row, password: '' })
  dialogVisible.value = true
}

const handleSave = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid && !isEdit.value) return
  
  submitLoading.value = true
  try {
    const url = isEdit.value 
      ? `${BASE_URL}/admin/users/${editForm.id}` 
      : `${BASE_URL}/admin/users`
    const method = isEdit.value ? 'PUT' : 'POST'
    
    const body = isEdit.value 
      ? { email: editForm.email, role: editForm.role }
      : { username: editForm.username, password: editForm.password, email: editForm.email, role: editForm.role }
    
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('admin_token')}`
      },
      body: JSON.stringify(body)
    })
    const data = await response.json()
    
    if (data.code === 200) {
      ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
      dialogVisible.value = false
      fetchData()
    } else {
      ElMessage.error(data.message || '操作失败')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleStatusChange = async (row) => {
  try {
    const response = await fetch(`${BASE_URL}/admin/users/${row.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('admin_token')}`
      },
      body: JSON.stringify({ is_active: row.is_active })
    })
    const data = await response.json()
    if (data.code === 200) {
      ElMessage.success('状态更新成功')
    } else {
      ElMessage.error(data.message || '更新失败')
      row.is_active = !row.is_active
    }
  } catch (error) {
    ElMessage.error('更新失败')
    row.is_active = !row.is_active
  }
}

const handleDelete = async (row) => {
  try {
    const response = await fetch(`${BASE_URL}/admin/users/${row.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${localStorage.getItem('admin_token')}` }
    })
    const data = await response.json()
    if (data.code === 200) {
      ElMessage.success('删除成功')
      fetchData()
    } else {
      ElMessage.error(data.message || '删除失败')
    }
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// 打开AI配额管理弹窗
const handleQuota = (row) => {
  Object.assign(quotaForm, {
    id: row.id,
    username: row.username,
    ai_quota: row.ai_quota || 200,
    ai_used: row.ai_used || 0,
    ai_remaining: row.ai_remaining || 200,
    reset_used: false
  })
  quotaDialogVisible.value = true
}

// 保存AI配额
const handleSaveQuota = async () => {
  quotaLoading.value = true
  try {
    const response = await fetch(`${BASE_URL}/admin/users/${quotaForm.id}/quota`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('admin_token')}`
      },
      body: JSON.stringify({
        ai_quota: quotaForm.ai_quota,
        reset_used: quotaForm.reset_used
      })
    })
    const data = await response.json()
    if (data.code === 200) {
      ElMessage.success('配额更新成功')
      quotaDialogVisible.value = false
      fetchData()
    } else {
      ElMessage.error(data.message || '更新失败')
    }
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    quotaLoading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.user-list {
  min-height: 100%;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.quota-text {
  display: block;
  font-size: 12px;
  color: #909399;
  text-align: center;
  margin-top: 4px;
}

.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}
</style>
