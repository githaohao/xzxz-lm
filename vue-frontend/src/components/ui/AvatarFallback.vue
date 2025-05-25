<template>
  <div
    :class="cn(
      'flex h-full w-full items-center justify-center rounded-full bg-muted',
      $attrs.class as string
    )"
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