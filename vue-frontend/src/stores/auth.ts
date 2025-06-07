import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo, UserInfoResponse, LoginRequest, CaptchaResponse, TokenInfo } from '@/types'
import { 
  login as apiLogin, 
  logout as apiLogout, 
  getUserInfo as apiGetUserInfo,
  getCaptcha as apiGetCaptcha,
  refreshToken as apiRefreshToken,
  updateUserProfile as apiUpdateUserProfile,
  uploadAvatar as apiUploadAvatar,
  checkLogin,
  getCurrentUser
} from '@/utils/api'
import { authManager } from '@/utils/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<UserInfo | null>(null)
  const token = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const captcha = ref<CaptchaResponse | null>(null)

  // 计算属性
  const isLoggedIn = computed(() => {
    // 只基于store内的响应式状态，确保登录状态能立即响应变化
    return !!token.value && !!user.value
  })
  const userProfile = computed(() => user.value?.user || null)
  const userRoles = computed(() => user.value?.roles || [])
  const userPermissions = computed(() => user.value?.permissions || [])
  const isAdmin = computed(() => user.value?.user?.admin === true)

  // 同步token状态的辅助方法
  const syncTokenState = () => {
    const currentToken = authManager.getToken()
    token.value = currentToken
  }

  // 初始化用户状态
  const initializeAuth = () => {
    const currentUser = getCurrentUser()
    const currentToken = authManager.getToken()
    
    if (currentUser && currentToken) {
      user.value = currentUser
      token.value = currentToken
      console.log('初始化用户状态成功:', currentUser.user.userName)
    } else {
      user.value = null
      token.value = null
      console.log('未发现已登录用户')
    }
  }

  // 获取验证码
  const fetchCaptcha = async () => {
    try {
      isLoading.value = true
      error.value = null
      captcha.value = await apiGetCaptcha()
    } catch (err: any) {
      error.value = err.message || '获取验证码失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 用户登录
  const login = async (loginData: LoginRequest) => {
    try {
      isLoading.value = true
      error.value = null
      const response = await apiLogin(loginData)
      if (response.code === 200) {
        // 登录成功，立即同步用户信息和token到store
        const currentUser = getCurrentUser()
        const currentToken = authManager.getToken()
        
        if (currentUser && currentToken) {
          user.value = currentUser
          token.value = currentToken
        }
        
        return { success: true, message: '登录成功' }
      } else {
        error.value = response.msg || '登录失败'
        return { success: false, message: response.msg || '登录失败' }
      }
    } catch (err: any) {
      error.value = err.message || '登录失败'
      return { success: false, message: err.message || '登录失败' }
    } finally {
      isLoading.value = false
    }
  }

  // 用户退出登录
  const logout = async () => {
    try {
      isLoading.value = true
      await apiLogout()
    } catch (err) {
      // 即使退出失败，也要清除本地状态
      console.warn('退出登录失败:', err)
    } finally {
      // 清除用户状态（包括Pinia store和AuthManager）
      user.value = null
      token.value = null
      error.value = null
      isLoading.value = false
      // apiLogout已经调用了authManager.clearAuth()
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      isLoading.value = true
      const response: UserInfoResponse = await apiGetUserInfo()
      
      if (response.code === 200) {
        // API返回的数据结构: { code: 200, msg: "", user: {}, permissions: [], roles: [] }
        // 构建用户信息对象
        const userInfo: UserInfo = {
          user: response.user,
          permissions: response.permissions || [],
          roles: response.roles || []
        }
        user.value = userInfo
        return userInfo
      } else {
        throw new Error(response.msg || '获取用户信息失败')
      }
    } catch (err: any) {
      error.value = err.message || '获取用户信息失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 更新用户资料
  const updateProfile = async (profileData: any) => {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await apiUpdateUserProfile(profileData)
      
      if (response.code === 200) {
        // 更新成功后刷新用户信息
        await fetchUserInfo()
        return { success: true, message: '更新成功' }
      } else {
        error.value = response.msg || '更新失败'
        return { success: false, message: response.msg || '更新失败' }
      }
    } catch (err: any) {
      error.value = err.message || '更新失败'
      return { success: false, message: err.message || '更新失败' }
    } finally {
      isLoading.value = false
    }
  }

  // 上传头像
  const uploadUserAvatar = async (file: File) => {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await apiUploadAvatar(file)
      
      if (response.code === 200) {
        // 上传成功后刷新用户信息
        await fetchUserInfo()
        return { success: true, message: '头像上传成功', avatarUrl: response.data?.imgUrl }
      } else {
        error.value = response.msg || '头像上传失败'
        return { success: false, message: response.msg || '头像上传失败' }
      }
    } catch (err: any) {
      error.value = err.message || '头像上传失败'
      return { success: false, message: err.message || '头像上传失败' }
    } finally {
      isLoading.value = false
    }
  }

  // 刷新Token
  const refreshTokenAction = async () => {
    try {
      const response = await apiRefreshToken()
      if (response.code === 200) {
        // 刷新成功后同步token状态
        syncTokenState()
        return true
      }
      return false
    } catch (err) {
      console.error('刷新Token失败:', err)
      return false
    }
  }

  // 检查权限
  const hasPermission = (permission: string): boolean => {
    return authManager.hasPermission(permission)
  }

  // 检查角色
  const hasRole = (role: string): boolean => {
    return authManager.hasRole(role)
  }

  // 清除错误状态
  const clearError = () => {
    error.value = null
  }

  // 初始化
  initializeAuth()

  return {
    // 状态
    user,
    token,
    isLoading,
    error,
    captcha,
    
    // 计算属性
    isLoggedIn,
    userProfile,
    userRoles,
    userPermissions,
    isAdmin,
    
    // 方法
    fetchCaptcha,
    login,
    logout,
    fetchUserInfo,
    updateProfile,
    uploadUserAvatar,
    refreshTokenAction,
    hasPermission,
    hasRole,
    clearError,
    initializeAuth,
    syncTokenState
  }
}) 