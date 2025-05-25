# TZ-LM 多模态聊天系统

基于 LM Studio 的智能多模态聊天助手，支持 PDF 扫描识别、图片文字提取、语音对话等功能。

## 功能特性

- 🤖 **智能对话**: 基于 Qwen3-32B 模型的自然语言对话
- 📄 **PDF 扫描**: 支持 PDF 文档内容识别和分析
- 🖼️ **图片识别**: OCR 文字提取，支持中英文混合识别
- 🎤 **语音对话**: TTS 文字转语音和语音识别功能
- 📁 **文件上传**: 拖拽上传，支持多种文件格式
- 🌐 **跨平台**: 前后端分离，易于扩展到小程序和 APP

## 技术栈

### 后端
- **FastAPI**: 高性能 Python Web 框架
- **PaddleOCR**: 中文 OCR 识别引擎
- **Edge-TTS**: 微软语音合成服务
- **pdf2image**: PDF 转图片处理
- **LM Studio API**: 本地大语言模型服务

### 前端
- **Next.js 14**: React 全栈框架
- **TypeScript**: 类型安全的 JavaScript
- **Tailwind CSS**: 实用优先的 CSS 框架
- **shadcn/ui**: 现代化 UI 组件库
- **Lucide React**: 精美的图标库

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+
- LM Studio (运行 Qwen3-32B 模型)

### 1. 启动 LM Studio

1. 下载并安装 [LM Studio](https://lmstudio.ai/)
2. 下载 Qwen3-32B-MLX 模型
3. 启动本地服务器，确保运行在 `http://127.0.0.1:1234/v1`

### 2. 后端设置

```bash
# 进入后端目录
cd backend

# 安装 Python 依赖
pip install -r requirements.txt

# 启动后端服务
python -m app.main
```

后端将运行在 `http://localhost:8000`

### 3. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装 Node.js 依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 `http://localhost:3000`

## 配置说明

### 后端配置 (backend/app/config.py)

```python
# LM Studio API 配置
lm_studio_base_url: str = "http://127.0.0.1:1234/v1"
lm_studio_model: str = "qwen3-14b-mlx"

# OCR 配置
use_paddleocr: bool = True  # 使用 PaddleOCR
tesseract_path: str = "/usr/local/bin/tesseract"  # Tesseract 路径

# TTS 配置
tts_voice: str = "zh-CN-XiaoxiaoNeural"  # 中文女声
```

### 前端配置 (frontend/next.config.js)

```javascript
// API 代理配置
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/api/:path*',
    },
  ]
}
```

## API 接口

### 聊天接口
- `POST /api/chat/multimodal` - 多模态聊天
- `POST /api/chat` - 纯文本聊天
- `POST /api/chat/stream` - 流式聊天

### 文件处理
- `POST /api/upload` - 文件上传
- `POST /api/ocr` - OCR 文字识别

### 语音功能
- `POST /api/tts` - 文字转语音
- `GET /api/tts/audio/{filename}` - 获取音频文件

### 系统状态
- `GET /api/health` - 健康检查

## 使用说明

1. **文本对话**: 直接在输入框中输入消息
2. **文件上传**: 点击附件按钮或拖拽文件到聊天区域
3. **PDF 识别**: 上传 PDF 文件，系统自动进行 OCR 识别
4. **图片识别**: 上传图片文件，提取其中的文字内容
5. **语音播放**: 点击 AI 回复旁的播放按钮听取语音
6. **语音输入**: 点击麦克风按钮进行语音输入（开发中）

## 支持的文件格式

- **文档**: PDF
- **图片**: PNG, JPG, JPEG
- **音频**: MP3, WAV（开发中）

## 部署说明

### Docker 部署（推荐）

```bash
# 构建后端镜像
cd backend
docker build -t tz-lm-backend .

# 构建前端镜像
cd frontend
docker build -t tz-lm-frontend .

# 使用 docker-compose 启动
docker-compose up -d
```

### 生产环境部署

1. **后端部署**:
   ```bash
   # 使用 gunicorn 部署
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **前端部署**:
   ```bash
   # 构建生产版本
   npm run build
   npm start
   ```

## 开发指南

### 添加新功能

1. **后端**: 在 `backend/app/routes/` 中添加新的路由
2. **前端**: 在 `frontend/components/` 中添加新的组件
3. **服务**: 在 `backend/app/services/` 中添加业务逻辑

### 扩展到移动端

项目采用前后端分离架构，可以轻松扩展到：
- **小程序**: 使用相同的 API 接口
- **移动 APP**: React Native 或原生开发
- **桌面应用**: Electron 封装

## 故障排除

### 常见问题

1. **LM Studio 连接失败**
   - 检查 LM Studio 是否正常运行
   - 确认端口 1234 未被占用
   - 检查防火墙设置

2. **OCR 识别失败**
   - 确保 PaddleOCR 正确安装
   - 检查图片质量和格式
   - 尝试切换到 Tesseract

3. **TTS 播放失败**
   - 检查网络连接
   - 确认 Edge-TTS 服务可用

### 日志查看

```bash
# 后端日志
tail -f backend/logs/app.log

# 前端日志
npm run dev  # 开发模式下查看控制台
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目地址: [GitHub](https://github.com/your-username/tz-lm)
- 问题反馈: [Issues](https://github.com/your-username/tz-lm/issues)

## 致谢

- [LM Studio](https://lmstudio.ai/) - 本地大语言模型服务
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 中文 OCR 引擎
- [shadcn/ui](https://ui.shadcn.com/) - 现代化 UI 组件库
- [Qwen](https://github.com/QwenLM/Qwen) - 通义千问大语言模型