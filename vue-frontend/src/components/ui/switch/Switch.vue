<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import {
  SwitchRoot,
  type SwitchRootEmits,
  type SwitchRootProps,
  SwitchThumb,
  useForwardPropsEmits,
} from 'reka-ui'
import { cn } from '@/lib/utils'

const props = defineProps<SwitchRootProps & { class?: HTMLAttributes['class'] }>()

const emits = defineEmits<SwitchRootEmits>()

const delegatedProps = reactiveOmit(props, 'class')

const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <SwitchRoot
    v-bind="forwarded"
    :class="cn(
      'peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent shadow-lg transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-primary data-[state=checked]:to-blue-600 data-[state=checked]:shadow-xl data-[state=unchecked]:bg-secondary/50 data-[state=unchecked]:backdrop-blur-sm hover:scale-105',
      props.class,
    )"
  >
    <SwitchThumb
      :class="cn('pointer-events-none block h-5 w-5 rounded-full bg-background shadow-xl ring-0 transition-all duration-300 data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0 data-[state=checked]:shadow-lg')"
    >
      <slot name="thumb" />
    </SwitchThumb>
  </SwitchRoot>
</template>
