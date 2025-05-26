<script setup lang="ts">
import { computed } from 'vue'
import { Button } from '@/components/ui/button'
import { useTheme } from '@/composables/useTheme'

const { theme, toggleTheme } = useTheme()

const themeIcon = computed(() => {
  switch (theme.value) {
    case 'light':
      return '☀️'
    case 'dark':
      return '🌙'
    case 'system':
      return '💻'
    default:
      return '💻'
  }
})

const themeText = computed(() => {
  switch (theme.value) {
    case 'light':
      return '浅色'
    case 'dark':
      return '深色'
    case 'system':
      return '跟随系统'
    default:
      return '跟随系统'
  }
})
</script>

<template>
  <Button
    variant="ghost"
    size="sm"
    @click="toggleTheme"
    class="flex items-center gap-2 px-3 py-2 transition-all duration-200"
    :title="`当前主题: ${themeText}`"
  >
    <span class="text-base">{{ themeIcon }}</span>
    <span class="text-xs hidden sm:inline">{{ themeText }}</span>
  </Button>
</template> 