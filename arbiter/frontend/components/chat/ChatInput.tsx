'use client'

import { useState, useRef, type KeyboardEvent } from 'react'
import { Spinner } from '@/components/ui/Spinner'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

/**
 * Chat input bar — textarea that auto-grows, sends on Enter (Shift+Enter for newline).
 */
export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Describe your legal issue…',
}: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  return (
    <div className="flex gap-3 items-end p-4 border-t border-[#111] bg-black">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onInput={handleInput}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className={cn(
          'flex-1 resize-none rounded-xl px-4 py-3 text-sm',
          'bg-[#0a0a0a] border border-[#222] text-white placeholder-[#333]',
          'focus:outline-none focus:border-[#444] transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'max-h-40 overflow-y-auto leading-relaxed'
        )}
        aria-label="Type your message"
      />

      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
        className={cn(
          'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center',
          'transition-all duration-150 active:scale-95',
          disabled || !value.trim()
            ? 'bg-[#111] border border-[#222] text-[#333] cursor-not-allowed'
            : 'bg-white text-black hover:bg-[#e0e0e0]'
        )}
      >
        {disabled ? (
          <Spinner size="sm" />
        ) : (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
          </svg>
        )}
      </button>
    </div>
  )
}
