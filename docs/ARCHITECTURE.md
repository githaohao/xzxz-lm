# 小智小智 项目架构文档

## 项目概述

小智小智 是一个基于 Vue 3 + FastAPI 的多模态聊天系统，支持文本对话、语音交互、文件处理等功能。

## 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue Frontend  │    │  FastAPI Backend│    │   LM Studio     │
│   (Port 3001)   │◄──►│   (Port 8000)   │◄──►│   (Port 1234)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────▼────┐             ┌────▼────┐             ┌────▼────┐
    │shadcn-ui│             │FastAPI  │             │Qwen3-32B│
    │组件库   │             │路由系统 │             │大语言模型│
    └─────────┘             └─────────┘             └─────────┘
                                   │
                            ┌──────▼──────┐
                            │   服务层     │
                            │ ┌─────────┐ │
                            │ │OCR服务  │ │
                            │ │TTS服务  │ │
                            │ │语音服务 │ │
                            │ │文件服务 │ │
                            │ └─────────┘ │
                            └─────────────┘
```

## 前端架构 (vue-frontend)

### 技术栈

- **Vue 3**: 使用 Composition API 和 `<script setup>` 语法
- **TypeScript**: 提供类型安全和更好的开发体验
- **Vite**: 快速的构建工具和开发服务器
- **Pinia**: Vue 3 官方推荐的状态管理库
- **Vue Router**: 单页应用路由管理
- **Tailwind CSS**: 实用优先的 CSS 框架
- **shadcn-ui**: 现代化的 UI 组件库（Vue 版本）

### 目录结构

```
vue-frontend/
├── src/
│   ├── components/          # 组件目录
│   │   └── ui/             # shadcn-ui 组件
│   │       ├── Avatar.vue
│   │       ├── Button.vue
│   │       ├── Card.vue
│   │       ├── Badge.vue
│   │       ├── Progress.vue
│   │       ├── Alert.vue
│   │       └── Skeleton.vue
│   ├── views/              # 页面组件
│   │   ├── HomeView.vue
│   │   ├── ChatView.vue
│   │   ├── VoiceChatView.vue
│   │   ├── SimpleVoiceChatView.vue
│   │   └── StyleShowcaseView.vue
│   ├── stores/             # Pinia 状态管理
│   │   ├── chat.ts
│   │   └── voice.ts
│   ├── router/             # 路由配置
│   │   └── index.ts
│   ├── utils/              # 工具函数
│   │   └── api.ts
│   ├── lib/                # 库文件
│   │   └── utils.ts        # shadcn-ui 工具函数
│   └── assets/             # 静态资源
├── public/                 # 公共资源
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

### 核心功能模块

#### 1. 状态管理 (Pinia)

**Chat Store** (`stores/chat.ts`)
- 管理聊天消息状态
- 处理文件上传
- API 调用封装

**Voice Store** (`stores/voice.ts`)
- 语音聊天状态管理
- 录音控制
- 语音引擎状态检查

#### 2. 路由系统

```typescript
// router/index.ts
const routes = [
  { path: '/', component: HomeView },
  { path: '/chat', component: ChatView },
  { path: '/voice-chat', component: VoiceChatView },
  { path: '/simple-voice-chat', component: SimpleVoiceChatView },
  { path: '/style-showcase', component: StyleShowcaseView }
]
```

#### 3. UI 组件系统

基于 shadcn-ui 构建的组件库：

- **Avatar**: 用户和 AI 头像显示
- **Button**: 各种交互按钮
- **Card**: 消息卡片和容器
- **Badge**: 状态标签
- **Progress**: 进度条显示
- **Alert**: 警告和提示信息
- **Skeleton**: 加载状态骨架屏

#### 4. API 通信

```typescript
// utils/api.ts
const api = axios.create({
  baseURL: '/',
  timeout: 30000
})

// 主要 API 接口
export const chatAPI = {
  sendMessage: (data) => api.post('/chat', data),
  uploadFile: (file) => api.post('/upload', file),
  // ...
}

export const voiceAPI = {
  checkEngine: () => api.get('/voice/engine'),
  startChat: (data) => api.post('/voice/chat', data),
  // ...
}
```

## 后端架构 (backend)

### 技术栈

- **FastAPI**: 现代化的 Python Web 框架
- **Pydantic**: 数据验证和序列化
- **SQLAlchemy**: ORM 数据库操作（如需要）
- **FunAudioLLM**: 高性能语音识别
- **Edge-TTS**: 文字转语音

### 服务层架构

```
backend/app/
├── routes/                 # API 路由
│   ├── chat.py            # 聊天相关接口
│   ├── voice.py           # 语音相关接口
│   ├── upload.py          # 文件上传接口
│   └── health.py          # 健康检查
├── services/              # 业务逻辑层
│   ├── chat_service.py    # 聊天服务
│   ├── voice_service.py   # 语音服务
│   ├── ocr_service.py     # OCR 服务
│   └── file_service.py    # 文件处理服务
├── models/                # 数据模型
├── config.py              # 配置文件
└── main.py               # 应用入口
```

## 数据流

### 1. 文本聊天流程

```
用户输入 → Vue组件 → Pinia Store → API调用 → FastAPI路由 → 
LM Studio → 响应处理 → 前端状态更新 → UI渲染
```

### 2. 语音聊天流程

```
用户点击录音 → 浏览器录音API → 音频数据 → FunAudioLLM识别 → 
文本处理 → LM Studio生成回复 → TTS语音合成 → 前端播放
```

### 3. 文件处理流程

```
文件上传 → 前端预处理 → 后端接收 → 文件类型判断 → 
OCR/PDF处理 → 文本提取 → 聊天上下文 → AI分析
```

## 部署架构

### 开发环境

```
开发者本地 → Vite Dev Server (3001) → FastAPI Dev (8000) → LM Studio (1234)
```

### 生产环境

```
用户 → Nginx → Vue Build → FastAPI (Gunicorn) → LM Studio
```

## 性能优化

### 前端优化

1. **代码分割**: 使用 Vue Router 的懒加载
2. **组件缓存**: 合理使用 `keep-alive`
3. **资源优化**: Vite 自动处理资源压缩和缓存
4. **状态管理**: Pinia 提供高效的响应式状态管理

### 后端优化

1. **异步处理**: FastAPI 原生支持异步操作
2. **连接池**: 数据库和外部服务连接复用
3. **缓存策略**: Redis 缓存热点数据
4. **负载均衡**: 多实例部署

## 安全考虑

### 前端安全

1. **XSS 防护**: Vue 3 自动转义用户输入
2. **CSRF 防护**: API 请求使用 token 验证
3. **内容安全策略**: 配置 CSP 头部

### 后端安全

1. **输入验证**: Pydantic 模型验证
2. **文件上传**: 文件类型和大小限制
3. **API 限流**: 防止恶意请求
4. **CORS 配置**: 跨域请求控制

## 扩展性设计

### 水平扩展

1. **微服务架构**: 按功能拆分服务
2. **消息队列**: 异步任务处理
3. **数据库分片**: 大数据量处理
4. **CDN 加速**: 静态资源分发

### 功能扩展

1. **插件系统**: 支持第三方功能扩展
2. **多语言支持**: i18n 国际化
3. **主题系统**: 可定制的 UI 主题
4. **移动端适配**: 响应式设计

## 监控和日志

### 前端监控

1. **错误监控**: 全局错误捕获和上报
2. **性能监控**: 页面加载和交互性能
3. **用户行为**: 操作路径分析

### 后端监控

1. **API 监控**: 请求响应时间和错误率
2. **系统监控**: CPU、内存、磁盘使用率
3. **业务监控**: 关键业务指标追踪

## 版本控制和发布

### Git 工作流

```
feature/xxx → develop → staging → main → production
```

### CI/CD 流程

1. **代码检查**: ESLint、TypeScript 检查
2. **自动测试**: 单元测试和集成测试
3. **构建部署**: 自动化构建和部署
4. **回滚机制**: 快速回滚到稳定版本

## 技术债务和改进计划

### 当前技术债务

1. **测试覆盖率**: 需要增加单元测试和集成测试
2. **文档完善**: API 文档和组件文档
3. **性能优化**: 大文件处理和长对话优化

### 改进计划

1. **Q1**: 完善测试体系，提高代码质量
2. **Q2**: 性能优化，支持更大规模使用
3. **Q3**: 移动端适配，扩展用户群体
4. **Q4**: 微服务拆分，提高系统可扩展性 