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
        <!-- 合成模式选择（普通拍照下、多个提示词时显示） -->
        <el-select 
          v-if="selectedScene === 'normal' && promptModes.length > 1" 
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

          <!-- 当前背景缩略图（浮层，点击更换） -->
          <div
            v-if="!compositeResult"
            class="bg-thumb"
            :title="selectedBackground ? '更换背景' : '选择背景'"
            @click="openBackgroundDialog"
          >
            <img v-if="selectedBackground" :src="selectedBackground.url" alt="当前背景" />
            <div v-else class="bg-thumb-empty">
              <el-icon :size="20"><PictureFilled /></el-icon>
              <span>选择背景</span>
            </div>
            <span v-if="selectedBackground" class="bg-thumb-label">更换背景</span>
          </div>
        </div>
      </div>

      <!-- 底部操作栏：玩法 + 控制按钮 -->
      <div class="bottom-bar">
        <div class="scene-group">
          <div class="scene-options">
            <span class="scene-label">选择玩法</span>
            <el-button
              v-for="scene in sceneModes"
              :key="scene.id"
              :type="selectedScene === scene.id ? 'primary' : 'default'"
              size="large"
              class="scene-btn"
              :disabled="generating"
              @click="selectScene(scene.id)"
            >
              <el-icon><component :is="scene.icon" /></el-icon>
              {{ scene.name }}
            </el-button>
          </div>
          <div v-if="selectedScene === 'baby'" class="child-count">
            <span class="child-count-label">宝宝数量</span>
            <el-radio-group v-model="childCount" size="small">
              <el-radio-button :label="1">1 个</el-radio-button>
              <el-radio-button :label="2">2 个</el-radio-button>
            </el-radio-group>
          </div>
          <p class="scene-hint">{{ sceneHint }}</p>
        </div>

        <!-- 控制按钮 -->
        <div class="capture-controls">
          <!-- 未拍照：拍照按钮 -->
          <template v-if="!capturedImage && !compositeResult">
            <el-button 
              type="danger" 
              size="large" 
              circle 
              class="capture-btn"
              @click="startCountdown"
              :disabled="!cameraReady || countdown > 0"
            >
              <el-icon :size="32"><Camera /></el-icon>
            </el-button>
          </template>
          
          <!-- 已拍照未合成：重拍 + 生成 -->
          <template v-else-if="capturedImage && !compositeResult">
            <el-button type="info" size="large" @click="retakePhoto" :disabled="generating">
              <el-icon><RefreshLeft /></el-icon>
              重新拍照
            </el-button>
            <el-button type="primary" size="large" @click="generateComposite" :loading="generating">
              <el-icon><MagicStick /></el-icon>
              {{ generating ? compositeStatus || '合成中...' : generateBtnText }}
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
    </div>

    <!-- 背景选择对话框 -->
    <el-dialog
      v-model="showBackgroundDialog"
      title="选择背景"
      width="min(800px, 92vw)"
      top="5vh"
      class="background-dialog"
    >
      <div v-loading="loadingBackgrounds">
        <p class="bg-dialog-tip">点击图片选中，然后点击「使用此背景」；双击图片可直接应用</p>
        <el-empty v-if="backgroundLoadError && !loadingBackgrounds" description="背景加载失败，请检查网络后重试">
          <el-button type="primary" @click="fetchBackgrounds">重新加载</el-button>
        </el-empty>
        <el-empty v-else-if="presetBackgrounds.length === 0 && !loadingBackgrounds" description="暂无背景图，请联系管理员上传" />
        <div v-else class="background-grid">
          <div 
            v-for="bg in presetBackgrounds" 
            :key="bg.id" 
            class="background-item"
            :class="{ selected: tempSelectedBackground?.id === bg.id }"
            @click="selectBackground(bg)"
            @dblclick="applyBackground(bg)"
          >
            <img :src="bg.url" :alt="bg.name" />
            <span class="bg-name">{{ bg.name }}</span>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="bg-dialog-footer">
          <span class="bg-dialog-selected">
            {{ tempSelectedBackground ? `已选择：${tempSelectedBackground.name}` : '请点击图片选择背景' }}
          </span>
          <div class="bg-dialog-actions">
            <el-button @click="showBackgroundDialog = false">取消</el-button>
            <el-button type="primary" :disabled="!tempSelectedBackground" @click="confirmBackground">
              使用此背景
            </el-button>
          </div>
        </div>
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
  MagicStick, Download, FolderAdd, Sunny, Close, EditPen, Setting, InfoFilled,
  Avatar, Trophy
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { generateAIComposite, savePhoto, getBackgrounds, getFonts, getLogo, getReference, getTextOverlay, getPrompts, uploadToTos, sharePhoto } from '@/api/photo'
import { getServerUrl, getAssetUrl } from '@/config'
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

// 玩法模式内置提示词（后台「提示词模式」里如有同名模式则优先使用后台配置）
// 可选玩法（先选玩法再拍照）
const sceneModes = [
  { id: 'normal', name: '普通拍照', icon: Camera },
  { id: 'baby', name: '宝宝合照', icon: Avatar, aliases: ['宝宝合照', '生成宝宝', '有宝宝的照片', '宝宝', '宝宝照', '宝宝照片'] },
  { id: 'golden', name: '金婚纪念照', icon: Trophy, aliases: ['金婚纪念照', '金婚照', '金婚'] }
]

const selectedScene = ref('normal')
const childCount = ref(1)

const currentScene = computed(() =>
  sceneModes.find(scene => scene.id === selectedScene.value) || sceneModes[0]
)

// 生成按钮文案随玩法变化
const generateBtnText = computed(() => {
  if (selectedScene.value === 'baby') return '生成全家福'
  if (selectedScene.value === 'golden') return '生成金婚照'
  return 'AI合成'
})

// 玩法说明
const sceneHint = computed(() => {
  if (selectedScene.value === 'baby') {
    return '拍下两人的合照，选择宝宝数量，点击「生成全家福」，宝宝会和你们一起合影'
  }
  if (selectedScene.value === 'golden') {
    return '拍下两人的合照，点击「生成金婚照」，AI 会生成金婚纪念照'
  }
  return '拍照后点击「AI合成」，将人像与所选背景融合'
})

// 切换玩法
function selectScene(sceneId) {
  selectedScene.value = sceneId
}

// 查找后台同义提示词模式
function findAdminMode(scene) {
  const aliases = scene.aliases || [scene.name]
  return promptModes.value.find(
    mode => aliases.includes((mode.name || '').trim()) && (mode.content || '').trim()
  )
}

// 宝宝合照提示词（图1实际人物 + 1个或2个宝宝的全家福）
function buildBabyPrompt() {
  const countText = childCount.value === 2 ? '两个' : '一个'
  let prompt = `以图1中的人物为基础，保持每一位人物的面部特征、发型与身份不变。严格保持图1中的人物数量不变：图1中有几个人就只保留几个人，不要新增、补出或虚构任何人物；如果图1只有一个人，就只生成这位家长与宝宝的合影，不要补出另一位家长。根据人物的相貌推断他们未来孩子的长相，生成${countText}宝宝（约6-12个月大，宝宝性别自然即可，五官自然融合父母特征，皮肤细腻，表情可爱）。让${countText}宝宝与图1中的人物一起拍一张温馨的全家福合影，宝宝由家长抱着或围绕在身边，全家人表情自然幸福，构图完整，真实自然，高清摄影质感。`
  if (selectedBackground.value) {
    prompt += ' 将全家人自然融入图2的背景场景中，保持光线、透视与色调协调一致。'
  } else {
    prompt += ' 背景使用柔和的浅色室内影棚背景，光线自然。'
  }
  return prompt
}

// 人物数量保护：不允许凭空补人
const NO_EXTRA_PERSON_GUARD = '严格保持图1中的人物数量不变：图1中有几个人就只生成几个人，不要新增、补出或虚构任何人物，只有一个人时不要补出伴侣。'

function ensureNoExtraPerson(prompt, extraTip = '') {
  if (/人物数量|不要新增|不要补出|不要虚构|单人金婚|另一位家长/.test(prompt)) {
    return prompt
  }
  return `${prompt} ${NO_EXTRA_PERSON_GUARD}${extraTip}`
}

// 给提示词补充背景融合要求（避免重复）
function withBackgroundHint(prompt) {
  if (selectedBackground.value && !/图\s*2|背景/.test(prompt)) {
    return `${prompt} 将人物自然融入图2的背景场景中，保持光线、透视与色调协调一致。`
  }
  return prompt
}

// 获取当前玩法的提示词（后台同名/同义模式 > 内置默认）
function resolveScenePrompt(scene) {
  if (!scene || scene.id === 'normal') return null

  const adminMode = findAdminMode(scene)
  if (adminMode) {
    const adminContent = adminMode.content.trim()
    const mentionsBackground = /图\s*2|背景/.test(adminContent)
    const hasBackground = !!selectedBackground.value

    if (scene.id === 'baby') {
      // 后台支持 {count} / {宝宝数量} 占位符，替换为用户选择的宝宝数量
      if (/\{count\}|\{宝宝数量\}/.test(adminContent)) {
        const prompt = adminContent.replace(/\{count\}|\{宝宝数量\}/g, String(childCount.value))
        return ensureNoExtraPerson(
          withBackgroundHint(prompt),
          ' 如果图1只有一个人，不要补出另一位家长。'
        )
      }
      // 旧版后台提示词固定写死"一个男孩/一个宝宝"，无法满足1/2个宝宝选择，改用内置提示词
      if (/一位男孩|一个男孩|一个宝宝/.test(adminContent)) {
        return buildBabyPrompt()
      }
      if (!mentionsBackground || hasBackground) {
        return ensureNoExtraPerson(
          withBackgroundHint(`${adminContent} 本次生成${childCount.value}个宝宝，并与图1中的人物一起合影。`),
          ' 如果图1只有一个人，不要补出另一位家长。'
        )
      }
      return buildBabyPrompt()
    }

    // 金婚纪念照
    if (!mentionsBackground || hasBackground) {
      return ensureNoExtraPerson(withBackgroundHint(adminContent))
    }
  }

  // 内置金婚照提示词
  if (scene.id === 'golden') {
    let prompt = '将图1中的人物转换为结婚50周年金婚纪念照：保持每一位人物的面部特征与身份不变，年龄自然变为70-80岁，头发花白、精神矍铄，身穿端庄的中式金婚礼服，面带幸福微笑，姿态自然。严格保持图1中的人物数量不变：图1中有几个人就只生成几个人，不要新增、补出或虚构任何人物；只有一个人时，就只生成这一个人的单人金婚纪念照，不要补出伴侣。'
    if (selectedBackground.value) {
      prompt += ' 将图1中的人物自然融入图2的背景场景中，保持光线、透视与色调协调一致。'
    } else {
      prompt += ' 背景使用温馨的暖色调中式厅堂或影棚背景，高清摄影质感。'
    }
    return prompt
  }

  return buildBabyPrompt()
}


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
    // 相对路径拼服务器地址；TOS 地址走服务器代理
    const fontUrl = getAssetUrl(font.url)
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

// 获取字体列表（只加载文字描述当前使用的字体，避免一次下载所有字体）
async function fetchFonts() {
  try {
    const result = await getFonts()
    if (result.code === 200 && result.data) {
      const selected = result.data.find(font => font.id === textSettings.fontId)
      fontList.value = selected
        ? [{ ...selected, fontFamily: await loadFont(selected) }]
        : []
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
const backgroundLoadError = ref(false)

// 获取背景列表
async function fetchBackgrounds() {
  loadingBackgrounds.value = true
  backgroundLoadError.value = false
  try {
    const result = await getBackgrounds()
    if (result.code === 200 && result.data) {
      // 缩略图走服务器代理（600px），AI 合成时使用原始地址
      presetBackgrounds.value = result.data.map(bg => ({
        ...bg,
        rawUrl: bg.url,
        url: getAssetUrl(bg.url, { width: 600 })
      }))
    } else {
      backgroundLoadError.value = true
    }
  } catch (error) {
    console.error('获取背景列表失败:', error)
    backgroundLoadError.value = true
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

// 打开背景选择（回显当前背景）
function openBackgroundDialog() {
  tempSelectedBackground.value = selectedBackground.value
  showBackgroundDialog.value = true
  // 之前加载失败或列表为空时，打开弹窗自动重试一次
  if (presetBackgrounds.value.length === 0 && !loadingBackgrounds.value) {
    fetchBackgrounds()
  }
}

// 选择背景
function selectBackground(bg) {
  tempSelectedBackground.value = bg
}

// 双击直接应用背景
function applyBackground(bg) {
  tempSelectedBackground.value = bg
  confirmBackground()
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

  // 设备断网时直接提示
  if (!navigator.onLine) {
    window.dispatchEvent(new Event('app-network-device-offline'))
    ElMessage.error('设备未联网，请联网后重试')
    return
  }

  const isSceneMode = selectedScene.value !== 'normal'
  const doneLabel = isSceneMode ? `「${generateBtnText.value.replace(/^生成/, '')}」` : 'AI 合成'

  // 普通拍照需要背景；宝宝/金婚照模式背景可选
  if (!isSceneMode && !selectedBackground.value) {
    ElMessage.warning('请先选择背景')
    return
  }
  
  generating.value = true
  compositeStatus.value = '正在上传人像照片...'
  
  try {
    // 1. 将人像照片（拍照的 base64）上传到 TOS 获取公网 URL
    const photoUrl = await uploadToTos(capturedImage.value, `portrait_${Date.now()}.jpg`)
    console.log('人像照片上传成功:', photoUrl)
    
    compositeStatus.value = isSceneMode
      ? `正在生成${currentScene.value.id === 'baby' ? '全家福' : '金婚纪念照'}...`
      : '正在调用 AI 合成...'
    
    // 2. 构建合成参数
    // photo: 人像照片（图1）
    // background: 背景图片（图2，可选）
    const params = {
      photo: photoUrl
    }

    if (selectedBackground.value) {
      // 合成使用原始地址（TOS 公网地址或服务器本地路径），缩略图代理地址不能给模型用
      params.background = selectedBackground.value.rawUrl || selectedBackground.value.url
    }
    
    // 添加参考图参数（如果有）
    if (referenceImage.value) {
      params.reference = referenceImage.value
    }
    
    // 添加提示词：宝宝/金婚照使用玩法提示词，普通拍照使用后台选中的提示词模式
    if (isSceneMode) {
      const scenePrompt = resolveScenePrompt(currentScene.value)
      if (scenePrompt) {
        params.prompt = scenePrompt
      }
    } else if (promptModes.value.length > 0 && promptModes.value[selectedPromptIndex.value]) {
      params.prompt = promptModes.value[selectedPromptIndex.value].content
    }
    
    // 3. 调用后端 Doubao API 进行合成
    const result = await generateAIComposite(params)
    
    if (result.code === 200 && result.data.compositeImage) {
      // 结果图也走服务器代理，避免客户端直连 TOS 失败、并解决 canvas 跨域
      compositeResult.value = getAssetUrl(result.data.compositeImage)
      compositeStatus.value = ''
      // 显示剩余次数
      if (result.data.ai_remaining !== null && result.data.ai_remaining !== undefined) {
        ElMessage.success(`${doneLabel}完成！剩余次数: ${result.data.ai_remaining}`)
      } else {
        ElMessage.success(`${doneLabel}完成！`)
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
    const msg = String((error && error.message) || '')
    if (!navigator.onLine) {
      window.dispatchEvent(new Event('app-network-device-offline'))
      ElMessage.error('设备未联网，请联网后重试')
    } else if (/Failed to fetch|NetworkError|Load failed|ERR_NETWORK|网络连接/i.test(msg)) {
      window.dispatchEvent(new Event('app-network-error'))
      ElMessage.error('网络连接异常，请检查网络后重试')
    } else if (msg.includes('次数已用完')) {
      ElMessage.error(msg)
    } else {
      ElMessage.error(`AI合成失败: ${msg || '请重试'}`)
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
    const msg = String((error && error.message) || '')
    if (!navigator.onLine) {
      window.dispatchEvent(new Event('app-network-device-offline'))
      ElMessage.error('设备未联网，请联网后重试')
    } else if (/Failed to fetch|NetworkError|Load failed|ERR_NETWORK/i.test(msg)) {
      window.dispatchEvent(new Event('app-network-error'))
      ElMessage.error('网络连接异常，请检查网络后重试')
    } else {
      ElMessage.error(`保存失败：${msg || '请重试'}`)
    }
  } finally {
    saving.value = false
  }
}

// 获取品牌 Logo
async function fetchLogo() {
  try {
    const result = await getLogo()
    if (result.code === 200 && result.data.url) {
      // 外部图片走服务器代理，避免客户端访问不了 TOS
      brandLogo.value = getAssetUrl(result.data.url, { width: 400 })
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

// 重新拉取服务端数据（网络恢复后调用）
async function refetchServerData() {
  // 先取文字描述设置，才能确定要加载哪个字体
  await fetchTextOverlay()
  await Promise.all([fetchBackgrounds(), fetchFonts(), fetchLogo(), fetchReference(), fetchPrompts()])
}

onMounted(async () => {
  await getCameraList()
  if (selectedCamera.value) {
    startCamera(selectedCamera.value)
  }
  // 获取背景列表、字体列表、Logo、参考图、文字描述设置和提示词模式
  window.addEventListener('app-network-online', refetchServerData)
  await refetchServerData()
})

onUnmounted(() => {
  stopCamera()
  window.removeEventListener('app-network-online', refetchServerData)
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
  width: 160px;
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
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 16px;
  overflow: hidden;
  min-height: 0;
}

.camera-section {
  flex: 1 1 auto;
  width: 100%;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  container-type: size;
}

.camera-container {
  position: relative;
  width: min(100cqw, calc(100cqh * 16 / 9));
  height: min(100cqh, calc(100cqw * 9 / 16));
  max-width: 100%;
  max-height: 100%;
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
  object-fit: contain;
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
  position: absolute;
  inset: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
}

/* 底部操作栏：玩法 + 控制按钮 */
.bottom-bar {
  width: 100%;
  background: #16213e;
  border: 1px solid #0f3460;
  border-radius: 12px;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.scene-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.scene-options {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.scene-label {
  font-size: 13px;
  color: #8a93a8;
  margin-right: 2px;
}

.scene-btn {
  min-width: 122px;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
}

.scene-btn:not(.el-button--primary) {
  background: rgba(255, 255, 255, 0.08);
  color: #e0e0e0;
  border-color: rgba(255, 255, 255, 0.25);
}

.scene-btn:not(.el-button--primary):hover {
  background: rgba(64, 158, 255, 0.18);
  color: #fff;
  border-color: #409eff;
}

.scene-hint {
  margin: 0;
  font-size: 11px;
  color: #8a93a8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 640px;
}

/* 宝宝数量选择 */
.child-count {
  display: flex;
  align-items: center;
  gap: 8px;
}

.child-count-label {
  font-size: 12px;
  color: #8a93a8;
}

.child-count :deep(.el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.22);
  color: #e0e0e0;
  padding: 7px 14px;
}

.child-count :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: #409eff;
  border-color: #409eff;
  color: #fff;
  box-shadow: -1px 0 0 0 #409eff;
}

/* 背景选择弹窗 */
.bg-dialog-tip {
  margin: 0 0 12px;
  font-size: 12px;
  color: #8a93a8;
}

.bg-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.bg-dialog-selected {
  font-size: 13px;
  color: #8a93a8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bg-dialog-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

:deep(.el-dialog.background-dialog) {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

:deep(.el-dialog.background-dialog .el-dialog__body) {
  overflow-y: auto;
}

.capture-btn {
  width: 72px;
  height: 72px;
  box-shadow: 0 0 20px rgba(255, 77, 77, 0.5);
}

/* 取景框内当前背景缩略图 */
.bg-thumb {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 160px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(15, 52, 96, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
  cursor: pointer;
  z-index: 15;
  transition: transform 0.2s, border-color 0.2s;
}

.bg-thumb:hover {
  transform: scale(1.03);
  border-color: #409eff;
}

.bg-thumb img {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}

.bg-thumb-label {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 4px;
  text-align: center;
  font-size: 11px;
  color: #fff;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.85));
}

.bg-thumb-empty {
  aspect-ratio: 16 / 9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: #c9d3e6;
  font-size: 11px;
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
