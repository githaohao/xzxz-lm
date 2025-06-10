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
- 👤 **用户隔离**: 每个用户拥有独立的聊天历史和知识库，数据完全隔离
- 🔐 **安全认证**: 集成若依Gateway身份验证，支持多租户架构
- 🧠 **个人知识库**: 用户可上传文档建立专属知识库，支持语义检索
- 💾 **数据持久化**: SQLite + ChromaDB 双数据库架构，保证数据安全
- 🔄 **实时同步**: 对话列表与后端实时同步，支持多设备数据一致性

## 技术栈

### 后端
- **FastAPI**: 高性能 Python Web 框架
- **SQLite**: 轻量级数据库，用于用户数据和聊天历史存储
- **ChromaDB**: 向量数据库，支持用户隔离的文档检索
- **Sentence Transformers**: 语义嵌入模型，用于文档向量化
- **用户认证中间件**: 基于若依Gateway的用户身份验证
- **FunAudioLLM**: 高性能语音识别引擎（比 Whisper 快 15 倍）
- **Edge-TTS**: 微软语音合成服务
- **PyPDF2 & python-docx**: 多格式文档解析
- **LM Studio API**: 本地大语言模型服务
- **Nacos**: 微服务注册与配置中心

### 前端
- **Vue 3**: 渐进式 JavaScript 框架
- **TypeScript**: 类型安全的 JavaScript
- **Vite**: 快速的前端构建工具
- **Tailwind CSS**: 实用优先的 CSS 框架
- **shadcn-ui**: 现代化 UI 组件库（Vue 版本）
- **Lucide Vue**: 精美的图标库
- **Pinia**: Vue 3 状态管理库
  

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

# 2. 启动NestJS聊天历史服务
cd nestjs-chat-service
./start.sh

# 3. 或使用Docker Compose启动完整微服务环境
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

### 环境变量配置 (.env)

```bash
# 复制配置模板文件
cp backend/.env.example backend/.env
```

**重要配置项：**

```bash
# 服务IP配置 - 注册到Nacos时使用
# 建议手动设置为实际网络接口的IP地址
SERVICE_IP=192.168.100.24
SERVICE_PORT=8000

# Nacos服务发现配置
NACOS_ENABLED=true
NACOS_SERVER_ADDRESSES=nacos:8848
NACOS_SERVICE_NAME=xzxz-lm-service

# LM Studio配置
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=deepseek-r1-0528-qwen3-8b-mlx@8bit
```

### IP地址配置说明

系统会按以下优先级检测和使用IP地址：

1. **手动配置优先**：如果在 `.env` 文件中设置了 `SERVICE_IP`，系统将优先使用该IP
2. **自动检测规则**：如果未配置或设置为 `0.0.0.0`，系统按以下顺序自动检测：
   - 优先选择 `192.168.x.x` 网段的IP（局域网）
   - 其次选择 `10.x.x.x` 网段的IP
   - 再次选择 `172.16-31.x.x` 网段的IP
   - 最后选择第一个非回环IP

**推荐做法**：在 `.env` 文件中手动设置 `SERVICE_IP=192.168.100.24`，避免自动检测错误。

### 网络接口调试

如需查看系统检测到的所有网络接口，可访问健康检查接口：

```bash
curl http://localhost:8000/health
```

返回的 `network_info` 字段包含：
- `current_ip`: 当前使用的IP
- `configured_ip`: 配置文件中的IP
- `all_interfaces`: 所有检测到的网络接口

### 对话列表同步机制

系统实现了前端与后端的对话列表双向同步：

#### 🔄 自动同步
- **应用启动**: 自动从后端同步对话列表到本地
- **智能合并**: 本地对话与后端会话自动关联，避免重复
- **缓存优化**: 优先从本地缓存加载，提升启动速度

#### 🔧 手动同步
- **刷新按钮**: 对话列表右上角的刷新按钮，随时同步最新数据
- **状态指示**: 同步过程中显示旋转动画，提供清晰的用户反馈

#### 📱 多设备支持
- **数据一致性**: 同一用户在不同设备间保持对话历史一致
- **离线优先**: 本地优先策略，即使网络异常也能正常使用
- **智能恢复**: 网络恢复后自动同步差异数据

#### 💾 存储策略
- **本地存储**: localStorage缓存对话列表，提升加载速度
- **后端持久化**: SQLite数据库存储用户聊天历史
- **增量同步**: 只同步变更的对话，减少网络开销

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

### 🤖 AI聊天服务 (/api/lm/*)
- `POST /api/lm/chat/stream` - 流式文本聊天
- `POST /api/lm/chat/multimodal/stream/processed` - 多模态流式聊天

### 🎤 语音功能 (/voice/*)
- `POST /voice/chat` - 语音对话
- `POST /voice/speech/synthesize` - 语音合成(TTS)
- `GET /voice/engine` - 获取语音引擎状态
- `DELETE /voice/conversation/{id}` - 清除对话历史
- `WebSocket /voice/ws/voice` - 实时语音WebSocket连接

### 📁 文件处理 (/api/lm/*)
- `POST /api/lm/upload` - 文件上传
- `POST /api/lm/ocr` - OCR文字识别

### 🧠 RAG智能检索 (/api/lm/rag/*)
- `GET /api/lm/rag/documents` - 获取文档列表
- `POST /api/lm/rag/search` - 文档检索
- `POST /api/lm/rag/process` - 文档处理
- `DELETE /api/lm/rag/documents/{id}` - 删除文档

### 🔧 系统监控 (/api/lm/*)
- `GET /api/lm/health` - 健康检查

### 💬 用户聊天历史服务 (/api/user/chat/*)
- `GET /api/user/chat/sessions` - 获取用户聊天会话列表
- `POST /api/user/chat/sessions` - 创建新的聊天会话
- `GET /api/user/chat/sessions/{id}` - 获取指定会话详情
- `PUT /api/user/chat/sessions/{id}` - 更新会话信息
- `DELETE /api/user/chat/sessions/{id}` - 删除会话
- `PUT /api/user/chat/sessions/{id}/archive` - 归档会话
- `PUT /api/user/chat/sessions/{id}/restore` - 恢复会话
- `GET /api/user/chat/sessions/{id}/messages` - 获取会话消息列表
- `POST /api/user/chat/sessions/{id}/messages` - 添加消息到会话
- `POST /api/user/chat/messages/batch` - 批量添加消息
- `DELETE /api/user/chat/messages/{id}` - 删除消息
- `GET /api/user/chat/stats` - 获取用户聊天统计信息
- `GET /api/user/chat/health` - 聊天历史服务健康检查

### 📚 用户知识库服务 (/api/user/rag/*)
- `POST /api/user/rag/documents/upload` - 上传文档到个人知识库
- `GET /api/user/rag/documents` - 获取用户文档列表
- `POST /api/user/rag/search` - 在用户知识库中搜索文档
- `DELETE /api/user/rag/documents/{id}` - 删除用户文档
- `GET /api/user/rag/documents/{id}/chunks` - 获取文档分块内容
- `GET /api/user/rag/stats` - 获取用户RAG统计信息
- `GET /api/user/rag/health` - 用户RAG服务健康检查

### 👤 若依用户系统 (/api/system/*)
- `GET /api/system/captcha` - 获取验证码
- `POST /api/system/login` - 用户登录
- `POST /api/system/logout` - 退出登录
- `GET /api/system/getInfo` - 获取用户信息
- `GET /api/system/user/profile` - 获取用户资料
- `POST /api/system/user/profile` - 更新用户资料
- `POST /api/system/user/avatar` - 上传用户头像
- `GET /api/system/menu/list` - 获取菜单列表
- `GET /api/system/getRouters` - 获取路由列表
- `POST /api/system/refresh` - 刷新Token

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

## 🔄 架构变更说明

### v2.0 用户绑定架构升级

本版本进行了重大架构升级，实现了完整的用户绑定功能：

#### 🛠️ 技术栈升级
- **响应模型重构**: `ChatHistoryResponse`类支持泛型参数化，继承`typing.Generic[T]`
- **类型安全增强**: 统一使用`TypeVar`实现类型安全的API响应
- **数据库双引擎**: SQLite + ChromaDB 实现关系型+向量型双存储
- **用户数据隔离**: 每个用户拥有独立的数据空间，确保隐私安全

#### 🗄️ 数据架构优化
1. **用户会话表** (`user_chat_sessions`)
   - 用户ID索引，支持快速查询
   - 会话状态管理（活跃/归档/删除）
   - 标签系统，支持分类管理

2. **用户消息表** (`user_chat_messages`)
   - 消息链式结构，支持回复引用
   - 序列号排序，保证消息顺序
   - 多类型消息支持（文本/语音/图片/文件）

3. **用户文档表** (`user_documents`)
   - RAG文档元数据管理
   - OCR状态追踪
   - 分块计数统计

4. **向量存储** (ChromaDB)
   - 用户专属Collection: `user_{id}_docs`
   - 高维向量检索 (768维度)
   - 语义相似度搜索

#### 🔌 API架构升级
```
传统架构: /api/chat/* (全局共享)
新架构: /api/user/chat/* (用户绑定)
       /api/user/rag/* (个人知识库)
```

#### 🎯 核心改进
- **泛型响应**: `ChatHistoryResponse[T]`支持任意数据类型
- **类型检查**: 编译时类型验证，运行时类型安全
- **用户认证**: 若依Gateway集成，自动提取用户信息
- **数据隔离**: 严格的用户权限控制，防止数据泄露
- **性能优化**: 索引优化、查询优化、缓存机制

#### 📊 升级影响
- **前端兼容**: 无需修改现有前端代码
- **API路径**: 新增用户绑定API，保留原有API
- **数据迁移**: 支持平滑数据迁移
- **性能提升**: 用户数据隔离带来的查询性能优化

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