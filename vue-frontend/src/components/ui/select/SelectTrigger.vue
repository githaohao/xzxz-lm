<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { ChevronDown } from 'lucide-vue-next'
import { SelectIcon, SelectTrigger, type SelectTriggerProps, useForwardProps } from 'reka-ui'
import { cn } from '@/lib/utils'

const props = defineProps<SelectTriggerProps & { class?: HTMLAttributes['class'] }>()

const delegatedProps = reactiveOmit(props, 'class')

const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <SelectTrigger
    v-bind="forwardedProps"
    :class="cn(
      'flex h-10 w-full items-center justify-between whitespace-nowrap rounded-lg border border-border/50 bg-background/50 backdrop-blur-sm px-4 py-2 text-sm shadow-lg ring-offset-background data-[placeholder]:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:border-border focus:bg-background/80 hover:border-border/80 hover:bg-background/70 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:truncate text-start transition-all duration-300',
      props.class,
    )"
  >
    <slot />
    <SelectIcon as-child>
      <ChevronDown class="w-4 h-4 opacity-50 shrink-0 transition-transform duration-300 data-[state=open]:rotate-180" />
    </SelectIcon>
  </SelectTrigger>
</template>
