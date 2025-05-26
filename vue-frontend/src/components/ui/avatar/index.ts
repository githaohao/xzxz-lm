import { cva, type VariantProps } from 'class-variance-authority'

export { default as Avatar } from './Avatar.vue'
export { default as AvatarFallback } from './AvatarFallback.vue'
export { default as AvatarImage } from './AvatarImage.vue'

export const avatarVariant = cva(
  'inline-flex items-center justify-center font-normal text-foreground select-none shrink-0 bg-gradient-to-br from-secondary to-secondary/80 overflow-hidden shadow-lg border-2 border-border/20 transition-all duration-300 hover:scale-110 hover:shadow-xl hover:border-border/50',
  {
    variants: {
      size: {
        xs: 'h-6 w-6 text-xs',
        sm: 'h-10 w-10 text-xs',
        base: 'h-16 w-16 text-2xl',
        lg: 'h-32 w-32 text-5xl',
        xl: 'h-40 w-40 text-6xl',
      },
      shape: {
        circle: 'rounded-full',
        square: 'rounded-xl',
      },
    },
  },
)

export type AvatarVariants = VariantProps<typeof avatarVariant>
