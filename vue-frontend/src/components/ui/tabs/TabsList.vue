<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { TabsList, type TabsListProps } from 'reka-ui'
import { cn } from '@/lib/utils'

const props = defineProps<TabsListProps & { class?: HTMLAttributes['class'] }>()

const delegatedProps = reactiveOmit(props, 'class')
</script>

<template>
  <TabsList
    v-bind="delegatedProps"
    :class="cn(
      'inline-flex items-center justify-center rounded-xl bg-secondary/50 backdrop-blur-sm border border-border/50 p-1.5 text-muted-foreground shadow-lg',
      props.class,
    )"
  >
    <slot />
  </TabsList>
</template>
