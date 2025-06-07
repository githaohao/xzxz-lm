<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <!-- 登录卡片 -->
      <div class="bg-white rounded-xl shadow-2xl p-8 border border-gray-100">
        <!-- 头部 -->
        <div class="text-center mb-8">
          <div class="flex items-center justify-center mb-4">
            <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <h2 class="text-3xl font-bold text-gray-900 mb-2">小智小智</h2>
          <p class="text-gray-600">多模态AI聊天系统</p>
        </div>

        <!-- 登录表单 -->
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- 用户名输入 -->
          <div>
            <label for="username" class="block text-sm font-medium text-gray-700 mb-2">
              用户名
            </label>
            <div class="relative">
              <input
                id="username"
                v-model="loginForm.username"
                type="text"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 placeholder-gray-400"
                placeholder="请输入用户名"
                :disabled="authStore.isLoading"
              />
              <div class="absolute inset-y-0 right-0 pr-3 flex items-center">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- 密码输入 -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
              密码
            </label>
            <div class="relative">
              <input
                id="password"
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 placeholder-gray-400"
                placeholder="请输入密码"
                :disabled="authStore.isLoading"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
              >
                <svg v-if="showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                </svg>
              </button>
            </div>
          </div>

          <!-- 验证码 -->
          <div v-if="authStore.captcha?.captchaEnabled">
            <label for="captcha" class="block text-sm font-medium text-gray-700 mb-2">
              验证码
            </label>
            <div class="flex space-x-3">
              <input
                id="captcha"
                v-model="loginForm.code"
                type="text"
                required
                class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 placeholder-gray-400"
                placeholder="请输入验证码"
                :disabled="authStore.isLoading"
              />
              <div 
                v-if="authStore.captcha?.img"
                @click="refreshCaptcha"
                class="w-24 h-12 border border-gray-300 rounded-lg cursor-pointer hover:border-blue-400 transition-colors duration-200 flex items-center justify-center bg-gray-50"
                title="点击刷新验证码"
              >
                <img 
                  :src="authStore.captcha.img" 
                  alt="验证码"
                  class="max-w-full max-h-full object-contain"
                />
              </div>
            </div>
          </div>

          <!-- 记住我 -->
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <input
                id="remember-me"
                v-model="loginForm.rememberMe"
                type="checkbox"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label for="remember-me" class="ml-2 block text-sm text-gray-700">
                记住我
              </label>
            </div>
            <div class="text-sm">
              <a href="#" class="font-medium text-blue-600 hover:text-blue-500 transition-colors duration-200">
                忘记密码？
              </a>
            </div>
          </div>

          <!-- 错误提示 -->
          <div v-if="authStore.error" class="bg-red-50 border border-red-200 rounded-lg p-3">
            <div class="flex">
              <svg class="w-5 h-5 text-red-400 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-sm text-red-700">{{ authStore.error }}</p>
            </div>
          </div>

          <!-- 登录按钮 -->
          <button
            type="submit"
            :disabled="authStore.isLoading || !isFormValid"
            class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            <svg v-if="authStore.isLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ authStore.isLoading ? '登录中...' : '登录' }}
          </button>
        </form>

        <!-- 底部链接 -->
        <div class="mt-6 text-center">
          <p class="text-sm text-gray-600">
            还没有账号？
            <a href="#" class="font-medium text-blue-600 hover:text-blue-500 transition-colors duration-200">
              立即注册
            </a>
          </p>
        </div>
      </div>

      <!-- 系统信息 -->
      <div class="text-center text-sm text-gray-500">
        <p>© 2025 小智小智多模态AI聊天系统</p>
        <p class="mt-1">基于若依微服务架构</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { LoginRequest } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

// 表单数据
const loginForm = ref<LoginRequest>({
  username: '',
  password: '',
  code: '',
  uuid: '',
  rememberMe: false
})

// 界面状态
const showPassword = ref(false)

// 表单验证
const isFormValid = computed(() => {
  const hasBasicFields = loginForm.value.username && loginForm.value.password
  const hasCaptcha = !authStore.captcha?.captchaEnabled || loginForm.value.code
  return hasBasicFields && hasCaptcha
})

// 获取验证码
const refreshCaptcha = async () => {
  try {
    await authStore.fetchCaptcha()
    if (authStore.captcha) {
      loginForm.value.uuid = authStore.captcha.uuid
      loginForm.value.code = '' // 清空验证码输入
    }
  } catch (error) {
    console.error('获取验证码失败:', error)
  }
}

// 处理登录
const handleLogin = async () => {
  if (!isFormValid.value) {
    return
  }

  // 清除之前的错误
  authStore.clearError()

  // 设置验证码UUID
  if (authStore.captcha) {
    loginForm.value.uuid = authStore.captcha.uuid
  }

  try {
    const result = await authStore.login(loginForm.value)
    
    if (result.success) {
      // 登录成功，跳转到首页或之前访问的页面
      const redirectPath = router.currentRoute.value.query.redirect as string || '/'
      await router.push(redirectPath)
    } else {
      // 登录失败，如果有验证码就刷新验证码
      if (authStore.captcha?.captchaEnabled) {
        await refreshCaptcha()
      }
    }
  } catch (error) {
    console.error('登录失败:', error)
    // 如果有验证码就刷新验证码
    if (authStore.captcha?.captchaEnabled) {
      await refreshCaptcha()
    }
  }
}

// 组件挂载时初始化
onMounted(async () => {
  // 如果已经登录，直接跳转
  if (authStore.isLoggedIn) {
    const redirectPath = router.currentRoute.value.query.redirect as string || '/'
    await router.push(redirectPath)
    return
  }

  // 获取验证码
  try {
    await refreshCaptcha()
  } catch (error) {
    console.warn('初始化验证码失败:', error)
  }
})
</script>

<style scoped>
/* 自定义样式 */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style> 