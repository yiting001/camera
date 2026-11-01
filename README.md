# 智能拍照合成系统

拍照合成系统 - 包含 PC桌面客户端（拍照合成）、Web后台管理端、服务端

## 项目结构

```
├── client/             # PC桌面客户端 (Electron + Vue3) - 拍照合成
│   ├── electron/       # Electron 主进程
│   ├── src/            # Vue 应用源码
│   └── package.json
│
├── admin/              # Web后台管理端 (Vue3 Web)
│   ├── src/
│   │   ├── views/      # 页面
│   │   ├── api/        # API 接口
│   │   └── router/     # 路由
│   └── package.json
│
├── server/             # 服务端 (Flask + MySQL)
│   ├── routes/         # API 路由
│   ├── models/         # 数据模型
│   ├── app.py          # 应用入口
│   └── requirements.txt
```

## 技术栈

| 模块 | 技术 | 平台 |
|------|------|------|
| PC桌面客户端 | Vue 3 + Element Plus + Electron | Mac / Windows |
| Web后台管理 | Vue 3 + Element Plus + ECharts | 浏览器 |
| 服务端 | Flask + SQLAlchemy + MySQL | 服务器 |

## 快速开始

### 1. 服务端

```bash
cd server
pip3 install -r requirements.txt
python3 init_db.py   # 初始化数据库
python3 app.py       # 启动服务 (端口 5000)
```

### 2. Web后台管理端

```bash
cd admin
npm install
npm run dev          # 启动开发服务器 (端口 3000)
```

### 3. PC桌面客户端（拍照合成）

```bash
cd client
npm install
npm run electron:dev # 启动 Electron 开发环境
```

## 打包

### PC桌面客户端打包

```bash
cd client

# 打包 Mac 版本 (.dmg)
npm run electron:build:mac

# 打包 Windows 版本 (.exe)
npm run electron:build:win

# 同时打包 Mac 和 Windows
npm run electron:build:all
```

打包输出目录：`client/dist_electron/`

### Web后台管理端打包

```bash
cd admin
npm run build        # 输出到 dist/ 目录
```

## 功能模块

### PC桌面客户端（拍照合成）
- 支持多相机切换（自动检测所有连接的相机设备）
- 预设背景选择（海滩、城市、森林等）
- 自定义背景上传
- AI人像合成（将用户人像与背景融合）
- 合成结果下载与保存

### Web后台管理端
- 数据看板（统计分析）
- 用户管理
- 照片管理
- 背景管理
- 系统配置

### 服务端 API
- AI合成接口
- 背景管理接口
- 照片存储接口

---

## AI合成服务配置

拍照合成功能需要配置AI服务来实现人像与背景的融合。支持以下方式：

### 环境变量配置
```bash
# AI服务地址
export AI_SERVICE_URL=http://localhost:8000/api/composite

# AI服务密钥（如需要）
export AI_API_KEY=your-api-key
```

### 支持的AI服务
- **本地部署模型**：如 Stable Diffusion + ControlNet
- **云端AI服务**：阿里云视觉智能、百度智能云、腾讯云AI
- **第三方API**：Replicate、Runway等

### 预设背景
将背景图片放置在以下目录：
- 前端：`client/public/backgrounds/`
- 后端：`server/static/backgrounds/`

---

等待用户补充具体业务需求...
