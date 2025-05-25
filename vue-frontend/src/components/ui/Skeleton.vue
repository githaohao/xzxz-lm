<template>
  <div
    :class="cn('animate-pulse rounded-md bg-primary/10', $attrs.class as string)"
  />
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

defineOptions({
  inheritAttrs: false,
})
</script> 