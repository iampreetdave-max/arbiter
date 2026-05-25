import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual style variant */
  variant?: 'primary' | 'ghost' | 'outline'
  /** Size preset */
  size?: 'sm' | 'md' | 'lg'
  /** Button content */
  children: React.ReactNode
}

/**
 * Arbiter base button component.
 *
 * - primary: shiny white button (black text) — use for main CTAs
 * - ghost:   transparent with subtle border
 * - outline: transparent with visible border
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { variant = 'primary', size = 'md', className, children, ...props },
    ref
  ) => {
    const base = [
      'inline-flex items-center justify-center font-medium rounded-lg',
      'transition-all duration-200 ease-out',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-black',
      'disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none',
      'select-none',
    ].join(' ')

    const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
      primary: 'btn-shiny text-black font-semibold hover:opacity-90 active:scale-[0.98]',
      ghost:   'bg-transparent text-white border border-[#2a2a2a] hover:border-[#555] hover:bg-white/5 active:scale-[0.98]',
      outline: 'bg-transparent text-white border border-[#444] hover:border-white hover:bg-white/5 active:scale-[0.98]',
    }

    const sizes: Record<NonNullable<ButtonProps['size']>, string> = {
      sm: 'px-4 py-2 text-sm gap-1.5',
      md: 'px-5 py-2.5 text-sm gap-2',
      lg: 'px-8 py-3.5 text-base gap-2',
    }

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], className)}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
