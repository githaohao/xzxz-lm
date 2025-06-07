import type { TokenInfo, UserInfo } from '@/types'

// Token存储键名
const TOKEN_KEY = 'xzxz-lm-token'
const USER_INFO_KEY = 'xzxz-lm-user-info'
const REFRESH_TOKEN_KEY = 'xzxz-lm-refresh-token'

/**
 * Token管理工具类
 */
export class AuthManager {
  private static instance: AuthManager
  private tokenInfo: TokenInfo | null = null
  private userInfo: UserInfo | null = null

  private constructor() {
    this.loadFromStorage()
  }

  public static getInstance(): AuthManager {
    if (!AuthManager.instance) {
      AuthManager.instance = new AuthManager()
    }
    return AuthManager.instance
  }

  /**
   * 从本地存储加载认证信息
   */
  private loadFromStorage(): void {
    try {
      const tokenStr = localStorage.getItem(TOKEN_KEY)
      const userInfoStr = localStorage.getItem(USER_INFO_KEY)
      
      if (tokenStr) {
        this.tokenInfo = JSON.parse(tokenStr)
      }
      
      if (userInfoStr) {
        this.userInfo = JSON.parse(userInfoStr)
      }
    } catch (error) {
      console.error('加载认证信息失败:', error)
      this.clearAuth()
    }
  }

  /**
   * 保存Token信息
   */
  public setToken(tokenInfo: TokenInfo): void {
    this.tokenInfo = tokenInfo
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokenInfo))
    
    if (tokenInfo.refresh_token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, tokenInfo.refresh_token)
    }
  }

  /**
   * 获取Token
   */
  public getToken(): string | null {
    if (!this.tokenInfo) {
      return null
    }

    // 检查token是否过期
    if (this.isTokenExpired()) {
      console.warn('Token已过期')
      return null
    }

    return this.tokenInfo.token
  }

  /**
   * 获取完整的Token信息
   */
  public getTokenInfo(): TokenInfo | null {
    return this.tokenInfo
  }

  /**
   * 检查Token是否过期
   */
  public isTokenExpired(): boolean {
    if (!this.tokenInfo || !this.tokenInfo.expires_in) {
      return true
    }

    // 获取token创建时间（从localStorage的存储时间推算）
    const tokenStr = localStorage.getItem(TOKEN_KEY)
    if (!tokenStr) {
      return true
    }

    try {
      // 简单的过期检查，实际项目中可能需要更精确的时间管理
      const now = Date.now()
      const expiresIn = this.tokenInfo.expires_in * 1000 // 转换为毫秒
      
      // 这里简化处理，实际应该记录token的创建时间
      // 暂时返回false，让后端来验证token有效性
      return false
    } catch (error) {
      console.error('检查token过期状态失败:', error)
      return true
    }
  }

  /**
   * 获取刷新Token
   */
  public getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  }

  /**
   * 保存用户信息
   */
  public setUserInfo(userInfo: UserInfo): void {
    this.userInfo = userInfo
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo))
  }

  /**
   * 获取用户信息
   */
  public getUserInfo(): UserInfo | null {
    return this.userInfo
  }

  /**
   * 检查是否已登录
   */
  public isLoggedIn(): boolean {
    return !!this.getToken() && !!this.userInfo
  }

  /**
   * 检查用户是否有指定权限
   */
  public hasPermission(permission: string): boolean {
    if (!this.userInfo || !this.userInfo.permissions) {
      return false
    }
    return this.userInfo.permissions.includes(permission)
  }

  /**
   * 检查用户是否有指定角色
   */
  public hasRole(role: string): boolean {
    if (!this.userInfo || !this.userInfo.roles) {
      return false
    }
    return this.userInfo.roles.includes(role)
  }

  /**
   * 检查用户是否为管理员
   */
  public isAdmin(): boolean {
    return this.userInfo?.user?.admin === true || this.hasRole('admin')
  }

  /**
   * 清除认证信息
   */
  public clearAuth(): void {
    this.tokenInfo = null
    this.userInfo = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_INFO_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  /**
   * 获取Authorization请求头
   */
  public getAuthHeader(): Record<string, string> {
    const token = this.getToken()
    if (token) {
      return {
        'Authorization': `Bearer ${token}`
      }
    }
    return {}
  }

  /**
   * 更新用户头像
   */
  public updateAvatar(avatarUrl: string): void {
    if (this.userInfo && this.userInfo.user) {
      this.userInfo.user.avatar = avatarUrl
      this.setUserInfo(this.userInfo)
    }
  }

  /**
   * 更新用户资料
   */
  public updateProfile(profile: Partial<UserInfo['user']>): void {
    if (this.userInfo && this.userInfo.user) {
      Object.assign(this.userInfo.user, profile)
      this.setUserInfo(this.userInfo)
    }
  }
}

// 导出单例实例
export const authManager = AuthManager.getInstance()

// 便捷函数
export const getToken = () => authManager.getToken()
export const isLoggedIn = () => authManager.isLoggedIn()
export const getUserInfo = () => authManager.getUserInfo()
export const hasPermission = (permission: string) => authManager.hasPermission(permission)
export const hasRole = (role: string) => authManager.hasRole(role)
export const isAdmin = () => authManager.isAdmin()
export const clearAuth = () => authManager.clearAuth()
export const getAuthHeader = () => authManager.getAuthHeader() 