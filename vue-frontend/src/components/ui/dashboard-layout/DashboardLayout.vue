<script setup lang="ts">
import { ref } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  sidebarCollapsed?: boolean
  showSidebar?: boolean
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  sidebarCollapsed: false,
  showSidebar: true
})

const emit = defineEmits<{
  toggleSidebar: []
}>()

const toggleSidebar = () => {
  emit('toggleSidebar')
}
</script>

<template>
  <div 
    :class="cn(
      'flex h-screen bg-background',
      props.class
    )"
  >
    <!-- 侧边栏 -->
    <aside 
      v-if="showSidebar"
      :class="cn(
        'flex flex-col border-r border-border/50 bg-sidebar backdrop-blur-sm transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )"
    >
      <!-- 侧边栏头部 -->
      <div class="flex items-center justify-between p-4 border-b border-border/50">
        <div v-if="!sidebarCollapsed" class="flex items-center space-x-2">
          <slot name="sidebar-logo">
            <div class="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
              <span class="text-primary text-sm font-bold">AI</span>
            </div>
            <span class="font-semibold text-sidebar-foreground">控制台</span>
          </slot>
        </div>
        <button 
          @click="toggleSidebar"
          class="p-1 rounded-md hover:bg-sidebar-accent text-sidebar-foreground"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </button>
      </div>
      
      <!-- 侧边栏内容 -->
      <div class="flex-1 overflow-y-auto p-2">
        <slot name="sidebar-content" />
      </div>
      
      <!-- 侧边栏底部 -->
      <div class="p-4 border-t border-border/50">
        <slot name="sidebar-footer" />
      </div>
    </aside>
    
    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- 顶部导航栏 -->
      <header class="flex items-center justify-between p-4 border-b border-border/50 bg-card/50 backdrop-blur-sm">
        <div class="flex items-center space-x-4">
          <button 
            v-if="!showSidebar"
            @click="toggleSidebar"
            class="p-2 rounded-md hover:bg-accent text-foreground"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
          
          <slot name="header-left" />
        </div>
        
        <div class="flex items-center space-x-4">
          <slot name="header-right" />
        </div>
      </header>
      
      <!-- 页面内容 -->
      <div class="flex-1 overflow-y-auto p-6 bg-background">
        <slot />
      </div>
    </main>
  </div>
</template> 