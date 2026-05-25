import { cn } from '@/lib/utils'
import type { CaseStatus } from '@/lib/api'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  className?: string
}

const variants = {
  default: 'border-[#222] text-[#666]',
  success: 'border-green-800/40 text-green-400',
  warning: 'border-yellow-800/40 text-yellow-400',
  error:   'border-red-800/40 text-red-400',
  info:    'border-blue-800/40 text-blue-400',
}

/**
 * Small status badge / chip.
 */
export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border uppercase tracking-wider',
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  )
}

/** Map a CaseStatus string to a Badge variant. */
export function statusVariant(status: CaseStatus): BadgeProps['variant'] {
  switch (status) {
    case 'intake':        return 'info'
    case 'research':      return 'info'
    case 'drafting':      return 'warning'
    case 'draft_ready':   return 'success'
    case 'paid':          return 'success'
    case 'closed':        return 'default'
    default:              return 'default'
  }
}

/** Human-readable label for a CaseStatus. */
export function statusLabel(status: CaseStatus): string {
  switch (status) {
    case 'intake':        return 'Intake'
    case 'research':      return 'Researching'
    case 'drafting':      return 'Drafting'
    case 'draft_ready':   return 'Ready'
    case 'paid':          return 'Paid'
    case 'closed':        return 'Closed'
    default:              return status
  }
}
