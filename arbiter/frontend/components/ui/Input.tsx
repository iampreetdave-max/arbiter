import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Label shown above the field */
  label?: string
  /** Error message shown below the field */
  error?: string
  /** Helper text shown below the field (when no error) */
  hint?: string
}

/**
 * Arbiter text input.
 * Monochrome — black bg, white border, white text.
 * Supports label, error, and hint text.
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-[#aaa]"
          >
            {label}
          </label>
        )}

        <input
          ref={ref}
          id={inputId}
          className={cn(
            'w-full px-4 py-3 rounded-lg text-sm',
            'bg-[#0a0a0a] border text-white placeholder-[#444]',
            'transition-colors duration-150',
            'focus:outline-none focus:ring-2 focus:ring-white/20',
            error
              ? 'border-red-500/60 focus:border-red-400'
              : 'border-[#222] focus:border-[#555]',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            className
          )}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
          {...props}
        />

        {error && (
          <p id={`${inputId}-error`} className="text-xs text-red-400" role="alert">
            {error}
          </p>
        )}
        {!error && hint && (
          <p id={`${inputId}-hint`} className="text-xs text-[#444]">
            {hint}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'
