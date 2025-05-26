<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <tr :class="cn('border-b border-border/30 transition-all duration-300 hover:bg-accent/50 hover:scale-[1.01] data-[state=selected]:bg-accent', props.class)">
    <slot />
  </tr>
</template>
