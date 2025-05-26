import { cva, type VariantProps } from 'class-variance-authority'

export { default as Toggle } from './Toggle.vue'

export const toggleVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-lg text-sm font-medium transition-all duration-300 hover:bg-muted hover:text-muted-foreground hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-gradient-to-br data-[state=on]:from-accent data-[state=on]:to-accent/80 data-[state=on]:text-accent-foreground data-[state=on]:shadow-lg backdrop-blur-sm [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default: 'bg-transparent border border-border/30 shadow-sm',
        outline:
          'border border-input bg-transparent shadow-md hover:bg-accent hover:text-accent-foreground hover:shadow-lg',
      },
      size: {
        default: 'h-9 px-3 min-w-9',
        sm: 'h-8 px-2 min-w-8',
        lg: 'h-11 px-4 min-w-11',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export type ToggleVariants = VariantProps<typeof toggleVariants>
