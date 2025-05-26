<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { useVModel } from '@vueuse/core'
import { cn } from '@/lib/utils'

const props = defineProps<{
  defaultValue?: string | number
  modelValue?: string | number
  class?: HTMLAttributes['class']
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
  <input 
    v-model="modelValue" 
    :class="cn(
      'flex h-10 w-full rounded-lg border border-border/50 bg-background/50 backdrop-blur-sm px-4 py-2 text-sm shadow-sm transition-all duration-300 file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:border-border focus-visible:bg-background/80 hover:border-border/80 hover:bg-background/70 disabled:cursor-not-allowed disabled:opacity-50', 
      props.class
    )"
  >
</template>
