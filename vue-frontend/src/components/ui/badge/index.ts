import { cva, type VariantProps } from 'class-variance-authority'

export { default as Badge } from './Badge.vue'

export const badgeVariants = cva(
  'inline-flex items-center rounded-lg border px-3 py-1 text-xs font-semibold transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 shadow-sm hover:shadow-md',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80 hover:scale-105',
        secondary:
          'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 hover:scale-105',
        destructive:
          'border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80 hover:scale-105',
        outline: 'text-foreground border-border/50 bg-background/50 backdrop-blur-sm hover:bg-accent hover:text-accent-foreground hover:border-border hover:scale-105',
        success: 'border-transparent bg-green-600 text-white shadow hover:bg-green-700 hover:scale-105',
        warning: 'border-transparent bg-yellow-600 text-white shadow hover:bg-yellow-700 hover:scale-105',
        info: 'border-transparent bg-blue-600 text-white shadow hover:bg-blue-700 hover:scale-105',
        gradient: 'border-transparent bg-gradient-to-r from-primary to-blue-600 text-white shadow-lg hover:shadow-xl hover:scale-105',
        glass: 'border-border/30 bg-background/10 backdrop-blur-md text-foreground hover:bg-background/20 hover:border-border/50 hover:scale-105',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export type BadgeVariants = VariantProps<typeof badgeVariants>
