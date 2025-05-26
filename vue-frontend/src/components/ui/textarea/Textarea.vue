<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { useVModel } from '@vueuse/core'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
  defaultValue?: string | number
  modelValue?: string | number
}>()

const emits = defineEmits<{
  (e: 'update:modelValue', payload: string | number): void
}>()

const modelValue = useVModel(props, 'modelValue', emits, {
  passive: true,
  defaultValue: props.defaultValue,
})
</script>

<template>
  <textarea 
    v-model="modelValue" 
    :class="cn(
      'flex min-h-[80px] w-full rounded-lg border border-border/50 bg-background/50 backdrop-blur-sm px-4 py-3 text-sm shadow-sm transition-all duration-300 placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:border-border focus-visible:bg-background/80 hover:border-border/80 hover:bg-background/70 disabled:cursor-not-allowed disabled:opacity-50 resize-none', 
      props.class
    )" 
  />
</template>
