<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface Props {
  status: 'online' | 'offline' | 'warning' | 'error' | 'processing'
  text?: string
  showDot?: boolean
  size?: 'sm' | 'md' | 'lg'
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  showDot: true,
  size: 'md'
})

const statusConfig = computed(() => {
  const configs = {
    online: {
      color: 'bg-green-500',
      textColor: 'text-green-400',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/20',
      text: '在线'
    },
    offline: {
      color: 'bg-gray-500',
      textColor: 'text-gray-400',
      bgColor: 'bg-gray-500/10',
      borderColor: 'border-gray-500/20',
      text: '离线'
    },
    warning: {
      color: 'bg-yellow-500',
      textColor: 'text-yellow-400',
      bgColor: 'bg-yellow-500/10',
      borderColor: 'border-yellow-500/20',
      text: '警告'
    },
    error: {
      color: 'bg-red-500',
      textColor: 'text-red-400',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/20',
      text: '错误'
    },
    processing: {
      color: 'bg-blue-500',
      textColor: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/20',
      text: '处理中'
    }
  }
  return configs[props.status]
})

const dotSize = computed(() => {
  const sizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5'
  }
  return sizes[props.size]
})

const textSize = computed(() => {
  const sizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  }
  return sizes[props.size]
})
</script>

<template>
  <div 
    :class="cn(
      'inline-flex items-center gap-2 px-2 py-1 rounded-full border backdrop-blur-sm',
      statusConfig.bgColor,
      statusConfig.borderColor,
      props.class
    )"
  >
    <div 
      v-if="showDot"
      :class="cn(
        'rounded-full animate-pulse',
        statusConfig.color,
        dotSize
      )"
    />
    <span 
      :class="cn(
        'font-medium',
        statusConfig.textColor,
        textSize
      )"
    >
      {{ text || statusConfig.text }}
    </span>
  </div>
</template> 