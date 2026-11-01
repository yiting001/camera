<template>
  <div class="dashboard" v-loading="loading">
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6" v-for="stat in stats" :key="stat.title">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: stat.bgColor }">
              <el-icon :size="28" color="#fff">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-title">{{ stat.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>合成照片趋势</span>
              <el-radio-group v-model="chartType" size="small" @change="fetchTrend">
                <el-radio-button value="week">近7天</el-radio-button>
                <el-radio-button value="month">近30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="chartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header>
            <span>最新合成照片</span>
          </template>
          <div class="recent-photos">
            <div v-for="photo in recentPhotos" :key="photo.id" class="photo-item">
              <el-image :src="photo.url" fit="cover" class="photo-thumb" :preview-src-list="[photo.url]" />
              <div class="photo-info">
                <span class="photo-user">{{ photo.username }}</span>
                <span class="photo-date">{{ photo.created_at }}</span>
              </div>
            </div>
            <el-empty v-if="recentPhotos.length === 0" description="暂无数据" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row :gutter="20" class="activity-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>最新用户</span>
          </template>
          <el-table :data="recentUsers" stripe>
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column prop="photo_count" label="合成照片数" width="120" />
            <el-table-column prop="last_login" label="最后登录" width="180" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, markRaw } from 'vue'
import { User, Picture, Camera, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const BASE_URL = '/api'

const loading = ref(false)
const chartType = ref('week')
const chartRef = ref(null)
let chartInstance = null

const stats = ref([
  { title: '用户总数', value: 0, icon: markRaw(User), bgColor: '#409eff' },
  { title: '合成照片', value: 0, icon: markRaw(Camera), bgColor: '#67c23a' },
  { title: '背景图数', value: 0, icon: markRaw(Picture), bgColor: '#e6a23c' },
  { title: '今日合成', value: 0, icon: markRaw(TrendCharts), bgColor: '#f56c6c' }
])

const recentUsers = ref([])
const recentPhotos = ref([])
const trendData = ref({ dates: [], counts: [] })

const fetchStats = async () => {
  loading.value = true
  try {
    const response = await fetch(`${BASE_URL}/admin/stats`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('admin_token')}`
      }
    })
    const data = await response.json()
    if (data.code === 200) {
      const s = data.data
      stats.value[0].value = s.user_count || 0
      stats.value[1].value = s.photo_count || 0
      stats.value[2].value = s.background_count || 0
      stats.value[3].value = s.today_count || 0
      recentUsers.value = s.recent_users || []
      recentPhotos.value = s.recent_photos || []
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchTrend = async () => {
  try {
    const days = chartType.value === 'week' ? 7 : 30
    const response = await fetch(`${BASE_URL}/admin/stats/trend?days=${days}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('admin_token')}`
      }
    })
    const data = await response.json()
    if (data.code === 200) {
      trendData.value = data.data
      renderChart()
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
  }
}

const renderChart = () => {
  if (!chartRef.value) return
  
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  
  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: trendData.value.dates || [],
      axisLabel: { rotate: 45 }
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      name: '合成数量',
      type: 'line',
      smooth: true,
      data: trendData.value.counts || [],
      areaStyle: { opacity: 0.3 },
      itemStyle: { color: '#409eff' }
    }]
  }
  
  chartInstance.setOption(option)
}

const handleResize = () => {
  chartInstance?.resize()
}

onMounted(async () => {
  await fetchStats()
  await nextTick()
  await fetchTrend()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.dashboard {
  min-height: 100%;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
}

.recent-photos {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.photo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 8px;
}

.photo-thumb {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  flex-shrink: 0;
}

.photo-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.photo-user {
  font-size: 14px;
  color: #303133;
}

.photo-date {
  font-size: 12px;
  color: #909399;
}

.activity-row {
  margin-top: 20px;
}
</style>
