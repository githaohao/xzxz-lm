<template>
  <div
    :class="cn(alertVariants({ variant }), $attrs.class as string)"
    role="alert"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'
import { cva, type VariantProps } from 'class-variance-authority'

const alertVariants = cva(
  'relative w-full rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm px-6 py-4 text-sm shadow-lg transition-all duration-300 hover:shadow-xl hover:border-border/80 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-6 [&>svg]:top-5 [&>svg]:text-foreground [&>svg~*]:pl-8',
  {
    variants: {
      variant: {
        default: 'bg-card/50 text-foreground border-border/50',
        destructive:
          'border-destructive/50 bg-destructive/10 text-destructive backdrop-blur-sm [&>svg]:text-destructive',
        success:
          'border-green-500/50 bg-green-500/10 text-green-700 dark:text-green-400 backdrop-blur-sm [&>svg]:text-green-500',
        warning:
          'border-yellow-500/50 bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 backdrop-blur-sm [&>svg]:text-yellow-500',
        info:
          'border-blue-500/50 bg-blue-500/10 text-blue-700 dark:text-blue-400 backdrop-blur-sm [&>svg]:text-blue-500',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

interface Props extends /* @vue-ignore */ VariantProps<typeof alertVariants> {}

defineProps<Props>()

defineOptions({
  inheritAttrs: false,
})
</script> 