import { cn } from '@/lib/utils'

interface SpinnerProps {
  /** Visual size of the spinner */
  size?: 'sm' | 'md' | 'lg'
  /** Screen-reader label */
  label?: string
  className?: string
}

const sizes = {
  sm: 'w-4 h-4 border-[1.5px]',
  md: 'w-6 h-6 border-2',
  lg: 'w-10 h-10 border-2',
}

/**
 * Lightweight CSS spinner — no animation library required.
 */
export function Spinner({ size = 'md', label = 'Loading…', className }: SpinnerProps) {
  return (
    <span role="status" aria-label={label} className={cn('inline-flex', className)}>
      <span
        className={cn(
          'rounded-full border-white/20 border-t-white animate-spin',
          sizes[size]
        )}
        aria-hidden="true"
      />
    </span>
  )
}
