<template>
  <div id="app" class="h-screen flex flex-col bg-background">
    <nav class="border-b border-border bg-card">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <router-link to="/" class="text-xl font-bold text-primary">
              小智小智 多模态聊天系统
            </router-link>
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
        </div>
      </div>
    </nav>
    
    <main class="flex-1 overflow-y-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { ThemeSelector } from '@/components/ui/theme-selector'
import { useTheme } from '@/composables/useTheme'
import { useConversationStore } from '@/stores/conversation'

// 初始化主题系统
useTheme()

// 初始化对话系统
const conversationStore = useConversationStore()

onMounted(() => {
  // 初始化对话store
  conversationStore.initialize()
})
</script> 