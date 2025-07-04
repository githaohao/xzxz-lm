// 消息类型
export interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  fileInfo?: {
    name: string
    size: number
    type: string
    rag_enabled?: boolean
    doc_id?: string
    ocrCompleted?: boolean
    content?: string
    attachments?: Array<{
      type: string
      url: string
      name: string
      size?: number
    }>
  }
  isStreaming?: boolean
}

// 语音消息类型
export interface VoiceMessage {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  duration?: number
  audioUrl?: string
  recognizedText?: string
}

// 流式事件类型
export interface StreamEvent {
  type: 'file_processing' | 'ocr_processing' | 'ocr_complete' | 'ocr_error' | 'thinking' | 'content' | 'complete' | 'error'
  message?: string
  content?: string
  file_info?: any
}

// 文件处理状态
export interface ProcessedFile {
  name: string
  size: number
  type: string
  processing?: boolean
  ocrCompleted?: boolean
  content?: string  // OCR处理后的内容，用于RAG
  doc_id?: string   // RAG文档ID
  knowledge_base_id?: string  // 知识库ID，用于知识库RAG检索
  rag_enabled?: boolean  // 是否启用RAG
  // PDF智能处理新增字段
  is_pdf?: boolean  // 是否为PDF文件
  is_text_pdf?: boolean | null  // true: 文本PDF, false: 扫描PDF, null: 未检测
  char_count?: number  // 字符数量
  processing_status?: string  // 处理状态信息
  rag_processed?: boolean  // 是否已进行RAG处理
  attachments?: Array<{
    type: string
    url: string
    name: string
    size?: number
  }>
}

// RAG文档块
export interface DocumentChunk {
  chunk_id: string
  content: string
  similarity: number
  metadata: Record<string, any>
}

// RAG检索请求
export interface RAGSearchRequest {
  query: string
  doc_ids?: string[]
  similarity_threshold?: number
}

// RAG检索响应
export interface RAGSearchResponse {
  chunks: DocumentChunk[]
  total_found: number
  search_time: number
  length?: number  // 兼容数组length属性
}

// RAG文档项
export interface RAGDocument {
  doc_id: string
  filename: string
  file_type: string
  created_at: string
  chunk_count: number
  total_length: number
}

// RAG文档列表响应
export interface RAGDocumentsResponse {
  documents: RAGDocument[]
  total_count: number
  processing_time: number
}

// 通话状态
export type CallState = 'idle' | 'connecting' | 'connected' | 'speaking' | 'listening' | 'processing'

// 后端消息格式
export interface BackendMessage {
  id: string
  content: string
  message_type: string
  timestamp: string
  is_user: boolean
  file_name: string | null
  file_size: number | null
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
}

// 语音识别响应
export interface VoiceRecognitionResponse {
  success: boolean
  recognized_text: string
  response: string
  history_length?: number
  error?: string
}

// TTS请求参数
export interface TTSRequest {
  text: string
  voice?: string
  rate?: number
  pitch?: number
}

// 对话类型
export interface Conversation {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  messageCount: number
  lastMessage?: string
  tags?: string[]
  isActive?: boolean
  historySessionId?: string  // 关联的聊天历史会话ID
}

// 对话消息历史
export interface ConversationData {
  conversation: Conversation
  messages: Message[]
  ragDocuments: RAGDocument[]  // 与该对话关联的文档
}

// 创建对话请求
export interface CreateConversationRequest {
  title?: string
  initialMessage?: string
}

// 对话列表响应
export interface ConversationsResponse {
  conversations: Conversation[]
  total: number
}

// 知识库类型
export interface KnowledgeBase {
  id: string
  name: string
  description?: string
  documentIds: string[]  // 关联的文档ID列表
  createdAt: Date
  updatedAt: Date
  color?: string  // 用于UI区分的颜色
  isDefault?: boolean  // 是否为默认知识库
}

// 知识库创建请求
export interface CreateKnowledgeBaseRequest {
  name: string
  description?: string
  color?: string
}

// 知识库更新请求
export interface UpdateKnowledgeBaseRequest {
  name?: string
  description?: string
  color?: string
}

// 文档移动请求
export interface MoveDocumentsRequest {
  documentIds: string[]
  targetKnowledgeBaseId: string
  sourceKnowledgeBaseId?: string
}

// 知识库统计信息
export interface KnowledgeBaseStats {
  totalDocuments: number
  totalChunks: number
  totalSize: number
  recentlyAdded: number  // 最近7天添加的文档数
}

// 文档搜索选项
export interface DocumentSearchOptions {
  query?: string
  knowledgeBaseId?: string
  fileTypes?: string[]
  dateRange?: {
    start: Date
    end: Date
  }
  sortBy?: 'name' | 'date' | 'size'
  sortOrder?: 'asc' | 'desc'
}

// ==================== 若依微服务用户系统类型定义 ====================

// 登录请求
export interface LoginRequest {
  username: string
  password: string
  code?: string      // 验证码
  uuid?: string      // 验证码UUID
  rememberMe?: boolean
}

// 登录响应
export interface LoginResponse {
  code: number
  msg: string
  access_token?: string
  expires_in?: number
}

// 用户信息
export interface UserInfo {
  user: {
    userId: number
    userName: string
    nickName: string
    email: string
    phonenumber: string
    sex: string
    avatar: string
    status: string
    delFlag: string
    loginIp: string
    loginDate: string
    createBy: string
    createTime: string
    updateBy: string
    updateTime: string
    remark: string
    dept: {
      deptId: number
      parentId: number
      ancestors: string
      deptName: string
      orderNum: number
      leader: string
      phone: string
      email: string
      status: string
      delFlag: string
      createBy: string
      createTime: string
      updateBy: string
      updateTime: string
    }
    roles: Array<{
      roleId: number
      roleName: string
      roleKey: string
      roleSort: number
      dataScope: string
      menuCheckStrictly: boolean
      deptCheckStrictly: boolean
      status: string
      delFlag: string
      createBy: string
      createTime: string
      updateBy: string
      updateTime: string
      flag: boolean
      menuIds: number[]
      deptIds: number[]
      permissions: string[]
    }>
    roleIds: number[]
    postIds: number[]
    roleId: number
    admin: boolean
  }
  roles: string[]
  permissions: string[]
}

// 菜单项
export interface MenuItem {
  menuId: number
  menuName: string
  parentId: number
  orderNum: number
  path: string
  component: string
  query: string
  isFrame: number
  isCache: number
  menuType: string
  visible: string
  status: string
  perms: string
  icon: string
  createBy: string
  createTime: string
  updateBy: string
  updateTime: string
  remark: string
  children?: MenuItem[]
}

// 路由信息
export interface RouterInfo {
  name: string
  path: string
  hidden: boolean
  redirect?: string
  component: string
  query?: string
  alwaysShow?: boolean
  meta: {
    title: string
    icon: string
    noCache: boolean
    link?: string
  }
  children?: RouterInfo[]
}

// 验证码响应
export interface CaptchaResponse {
  code: number
  msg: string
  captchaEnabled: boolean
  uuid: string
  img: string
}

// 用户资料更新请求
export interface UpdateProfileRequest {
  nickName?: string
  email?: string
  phonenumber?: string
  sex?: string
  remark?: string
}

// 密码修改请求
export interface ChangePasswordRequest {
  oldPassword: string
  newPassword: string
  confirmPassword: string
}

// 头像上传响应
export interface AvatarUploadResponse {
  code: number
  msg: string
  imgUrl?: string
}

// 通用API响应格式（若依标准）
export interface RuoyiResponse<T = any> {
  code: number
  msg: string
  data?: T
  rows?: T[]
  total?: number
}

// 用户信息API特殊响应格式（实际返回格式）
export interface UserInfoResponse {
  code: number
  msg: string
  permissions: string[]
  roles: string[]
  user: UserInfo['user']
}

// Token信息
export interface TokenInfo {
  token: string
  expires_in: number
  refresh_token?: string
  token_type?: string
}

// ==================== 聊天历史服务相关类型 ====================

// 聊天会话类型
export interface ChatSession {
  id: string
  user_id: number
  title: string
  description?: string
  status: 'active' | 'archived' | 'deleted'
  tags?: string[]
  last_message_at?: string
  message_count: number
  created_at: string
  updated_at: string
  messages?: ChatMessage[]
}

// 聊天消息类型
export interface ChatMessage {
  id: string
  session_id: string
  user_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  message_type: 'text' | 'voice' | 'image' | 'file' | 'multimodal'
  metadata?: {
    filePath?: string
    fileName?: string
    fileSize?: number
    duration?: number
    imageWidth?: number
    imageHeight?: number
    voiceUrl?: string
    attachments?: Array<{
      type: string
      url: string
      name: string
      size?: number
    }>
    [key: string]: any
  }
  status: 'sent' | 'delivered' | 'read' | 'failed'
  parent_message_id?: string
  sequence_number: number
  created_at: string
}

// 创建会话DTO
export interface CreateSessionDto {
  title?: string
  description?: string
  tags?: string[]
}

// 创建消息DTO
export interface CreateMessageDto {
  sessionId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  messageType?: 'text' | 'voice' | 'image' | 'file' | 'multimodal'
  metadata?: {
    filePath?: string
    fileName?: string
    fileSize?: number
    duration?: number
    imageWidth?: number
    imageHeight?: number
    voiceUrl?: string
    attachments?: Array<{
      type: string
      url: string
      name: string
      size?: number
    }>
    [key: string]: any
  }
  parentMessageId?: string
}

// 查询会话DTO
export interface QuerySessionsDto {
  page?: number
  limit?: number
  status?: 'active' | 'archived' | 'deleted'
  search?: string
  sortBy?: 'createdAt' | 'updatedAt' | 'lastMessageAt' | 'messageCount'
  sortOrder?: 'ASC' | 'DESC'
}

// 聊天历史服务响应类型
export interface ChatHistoryResponse<T = any> {
  code: number
  msg: string
  data?: T
  pagination?: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

// 聊天统计信息
export interface ChatStatsResponse {
  totalSessions: number
  totalMessages: number
  archivedSessions: number
}

// 分页响应类型
export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
} 