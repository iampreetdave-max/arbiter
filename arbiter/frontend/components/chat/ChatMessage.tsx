import { cn } from '@/lib/utils'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  /** ISO timestamp string */
  timestamp?: string
}

/**
 * Single message bubble in the intake chat interface.
 * User messages align right (white bg, black text).
 * Assistant messages align left (dark bg, white text).
 */
export function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  const isUser = role === 'user'

  return (
    <div
      className={cn(
        'flex gap-3 max-w-[85%]',
        isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold mt-1',
          isUser
            ? 'bg-white text-black'
            : 'bg-[#111] border border-[#222] text-white'
        )}
        aria-hidden="true"
      >
        {isUser ? 'U' : '⚖'}
      </div>

      {/* Bubble */}
      <div className="flex flex-col gap-1">
        <div
          className={cn(
            'rounded-2xl px-4 py-3 text-sm leading-relaxed',
            isUser
              ? 'bg-white text-black rounded-tr-sm'
              : 'bg-[#0f0f0f] border border-[#1a1a1a] text-[#ddd] rounded-tl-sm'
          )}
        >
          {/* Preserve newlines */}
          {content.split('\n').map((line, i) => (
            <span key={i}>
              {line}
              {i < content.split('\n').length - 1 && <br />}
            </span>
          ))}
        </div>

        {timestamp && (
          <span
            className={cn(
              'text-[10px] text-[#333] px-1',
              isUser ? 'text-right' : 'text-left'
            )}
          >
            {new Date(timestamp).toLocaleTimeString('en-IN', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        )}
      </div>
    </div>
  )
}

/**
 * Typing indicator — 3 bouncing dots shown while AI is processing.
 */
export function TypingIndicator() {
  return (
    <div className="flex gap-3 max-w-[85%] mr-auto">
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-[#111] border border-[#222] flex items-center justify-center text-xs mt-1" aria-hidden="true">
        ⚖
      </div>
      <div className="bg-[#0f0f0f] border border-[#1a1a1a] rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex gap-1 items-center h-4" aria-label="AI is typing">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-[#444] animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
