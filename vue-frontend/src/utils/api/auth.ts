import type { 
  LoginRequest, 
  LoginResponse, 
  UserInfo, 
  UserInfoResponse, 
  CaptchaResponse, 
  UpdateProfileRequest, 
  AvatarUploadResponse, 
  MenuItem, 
  RouterInfo, 
  RuoyiResponse 
} from '@/types'
import { API_CONFIG } from '../api-config'
import { authManager } from '../auth'
import { api } from './client'

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
    throw new Error('没有可用的刷新Token')
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