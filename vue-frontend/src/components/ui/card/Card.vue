<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <div
    :class="
      cn(
        'rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm text-card-foreground shadow-lg hover:shadow-xl transition-all duration-300 hover:border-border/80 hover:bg-card/70',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>
