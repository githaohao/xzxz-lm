<template>
  <div
    :class="cn('text-sm [&_p]:leading-relaxed', $attrs.class as string)"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

defineOptions({
  inheritAttrs: false,
})
</script> 