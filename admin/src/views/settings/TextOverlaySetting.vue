<template>
  <div class="text-overlay-setting">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>底部文字描述设置</span>
          <span class="header-tip">此设置将应用到前端客户端的拍照合成功能</span>
        </div>
      </template>
      
      <el-form 
        ref="formRef" 
        :model="form" 
        label-width="100px" 
        v-loading="loading"
        class="setting-form"
      >
        <el-form-item label="启用文字">
          <el-switch v-model="form.enabled" />
          <span class="form-tip">启用后，合成的照片底部将显示文字描述条</span>
        </el-form-item>
        
        <el-form-item label="文字内容">
          <el-input 
            v-model="form.content" 
            placeholder="请输入文字描述，如：品牌名称、活动名称等"
            maxlength="100"
            show-word-limit
            :disabled="!form.enabled"
          />
        </el-form-item>
        
        <el-form-item label="选择字体">
          <el-select 
            v-model="form.fontId" 
            placeholder="选择字体" 
            style="width: 100%"
            :disabled="!form.enabled"
          >
            <el-option label="默认字体" :value="0" />
            <el-option 
              v-for="font in fontList" 
              :key="font.id" 
              :label="font.name" 
              :value="font.id"
            />
          </el-select>
          <span class="form-tip">可在字体管理中上传自定义字体</span>
        </el-form-item>
        
        <el-form-item label="字体大小">
          <el-slider 
            v-model="form.fontSize" 
            :min="12" 
            :max="48" 
            :step="2"
            :disabled="!form.enabled"
            show-input
            style="max-width: 400px"
          />
        </el-form-item>
        
        <el-form-item label="文字颜色">
          <el-color-picker 
            v-model="form.textColor" 
            :disabled="!form.enabled"
            show-alpha
            color-format="rgb"
            @active-change="(val) => { if(val) form.textColor = val }"
          />
          <span class="color-preview" :style="{ color: form.textColor || '#ffffff' }">预览文字</span>
        </el-form-item>
        
        <el-form-item label="背景颜色">
          <el-color-picker 
            v-model="form.bgColor" 
            :disabled="!form.enabled"
            show-alpha
            color-format="rgb"
            @active-change="(val) => { if(val) form.bgColor = val }"
          />
          <span 
            class="bg-preview" 
            :style="{ backgroundColor: form.bgColor || 'rgba(0, 0, 0, 0.7)', color: form.textColor || '#ffffff' }"
          >预览效果</span>
        </el-form-item>
        
        <el-divider />
        
        <!-- 预览区域 -->
        <el-form-item label="效果预览">
          <div class="preview-container">
            <div class="preview-image">
              <div class="preview-placeholder">
                <el-icon :size="48"><Picture /></el-icon>
                <span>示例照片区域</span>
              </div>
              <div 
                v-if="form.enabled"
                class="preview-overlay"
                :style="previewOverlayStyle"
              >
                <span :style="previewTextStyle">
                  {{ form.content || '预览文字' }}
                </span>
              </div>
            </div>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">
            <el-icon><Check /></el-icon>
            保存设置
          </el-button>
          <el-button @click="fetchSettings">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Refresh, Picture } from '@element-plus/icons-vue'
import api from '@/api'

const loading = ref(false)
const saving = ref(false)
const fontList = ref([])
const loadedFonts = new Map() // 已加载的字体

const form = reactive({
  enabled: true,
  content: '',
  fontId: 0,
  fontSize: 24,
  textColor: '#ffffff',
  bgColor: 'rgba(0, 0, 0, 0.7)'
})

// 获取设置
async function fetchSettings() {
  loading.value = true
  try {
    const res = await api.getTextOverlay()
    if (res.code === 200 && res.data) {
      Object.assign(form, res.data)
    }
  } catch (error) {
    console.error('获取设置失败:', error)
    ElMessage.error('获取设置失败')
  } finally {
    loading.value = false
  }
}

// 保存设置
async function saveSettings() {
  saving.value = true
  try {
    const res = await api.saveTextOverlay(form)
    if (res.code === 200) {
      ElMessage.success('保存成功')
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

// 获取字体列表
async function fetchFonts() {
  try {
    const res = await api.getFonts()
    if (res.code === 200 && res.data) {
      fontList.value = res.data.list || []
      // 加载所有字体
      for (const font of fontList.value) {
        await loadFont(font)
      }
    }
  } catch (error) {
    console.error('获取字体列表失败:', error)
  }
}

// 加载字体到页面
async function loadFont(font) {
  const fontFamily = `font_${font.id}`
  if (loadedFonts.has(font.id)) return fontFamily
  
  try {
    // 如果URL是完整URL直接使用，否则拼接
    const fontUrl = font.url.startsWith('http') ? font.url : `/api${font.url}`
    const fontFace = new FontFace(fontFamily, `url(${fontUrl})`)
    await fontFace.load()
    document.fonts.add(fontFace)
    loadedFonts.set(font.id, fontFamily)
    console.log(`字体 ${font.name} 加载成功`)
  } catch (error) {
    console.error(`字体 ${font.name} 加载失败:`, error)
  }
  return fontFamily
}

// 获取当前字体的 fontFamily
const currentFontFamily = computed(() => {
  if (form.fontId === 0) return 'inherit'
  return loadedFonts.get(form.fontId) || 'inherit'
})

// 预览文字样式
const previewTextStyle = computed(() => ({
  color: form.textColor || '#ffffff',
  fontSize: `${form.fontSize || 24}px`,
  fontFamily: currentFontFamily.value !== 'inherit' ? `"${currentFontFamily.value}", sans-serif` : 'inherit'
}))

// 预览背景样式
const previewOverlayStyle = computed(() => ({
  backgroundColor: form.bgColor || 'rgba(0, 0, 0, 0.7)'
}))

onMounted(() => {
  fetchSettings()
  fetchFonts()
})
</script>

<style scoped>
.text-overlay-setting {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-tip {
  font-size: 12px;
  color: #909399;
}

.setting-form {
  max-width: 600px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-left: 12px;
}

.color-preview {
  margin-left: 16px;
  font-weight: 500;
}

.bg-preview {
  margin-left: 16px;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
}

.preview-container {
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  padding: 16px;
  background: #f5f7fa;
}

.preview-image {
  position: relative;
  width: 400px;
  max-width: 100%;
  border-radius: 4px;
  overflow: visible;
}

.preview-placeholder {
  width: 100%;
  height: 200px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.preview-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  text-align: left;
  min-height: 50px;
  display: flex;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.7); /* 默认背景，会被内联样式覆盖 */
}

.preview-overlay span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
</style>
