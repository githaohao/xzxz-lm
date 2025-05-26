<template>
  <div
    :class="cn('animate-pulse rounded-lg bg-gradient-to-r from-muted/50 via-muted/80 to-muted/50 bg-[length:200%_100%] animate-shimmer', $attrs.class as string)"
  />
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

defineOptions({
  inheritAttrs: false,
})
</script> 