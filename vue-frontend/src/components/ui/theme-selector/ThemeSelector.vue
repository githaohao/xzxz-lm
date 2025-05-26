<script setup lang="ts">
import { computed } from 'vue'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { useTheme, type Theme } from '@/composables/useTheme'

const { theme, setTheme, getSystemTheme } = useTheme()

const themeOptions = [
  { value: 'light', label: '浅色模式', icon: '☀️' },
  { value: 'dark', label: '深色模式', icon: '🌙' },
  { value: 'system', label: '跟随系统', icon: '💻' }
] as const

const currentThemeInfo = computed(() => {
  return themeOptions.find(option => option.value === theme.value) || themeOptions[2]
})

const systemThemeInfo = computed(() => {
  if (theme.value === 'system') {
    const systemTheme = getSystemTheme()
    return ` (当前: ${systemTheme === 'dark' ? '深色' : '浅色'})`
  }
  return ''
})
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button
        variant="ghost"
        size="sm"
        class="flex items-center gap-2 px-3 py-2 transition-all duration-200"
      >
        <span class="text-base">{{ currentThemeInfo.icon }}</span>
        <span class="text-xs hidden sm:inline">
          {{ currentThemeInfo.label }}{{ systemThemeInfo }}
        </span>
        <svg class="w-3 h-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
        </svg>
      </Button>
    </DropdownMenuTrigger>
    
    <DropdownMenuContent align="end" class="w-40">
      <DropdownMenuItem
        v-for="option in themeOptions"
        :key="option.value"
        @click="setTheme(option.value as Theme)"
        :class="{ 'bg-accent': theme === option.value }"
        class="flex items-center gap-2 cursor-pointer"
      >
        <span class="text-base">{{ option.icon }}</span>
        <span class="text-sm">{{ option.label }}</span>
        <span v-if="theme === option.value" class="ml-auto text-primary">✓</span>
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template> 