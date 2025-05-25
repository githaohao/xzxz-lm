<template>
  <div
    :class="cn(
      'relative h-2 w-full overflow-hidden rounded-full bg-primary/20',
      $attrs.class as string
    )"
  >
    <div
      class="h-full w-full flex-1 bg-primary transition-all"
      :style="{ transform: `translateX(-${100 - (value || 0)}%)` }"
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