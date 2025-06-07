# 小智小智 多模态聊天系统

基于 LM Studio 的智能多模态聊天助手，支持 PDF 扫描识别、图片文字提取、语音对话等功能。

## 功能特性

- 🤖 **智能对话**: 基于 Qwen3-32B 模型的自然语言对话
- 📄 **PDF 扫描**: 支持 PDF 文档内容识别和分析
- 🖼️ **图片识别**: OCR 文字提取，支持中英文混合识别
- 🎤 **语音对话**: 基于 FunAudioLLM 的高性能语音识别和 TTS 功能
- 📁 **文件上传**: 拖拽上传，支持多种文件格式
- 🌐 **跨平台**: 前后端分离，易于扩展到小程序和 APP
- 🎨 **现代化 UI**: 使用 shadcn-ui 组件库，提供优秀的用户体验

## 技术栈

### 后端
- **FastAPI**: 高性能 Python Web 框架
- **FunAudioLLM**: 高性能语音识别引擎（比 Whisper 快 15 倍）
- **Edge-TTS**: 微软语音合成服务
- **pdf2image**: PDF 转图片处理
- **LM Studio API**: 本地大语言模型服务

### 前端
- **Vue 3**: 渐进式 JavaScript 框架
- **TypeScript**: 类型安全的 JavaScript
- **Vite**: 快速的前端构建工具
- **Tailwind CSS**: 实用优先的 CSS 框架
- **shadcn-ui**: 现代化 UI 组件库（Vue 版本）
- **Lucide Vue**: 精美的图标库
- **Pinia**: Vue 3 状态管理库
  

截屏2025-06-04 下午2.30.51.png
### 界面示例
![image](https://gitee.com/githaohao/xzxz-lm/raw/main/docs/%E6%88%AA%E5%B1%8F2025-05-26%20%E4%B8%8A%E5%8D%889.36.01.png)
![image](https://gitee.com/githaohao/xzxz-lm/raw/main/docs/%E6%88%AA%E5%B1%8F2025-06-04%20%E4%B8%8B%E5%8D%882.30.51.png)
![image](https://gitee.com/githaohao/xzxz-lm/raw/main/docs/%E6%88%AA%E5%B1%8F2025-06-04%20%E4%B8%8B%E5%8D%882.31.08.png)
![image](https://gitee.com/githaohao/xzxz-lm/raw/main/docs/%E6%88%AA%E5%B1%8F2025-06-04%20%E4%B8%8B%E5%8D%882.31.20.png)
![image](https://gitee.com/githaohao/xzxz-lm/raw/main/docs/%E6%88%AA%E5%B1%8F2025-06-04%20%E4%B8%8B%E5%8D%882.31.30.png)
![image](https://gitee.com/githaohao/xzxz-lm/raw/main/docs/%E6%88%AA%E5%B1%8F2025-05-26%20%E4%B8%8A%E5%8D%889.36.30.png)
![image](https://gitee.com/githaohao/xzxz-lm/raw/main/docs/%E6%88%AA%E5%B1%8F2025-05-26%20%E4%B8%8A%E5%8D%889.36.45.png)
![image](https://gitee.com/githaohao/xzxz-lm/raw/main/docs/%E6%88%AA%E5%B1%8F2025-05-26%20%E4%B8%8A%E5%8D%889.36.53.png)
![image](https://gitee.com/githaohao/xzxz-lm/raw/main/docs/%E6%88%AA%E5%B1%8F2025-05-26%20%E4%B8%8A%E5%8D%889.37.13.png)
![image](https://gitee.com/githaohao/xzxz-lm/raw/main/docs/%E6%88%AA%E5%B1%8F2025-05-26%20%E4%B8%8A%E5%8D%889.37.22.png)

## 🚀 快速启动

### 微服务模式启动（推荐）

```bash
# 1. 启动Nacos集成版本
./scripts/start_with_nacos.sh

# 2. 或使用Docker Compose启动完整微服务环境
docker-compose -f docker-compose.nacos.yml up -d
```

### 独立模式启动

#### 环境变量设置（推荐）

为了避免 tokenizers 并行处理警告，建议先设置环境变量：

```bash
# 方法1：使用提供的脚本（推荐）
source scripts/set_env.sh

# 方法2：手动设置
export TOKENIZERS_PARALLELISM=false
export PYTORCH_ENABLE_MPS_FALLBACK=1  # Apple Silicon 用户
export MPS_MEMORY_FRACTION=0.8        # Apple Silicon 用户
```

#### 启动服务

### 环境要求

- Python 3.8+
- Node.js 18+
- pnpm（推荐）或 npm
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
cd vue-frontend

# 安装 Node.js 依赖（推荐使用 pnpm）
pnpm install
# 或者使用 npm
# npm install

# 启动开发服务器
pnpm dev
# 或者使用 npm
# npm run dev
```

前端将运行在 `http://localhost:3001`

## 配置说明

### 后端配置 (backend/app/config.py)

```python
# LM Studio API 配置
lm_studio_base_url: str = "http://127.0.0.1:1234/v1"
lm_studio_model: str = "qwen3-14b-mlx"

# OCR 配置
tesseract_path: str = "/usr/local/bin/tesseract"  # Tesseract 路径

# TTS 配置
tts_voice: str = "zh-CN-XiaoxiaoNeural"  # 中文女声

# FunAudioLLM 配置
funaudio_enabled: bool = True  # 启用 FunAudioLLM
```

### 前端配置 (vue-frontend/vite.config.ts)

```typescript
// API 代理配置
export default defineConfig({
  server: {
    port: 3001,
    proxy: {
      '^/(chat|health|voice|upload|ocr|tts|rag)': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

## API 接口

### 聊天接口
- `POST /chat/multimodal` - 多模态聊天
- `POST /chat` - 纯文本聊天
- `POST /chat/stream` - 流式聊天

### 文件处理
- `POST /upload` - 文件上传
- `POST /ocr` - OCR 文字识别

### 语音功能
- `POST /voice/tts` - 文字转语音
- `POST /voice/stt` - 语音转文字（FunAudioLLM）
- `GET /voice/engine` - 获取语音引擎状态
- `POST /voice/chat` - 语音对话
- `GET /voice/audio/{filename}` - 获取音频文件

### 系统状态和监控
- `GET /health` - 标准健康检查
- `GET /status` - 详细系统状态信息

### 微服务集成
- **服务注册**: 自动注册到Nacos服务注册中心
- **配置管理**: 支持从Nacos获取动态配置
- **健康检查**: 提供多种格式的健康检查端点
- **服务发现**: 支持通过Nacos进行服务发现

## 页面路由

- `/` - 首页
- `/chat` - 文本聊天页面
- `/voice-chat` - 详细版语音聊天页面
- `/simple-voice-chat` - 简化版语音聊天页面
- `/style-showcase` - shadcn-ui 组件展示页面

## 测试工具

### 健康检查端点测试
```bash
# 测试所有健康检查端点
python3 scripts/test_health_endpoints.py

# 或者直接执行
./scripts/test_health_endpoints.py
```

该脚本会测试以下端点：
- `/health` - 标准健康检查
- `/status` - 详细系统状态

## 使用说明

1. **文本对话**: 直接在输入框中输入消息
2. **文件上传**: 点击附件按钮或拖拽文件到聊天区域
3. **PDF 识别**: 上传 PDF 文件，系统自动进行 OCR 识别
4. **图片识别**: 上传图片文件，提取其中的文字内容
5. **语音对话**: 
   - 点击绿色电话按钮开始语音通话
   - 系统自动录音并使用 FunAudioLLM 进行语音识别
   - AI 回复支持 TTS 语音播放
   - 支持静音控制和会话管理

## 支持的文件格式

- **文档**: PDF
- **图片**: PNG, JPG, JPEG
- **音频**: MP3, WAV, M4A

## 部署说明

### 微服务部署（Nacos + 若依Gateway）

#### 1. 启用Nacos服务注册

```bash
# 1. 复制环境配置文件
cp backend/env.example backend/.env

# 2. 编辑配置文件，启用Nacos
vim backend/.env
# 设置 NACOS_ENABLED=true
# 设置 NACOS_SERVER_ADDRESSES=your-nacos-server:8848

# 3. 使用Nacos启动脚本
./scripts/start_with_nacos.sh
```

#### 2. Docker Compose 部署（包含Nacos）

```bash
# 启动完整的微服务环境（包含Nacos、MySQL、Redis、Gateway）
docker-compose -f docker-compose.nacos.yml up -d

# 查看服务状态
docker-compose -f docker-compose.nacos.yml ps

# 查看日志
docker-compose -f docker-compose.nacos.yml logs -f xzxz-lm-service
```

#### 3. 若依Gateway配置

将 `configs/gateway-routes.yml` 中的配置添加到您的若依Gateway配置中：

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: xzxz-lm-service
          uri: lb://xzxz-lm-service
          predicates:
            - Path=/lm/**
          filters:
            - StripPrefix=1
```

#### 4. 服务访问

- **直接访问**: `http://localhost:8000/health`
- **通过Gateway**: `http://gateway:8080/lm/health`
- **Nacos控制台**: `http://localhost:8848/nacos`

### 传统Docker部署

```bash
# 构建后端镜像
cd backend
docker build -t xzxz-lm-backend .

# 构建前端镜像
cd vue-frontend
docker build -t xzxz-lm-frontend .

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
   cd vue-frontend
   pnpm build
   pnpm preview
   ```

## 开发指南

### 添加新功能

1. **后端**: 在 `backend/app/routes/` 中添加新的路由
2. **前端**: 在 `vue-frontend/src/components/` 中添加新的组件
3. **服务**: 在 `backend/app/services/` 中添加业务逻辑
4. **页面**: 在 `vue-frontend/src/views/` 中添加新的页面

### 前端组件开发

项目使用 shadcn-ui 组件库，所有 UI 组件位于 `vue-frontend/src/components/ui/`：

- `Avatar.vue` - 头像组件
- `Button.vue` - 按钮组件
- `Card.vue` - 卡片组件
- `Badge.vue` - 徽章组件
- `Progress.vue` - 进度条组件
- `Alert.vue` - 警告组件
- `Skeleton.vue` - 骨架屏组件

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
   - 检查图片质量和格式

3. **语音功能异常**
   - 检查 FunAudioLLM 服务状态
   - 确认麦克风权限已授权
   - 检查音频设备连接

4. **前端编译错误**
   - 确保使用 Node.js 18+
   - 清除缓存：`pnpm store prune`
   - 重新安装依赖：`rm -rf node_modules && pnpm install`

### 日志查看

```bash
# 后端日志
tail -f backend/logs/app.log

# 前端日志
cd vue-frontend
pnpm dev  # 开发模式下查看控制台
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

- 项目地址: [GitHub](https://github.com/githaohao/xzxz-lm)
- 项目地址: [Gitee](https://gitee.com/githaohao/xzxz-lm)
- 问题反馈: [Issues](https://gitee.com/githaohao/xzxz-lm/issues)

## 致谢

- [LM Studio](https://lmstudio.ai/) - 本地大语言模型服务
- [FunAudioLLM](https://github.com/FunAudioLLM/FunAudioLLM) - 高性能语音识别引擎
- [shadcn-ui](https://ui.shadcn.com/) - 现代化 UI 组件库
- [Vue 3](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Qwen](https://github.com/QwenLM/Qwen) - 通义千问大语言模型