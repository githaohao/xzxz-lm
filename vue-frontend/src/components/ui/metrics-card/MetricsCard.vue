<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface Props {
  title: string
  value: string | number
  subtitle?: string
  icon?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  badge?: string
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline'
  gradient?: boolean
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  trendValue: '',
  badge: '',
  badgeVariant: 'default',
  gradient: false
})

const trendIcon = computed(() => {
  switch (props.trend) {
    case 'up':
      return '↗'
    case 'down':
      return '↘'
    default:
      return '→'
  }
})

const trendColor = computed(() => {
  switch (props.trend) {
    case 'up':
      return 'text-green-400'
    case 'down':
      return 'text-red-400'
    default:
      return 'text-muted-foreground'
  }
})
</script>

<template>
  <Card 
    :class="cn(
      'relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:scale-[1.02]',
      gradient && 'bg-gradient-to-br from-card via-card to-secondary/20',
      'border-border/50 backdrop-blur-sm',
      props.class
    )"
  >
    <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-3">
      <CardTitle class="text-sm font-medium text-muted-foreground">
        {{ title }}
      </CardTitle>
      <div class="flex items-center space-x-2">
        <Badge v-if="badge" :variant="badgeVariant" class="text-xs">
          {{ badge }}
        </Badge>
        <span v-if="icon" class="text-lg opacity-70">{{ icon }}</span>
      </div>
    </CardHeader>
    
    <CardContent class="space-y-3">
      <div class="flex items-end justify-between">
        <div class="space-y-1">
          <div 
            :class="cn(
              'text-3xl font-bold tracking-tight',
              gradient && 'gradient-text'
            )"
          >
            {{ value }}
          </div>
          <p v-if="subtitle" class="text-xs text-muted-foreground">
            {{ subtitle }}
          </p>
        </div>
        
        <div v-if="trend && trendValue" class="flex items-center space-x-1 text-xs">
          <span :class="trendColor">{{ trendIcon }}</span>
          <span :class="trendColor" class="font-medium">{{ trendValue }}</span>
        </div>
      </div>
      
      <!-- 可选的进度条或图表区域 -->
      <slot name="chart" />
    </CardContent>
    
    <!-- 渐变光效 -->
    <div 
      v-if="gradient" 
      class="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-accent/5 pointer-events-none"
    />
  </Card>
</template> 