<template>
  <div id="app" class="h-screen flex flex-col bg-background">
    <!-- Stagewise工具栏 - 仅在开发模式下显示 -->
    <StagewiseToolbar 
      v-if="isDev"
      :config="stagewiseConfig" 
    />
    
    <nav class="border-b border-border bg-card">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
   <!-- 左侧Logo -->
         <div class="flex items-center space-x-4">
            <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h1 class="text-xl font-bold text-gray-900">小智小智</h1>
          </div>

          <div class="flex items-center space-x-4">
            <router-link
              to="/"
              class="text-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'text-primary': $route.name === 'home' }"
            >
              首页
            </router-link>
            <router-link
              to="/chat"
              class="text-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'text-primary': $route.name === 'chat' }"
            >
              文本聊天
            </router-link>
            <router-link
              to="/voice-chat"
              class="text-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'text-primary': $route.name === 'voice-chat' }"
            >
              语音聊天
            </router-link>
            <router-link
              to="/simple-voice-chat"
              class="text-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'text-primary': $route.name === 'simple-voice-chat' }"
            >
              简洁语音
            </router-link>
            <router-link
              to="/components"
              class="text-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium"
              :class="{ 'text-primary': $route.name === 'components' }"
            >
              组件展示
            </router-link>
            <ThemeSelector />
          </div>

          <div class="flex items-center space-x-4">
            <!-- 登录/用户信息 -->
            <div v-if="!authStore.isLoggedIn">
              <router-link
                to="/login"
                class="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-all duration-200 shadow-sm"
              >
                登录
              </router-link>
            </div>
            <UserProfile v-else />
          </div>
        </div>
      </div>
    </nav>
    
    <main class="flex-1 overflow-y-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { ThemeSelector } from '@/components/ui/theme-selector'
import { useTheme } from '@/composables/useTheme'
import { useConversationStore } from '@/stores/conversation'
import { useAuthStore } from '@/stores/auth'
import UserProfile from '@/components/UserProfile.vue'
import { StagewiseToolbar } from '@stagewise/toolbar-vue'
import { VuePlugin } from '@stagewise-plugins/vue'

const authStore = useAuthStore()

// Stagewise配置 - 仅在开发模式下启用
const isDev = computed(() => import.meta.env.DEV)
const stagewiseConfig = {
  plugins: [VuePlugin]
}


// 初始化主题系统
useTheme()

// 初始化对话系统
const conversationStore = useConversationStore()

onMounted(async () => {
  // 初始化对话store，从后端同步对话列表
  await conversationStore.initialize()
})
</script> 