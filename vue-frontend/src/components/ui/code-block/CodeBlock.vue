<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface Props {
  code: string
  language?: string
  filename?: string
  copyable?: boolean
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  language: 'javascript',
  copyable: true
})

const copied = ref(false)

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}
</script>

<template>
  <div 
    :class="cn(
      'relative rounded-lg border border-border/50 bg-muted/50 backdrop-blur-sm overflow-hidden',
      props.class
    )"
  >
    <!-- 头部 -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-border/50 bg-card/50">
      <div class="flex items-center space-x-2">
        <div class="flex space-x-1">
          <div class="w-3 h-3 rounded-full bg-red-500/60"></div>
          <div class="w-3 h-3 rounded-full bg-yellow-500/60"></div>
          <div class="w-3 h-3 rounded-full bg-green-500/60"></div>
        </div>
        <span v-if="filename" class="text-sm text-muted-foreground font-mono">
          {{ filename }}
        </span>
        <span v-else class="text-sm text-muted-foreground">
          {{ language }}
        </span>
      </div>
      
      <Button
        v-if="copyable"
        variant="ghost"
        size="sm"
        @click="copyToClipboard"
        class="h-8 px-2 text-muted-foreground hover:text-foreground"
      >
        <span v-if="copied" class="text-xs">已复制</span>
        <span v-else class="text-xs">复制</span>
      </Button>
    </div>
    
    <!-- 代码内容 -->
    <div class="p-4 overflow-auto">
      <pre class="text-sm font-mono text-foreground leading-relaxed"><code>{{ code }}</code></pre>
    </div>
    
    <!-- 渐变光效 -->
    <div class="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-accent/5 pointer-events-none" />
  </div>
</template> 