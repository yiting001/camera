<template>
  <div class="api-setting">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Doubao API 配置</span>
        </div>
      </template>
      
      <div class="setting-content">
        <el-alert 
          type="warning" 
          :closable="false"
          style="margin-bottom: 20px"
        >
          请配置火山引擎豆包 Doubao Seedream API，用于 AI 图像合成功能
        </el-alert>
        
        <el-form :model="form" label-width="120px" style="max-width: 600px">
          <el-form-item label="模型">
            <el-select v-model="form.model" placeholder="选择模型" style="width: 100%">
              <el-option label="doubao-seedream-4-5-251128 (推荐)" value="doubao-seedream-4-5-251128" />
              <el-option label="doubao-seedream-3-0-t2i-250116" value="doubao-seedream-3-0-t2i-250116" />
            </el-select>
            <div class="form-tip">图像生成模型</div>
          </el-form-item>
          
          <el-form-item label="提示词模式">
            <div class="prompts-list">
              <div v-for="(prompt, index) in form.prompts" :key="index" class="prompt-item">
                <div class="prompt-header">
                  <el-input 
                    v-model="prompt.name" 
                    placeholder="模式名称"
                    style="width: 120px"
                  />
                  <el-button 
                    type="danger" 
                    :icon="Delete" 
                    circle 
                    size="small"
                    @click="removePrompt(index)"
                    :disabled="form.prompts.length <= 1"
                  />
                </div>
                <el-input 
                  v-model="prompt.content" 
                  type="textarea"
                  :rows="2"
                  placeholder="合成提示词内容"
                  style="margin-top: 8px"
                />
              </div>
              <el-button type="primary" plain @click="addPrompt" :icon="Plus" style="margin-top: 10px">
                添加提示词模式
              </el-button>
            </div>
            <div class="form-tip">前端合成时可选择不同模式，每个模式使用不同的提示词</div>
          </el-form-item>
          
          <el-form-item label="输出尺寸">
            <el-select v-model="form.size" placeholder="选择输出图片尺寸" style="width: 100%">
              <el-option 
                v-for="opt in sizeOptions" 
                :key="opt.value" 
                :label="opt.label" 
                :value="opt.value"
              />
            </el-select>
            <div class="form-tip">生成图片的宽高比例，默认 16:9 横版</div>
          </el-form-item>
          
          <el-form-item label="API Key">
            <el-input 
              v-model="form.apiKey" 
              placeholder="输入新的 API Key（留空保持原有）"
              show-password
            />
            <div class="form-tip" v-if="hasKey">
              <el-tag type="success" size="small">已配置</el-tag>
              当前密钥: {{ maskedKey }}
            </div>
            <div class="form-tip" v-else>
              <el-tag type="info" size="small">使用默认</el-tag>
              已使用服务器环境变量中配置的 API Key
            </div>
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="saveConfig" :loading="saving">
              保存配置
            </el-button>
          </el-form-item>
        </el-form>
        
        <el-divider />
        
        <div class="help-section">
          <h4>使用说明</h4>
          <ul>
            <li>Doubao Seedream 用于将用户照片与背景图合成</li>
            <li>合成需要两个参数：用户照片(图1)、背景图(图2)</li>
            <li>图片会自动上传到 TOS 获取公网 URL</li>
            <li>请确保已配置 TOS 对象存储</li>
          </ul>
        </div>
      </div>
    </el-card>
    
    <!-- 合成测试 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>图像合成测试</span>
        </div>
      </template>
      
      <div class="test-content">
        <el-alert 
          type="info" 
          :closable="false"
          style="margin-bottom: 20px"
        >
          上传用户照片和背景图，测试 Doubao 图像合成功能
        </el-alert>
        
        <div class="upload-row">
          <div class="upload-item">
            <h4>用户照片 (Couple)</h4>
            <el-upload
              class="image-uploader"
              action="#"
              :show-file-list="false"
              :on-change="(f) => handleFileChange(f, 'photo')"
              :auto-upload="false"
              accept="image/*"
            >
              <img v-if="testFiles.photoPreview" :src="testFiles.photoPreview" class="preview-image" />
              <div v-else class="upload-placeholder">
                <el-icon class="upload-icon"><Plus /></el-icon>
                <span>点击上传</span>
              </div>
            </el-upload>
          </div>
          
          <div class="upload-item">
            <h4>背景图 (Background)</h4>
            <el-upload
              class="image-uploader"
              action="#"
              :show-file-list="false"
              :on-change="(f) => handleFileChange(f, 'background')"
              :auto-upload="false"
              accept="image/*"
            >
              <img v-if="testFiles.bgPreview" :src="testFiles.bgPreview" class="preview-image" />
              <div v-else class="upload-placeholder">
                <el-icon class="upload-icon"><Plus /></el-icon>
                <span>点击上传</span>
              </div>
            </el-upload>
          </div>
          
          <div class="upload-item">
            <h4>参考图 (Reference)</h4>
            <el-upload
              class="image-uploader"
              action="#"
              :show-file-list="false"
              :on-change="(f) => handleFileChange(f, 'reference')"
              :auto-upload="false"
              accept="image/*"
            >
              <img v-if="testFiles.refPreview" :src="testFiles.refPreview" class="preview-image" />
              <div v-else class="upload-placeholder">
                <el-icon class="upload-icon"><Plus /></el-icon>
                <span>可选，留空用系统配置</span>
              </div>
            </el-upload>
          </div>
        </div>
        
        <div class="test-actions">
          <el-button 
            type="primary" 
            @click="runTest" 
            :loading="testRunning"
            :disabled="!testFiles.photo || !testFiles.background"
          >
            {{ testRunning ? '合成中（约1-2分钟）...' : '开始测试合成' }}
          </el-button>
          <el-button @click="clearTest">清空</el-button>
        </div>
        
        <div v-if="testRunning" class="test-progress">
          <el-progress :percentage="testProgress" :format="() => testStatus" />
        </div>
        
        <div v-if="testResult" class="result-section">
          <h4>合成结果</h4>
          <div class="result-wrapper">
            <img :src="testResult" class="result-image" />
          </div>
          <el-input v-model="testResult" readonly style="margin-top: 10px">
            <template #append>
              <el-button @click="copyResult">复制链接</el-button>
            </template>
          </el-input>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import api from '@/api'

const form = reactive({
  model: 'doubao-seedream-4-5-251128',
  prompts: [
    { name: '模式1', content: '将图1的人物与图2的背景完美融合，保持人物特征不变，自然融入背景场景' }
  ],
  size: '16:9',
  apiKey: ''
})

// 添加提示词
function addPrompt() {
  form.prompts.push({ name: `模式${form.prompts.length + 1}`, content: '' })
}

// 删除提示词
function removePrompt(index) {
  if (form.prompts.length > 1) {
    form.prompts.splice(index, 1)
  }
}

const hasKey = ref(false)
const maskedKey = ref('')
const saving = ref(false)

// 尺寸选项（从后端获取或使用默认值）
const sizeOptions = ref([
  { value: '16:9', label: '16:9 横版 (2560x1440)' },
  { value: '9:16', label: '9:16 竖版 (1440x2560)' },
  { value: '1:1', label: '1:1 正方形 (2048x2048)' },
  { value: '4:3', label: '4:3 横版 (2304x1728)' },
  { value: '3:4', label: '3:4 竖版 (1728x2304)' },
  { value: '3:2', label: '3:2 横版 (2496x1664)' },
  { value: '2:3', label: '2:3 竖版 (1664x2496)' },
  { value: '21:9', label: '21:9 超宽 (3024x1296)' },
  { value: '2K', label: '2K 自动比例' },
  { value: '4K', label: '4K 自动比例' },
])

// 测试相关 - 文件上传
const testFiles = reactive({
  photo: null,
  background: null,
  reference: null,
  photoPreview: '',
  bgPreview: '',
  refPreview: ''
})
const testResult = ref('')
const testRunning = ref(false)
const testProgress = ref(0)
const testStatus = ref('')

// 获取当前配置
async function fetchConfig() {
  try {
    const res = await api.getMjConfig()
    if (res.code === 200) {
      form.model = res.data.model || 'doubao-seedream-4-5-251128'
      // 支持新的多提示词格式和旧的单提示词格式
      if (res.data.prompts && res.data.prompts.length > 0) {
        form.prompts = res.data.prompts
      } else if (res.data.prompt) {
        form.prompts = [{ name: '模式1', content: res.data.prompt }]
      }
      form.size = res.data.size || '16:9'
      hasKey.value = res.data.hasKey
      maskedKey.value = res.data.apiKey || ''
      // 更新尺寸选项（如果后端返回）
      if (res.data.sizeOptions) {
        sizeOptions.value = res.data.sizeOptions
      }
    }
  } catch (error) {
    console.error('获取配置失败:', error)
  }
}

// 保存配置
async function saveConfig() {
  // 验证提示词
  const validPrompts = form.prompts.filter(p => p.name && p.content)
  if (validPrompts.length === 0) {
    ElMessage.warning('请至少配置一个有效的提示词模式')
    return
  }
  
  saving.value = true
  try {
    const res = await api.saveMjConfig({
      model: form.model,
      prompts: validPrompts,
      size: form.size,
      apiKey: form.apiKey
    })
    if (res.code === 200) {
      ElMessage.success('保存成功')
      form.apiKey = '' // 清空输入框
      fetchConfig() // 刷新显示
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 处理文件选择
function handleFileChange(uploadFile, type) {
  const file = uploadFile.raw
  const reader = new FileReader()
  reader.onload = (e) => {
    if (type === 'photo') {
      testFiles.photo = file
      testFiles.photoPreview = e.target.result
    } else if (type === 'background') {
      testFiles.background = file
      testFiles.bgPreview = e.target.result
    } else if (type === 'reference') {
      testFiles.reference = file
      testFiles.refPreview = e.target.result
    }
  }
  reader.readAsDataURL(file)
}

// 执行测试
async function runTest() {
  if (!testFiles.photo || !testFiles.background) {
    ElMessage.warning('请上传用户照片和背景图')
    return
  }
  
  testRunning.value = true
  testProgress.value = 10
  testStatus.value = '上传图片到 TOS...'
  testResult.value = ''
  
  try {
    const formData = new FormData()
    formData.append('photo', testFiles.photo)
    formData.append('background', testFiles.background)
    if (testFiles.reference) {
      formData.append('reference', testFiles.reference)
    }
    
    testProgress.value = 30
    testStatus.value = '调用 Doubao 合成...'
    
    const res = await api.testMjComposite(formData)
    
    if (res.code === 200) {
      testProgress.value = 100
      testStatus.value = '合成完成！'
      testResult.value = res.data.resultUrl
      ElMessage.success('测试成功！图像合成完成')
    } else {
      ElMessage.error(res.message || '测试失败')
    }
  } catch (error) {
    console.error('测试失败:', error)
    ElMessage.error('测试失败: ' + (error.response?.data?.message || error.message))
  } finally {
    testRunning.value = false
  }
}

// 复制结果链接
function copyResult() {
  navigator.clipboard.writeText(testResult.value)
  ElMessage.success('链接已复制')
}

// 清空测试
function clearTest() {
  testFiles.photo = null
  testFiles.background = null
  testFiles.reference = null
  testFiles.photoPreview = ''
  testFiles.bgPreview = ''
  testFiles.refPreview = ''
  testResult.value = ''
  testProgress.value = 0
  testStatus.value = ''
}

onMounted(() => {
  fetchConfig()
})
</script>

<style scoped>
.api-setting {
  padding: 20px;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
}

.setting-content {
  max-width: 800px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.help-section h4 {
  margin-bottom: 12px;
  color: #303133;
}

.help-section ul {
  padding-left: 20px;
  color: #606266;
  line-height: 2;
}

/* 测试区域样式 */
.test-content {
  max-width: 100%;
}

.upload-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.upload-item {
  flex: 1;
  min-width: 200px;
  max-width: 280px;
}

.upload-item h4 {
  margin-bottom: 10px;
  font-size: 14px;
  color: #303133;
}

.image-uploader {
  width: 100%;
}

.image-uploader :deep(.el-upload) {
  width: 100%;
  height: 180px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.3s;
  overflow: hidden;
}

.image-uploader :deep(.el-upload):hover {
  border-color: #409eff;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #909399;
}

.upload-icon {
  font-size: 32px;
  color: #c0c4cc;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.test-actions {
  margin-bottom: 20px;
}

.test-progress {
  max-width: 400px;
  margin-bottom: 20px;
}

.result-section {
  margin-top: 20px;
  padding: 20px;
  background: #f0f9eb;
  border-radius: 8px;
  border: 1px solid #67c23a;
}

.result-section h4 {
  margin-bottom: 12px;
  color: #67c23a;
}

.result-wrapper {
  width: 100%;
  max-width: 500px;
  border-radius: 8px;
  overflow: hidden;
}

.result-image {
  width: 100%;
  height: auto;
  max-height: 400px;
  object-fit: contain;
}

/* 提示词列表样式 */
.prompts-list {
  width: 100%;
}

.prompt-item {
  padding: 12px;
  margin-bottom: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.prompt-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
