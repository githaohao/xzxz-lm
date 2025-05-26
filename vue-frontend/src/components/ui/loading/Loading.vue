<template>
  <div :class="cn('inline-flex items-center justify-center', props.class)">
    <div
      v-if="variant === 'spinner'"
      :class="cn('animate-spin rounded-full border-2 border-muted border-t-primary', sizeClasses)"
    />
    
    <div
      v-else-if="variant === 'pulse'"
      :class="cn('animate-pulse rounded-full bg-gradient-to-r from-primary via-blue-600 to-primary', sizeClasses)"
    />
    
    <div
      v-else-if="variant === 'dots'"
      class="flex space-x-1"
    >
      <div
        v-for="i in 3"
        :key="i"
        :class="cn('animate-bounce rounded-full bg-primary', dotSizeClasses)"
        :style="{ animationDelay: `${i * 0.1}s` }"
      />
    </div>
    
    <div
      v-else-if="variant === 'wave'"
      class="flex space-x-0.5"
    >
      <div
        v-for="i in 5"
        :key="i"
        :class="cn('animate-pulse bg-gradient-to-t from-primary to-blue-600 rounded-sm', waveSizeClasses)"
        :style="{ 
          animationDelay: `${i * 0.1}s`,
          animationDuration: '1s',
          transform: `scaleY(${0.4 + Math.sin(i * 0.5) * 0.6})`
        }"
      />
    </div>
    
    <div
      v-else-if="variant === 'glow'"
      :class="cn('animate-glow rounded-full bg-gradient-to-r from-primary via-blue-600 to-primary shadow-xl', sizeClasses)"
    />
  </div>
</template>

<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  variant?: 'spinner' | 'pulse' | 'dots' | 'wave' | 'glow'
  size?: 'sm' | 'md' | 'lg'
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'spinner',
  size: 'md',
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-4 w-4'
    case 'lg':
      return 'h-8 w-8'
    default:
      return 'h-6 w-6'
  }
})

const dotSizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-1.5 w-1.5'
    case 'lg':
      return 'h-3 w-3'
    default:
      return 'h-2 w-2'
  }
})

const waveSizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-3 w-0.5'
    case 'lg':
      return 'h-8 w-1'
    default:
      return 'h-6 w-0.5'
  }
})
</script>
