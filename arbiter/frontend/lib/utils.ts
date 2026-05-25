/** Utility functions */

/**
 * Merge Tailwind class names — lightweight alternative to clsx + tailwind-merge.
 * Filters out falsy values and joins with a space.
 */
export function cn(...classes: (string | undefined | null | false | 0)[]): string {
  return classes.filter(Boolean).join(' ')
}

/**
 * Format Indian Rupees from paise.
 * @example formatINR(29900) → "₹299"
 */
export function formatINR(paise: number): string {
  return `₹${(paise / 100).toLocaleString('en-IN')}`
}

/**
 * Truncate text to a character limit with ellipsis.
 */
export function truncate(text: string, chars: number): string {
  if (text.length <= chars) return text
  return text.substring(0, chars).trimEnd() + '…'
}
