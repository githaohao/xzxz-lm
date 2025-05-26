import { cva, type VariantProps } from 'class-variance-authority'

export { default as Button } from './Button.vue'

export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 relative overflow-hidden',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]',
        destructive:
          'bg-destructive text-destructive-foreground shadow-lg hover:bg-destructive/90 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]',
        outline:
          'border border-border/50 bg-background/50 backdrop-blur-sm shadow-sm hover:bg-accent hover:text-accent-foreground hover:border-border hover:shadow-md hover:scale-[1.02] active:scale-[0.98]',
        secondary:
          'bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80 hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]',
        ghost: 'hover:bg-accent hover:text-accent-foreground hover:scale-[1.02] active:scale-[0.98]',
        link: 'text-primary underline-offset-4 hover:underline',
        gradient: 'bg-gradient-to-r from-primary via-blue-600 to-blue-700 text-primary-foreground shadow-lg hover:shadow-xl hover:scale-[1.02] hover:from-primary/90 hover:via-blue-600/90 hover:to-blue-700/90 active:scale-[0.98]',
        'gradient-secondary': 'bg-gradient-to-r from-purple-500 via-indigo-600 to-purple-700 text-white shadow-lg hover:shadow-xl hover:scale-[1.02] hover:from-purple-600 hover:via-indigo-700 hover:to-purple-800 active:scale-[0.98]',
        'gradient-accent': 'bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-700 text-white shadow-lg hover:shadow-xl hover:scale-[1.02] hover:from-cyan-600 hover:via-blue-700 hover:to-indigo-800 active:scale-[0.98]',
        neon: 'bg-primary text-primary-foreground shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-[0.98] before:absolute before:inset-0 before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent before:translate-x-[-100%] hover:before:translate-x-[100%] before:transition-transform before:duration-700',
        glass: 'backdrop-blur-md bg-background/10 border border-border/30 text-foreground shadow-lg hover:bg-background/20 hover:border-border/50 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]',
        modern: 'bg-gradient-to-b from-background to-muted text-foreground border border-border/20 shadow-lg hover:from-muted hover:to-background hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]',
      },
      size: {
        default: 'h-10 px-6 py-2',
        xs: 'h-7 rounded-md px-3 text-xs',
        sm: 'h-8 rounded-md px-4 text-xs',
        lg: 'h-12 rounded-lg px-8 text-base',
        xl: 'h-14 rounded-xl px-10 text-lg',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>
