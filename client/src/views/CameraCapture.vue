<template>
  <div class="camera-capture-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <img v-if="brandLogo" :src="brandLogo" class="brand-logo" alt="Logo" />
        <el-select v-model="selectedCamera" placeholder="选择相机" @change="switchCamera" class="camera-select">
          <el-option
            v-for="camera in cameraList"
            :key="camera.deviceId"
            :label="camera.label || `相机 ${camera.deviceId.slice(0, 8)}`"
            :value="camera.deviceId"
          />
        </el-select>
        <el-button @click="refreshCameras" :icon="Refresh" circle title="刷新相机列表" />
      </div>
      <div class="toolbar-right">
        <!-- 合成模式选择（多个提示词时显示） -->
        <el-select 
          v-if="promptModes.length > 1" 
          v-model="selectedPromptIndex" 
          placeholder="合成模式"
          class="mode-select"
        >
          <el-option
            v-for="(mode, index) in promptModes"
            :key="index"
            :label="mode.name"
            :value="index"
          />
        </el-select>
        <el-button @click="showBeautyPanel = !showBeautyPanel" :type="showBeautyPanel ? 'warning' : 'default'">
          <el-icon><Sunny /></el-icon>
          美颜
        </el-button>
        <el-button @click="showFilterPanel = !showFilterPanel" :type="showFilterPanel ? 'warning' : 'default'">
          <el-icon><MagicStick /></el-icon>
          滤镜
        </el-button>
        <el-button type="primary" @click="showBackgroundDialog = true">
          <el-icon><PictureFilled /></el-icon>
          选择背景
        </el-button>
      </div>
    </div>

    <!-- 遮罩层 - 点击关闭面板 -->
    <div 
      v-if="showBeautyPanel || showFilterPanel" 
      class="panel-overlay" 
      @click="closeAllPanels"
    ></div>

    <!-- 美颜控制面板 -->
    <transition name="slide">
      <div v-if="showBeautyPanel" class="beauty-panel">
        <div class="panel-header">
          <span class="panel-title">美颜设置</span>
          <el-button size="small" circle :icon="Close" @click="showBeautyPanel = false" />
        </div>
        <div class="beauty-item">
          <span>磨皮</span>
          <el-slider v-model="beautySettings.smooth" :min="0" :max="10" :step="1" />
        </div>
        <div class="beauty-item">
          <span>美白</span>
          <el-slider v-model="beautySettings.whitening" :min="0" :max="10" :step="1" />
        </div>
        <div class="beauty-item">
          <span>亮度</span>
          <el-slider v-model="beautySettings.brightness" :min="-5" :max="5" :step="1" />
        </div>
        <div class="beauty-item">
          <span>对比度</span>
          <el-slider v-model="beautySettings.contrast" :min="-5" :max="5" :step="1" />
        </div>
        <el-button size="small" @click="resetBeauty">重置</el-button>
      </div>
    </transition>

    <!-- 滤镜选择面板 -->
    <transition name="slide">
      <div v-if="showFilterPanel" class="filter-panel">
        <div class="panel-header">
          <span class="panel-title">滤镜效果</span>
          <el-button size="small" circle :icon="Close" @click="showFilterPanel = false" />
        </div>
        <div class="filter-grid">
          <div 
            v-for="filter in filters" 
            :key="filter.id"
            class="filter-item"
            :class="{ active: currentFilter === filter.id }"
            @click="currentFilter = filter.id"
          >
            <div class="filter-preview" :style="{ filter: filter.style }"></div>
            <span>{{ filter.name }}</span>
          </div>
        </div>
      </div>
    </transition>


    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 相机预览区 -->
      <div class="camera-section">
        <div class="camera-container" ref="previewContainerRef">
          <video 
            ref="videoRef" 
            autoplay 
            playsinline 
            class="camera-video" 
            :class="{ hidden: capturedImage || compositeResult }"
            :style="{ filter: videoFilterStyle }"
          ></video>
          <!-- 拍照结果或 AI 合成结果 -->
          <img v-if="compositeResult" :src="compositeResult" class="captured-preview" />
          <img v-else-if="capturedImage" :src="capturedImage" class="captured-preview" />
          <!-- 底部文字描述条 -->
          <div 
            v-if="textSettings.enabled && textSettings.content" 
            class="text-overlay"
            :style="textOverlayBgStyle"
          >
            <img v-if="brandLogo" :src="brandLogo" class="text-overlay-logo" />
            <span :style="textOverlayTextStyle">{{ textSettings.content }}</span>
          </div>
          <!-- 倒计时遮罩 -->
          <div v-if="countdown > 0" class="countdown-overlay">
            <div class="countdown-number">{{ countdown }}</div>
            <div class="countdown-tip">请调整姿势...</div>
          </div>
          <div v-if="!cameraReady && !capturedImage && !compositeResult" class="camera-loading">
            <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
            <p>正在连接相机...</p>
          </div>
        </div>
        
        <!-- 控制按钮 -->
        <div class="capture-controls">
          <!-- 未拍照：显示拍照按钮 -->
          <el-button 
            v-if="!capturedImage && !compositeResult" 
            type="danger" 
            size="large" 
            circle 
            class="capture-btn"
            @click="startCountdown"
            :disabled="!cameraReady || countdown > 0"
          >
            <el-icon :size="32"><Camera /></el-icon>
          </el-button>
          
          <!-- 已拍照未合成：显示重拍和合成按钮 -->
          <template v-else-if="capturedImage && !compositeResult">
            <el-button type="info" size="large" @click="retakePhoto" :disabled="generating">
              <el-icon><RefreshLeft /></el-icon>
              重新拍照
            </el-button>
            <el-button type="primary" size="large" @click="generateComposite" :loading="generating">
              <el-icon><MagicStick /></el-icon>
              {{ generating ? compositeStatus || '合成中...' : 'AI合成' }}
            </el-button>
          </template>
          
          <!-- 已合成：显示重拍、下载、保存按钮 -->
          <template v-else-if="compositeResult">
            <el-button type="info" size="large" @click="retakePhoto" :disabled="saving">
              <el-icon><RefreshLeft /></el-icon>
              重新拍照
            </el-button>
            <el-button type="primary" size="large" @click="downloadResult" :disabled="saving">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button type="success" size="large" @click="saveToAlbum" :loading="saving">
              <el-icon><FolderAdd /></el-icon>
              {{ saving ? '保存中...' : '保存并扫码' }}
            </el-button>
          </template>
        </div>
      </div>

      <!-- 背景预览区 -->
      <div class="background-section">
        <h3>当前背景</h3>
        <div class="background-preview">
          <img v-if="selectedBackground" :src="selectedBackground.url" alt="背景" />
          <div v-else class="no-background">
            <el-icon :size="48"><PictureFilled /></el-icon>
            <p>未选择背景</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 背景选择对话框 -->
    <el-dialog v-model="showBackgroundDialog" title="选择背景" width="800px">
      <div v-loading="loadingBackgrounds">
        <el-empty v-if="presetBackgrounds.length === 0 && !loadingBackgrounds" description="暂无背景图，请联系管理员上传" />
        <div v-else class="background-grid">
          <div 
            v-for="bg in presetBackgrounds" 
            :key="bg.id" 
            class="background-item"
            :class="{ selected: tempSelectedBackground?.id === bg.id }"
            @click="selectBackground(bg)"
          >
            <img :src="bg.url" :alt="bg.name" />
            <span class="bg-name">{{ bg.name }}</span>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showBackgroundDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmBackground">确认</el-button>
      </template>
    </el-dialog>

    <!-- 隐藏的canvas用于拍照 -->
    <canvas ref="canvasRef" style="display: none;"></canvas>
    
    <!-- 下载二维码弹窗 -->
    <el-dialog 
      v-model="showQrCodeDialog" 
      title="扫码下载照片" 
      width="400px"
      center
      :close-on-click-modal="false"
    >
      <div class="qr-code-container">
        <p class="qr-tip">请使用手机（微信）扫描下方二维码，长按图片即可保存</p>
        <div class="qr-code-wrapper">
          <QrcodeVue :value="downloadQrUrl" :size="200" level="H" />
        </div>
        <p class="download-url">{{ downloadQrUrl }}</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="showQrCodeDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Camera, Refresh, PictureFilled, Loading, RefreshLeft, 
  MagicStick, Download, FolderAdd, Sunny, Close, EditPen, Setting, InfoFilled 
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { generateAIComposite, savePhoto, getBackgrounds, getFonts, getLogo, getReference, getTextOverlay, getPrompts, uploadToTos, sharePhoto } from '@/api/photo'
import { getServerUrl } from '@/config'
import QrcodeVue from 'qrcode.vue'
import html2canvas from 'html2canvas'

// 路由
const router = useRouter()

// 跳转设置页
function goToSettings() {
  router.push('/settings')
}

// 品牌 Logo
const brandLogo = ref(null)

// 合成参考图
const referenceImage = ref(null)

// 提示词模式列表
const promptModes = ref([])
const selectedPromptIndex = ref(0)

// 下载二维码
const showQrCodeDialog = ref(false)
const downloadQrUrl = ref('')

// 相机相关
const videoRef = ref(null)
const canvasRef = ref(null)
const previewContainerRef = ref(null)
const cameraList = ref([])
const selectedCamera = ref('')
const cameraReady = ref(false)
let mediaStream = null

// 拍照相关
const capturedImage = ref(null)
const countdown = ref(0)
let countdownTimer = null

// 美颜设置
const showBeautyPanel = ref(false)
const beautySettings = reactive({
  smooth: 0,      // 磨皮 0-10
  whitening: 0,   // 美白 0-10
  brightness: 0,  // 亮度 -5 to 5
  contrast: 0     // 对比度 -5 to 5
})

// 滤镜设置
const showFilterPanel = ref(false)
const currentFilter = ref('none')
const filters = [
  { id: 'none', name: '原图', style: 'none' },
  { id: 'bw', name: '黑白', style: 'grayscale(100%)' },
  { id: 'vintage', name: '复古', style: 'sepia(80%)' },
  { id: 'fresh', name: '清新', style: 'saturate(130%) brightness(105%)' },
  { id: 'warm', name: '暖色', style: 'sepia(30%) saturate(120%)' },
  { id: 'cold', name: '冷色', style: 'saturate(80%) hue-rotate(20deg)' },
  { id: 'vivid', name: '鲜艳', style: 'saturate(150%) contrast(110%)' },
  { id: 'soft', name: '柔和', style: 'contrast(90%) brightness(105%)' },
  { id: 'film', name: '胶片', style: 'sepia(20%) contrast(110%) saturate(90%)' }
]

// 计算美颜+滤镜的综合样式
const videoFilterStyle = computed(() => {
  const parts = []
  
  // 美颜效果
  if (beautySettings.smooth > 0) {
    parts.push(`blur(${beautySettings.smooth * 0.15}px)`)
  }
  if (beautySettings.whitening !== 0) {
    parts.push(`brightness(${100 + beautySettings.whitening * 5}%)`)
  }
  if (beautySettings.brightness !== 0) {
    const brightnessValue = 100 + beautySettings.brightness * 8
    // 如果已经有 whitening 的 brightness，需要叠加
    if (beautySettings.whitening === 0) {
      parts.push(`brightness(${brightnessValue}%)`)
    }
  }
  if (beautySettings.contrast !== 0) {
    parts.push(`contrast(${100 + beautySettings.contrast * 10}%)`)
  }
  
  // 滤镜效果
  const selectedFilter = filters.find(f => f.id === currentFilter.value)
  if (selectedFilter && selectedFilter.style !== 'none') {
    parts.push(selectedFilter.style)
  }
  
  return parts.length > 0 ? parts.join(' ') : 'none'
})

// 重置美颜设置
function resetBeauty() {
  beautySettings.smooth = 0
  beautySettings.whitening = 0
  beautySettings.brightness = 0
  beautySettings.contrast = 0
}

// 关闭所有面板
function closeAllPanels() {
  showBeautyPanel.value = false
  showFilterPanel.value = false
  showTextPanel.value = false
}

// 文字描述设置
const showTextPanel = ref(false)
const textSettings = reactive({
  enabled: false,
  content: '',
  fontId: 0,
  fontSize: 24,
  textColor: '#ffffff',
  bgColor: 'rgba(0, 0, 0, 0.7)'
})

// 字体列表
const fontList = ref([])
const loadedFontFaces = new Map() // fontId -> FontFace

// 加载字体到页面（使用 FontFace API）
async function loadFont(font) {
  const fontFamily = `font_${font.id}`
  
  if (loadedFontFaces.has(font.id)) {
    return fontFamily
  }
  
  try {
    // 如果URL已经是完整URL则直接使用，否则拼接服务器地址
    const fontUrl = font.url.startsWith('http') ? font.url : `${getServerUrl()}${font.url}`
    const fontFace = new FontFace(fontFamily, `url(${fontUrl})`)
    await fontFace.load()
    document.fonts.add(fontFace)
    loadedFontFaces.set(font.id, fontFace)
    console.log(`字体 ${font.name} 加载成功`)
  } catch (error) {
    console.error(`字体 ${font.name} 加载失败:`, error)
  }
  
  return fontFamily
}

// 获取字体列表
async function fetchFonts() {
  try {
    const result = await getFonts()
    if (result.code === 200 && result.data) {
      // 并行加载所有字体
      const fontsWithFamily = await Promise.all(
        result.data.map(async font => ({
          ...font,
          fontFamily: await loadFont(font)
        }))
      )
      fontList.value = fontsWithFamily
    }
  } catch (error) {
    console.error('获取字体列表失败:', error)
  }
}

// 获取当前选中字体的 fontFamily
const currentFontFamily = computed(() => {
  if (textSettings.fontId === 0) return 'inherit'
  const font = fontList.value.find(f => f.id === textSettings.fontId)
  return font ? font.fontFamily : 'inherit'
})

// 获取当前选中字体的名称（用于显示）
const currentFontName = computed(() => {
  if (textSettings.fontId === 0) return '默认字体'
  const font = fontList.value.find(f => f.id === textSettings.fontId)
  return font ? font.name : '默认字体'
})

// 文字描述条背景样式
const textOverlayBgStyle = computed(() => ({
  backgroundColor: textSettings.bgColor || 'rgba(0, 0, 0, 0.7)'
}))

// 文字描述条文字样式
const textOverlayTextStyle = computed(() => {
  const fontFamily = currentFontFamily.value === 'inherit' 
    ? 'inherit' 
    : `"${currentFontFamily.value}", sans-serif`
  return {
    fontFamily,
    fontSize: `${textSettings.fontSize || 24}px`,
    color: textSettings.textColor || '#ffffff'
  }
})

// 背景相关
const showBackgroundDialog = ref(false)
const selectedBackground = ref(null)
const tempSelectedBackground = ref(null)

// 预设背景列表（从后端获取）
const presetBackgrounds = ref([])
const loadingBackgrounds = ref(false)

// 获取背景列表
async function fetchBackgrounds() {
  loadingBackgrounds.value = true
  try {
    const result = await getBackgrounds()
    if (result.code === 200 && result.data) {
      // 转换 URL 为完整路径（如果已经是完整URL则不拼接）
      presetBackgrounds.value = result.data.map(bg => ({
        ...bg,
        url: bg.url.startsWith('http') ? bg.url : `${getServerUrl()}${bg.url}`
      }))
    }
  } catch (error) {
    console.error('获取背景列表失败:', error)
  } finally {
    loadingBackgrounds.value = false
  }
}

// AI合成相关
const generating = ref(false)
const compositeResult = ref(null)

// 获取相机列表
async function getCameraList() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    cameraList.value = devices.filter(device => device.kind === 'videoinput')
    
    if (cameraList.value.length > 0 && !selectedCamera.value) {
      selectedCamera.value = cameraList.value[0].deviceId
    }
  } catch (error) {
    console.error('获取相机列表失败:', error)
    ElMessage.error('获取相机列表失败')
  }
}

// 刷新相机列表
async function refreshCameras() {
  await getCameraList()
  ElMessage.success('相机列表已刷新')
}

// 启动相机
async function startCamera(deviceId) {
  try {
    // 先停止之前的流
    stopCamera()
    
    const constraints = {
      video: {
        deviceId: deviceId ? { exact: deviceId } : undefined,
        width: { ideal: 1920 },
        height: { ideal: 1080 },
        facingMode: 'user'
      }
    }
    
    mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
    
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      videoRef.value.onloadedmetadata = () => {
        cameraReady.value = true
      }
    }
  } catch (error) {
    console.error('启动相机失败:', error)
    ElMessage.error('无法访问相机，请检查权限设置')
  }
}

// 停止相机
function stopCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  cameraReady.value = false
}

// 切换相机
function switchCamera(deviceId) {
  startCamera(deviceId)
}

// Logo 图片对象（用于 canvas 绘制）
let logoImage = null

// 加载 Logo 图片
function loadLogoImage(url) {
  return new Promise((resolve) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => resolve(img)
    img.onerror = () => resolve(null)
    img.src = url
  })
}

// 倒计时拍照
function startCountdown() {
  if (countdown.value > 0) return
  ElMessage.info('5秒后自动拍照，请调整姿势')
  countdown.value = 5
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
      capturePhoto()
    }
  }, 1000)
}

// 拍照（应用美颜和滤镜效果）
async function capturePhoto() {
  if (!videoRef.value || !canvasRef.value) return
  
  const video = videoRef.value
  const canvas = canvasRef.value
  
  // 计算底部文字条高度
  const textBarHeight = textSettings.enabled && textSettings.content ? textSettings.fontSize + 24 : 0
  
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight + textBarHeight
  
  const ctx = canvas.getContext('2d')
  
  // 应用滤镜效果到 canvas
  ctx.filter = videoFilterStyle.value
  ctx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight)
  ctx.filter = 'none' // 重置
  
  // 绘制底部文字条
  if (textSettings.enabled && textSettings.content) {
    // 绘制背景条
    ctx.fillStyle = textSettings.bgColor
    ctx.fillRect(0, video.videoHeight, canvas.width, textBarHeight)
    
    const padding = 16
    let textX = padding
    
    // 绘制 Logo（如果有）
    if (brandLogo.value) {
      if (!logoImage) {
        logoImage = await loadLogoImage(brandLogo.value)
      }
      if (logoImage) {
        const logoHeight = textBarHeight - 8
        const logoWidth = logoImage.width * (logoHeight / logoImage.height)
        ctx.drawImage(logoImage, padding, video.videoHeight + 4, logoWidth, logoHeight)
        textX = padding + logoWidth + 12
      }
    }
    
    // 绘制文字（左对齐）
    ctx.fillStyle = textSettings.textColor
    const fontName = currentFontFamily.value === 'inherit' ? 'sans-serif' : `"${currentFontFamily.value}"`
    ctx.font = `${textSettings.fontSize}px ${fontName}`
    ctx.textAlign = 'left'
    ctx.textBaseline = 'middle'
    ctx.fillText(textSettings.content, textX, video.videoHeight + textBarHeight / 2)
  }
  
  capturedImage.value = canvas.toDataURL('image/jpeg', 0.95)
  ElMessage.success('拍照成功')
}

// 重新拍照
function retakePhoto() {
  capturedImage.value = null
  compositeResult.value = null
}

// 选择背景
function selectBackground(bg) {
  tempSelectedBackground.value = bg
}

// 确认背景选择
function confirmBackground() {
  if (tempSelectedBackground.value) {
    selectedBackground.value = tempSelectedBackground.value
  }
  showBackgroundDialog.value = false
}

// AI 合成状态
const compositeStatus = ref('')

// AI合成（使用豆包 Doubao API）
async function generateComposite() {
  if (!capturedImage.value) {
    ElMessage.warning('请先拍照')
    return
  }
  if (!selectedBackground.value) {
    ElMessage.warning('请先选择背景')
    return
  }
  
  generating.value = true
  compositeStatus.value = '正在上传人像照片...'
  
  try {
    // 1. 将人像照片（拍照的 base64）上传到 TOS 获取公网 URL
    const photoUrl = await uploadToTos(capturedImage.value, `portrait_${Date.now()}.jpg`)
    console.log('人像照片上传成功:', photoUrl)
    
    compositeStatus.value = '正在调用 AI 合成...'
    
    // 2. 构建合成参数
    // photo: 人像照片（图1）
    // background: 背景图片（图2）
    const params = {
      photo: photoUrl,
      background: selectedBackground.value.url
    }
    
    // 添加参考图参数（如果有）
    if (referenceImage.value) {
      params.reference = referenceImage.value
    }
    
    // 添加选中的提示词（如果有模式可选）
    if (promptModes.value.length > 0 && promptModes.value[selectedPromptIndex.value]) {
      params.prompt = promptModes.value[selectedPromptIndex.value].content
    }
    
    // 3. 调用后端 Doubao API 进行合成
    const result = await generateAIComposite(params)
    
    if (result.code === 200 && result.data.compositeImage) {
      compositeResult.value = result.data.compositeImage
      compositeStatus.value = ''
      // 显示剩余次数
      if (result.data.ai_remaining !== null && result.data.ai_remaining !== undefined) {
        ElMessage.success(`AI 合成完成！剩余次数: ${result.data.ai_remaining}`)
      } else {
        ElMessage.success('AI 合成完成！')
      }
    } else if (result.code === 403) {
      // 配额不足
      ElMessage.error(result.message || '您的 AI 生成次数已用完，请联系管理员充值')
      compositeStatus.value = ''
    } else {
      throw new Error(result.message || '合成失败')
    }
  } catch (error) {
    console.error('AI合成失败:', error)
    // 检查是否是配额不足错误
    if (error.message && error.message.includes('次数已用完')) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error(`AI合成失败: ${error.message}`)
    }
    compositeStatus.value = ''
  } finally {
    generating.value = false
  }
}

// 截图 camera-container 容器（包含文字描述）
// 使用 Canvas 手动绘制，确保跨域图片和文字都能正确渲染
async function captureContainerAsImage() {
  if (!compositeResult.value) {
    throw new Error('没有合成图片')
  }
  
  // 直接使用 Canvas 绘制方案，更加可靠
  return await addTextOverlayToImage(compositeResult.value)
}

// 下载结果（截图整个容器，包含文字描述）
async function downloadResult() {
  if (!compositeResult.value) return
  
  try {
    ElMessage.info('正在生成图片...')
    
    // 截图整个容器（包含文字描述）
    const finalImage = await captureContainerAsImage()
    
    const link = document.createElement('a')
    link.download = `composite_${Date.now()}.jpg`
    link.href = finalImage
    link.click()
    
    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

// 在图片上绘制文字描述
async function addTextOverlayToImage(imageUrl) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = async () => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      
      // 计算缩放比例（基于图片实际尺寸）
      const scale = img.width / 800 // 以800px为基准
      const padding = Math.round(20 * scale)
      // 使用后端设置的字体大小，并根据图片尺寸缩放
      const fontSize = Math.round((textSettings.fontSize || 24) * scale)
      const barHeight = fontSize + padding * 2
      
      // 如果有文字描述，增加画布高度
      const extraHeight = (textSettings.enabled && textSettings.content) ? barHeight : 0
      canvas.width = img.width
      canvas.height = img.height + extraHeight
      
      // 填充黑色背景
      ctx.fillStyle = '#000'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      
      // 绘制原图
      ctx.drawImage(img, 0, 0)
      
      // 如果有文字描述，绘制到底部
      if (textSettings.enabled && textSettings.content) {
        // 绘制背景条
        ctx.fillStyle = textSettings.bgColor || 'rgba(0, 0, 0, 0.7)'
        ctx.fillRect(0, img.height, img.width, barHeight)
        
        // 获取字体样式
        const fontFamily = textSettings.fontId && loadedFontFaces.has(textSettings.fontId) 
          ? `font_${textSettings.fontId}` 
          : 'sans-serif'
        
        // 绘制文字的辅助函数
        const drawText = (logoWidth = 0) => {
          ctx.font = `${fontSize}px "${fontFamily}"`
          ctx.fillStyle = textSettings.textColor || '#ffffff'
          ctx.textBaseline = 'middle'
          const textX = padding + logoWidth + (logoWidth > 0 ? 10 * scale : 0)
          ctx.fillText(textSettings.content, textX, img.height + barHeight / 2)
          resolve(canvas.toDataURL('image/jpeg', 0.95))
        }
        
        // 绘制 Logo（如果有）
        if (brandLogo.value) {
          const logoImg = new Image()
          logoImg.crossOrigin = 'anonymous'
          logoImg.onload = () => {
            const logoHeight = barHeight - padding
            const logoWidth = logoHeight * (logoImg.width / logoImg.height)
            ctx.drawImage(logoImg, padding, img.height + padding / 2, logoWidth, logoHeight)
            drawText(logoWidth)
          }
          logoImg.onerror = () => drawText(0)
          logoImg.src = brandLogo.value
        } else {
          drawText(0)
        }
      } else {
        resolve(canvas.toDataURL('image/jpeg', 0.95))
      }
    }
    img.onerror = () => reject(new Error('图片加载失败'))
    img.src = imageUrl
  })
}

// 保存状态
const saving = ref(false)

// 保存到服务器并显示下载二维码
async function saveToAlbum() {
  if (!compositeResult.value) return
  
  saving.value = true
  try {
    ElMessage.info('正在生成分享链接...')
    
    // 截图整个容器（包含文字描述）
    const finalImage = await captureContainerAsImage()
    
    // 上传到自己服务器生成站内分享链接（微信内可直接打开，不再依赖 OSS/TOS 直链）
    const result = await sharePhoto(finalImage)
    if (result.code !== 200 || !result.data?.sharePath) {
      throw new Error(result.message || '保存失败')
    }
    
    // 二维码指向自己服务器的分享页（页面内嵌 base64 图片，长按即可保存）
    downloadQrUrl.value = `${getServerUrl()}${result.data.sharePath}`
    showQrCodeDialog.value = true
    ElMessage.success('保存成功，请扫码下载')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(`保存失败：${error.message || '请重试'}`)
  } finally {
    saving.value = false
  }
}

// 获取品牌 Logo
async function fetchLogo() {
  try {
    const result = await getLogo()
    if (result.code === 200 && result.data.url) {
      // 如果URL已经是完整URL则直接使用，否则拼接服务器地址
      const url = result.data.url
      brandLogo.value = url.startsWith('http') ? url : `${getServerUrl()}${url}`
    }
  } catch (error) {
    console.error('获取 Logo 失败:', error)
  }
}

// 获取参考图
async function fetchReference() {
  try {
    const result = await getReference()
    if (result.code === 200 && result.data.url) {
      // 如果URL已经是完整URL则直接使用，否则拼接服务器地址
      const url = result.data.url
      referenceImage.value = url.startsWith('http') ? url : `${getServerUrl()}${url}`
    }
  } catch (error) {
    console.error('获取参考图失败:', error)
  }
}

// 获取文字描述设置（由后端管理控制）
async function fetchTextOverlay() {
  try {
    const result = await getTextOverlay()
    if (result.code === 200 && result.data) {
      // 直接应用后端的设置
      textSettings.enabled = result.data.enabled
      textSettings.content = result.data.content || ''
      textSettings.fontId = result.data.fontId || 0
      textSettings.fontSize = result.data.fontSize || 24
      textSettings.textColor = result.data.textColor || '#ffffff'
      textSettings.bgColor = result.data.bgColor || 'rgba(0, 0, 0, 0.7)'
    }
  } catch (error) {
    console.error('获取文字描述设置失败:', error)
  }
}

// 获取提示词模式列表
async function fetchPrompts() {
  try {
    const result = await getPrompts()
    if (result.code === 200 && result.data && result.data.length > 0) {
      promptModes.value = result.data
      selectedPromptIndex.value = 0
    }
  } catch (error) {
    console.error('获取提示词模式失败:', error)
  }
}

onMounted(async () => {
  await getCameraList()
  if (selectedCamera.value) {
    startCamera(selectedCamera.value)
  }
  // 获取背景列表、字体列表、Logo、参考图、文字描述设置和提示词模式
  await Promise.all([fetchBackgrounds(), fetchFonts(), fetchLogo(), fetchReference(), fetchTextOverlay(), fetchPrompts()])
})

onUnmounted(() => {
  stopCamera()
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})
</script>

<style scoped>
.camera-capture-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1a1a2e;
  color: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #16213e;
  border-bottom: 1px solid #0f3460;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  height: 36px;
  max-width: 120px;
  object-fit: contain;
  margin-right: 8px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mode-select {
  width: 120px;
}

.mode-select :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.mode-select :deep(.el-input__inner) {
  color: #fff;
}

/* 遮罩层 */
.panel-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99;
}

/* 美颜面板 */
.beauty-panel {
  position: absolute;
  top: 70px;
  right: 20px;
  width: 280px;
  background: rgba(22, 33, 62, 0.95);
  border-radius: 12px;
  padding: 16px;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #e0e0e0;
}

.beauty-item {
  margin-bottom: 16px;
}

.beauty-item span {
  display: block;
  font-size: 12px;
  color: #aaa;
  margin-bottom: 8px;
}

/* 滤镜面板 */
.filter-panel {
  position: absolute;
  top: 70px;
  right: 20px;
  width: 320px;
  background: rgba(22, 33, 62, 0.95);
  border-radius: 12px;
  padding: 16px;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

/* 文字描述面板 */
.text-panel {
  position: absolute;
  top: 70px;
  right: 20px;
  width: 320px;
  background: rgba(22, 33, 62, 0.95);
  border-radius: 12px;
  padding: 16px;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.text-item {
  margin-bottom: 16px;
}

.text-item > span:first-child {
  display: block;
  font-size: 12px;
  color: #aaa;
  margin-bottom: 8px;
}

.text-content-preview {
  background: rgba(0, 0, 0, 0.3);
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  color: #e0e0e0;
}

.text-value {
  color: #e0e0e0;
  font-size: 14px;
}

.color-swatch {
  display: inline-block;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  vertical-align: middle;
}

.panel-tip {
  margin-top: 16px;
  padding: 12px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 底部文字叠加层 */
.text-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  pointer-events: none;
  z-index: 10;
}

.text-overlay-logo {
  height: 100%;
  max-height: 32px;
  width: auto;
  object-fit: contain;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.filter-item {
  cursor: pointer;
  text-align: center;
  transition: transform 0.2s;
}

.filter-item:hover {
  transform: scale(1.05);
}

.filter-item.active .filter-preview {
  border-color: #409eff;
}

.filter-preview {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  border: 3px solid transparent;
  background: linear-gradient(135deg, #f5af19, #f12711);
  margin-bottom: 6px;
}

.filter-item span {
  font-size: 12px;
  color: #aaa;
}

.filter-item.active span {
  color: #409eff;
}

/* 面板动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.camera-select {
  width: 280px;
}

.main-content {
  flex: 1;
  display: grid;
  grid-template-columns: 2fr 1fr;
  grid-template-rows: 1fr auto;
  gap: 20px;
  padding: 20px;
  overflow: auto;
}

.camera-section {
  grid-row: span 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.camera-container {
  position: relative;
  width: 100%;
  max-width: 800px;
  aspect-ratio: 16 / 9;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: relative;
  z-index: 1;
}

.camera-video.hidden {
  display: none;
}

.captured-preview {
  width: 100%;
  height: 100%;
  object-fit: contain;
  position: relative;
  z-index: 1;
}

.camera-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #888;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 倒计时遮罩 */
.countdown-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

.countdown-number {
  font-size: 120px;
  font-weight: bold;
  color: #fff;
  text-shadow: 0 0 30px rgba(255, 77, 77, 0.8);
  animation: countdown-pulse 1s ease-in-out infinite;
}

.countdown-tip {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.85);
  margin-top: 12px;
}

@keyframes countdown-pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.8; }
  100% { transform: scale(1); opacity: 1; }
}

.capture-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.capture-btn {
  width: 80px;
  height: 80px;
  box-shadow: 0 0 20px rgba(255, 77, 77, 0.5);
}

.background-section,
.result-section {
  background: #16213e;
  border-radius: 12px;
  padding: 16px;
}

.background-section h3,
.result-section h3 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #e0e0e0;
}

.background-preview,
.result-preview {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #0f3460;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.background-preview img,
.result-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-background {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #666;
}

.result-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

/* 背景选择对话框 */
.background-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.background-item {
  position: relative;
  aspect-ratio: 16 / 9;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 3px solid transparent;
  transition: all 0.3s;
}

.background-item:hover {
  transform: scale(1.02);
}

.background-item.selected {
  border-color: #409eff;
}

.background-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.background-item .bg-name {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  color: #fff;
  font-size: 12px;
  text-align: center;
}

.background-item .delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.background-item:hover .delete-btn {
  opacity: 1;
}

.background-uploader {
  width: 100%;
}

/* 深色主题调整 */
:deep(.el-select) {
  --el-fill-color-blank: #0f3460;
  --el-text-color-regular: #fff;
  --el-border-color: #0f3460;
}

:deep(.el-dialog) {
  background: #1a1a2e;
}

:deep(.el-dialog__header) {
  color: #fff;
}

:deep(.el-tabs__item) {
  color: #888;
}

:deep(.el-tabs__item.is-active) {
  color: #409eff;
}

/* 二维码弹窗样式 */
.qr-code-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.qr-tip {
  font-size: 16px;
  color: #606266;
  margin-bottom: 20px;
}

.qr-code-wrapper {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.download-url {
  font-size: 12px;
  color: #909399;
  word-break: break-all;
  text-align: center;
  max-width: 300px;
}
</style>
