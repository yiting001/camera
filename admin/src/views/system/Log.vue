<template>
  <div class="operation-log">
    <el-card>
      <template #header>
        <span>操作日志</span>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="操作类型">
          <el-select v-model="searchForm.type" placeholder="全部" clearable>
            <el-option label="登录" value="login" />
            <el-option label="上传" value="upload" />
            <el-option label="删除" value="delete" />
            <el-option label="修改" value="update" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 日志列表 -->
      <el-table :data="tableData" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="操作用户" width="120" />
        <el-table-column prop="type" label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.type)">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="操作内容" />
        <el-table-column prop="ip" label="IP地址" width="140" />
        <el-table-column prop="created_at" label="操作时间" width="180" />
      </el-table>

      <!-- 分页 -->
      <el-pagination
        class="pagination"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @change="fetchData"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const loading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  type: '',
  dateRange: []
})

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const getTypeTag = (type) => {
  const map = {
    login: 'success',
    upload: 'primary',
    delete: 'danger',
    update: 'warning'
  }
  return map[type] || 'info'
}

const fetchData = async () => {
  loading.value = true
  // TODO: 调用后端 API
  loading.value = false
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.type = ''
  searchForm.dateRange = []
  handleSearch()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.operation-log {
  min-height: 100%;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
