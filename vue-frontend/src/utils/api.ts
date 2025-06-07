import type { 
  Message, 
  VoiceMessage, 
  BackendMessage, 
  VoiceRecognitionResponse, 
  TTSRequest,
  ProcessedFile,
  RAGSearchRequest,
  RAGSearchResponse,
  LoginRequest,
  LoginResponse,
  UserInfo,
  UserInfoResponse,
  CaptchaResponse,
  UpdateProfileRequest,
  ChangePasswordRequest,
  AvatarUploadResponse,
  MenuItem,
  RouterInfo,
  RuoyiResponse
} from '@/types'
import { API_CONFIG } from './api-config'
import { authManager } from './auth'

// 统一的fetch封装类
class ApiClient {
  private baseURL: string
  private timeout: number

  constructor(baseURL: string = '', timeout: number = 30000) {
    this.baseURL = baseURL
    this.timeout = timeout
  }

  // 统一的请求方法
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {},
    skipAuth: boolean = false
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    // 创建AbortController用于超时控制
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    // 合并请求头，自动添加认证头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }

    // 如果不跳过认证且有token，添加Authorization头
    if (!skipAuth && authManager.getToken()) {
      Object.assign(headers, authManager.getAuthHeader())
    }

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new ApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          endpoint
        )
      }

      // 如果是流式响应，直接返回Response对象
      const responseHeaders = options.headers as Record<string, string> | undefined
      if (responseHeaders?.['Accept'] === 'text/event-stream') {
        return response as unknown as T
      }

      // 如果是ArrayBuffer响应
      if (response.headers.get('content-type')?.includes('application/octet-stream')) {
        return (await response.arrayBuffer()) as unknown as T
      }

      // 默认JSON响应
      return await response.json()
    } catch (error: any) {
      clearTimeout(timeoutId)
      
      if (error instanceof ApiError) {
        throw error
      }

      if (error.name === 'AbortError') {
        throw new ApiError(`${API_CONFIG.ERROR_MESSAGES.TIMEOUT} (${this.timeout}ms)`, 408, endpoint)
      }

      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new ApiError(API_CONFIG.ERROR_MESSAGES.NETWORK, 0, endpoint)
      }

      throw new ApiError(
        error.message || API_CONFIG.ERROR_MESSAGES.UNKNOWN,
        0,
        endpoint
      )
    }
  }

  // GET请求
  async get<T>(endpoint: string, params?: Record<string, any>, skipAuth: boolean = false): Promise<T> {
    const url = params ? `${endpoint}?${new URLSearchParams(params)}` : endpoint
    return this.request<T>(url, { method: 'GET' }, skipAuth)
  }

  // POST请求
  async post<T>(
    endpoint: string, 
    data?: any, 
    options: RequestInit = {},
    skipAuth: boolean = false
  ): Promise<T> {
    const body = data instanceof FormData ? data : JSON.stringify(data)
    const postHeaders: Record<string, string> = data instanceof FormData 
      ? {} 
      : { 'Content-Type': 'application/json' }

    return this.request<T>(endpoint, {
      method: 'POST',
      body,
      headers: { ...postHeaders, ...(options.headers as Record<string, string> || {}) },
      ...options,
    }, skipAuth)
  }

  // DELETE请求
  async delete<T>(endpoint: string, skipAuth: boolean = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' }, skipAuth)
  }

  // 流式请求
  async stream(
    endpoint: string, 
    data?: any, 
    signal?: AbortSignal
  ): Promise<Response> {
    const url = `${this.baseURL}${endpoint}`
    
    // 准备请求头，包含认证信息
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    }
    
    // 添加认证头
    if (authManager.getToken()) {
      Object.assign(headers, authManager.getAuthHeader())
    }
    
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal,
    })

    if (!response.ok) {
      throw new ApiError(
        `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        endpoint
      )
    }

    return response
  }

  // 文件上传请求
  async upload<T>(
    endpoint: string, 
    formData: FormData, 
    timeout?: number
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    const uploadTimeout = timeout || 60000

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), uploadTimeout)

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new ApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          endpoint
        )
      }

      return await response.json()
    } catch (error: any) {
      clearTimeout(timeoutId)
      
      if (error instanceof ApiError) {
        throw error
      }

      if (error.name === 'AbortError') {
        throw new ApiError(`${API_CONFIG.ERROR_MESSAGES.UPLOAD_TIMEOUT} (${uploadTimeout}ms)`, 408, endpoint)
      }

      throw new ApiError(
        error.message || API_CONFIG.ERROR_MESSAGES.UPLOAD_FAILED,
        0,
        endpoint
      )
    }
  }
}

// 自定义错误类
export class ApiError extends Error {
  public status: number
  public endpoint: string

  constructor(message: string, status: number, endpoint: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.endpoint = endpoint
  }
}

// 创建API客户端实例
const api = new ApiClient(API_CONFIG.BASE_URL)

// 转换消息格式为后端需要的格式
export function convertToBackendMessages(messages: Message[], limit: number = 10): BackendMessage[] {
  const recentMessages = messages.slice(-limit)
  
  return recentMessages.map(msg => ({
    id: msg.id,
    content: msg.content,
    message_type: "text",
    timestamp: msg.timestamp.toISOString(),
    is_user: msg.isUser,
    file_name: msg.fileInfo?.name || null,
    file_size: msg.fileInfo?.size || null
  }))
}

// 文本聊天流式API
export async function sendTextMessage(
  message: string,
  history: Message[],
  temperature: number = 0.7,
  maxTokens: number = 2048,
  signal?: AbortSignal
): Promise<Response> {
  return api.stream(API_CONFIG.ENDPOINTS.CHAT_STREAM, {
    message,
    history: convertToBackendMessages(history),
    temperature,
    max_tokens: maxTokens
  }, signal)
}

// 多模态聊天流式API
export async function sendMultimodalMessage(
  message: string,
  history: Message[],
  fileData: ProcessedFile,
  temperature: number = 0.7,
  maxTokens: number = 2048,
  signal?: AbortSignal
): Promise<Response> {
  return api.stream(API_CONFIG.ENDPOINTS.MULTIMODAL_STREAM, {
    message,
    history: convertToBackendMessages(history),
    file_data: {
      name: fileData.name,
      type: fileData.type,
      size: fileData.size,
      content: fileData.content || null,
      ocr_completed: fileData.ocrCompleted || false,
      doc_id: fileData.doc_id || null,
      rag_enabled: fileData.rag_enabled || false
    },
    temperature,
    max_tokens: maxTokens
  }, signal)
}

// 语音聊天API
export async function sendVoiceMessage(
  audioBlob: Blob,
  sessionId: string,
  language: string = 'auto'
): Promise<VoiceRecognitionResponse> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'voice.wav')
  formData.append('session_id', sessionId)
  formData.append('language', language)

  return api.upload<VoiceRecognitionResponse>(
    API_CONFIG.ENDPOINTS.VOICE_CHAT, 
    formData, 
    API_CONFIG.TIMEOUT.VOICE
  )
}

// TTS语音合成API
export async function synthesizeSpeech(params: TTSRequest): Promise<ArrayBuffer> {
  return api.post<ArrayBuffer>(API_CONFIG.ENDPOINTS.VOICE_TTS, params, {
    headers: API_CONFIG.HEADERS.BINARY
  })
}

// 检查FunAudioLLM服务状态
export async function checkFunAudioStatus(): Promise<boolean> {
  try {
    const response = await api.get<any>(API_CONFIG.ENDPOINTS.VOICE_ENGINE)
    // 处理后端返回的嵌套数据结构
    if (response.success && response.engine && response.engine.status) {
      return response.engine.status.available || false
    }
    // 兼容旧的数据结构
    return response.available || false
  } catch (error) {
    console.error('检查FunAudioLLM状态失败:', error)
    return false
  }
}

// 清除对话历史
export async function clearConversationHistory(sessionId: string): Promise<boolean> {
  try {
    await api.delete(`${API_CONFIG.ENDPOINTS.VOICE_CONVERSATION}/${sessionId}`)
    return true
  } catch (error) {
    console.error('清除对话历史失败:', error)
    return false
  }
}

// 文件上传和处理
export async function uploadFile(file: File): Promise<ProcessedFile> {
  const formData = new FormData()
  formData.append('file', file)

  // 1. 先上传文件
  const uploadResult = await api.upload<any>(
    API_CONFIG.ENDPOINTS.UPLOAD, 
    formData, 
    API_CONFIG.TIMEOUT.UPLOAD
  )

  let ocrCompleted = false
  let content: string | undefined = undefined
  let docId: string | undefined = undefined
  let ragEnabled = false

  // 2. 如果是支持OCR的文件类型，进行OCR处理
  const fileExt = file.name.toLowerCase().split('.').pop()
  if (fileExt && ['pdf', 'png', 'jpg', 'jpeg'].includes(fileExt)) {
    try {
      const ocrFormData = new FormData()
      ocrFormData.append('file_path', uploadResult.file_path)

      const ocrResponse = await api.upload<any>(
        API_CONFIG.ENDPOINTS.OCR, 
        ocrFormData, 
        API_CONFIG.TIMEOUT.OCR
      )
      content = ocrResponse.text // 保存OCR文本用于RAG
      ocrCompleted = true // OCR处理完成

      // 3. 如果OCR成功且有内容，进行RAG文档处理
      if (content && content.trim().length > 50) {
        try {
          docId = await processDocumentForRAG(content, file.name, file.type)
          ragEnabled = true
          console.log('✅ RAG文档处理完成，doc_id:', docId)
        } catch (ragError) {
          console.warn('⚠️ RAG文档处理失败:', ragError)
          // RAG处理失败不影响文件使用
        }
      }
    } catch (ocrError) {
      console.warn('OCR处理失败:', ocrError)
      // OCR失败不影响文件上传，继续处理
      ocrCompleted = false
    }
  } else {
    // 非OCR文件类型，直接标记为完成
    ocrCompleted = true
  }

  return {
    name: file.name,
    size: file.size,
    type: file.type,
    content,
    ocrCompleted,
    processing: !ocrCompleted, // 如果OCR未完成，则仍处于处理中状态
    doc_id: docId,
    rag_enabled: ragEnabled
  }
}

// 健康检查
export async function healthCheck(): Promise<any> {
  return api.get(API_CONFIG.ENDPOINTS.HEALTH)
}

// 获取所有RAG文档列表
export async function getAllDocuments(): Promise<any> {
  return api.get(API_CONFIG.ENDPOINTS.RAG_DOCUMENTS)
}

// 删除RAG文档
export async function deleteDocument(docId: string): Promise<boolean> {
  try {
    await api.delete(`${API_CONFIG.ENDPOINTS.RAG_DOCUMENTS}/${docId}`)
    return true
  } catch (error) {
    console.error('删除文档失败:', error)
    return false
  }
}

// RAG文档检索
export async function searchDocuments(request: RAGSearchRequest): Promise<RAGSearchResponse> {
  return api.post<RAGSearchResponse>(API_CONFIG.ENDPOINTS.RAG_SEARCH, request)
}

// 处理文档进行RAG索引
export async function processDocumentForRAG(
  content: string,
  filename: string,
  fileType: string
): Promise<string> {
  const formData = new FormData()
  formData.append('content', content)
  formData.append('filename', filename)
  formData.append('file_type', fileType)

  const response = await api.upload<any>(
    API_CONFIG.ENDPOINTS.RAG_PROCESS, 
    formData, 
    API_CONFIG.TIMEOUT.RAG
  )
  return response.doc_id
}

// 获取文档信息
export async function getDocumentInfo(docId: string): Promise<any> {
  return api.get(`${API_CONFIG.ENDPOINTS.RAG_DOCUMENTS}/${docId}`)
}

// ==================== 若依微服务用户系统API ====================

/**
 * 获取验证码
 */
export async function getCaptcha(): Promise<CaptchaResponse> {
  return api.get<CaptchaResponse>(API_CONFIG.ENDPOINTS.SYSTEM_CAPTCHA, undefined, true)
}

/**
 * 用户登录
 */
export async function login(loginData: LoginRequest): Promise<RuoyiResponse<LoginResponse>> {
  const response = await api.post<RuoyiResponse<LoginResponse>>(
    API_CONFIG.ENDPOINTS.SYSTEM_LOGIN, 
    loginData,
    {},
    true // 跳过认证，因为这是登录请求
  )
  
  // 如果登录成功，保存token和用户信息
  if (response.code === 200 && response.data?.access_token) {
    authManager.setToken({
      token: response.data.access_token,
      expires_in: response.data.expires_in || 7200,
      token_type: 'Bearer'
    })
    
    // 登录成功后获取用户信息
    try {
      await getUserInfo()
    } catch (error) {
      console.warn('获取用户信息失败:', error)
    }
  }
  
  return response
}

/**
 * 用户退出登录
 */
export async function logout(): Promise<RuoyiResponse> {
  try {
    const response = await api.post<RuoyiResponse>(API_CONFIG.ENDPOINTS.SYSTEM_LOGOUT)
    return response
  } finally {
    // 无论后端响应如何，都清除本地认证信息
    authManager.clearAuth()
  }
}

/**
 * 获取用户信息
 */
export async function getUserInfo(): Promise<UserInfoResponse> {
  const response = await api.get<UserInfoResponse>(API_CONFIG.ENDPOINTS.SYSTEM_USER_INFO)
  
  // 如果获取成功，保存用户信息
  if (response.code === 200 && response.user) {
    // 构建标准的UserInfo格式
    const userInfo: UserInfo = {
      user: response.user,
      permissions: response.permissions || [],
      roles: response.roles || []
    }
    authManager.setUserInfo(userInfo)
  }
  
  return response
}

/**
 * 获取用户资料
 */
export async function getUserProfile(): Promise<RuoyiResponse<UserInfo['user']>> {
  return api.get<RuoyiResponse<UserInfo['user']>>(API_CONFIG.ENDPOINTS.SYSTEM_USER_PROFILE)
}

/**
 * 更新用户资料
 */
export async function updateUserProfile(profileData: UpdateProfileRequest): Promise<RuoyiResponse> {
  const response = await api.post<RuoyiResponse>(
    API_CONFIG.ENDPOINTS.SYSTEM_USER_PROFILE, 
    profileData
  )
  
  // 如果更新成功，更新本地用户信息
  if (response.code === 200) {
    authManager.updateProfile(profileData)
  }
  
  return response
}

/**
 * 上传用户头像
 */
export async function uploadAvatar(avatarFile: File): Promise<RuoyiResponse<AvatarUploadResponse>> {
  const formData = new FormData()
  formData.append('avatarfile', avatarFile)
  
  const response = await api.upload<RuoyiResponse<AvatarUploadResponse>>(
    API_CONFIG.ENDPOINTS.SYSTEM_USER_AVATAR,
    formData,
    API_CONFIG.TIMEOUT.UPLOAD
  )
  
  // 如果上传成功，更新本地用户头像
  if (response.code === 200 && response.data?.imgUrl) {
    authManager.updateAvatar(response.data.imgUrl)
  }
  
  return response
}

/**
 * 获取菜单列表
 */
export async function getMenuList(): Promise<RuoyiResponse<MenuItem[]>> {
  return api.get<RuoyiResponse<MenuItem[]>>(API_CONFIG.ENDPOINTS.SYSTEM_MENU_LIST)
}

/**
 * 获取路由列表
 */
export async function getRouterList(): Promise<RuoyiResponse<RouterInfo[]>> {
  return api.get<RuoyiResponse<RouterInfo[]>>(API_CONFIG.ENDPOINTS.SYSTEM_ROUTER_LIST)
}

/**
 * 刷新Token
 */
export async function refreshToken(): Promise<RuoyiResponse<LoginResponse>> {
  const refreshToken = authManager.getRefreshToken()
  if (!refreshToken) {
    throw new ApiError('没有可用的刷新Token', 401, API_CONFIG.ENDPOINTS.SYSTEM_REFRESH_TOKEN)
  }
  
  const response = await api.post<RuoyiResponse<LoginResponse>>(
    API_CONFIG.ENDPOINTS.SYSTEM_REFRESH_TOKEN,
    { refreshToken },
    {},
    true // 跳过认证，因为这是刷新token请求
  )
  
  // 如果刷新成功，更新token
  if (response.code === 200 && response.data?.access_token) {
    authManager.setToken({
      token: response.data.access_token,
      expires_in: response.data.expires_in || 7200,
      refresh_token: refreshToken,
      token_type: 'Bearer'
    })
  }
  
  return response
}

/**
 * 检查用户是否有指定权限
 */
export function checkPermission(permission: string): boolean {
  return authManager.hasPermission(permission)
}

/**
 * 检查用户是否有指定角色
 */
export function checkRole(role: string): boolean {
  return authManager.hasRole(role)
}

/**
 * 检查用户是否为管理员
 */
export function checkAdmin(): boolean {
  return authManager.isAdmin()
}

/**
 * 获取当前登录用户信息
 */
export function getCurrentUser(): UserInfo | null {
  return authManager.getUserInfo()
}

/**
 * 检查是否已登录
 */
export function checkLogin(): boolean {
  return authManager.isLoggedIn()
}

export default api 