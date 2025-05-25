<template>
  <img
    v-if="src"
    :src="src"
    :alt="alt"
    :class="cn('aspect-square h-full w-full', $attrs.class as string)"
    @error="onError"
  />
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
  src?: string
  alt?: string
}

defineProps<Props>()

defineOptions({
  inheritAttrs: false,
})

const emit = defineEmits<{
  error: []
}>()

function onError() {
  emit('error')
}
</script> 