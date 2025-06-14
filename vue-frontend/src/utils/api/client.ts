import { API_CONFIG } from '../api-config'
import { authManager } from '../auth'

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

// 统一的fetch封装类
export class ApiClient {
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

  // PUT请求
  async put<T>(
    endpoint: string, 
    data?: any, 
    skipAuth: boolean = false
  ): Promise<T> {
    const body = data instanceof FormData ? data : JSON.stringify(data)
    const putHeaders: Record<string, string> = data instanceof FormData 
      ? {} 
      : { 'Content-Type': 'application/json' }

    return this.request<T>(endpoint, {
      method: 'PUT',
      body,
      headers: putHeaders,
    }, skipAuth)
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

  // 二进制响应请求（如音频、图片等）
  async binary(
    endpoint: string, 
    data?: any, 
    method: string = 'POST'
  ): Promise<ArrayBuffer> {
    const url = `${this.baseURL}${endpoint}`
    
    // 创建AbortController用于超时控制
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    // 准备请求头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    // 添加认证头
    if (authManager.getToken()) {
      Object.assign(headers, authManager.getAuthHeader())
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined,
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

      // 直接返回二进制数据
      return await response.arrayBuffer()
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
}

// 创建API客户端实例
export const api = new ApiClient(API_CONFIG.BASE_URL) 