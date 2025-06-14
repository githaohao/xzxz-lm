# 小智小智 项目架构文档

## 项目概述

小智小智是一个基于Vue 3.5 + FastAPI的企业级多模态AI聊天系统，支持文本对话、语音交互、OCR文档处理、RAG智能检索、知识库管理等功能。系统采用前后端分离架构，支持用户数据隔离和微服务部署。

## 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue Frontend  │    │  FastAPI Backend│    │   LM Studio     │    │     Nacos       │
│   (Port 3004)   │◄──►│   (Port 8000)   │◄──►│   (Port 1234)   │    │   (Port 8848)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
    ┌────▼────┐             ┌────▼────┐             ┌────▼────┐             ┌────▼────┐
    │shadcn-ui│             │FastAPI  │             │Qwen3-32B│             │服务发现 │
    │组件库   │             │路由系统 │             │大语言模型│             │配置中心 │
    └─────────┘             └─────────┘             └─────────┘             └─────────┘
                                   │
                            ┌──────▼──────┐
                            │   服务层     │
                            │ ┌─────────┐ │
                            │ │OCR服务  │ │
                            │ │TTS服务  │ │
                            │ │语音服务 │ │
                            │ │RAG服务  │ │
                            │ │文件服务 │ │
                            │ │知识库   │ │
                            │ └─────────┘ │
                            └─────────────┘
                                   │
                            ┌──────▼──────┐
                            │   数据层     │
                            │ ┌─────────┐ │
                            │ │SQLite   │ │
                            │ │ChromaDB │ │
                            │ │文件存储 │ │
                            │ └─────────┘ │
                            └─────────────┘
```

## 前端架构 (vue-frontend)

### 技术栈

- **Vue 3.5**: 使用 Composition API 和 `<script setup>` 语法
- **TypeScript**: 提供类型安全和更好的开发体验
- **Vite 6.3**: 快速的构建工具和开发服务器
- **Pinia**: Vue 3 官方推荐的状态管理库
- **Vue Router 4**: 单页应用路由管理
- **Tailwind CSS 3.4**: 实用优先的 CSS 框架
- **shadcn-vue 2.1**: 现代化的 UI 组件库（Vue 版本）
- **Lucide Vue Next**: 精美的图标库
- **Axios**: HTTP 客户端
- **Vue Sonner**: 现代化的通知组件
- **VeeValidate + Zod**: 表单验证
- **@vueuse/core**: Vue 组合式工具库

### 目录结构

```
vue-frontend/
├── src/
│   ├── components/          # 组件目录
│   │   └── ui/             # shadcn-ui 组件
│   │       ├── avatar/     # 头像组件
│   │       ├── button/     # 按钮组件
│   │       ├── card/       # 卡片组件
│   │       ├── badge/      # 标签组件
│   │       ├── dialog/     # 对话框组件
│   │       ├── progress/   # 进度条组件
│   │       ├── alert/      # 警告组件
│   │       ├── skeleton/   # 骨架屏组件
│   │       ├── scroll-area/# 滚动区域组件
│   │       ├── toast/      # 提示组件
│   │       └── ...         # 其他UI组件
│   ├── views/              # 页面组件
│   │   ├── HomeView.vue           # 首页
│   │   ├── ChatView.vue           # 聊天页面
│   │   ├── VoiceChatView.vue      # 语音聊天页面
│   │   ├── SimpleVoiceChatView.vue # 简洁语音聊天
│   │   ├── KnowledgeBaseView.vue  # 知识库管理
│   │   ├── ComponentShowcaseView.vue # 组件展示
│   │   └── LoginView.vue          # 登录页面
│   ├── stores/             # Pinia 状态管理
│   │   ├── chat.ts         # 聊天状态管理
│   │   ├── voice.ts        # 语音状态管理
│   │   ├── conversation.ts # 对话历史管理
│   │   ├── knowledgeBase.ts# 知识库状态管理
│   │   ├── rag.ts          # RAG检索状态
│   │   └── auth.ts         # 用户认证状态
│   ├── utils/              # 工具函数
│   │   └── api/            # API调用模块
│   │       ├── client.ts   # API客户端
│   │       ├── chat.ts     # 聊天API
│   │       ├── voice.ts    # 语音API
│   │       ├── file.ts     # 文件API
│   │       ├── history.ts  # 历史记录API
│   │       └── index.ts    # API统一导出
│   ├── types/              # TypeScript类型定义
│   ├── composables/        # 组合式函数
│   ├── router/             # 路由配置
│   │   └── index.ts
│   ├── lib/                # 库文件
│   │   └── utils.ts        # shadcn-ui 工具函数
│   └── assets/             # 静态资源
├── public/                 # 公共资源
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── components.json         # shadcn-ui配置
```

### 核心功能模块

#### 1. 状态管理 (Pinia)

**Chat Store** (`stores/chat.ts`)
- 管理聊天消息状态
- 处理文件上传和多模态消息
- 流式响应处理
- API 调用封装

**Voice Store** (`stores/voice.ts`)
- 语音聊天状态管理
- 录音控制和音频处理
- 语音引擎状态检查
- TTS语音合成

**Conversation Store** (`stores/conversation.ts`)
- 对话历史管理
- 前后端数据同步
- 本地缓存机制
- 会话CRUD操作

**Knowledge Base Store** (`stores/knowledgeBase.ts`)
- 知识库管理
- 文档分类和标签
- 智能归档功能
- 批量操作支持

**RAG Store** (`stores/rag.ts`)
- RAG检索状态管理
- 文档向量化处理
- 相似度搜索
- 检索结果缓存

**Auth Store** (`stores/auth.ts`)
- 用户认证状态
- 权限管理
- 用户信息存储

#### 2. 路由系统

```typescript
// router/index.ts
const routes = [
  { path: '/', component: HomeView },
  { path: '/chat', component: ChatView },
  { path: '/voice-chat', component: VoiceChatView },
  { path: '/simple-voice-chat', component: SimpleVoiceChatView },
  { path: '/knowledge-base', component: KnowledgeBaseView },
  { path: '/component-showcase', component: ComponentShowcaseView },
  { path: '/login', component: LoginView }
]
```

#### 3. UI 组件系统

基于 shadcn-vue 构建的完整组件库：

- **Avatar**: 用户和 AI 头像显示，支持图片和文字头像
- **Button**: 各种交互按钮，支持多种变体和状态
- **Card**: 消息卡片和容器，支持头部、内容、底部布局
- **Badge**: 状态标签，支持多种颜色和样式
- **Dialog**: 模态对话框，支持嵌套和自定义内容
- **Progress**: 进度条显示，支持动画和自定义样式
- **Alert**: 警告和提示信息，支持多种类型
- **Skeleton**: 加载状态骨架屏，提升用户体验
- **ScrollArea**: 自定义滚动区域，支持虚拟滚动
- **Toast**: 消息提示，支持多种类型和位置
- **Table**: 数据表格，支持排序、筛选、分页
- **Form**: 表单组件，集成验证和错误处理

#### 4. API 通信架构

```typescript
// utils/api/client.ts
class ApiClient {
  private baseURL: string
  private timeout: number
  
  async get<T>(url: string): Promise<T>
  async post<T>(url: string, data?: any): Promise<T>
  async delete<T>(url: string): Promise<T>
  async upload<T>(url: string, file: File): Promise<T>
  async stream(url: string, data: any): Promise<ReadableStream>
  async binary(url: string, data: any): Promise<ArrayBuffer>
}

// API模块化设计
export const chatAPI = {
  sendMessage: (data) => api.post('/api/lm/chat/stream', data),
  uploadFile: (file, sessionId?) => api.upload('/api/lm/chat/upload', file),
  getHistory: () => api.get('/api/user/chat/sessions')
}

export const voiceAPI = {
  checkEngine: () => api.get('/api/lm/voice/engine'),
  sendVoiceMessage: (data) => api.post('/api/lm/voice/chat', data),
  synthesizeSpeech: (text) => api.binary('/api/lm/voice/speech/synthesize', { text })
}

export const ragAPI = {
  searchDocuments: (query) => api.post('/api/user/rag/search', { query }),
  uploadDocument: (file) => api.upload('/api/user/rag/upload', file),
  getKnowledgeBases: () => api.get('/api/user/rag/knowledge-bases')
}
```

## 后端架构 (backend)

### 技术栈

- **FastAPI**: 现代化的 Python Web 框架，支持异步和自动API文档
- **Pydantic**: 数据验证和序列化，提供类型安全
- **SQLite**: 轻量级关系数据库，存储用户数据和聊天历史
- **ChromaDB**: 向量数据库，支持语义搜索和用户数据隔离
- **Sentence Transformers**: 语义嵌入模型 (moka-ai/m3e-base)
- **FunAudioLLM**: 高性能语音识别引擎，比Whisper快15倍
- **Edge-TTS**: 微软语音合成服务
- **PaddleOCR**: OCR文字识别，支持Apple Silicon GPU加速
- **PyPDF2 & python-docx**: 多格式文档解析
- **Nacos**: 微服务注册与配置中心
- **Uvicorn**: ASGI服务器

### 服务层架构

```
backend/app/
├── main.py                 # 应用入口和配置
├── config.py              # 全局配置管理
├── database.py            # 数据库连接和初始化
├── utils.py               # 通用工具函数
├── routes/                # API 路由层
│   ├── chat.py           # 聊天相关接口
│   ├── voice.py          # 语音相关接口
│   ├── rag.py            # RAG检索接口
│   ├── chat_history.py   # 聊天历史接口
│   └── health.py         # 健康检查接口
├── services/             # 业务逻辑层
│   ├── chat_history_service.py    # 聊天历史服务
│   ├── rag_service.py             # RAG检索服务
│   ├── ocr_service.py             # OCR处理服务
│   ├── file_extraction_service.py # 文件提取服务
│   ├── funaudio_service.py        # 语音识别服务
│   ├── tts_service.py             # 语音合成服务
│   ├── lm_studio_service.py       # LM Studio集成
│   └── nacos_service.py           # Nacos服务发现
├── models/               # 数据模型
├── middleware/           # 中间件
│   └── auth.py          # 用户认证中间件
└── examples/            # 示例代码
```

### 核心服务详解

#### 1. RAG服务 (rag_service.py)

```python
class RAGService:
    def __init__(self):
        self.embedding_model = SentenceTransformer('moka-ai/m3e-base')
        self.chroma_client = chromadb.Client()
        
    async def add_document(self, user_id: str, file_path: str, content: str):
        """添加文档到用户专属向量数据库"""
        
    async def search_documents(self, user_id: str, query: str, top_k: int = 5):
        """在用户文档中进行语义搜索"""
        
    async def create_knowledge_base(self, user_id: str, name: str):
        """创建知识库"""
        
    async def smart_archive_documents(self, user_id: str, files: List[File]):
        """智能归档文档到合适的知识库"""
```

**特性：**
- 用户数据隔离：每个用户拥有独立的Collection (`user_{id}_docs`)
- 智能分块：支持结构化数据保护，避免URL等重要信息被切断
- 相似度优化：精确调优阈值0.355，确保准确检索
- 缓存机制：避免重复处理，提升性能
- 多格式支持：PDF、Word、图片等多种文档格式

#### 2. OCR服务 (ocr_service.py)

```python
class OCRService:
    def __init__(self):
        self.paddleocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            use_gpu=True  # Apple Silicon MPS加速
        )
        
    async def extract_text_from_image(self, image_path: str) -> str:
        """从图片提取文字"""
        
    async def extract_text_from_pdf(self, pdf_path: str) -> str:
        """智能PDF处理：文本PDF直接提取，扫描PDF先OCR"""
        
    async def detect_pdf_text_content(self, pdf_path: str) -> bool:
        """检测PDF是否包含可提取文本"""
```

**特性：**
- 双引擎架构：PaddleOCR(主) + Tesseract(备用)
- Apple Silicon优化：MPS硬件加速，性能提升5.4倍
- 智能PDF处理：自动识别文本PDF和扫描PDF
- 并行处理：支持多页PDF并行转换
- 缓存机制：基于MD5避免重复处理

#### 3. 语音服务 (funaudio_service.py)

```python
class FunAudioService:
    def __init__(self):
        self.model = AutoModel(
            model="iic/SenseVoiceSmall",
            device="mps" if torch.backends.mps.is_available() else "cpu"
        )
        
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """语音转文字"""
        
    async def synthesize_speech(self, text: str) -> bytes:
        """文字转语音"""
```

**特性：**
- 高性能识别：比Whisper快15倍，准确率95%+
- Apple Silicon优化：MPS硬件加速
- 多语言支持：中英文混合识别
- 情感分析：支持语音情感检测
- 流式处理：支持实时语音识别

#### 4. 聊天历史服务 (chat_history_service.py)

```python
class ChatHistoryService:
    def __init__(self):
        self.db = get_database()
        
    async def create_session(self, user_id: str, title: str) -> ChatSession:
        """创建聊天会话"""
        
    async def add_message(self, session_id: str, message: CreateMessageDto):
        """添加消息到会话"""
        
    async def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """获取用户所有会话"""
```

**特性：**
- 用户数据隔离：严格的用户权限控制
- 消息类型支持：文本、图片、文件、语音等多模态
- 会话管理：创建、更新、删除、归档等完整操作
- 数据同步：前后端实时同步机制

### 数据库架构

#### 1. SQLite 关系数据库

```sql
-- 聊天会话表
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP
);

-- 聊天消息表
CREATE TABLE chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
);

-- 知识库表
CREATE TABLE knowledge_bases (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档表
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知识库文档关联表
CREATE TABLE knowledge_base_documents (
    knowledge_base_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (knowledge_base_id, document_id)
);
```

#### 2. ChromaDB 向量数据库

```python
# 用户专属Collection命名规则
collection_name = f"user_{user_id}_docs"

# 文档向量化存储
collection.add(
    documents=[chunk_text],
    metadatas=[{
        "doc_id": doc_id,
        "filename": filename,
        "chunk_index": index,
        "user_id": user_id,
        "knowledge_base_id": kb_id,
        "file_type": file_type,
        "created_at": timestamp
    }],
    ids=[chunk_id]
)
```

**特性：**
- 用户数据隔离：每个用户独立的Collection
- 丰富元数据：支持文档信息、分块索引、知识库关联等
- 高效检索：基于余弦相似度的语义搜索
- 持久化存储：数据持久化到磁盘

## 数据流

### 1. 文本聊天流程

```
用户输入 → ChatView组件 → Chat Store → 
sendMessage API → FastAPI路由 → LM Studio → 
流式响应 → 前端实时显示 → 消息保存到数据库
```

### 2. 语音聊天流程

```
用户点击录音 → 浏览器录音API → 音频数据上传 → 
FunAudioLLM识别 → 文本处理 → LM Studio生成回复 → 
TTS语音合成 → 前端播放音频 → 对话历史保存
```

### 3. 文件处理流程

```
文件拖拽上传 → 前端预处理 → 后端接收 → 
文件类型判断 → OCR/PDF处理 → 文本提取 → 
向量化存储 → RAG检索 → AI分析回复
```

### 4. RAG检索流程

```
用户查询 → 查询向量化 → ChromaDB相似度搜索 → 
检索相关文档片段 → 构建上下文 → LM Studio生成回复 → 
引用来源显示 → 用户获得基于文档的准确回答
```

### 5. 智能归档流程

```
文档上传 → 内容分析 → LLM智能分类 → 
知识库推荐 → 用户确认 → 自动归档 → 
向量化索引 → 知识库更新
```

## 微服务架构

### 服务注册与发现

```python
# Nacos服务注册
nacos_client.add_naming_instance(
    service_name="xzxz-lm-service",
    ip=service_ip,
    port=8000,
    cluster_name="DEFAULT",
    weight=1.0,
    metadata={
        "version": "1.0.0",
        "service_type": "ai_chat",
        "framework": "fastapi",
        "features": "multimodal,voice,ocr,rag"
    }
)
```

### 配置管理

```python
# Nacos配置中心
config_data = nacos_client.get_config(
    data_id="xzxz-lm-config",
    group="DEFAULT_GROUP"
)
```

### 健康检查

```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "lm_studio": await check_lm_studio(),
            "database": await check_database(),
            "vector_db": await check_chromadb()
        },
        "network_info": get_network_info()
    }
```

## 性能优化

### 前端优化

1. **代码分割**: 使用 Vue Router 的懒加载和动态导入
2. **组件缓存**: 合理使用 `keep-alive` 缓存页面状态
3. **资源优化**: Vite 自动处理资源压缩、Tree Shaking和缓存
4. **状态管理**: Pinia 提供高效的响应式状态管理
5. **虚拟滚动**: 长列表使用虚拟滚动提升性能
6. **图片懒加载**: 大量图片使用懒加载策略
7. **API缓存**: 合理缓存API响应，减少重复请求

### 后端优化

1. **异步处理**: FastAPI 原生支持异步操作，提升并发性能
2. **连接池**: 数据库和外部服务连接复用
3. **缓存策略**: 
   - OCR结果缓存：避免重复处理相同文件
   - RAG检索缓存：缓存热点查询结果
   - 模型缓存：预加载常用模型
4. **硬件加速**: 
   - Apple Silicon MPS加速
   - GPU加速OCR和语音处理
5. **批量处理**: 文档向量化支持批量操作
6. **智能分块**: 优化文档分块策略，提升检索准确性

### 数据库优化

1. **索引优化**: 为常用查询字段创建索引
2. **分页查询**: 大数据量使用分页避免内存溢出
3. **连接优化**: 使用连接池管理数据库连接
4. **向量数据库优化**: ChromaDB集合分离，提升查询效率

## 安全考虑

### 前端安全

1. **XSS 防护**: Vue 3 自动转义用户输入，防止脚本注入
2. **CSRF 防护**: API 请求使用 token 验证
3. **内容安全策略**: 配置 CSP 头部限制资源加载
4. **输入验证**: 使用 VeeValidate + Zod 进行客户端验证
5. **敏感信息保护**: 避免在前端存储敏感信息

### 后端安全

1. **输入验证**: Pydantic 模型严格验证所有输入数据
2. **文件上传安全**: 
   - 文件类型白名单验证
   - 文件大小限制 (50MB)
   - 文件内容扫描
3. **API 限流**: 防止恶意请求和DDoS攻击
4. **CORS 配置**: 严格控制跨域请求来源
5. **用户认证**: 集成若依Gateway身份验证
6. **数据隔离**: 严格的用户数据隔离机制
7. **SQL注入防护**: 使用参数化查询
8. **日志审计**: 记录关键操作日志

### 数据安全

1. **用户数据隔离**: 每个用户拥有独立的数据空间
2. **数据加密**: 敏感数据加密存储
3. **备份策略**: 定期数据备份和恢复测试
4. **访问控制**: 基于角色的权限控制

## 扩展性设计

### 水平扩展

1. **微服务架构**: 按功能拆分独立服务
2. **负载均衡**: Nginx + 多实例部署
3. **消息队列**: 异步任务处理和服务解耦
4. **数据库分片**: 支持大规模用户数据
5. **CDN 加速**: 静态资源全球分发
6. **容器化部署**: Docker + Kubernetes

### 功能扩展

1. **插件系统**: 支持第三方功能扩展
2. **多语言支持**: Vue i18n 国际化
3. **主题系统**: 可定制的 UI 主题
4. **移动端适配**: 响应式设计 + PWA
5. **API开放**: RESTful API 支持第三方集成
6. **Webhook支持**: 事件驱动的外部集成

### 模型扩展

1. **多模型支持**: 支持不同的LLM模型切换
2. **模型微调**: 支持领域特定模型训练
3. **多语言模型**: 支持多种语言的嵌入模型
4. **专业模型**: 支持代码、医疗、法律等专业模型

## 监控和日志

### 前端监控

1. **错误监控**: 
   - 全局错误捕获和上报
   - 组件错误边界
   - API调用错误追踪
2. **性能监控**: 
   - 页面加载时间
   - 组件渲染性能
   - 内存使用情况
3. **用户行为**: 
   - 操作路径分析
   - 功能使用统计
   - 用户体验指标

### 后端监控

1. **API 监控**: 
   - 请求响应时间
   - 错误率统计
   - 并发量监控
2. **系统监控**: 
   - CPU、内存、磁盘使用率
   - 网络I/O监控
   - 进程状态监控
3. **业务监控**: 
   - 聊天消息量统计
   - 文件处理成功率
   - RAG检索准确性
4. **服务健康**: 
   - 依赖服务状态检查
   - 数据库连接监控
   - 外部API可用性

### 日志系统

```python
# 结构化日志
logger.info("User message processed", extra={
    "user_id": user_id,
    "session_id": session_id,
    "message_type": "text",
    "processing_time": 0.5,
    "model_used": "qwen3-32b"
})
```

## 部署架构

### 开发环境

```
开发者本地 → Vite Dev Server (3004) → FastAPI Dev (8000) → LM Studio (1234)
```

### 生产环境

```
用户 → Nginx (80/443) → Vue Build → FastAPI (Gunicorn) → LM Studio
                     ↓
                  Nacos (8848) ← 服务注册发现
                     ↓
              SQLite + ChromaDB ← 数据持久化
```

### Docker部署

```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./vue-frontend
    ports:
      - "3004:80"
    
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
      - CHROMA_DB_PATH=./data/chroma
    
  nacos:
    image: nacos/nacos-server:v2.2.0
    ports:
      - "8848:8848"
```

## 版本控制和发布

### Git 工作流

```
feature/xxx → develop → staging → main → production
```

### CI/CD 流程

1. **代码检查**: 
   - ESLint、TypeScript 检查
   - Python代码格式化和类型检查
   - 安全漏洞扫描
2. **自动测试**: 
   - 单元测试
   - 集成测试
   - E2E测试
3. **构建部署**: 
   - 自动化构建
   - Docker镜像构建
   - 多环境部署
4. **回滚机制**: 
   - 快速回滚到稳定版本
   - 数据库迁移回滚
   - 配置回滚

## 技术债务和改进计划

### 当前技术债务

1. **测试覆盖率**: 需要增加单元测试和集成测试覆盖率
2. **文档完善**: API 文档和组件文档需要持续更新
3. **性能优化**: 大文件处理和长对话的性能优化
4. **错误处理**: 更完善的错误处理和用户提示机制
5. **国际化**: 多语言支持的完整实现

### 改进计划

#### Q1 2025: 质量提升
- [ ] 完善测试体系，单元测试覆盖率达到80%+
- [ ] 集成测试覆盖核心业务流程
- [ ] 性能基准测试和优化
- [ ] 安全审计和漏洞修复

#### Q2 2025: 功能扩展
- [ ] 移动端适配和PWA支持
- [ ] 多模型支持和模型切换
- [ ] 高级RAG功能（图表理解、表格解析）
- [ ] 协作功能（团队知识库、共享对话）

#### Q3 2025: 企业级功能
- [ ] 多租户架构完善
- [ ] 企业级权限管理
- [ ] 数据分析和报表功能
- [ ] API开放平台

#### Q4 2025: 智能化升级
- [ ] AI Agent功能
- [ ] 工作流自动化
- [ ] 智能推荐系统
- [ ] 个性化定制

## 总结

小智小智项目采用现代化的技术栈和架构设计，具备以下核心优势：

1. **技术先进性**: Vue 3.5 + FastAPI + 最新AI技术栈
2. **用户体验**: 现代化UI设计，流畅的交互体验
3. **功能完整性**: 多模态聊天、语音交互、文档处理、知识库管理
4. **性能优化**: Apple Silicon优化，硬件加速，智能缓存
5. **安全可靠**: 用户数据隔离，完善的权限控制
6. **扩展性强**: 微服务架构，支持水平扩展
7. **企业级**: 支持大规模部署和多租户使用

项目已经具备了生产环境部署的条件，同时保持了良好的可维护性和扩展性，为未来的功能迭代和技术升级奠定了坚实的基础。 