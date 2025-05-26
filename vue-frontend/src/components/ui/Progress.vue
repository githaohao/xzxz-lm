<template>
  <div
    :class="cn(
      'relative h-3 w-full overflow-hidden rounded-full bg-secondary/50 backdrop-blur-sm shadow-inner',
      $attrs.class as string
    )"
  >
    <div
      class="h-full w-full flex-1 bg-gradient-to-r from-primary via-blue-600 to-blue-700 transition-all duration-500 ease-out rounded-full shadow-sm"
      :style="{ transform: `translateX(-${100 - (value || 0)}%)` }"
    />
    <div
      class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-50 animate-pulse"
    />
  </div>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
  value?: number
}

defineProps<Props>()

defineOptions({
  inheritAttrs: false,
})
</script> 