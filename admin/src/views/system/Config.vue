<template>
  <div class="system-config">
    <el-card>
      <template #header>
        <span>系统配置</span>
      </template>

      <el-form :model="configForm" label-width="150px" style="max-width: 600px;">
        <el-divider content-position="left">基础设置</el-divider>
        
        <el-form-item label="网站名称">
          <el-input v-model="configForm.siteName" />
        </el-form-item>
        
        <el-form-item label="网站描述">
          <el-input v-model="configForm.siteDesc" type="textarea" :rows="3" />
        </el-form-item>

        <el-divider content-position="left">存储设置</el-divider>
        
        <el-form-item label="最大上传大小">
          <el-input-number v-model="configForm.maxUploadSize" :min="1" :max="100" />
          <span style="margin-left: 10px;">MB</span>
        </el-form-item>
        
        <el-form-item label="允许的文件类型">
          <el-checkbox-group v-model="configForm.allowedTypes">
            <el-checkbox label="jpg">JPG</el-checkbox>
            <el-checkbox label="png">PNG</el-checkbox>
            <el-checkbox label="gif">GIF</el-checkbox>
            <el-checkbox label="webp">WebP</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-divider content-position="left">用户设置</el-divider>
        
        <el-form-item label="允许注册">
          <el-switch v-model="configForm.allowRegister" />
        </el-form-item>
        
        <el-form-item label="默认用户空间">
          <el-input-number v-model="configForm.defaultSpace" :min="1" :max="100" />
          <span style="margin-left: 10px;">GB</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave">保存配置</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'

const configForm = reactive({
  siteName: 'Photo App',
  siteDesc: '照片管理系统',
  maxUploadSize: 16,
  allowedTypes: ['jpg', 'png', 'gif', 'webp'],
  allowRegister: true,
  defaultSpace: 10
})

const handleSave = () => {
  // TODO: 调用后端 API
  ElMessage.success('配置保存成功')
}

const handleReset = () => {
  // 重置为默认值
}
</script>

<style scoped>
.system-config {
  min-height: 100%;
}
</style>
