'use client'

import { useState, useEffect } from 'react'
import { TYPEWRITER_PHRASES } from '@/lib/constants'

interface TypewriterTextProps {
  /** Phrases to cycle through */
  phrases?: string[]
  /** Milliseconds per character while typing */
  typingSpeed?: number
  /** Milliseconds per character while deleting */
  deletingSpeed?: number
  /** Pause duration at end of each phrase (ms) */
  pauseDuration?: number
  /** Additional class names */
  className?: string
}

/**
 * Animated typewriter component.
 * Cycles through phrases with a blinking cursor — no external library needed.
 */
export function TypewriterText({
  phrases = TYPEWRITER_PHRASES,
  typingSpeed = 75,
  deletingSpeed = 38,
  pauseDuration = 2200,
  className = '',
}: TypewriterTextProps) {
  const [phraseIndex, setPhraseIndex] = useState(0)
  const [charIndex, setCharIndex]     = useState(0)
  const [isDeleting, setIsDeleting]   = useState(false)
  const [isPaused, setIsPaused]       = useState(false)

  useEffect(() => {
    if (isPaused) return

    const phrase = phrases[phraseIndex]

    const timer = setTimeout(
      () => {
        if (!isDeleting) {
          // Still typing
          if (charIndex < phrase.length) {
            setCharIndex((c) => c + 1)
          } else {
            // Finished typing — pause, then start deleting
            setIsPaused(true)
            setTimeout(() => {
              setIsPaused(false)
              setIsDeleting(true)
            }, pauseDuration)
          }
        } else {
          // Deleting
          if (charIndex > 0) {
            setCharIndex((c) => c - 1)
          } else {
            // Finished deleting — move to next phrase
            setIsDeleting(false)
            setPhraseIndex((p) => (p + 1) % phrases.length)
          }
        }
      },
      isDeleting ? deletingSpeed : typingSpeed
    )

    return () => clearTimeout(timer)
  }, [charIndex, phraseIndex, isDeleting, isPaused, phrases, typingSpeed, deletingSpeed, pauseDuration])

  const displayText = phrases[phraseIndex].substring(0, charIndex)

  return (
    <span className={className} aria-live="polite" aria-label={displayText}>
      {displayText}
      <span
        className="animate-blink ml-[1px] inline-block w-[2px] h-[0.9em] bg-current align-middle"
        aria-hidden="true"
      />
    </span>
  )
}
