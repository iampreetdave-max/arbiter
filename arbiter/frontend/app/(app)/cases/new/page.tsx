'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { casesApi, type ChatResponse, type DocumentType } from '@/lib/api'
import { ChatMessage, TypingIndicator } from '@/components/chat/ChatMessage'
import { ChatInput } from '@/components/chat/ChatInput'
import { Spinner } from '@/components/ui/Spinner'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

const WELCOME_MSG: Message = {
  role: 'assistant',
  content:
    "Namaste! I'm Arbiter, your AI legal assistant.\n\nDescribe your legal issue and I'll help you draft the right document — demand letter, RTI application, consumer complaint, or more.\n\nWhat's the problem you're facing?",
  timestamp: new Date().toISOString(),
}

/**
 * Intake chat page — /cases/new
 *
 * Flow:
 *   1. User describes problem → AI asks follow-up questions
 *   2. Once enough info collected, AI offers to generate document
 *   3. User clicks "Generate" → SSE stream shows document being written live
 *   4. When done, redirect to case detail page
 */
export default function NewCasePage() {
  const router = useRouter()
  const [messages, setMessages]     = useState<Message[]>([WELCOME_MSG])
  const [thinking, setThinking]     = useState(false)
  const [caseId, setCaseId]         = useState<string | null>(null)
  const [readyToGenerate, setReadyToGenerate] = useState(false)
  const [suggestedDocType, setSuggestedDocType] = useState<DocumentType | null>(null)
  const [generating, setGenerating] = useState(false)
  const [streamedText, setStreamedText] = useState('')
  const [generatedDocId, setGeneratedDocId] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking, streamedText])

  const addMessage = (msg: Message) =>
    setMessages((prev) => [...prev, msg])

  const handleSend = async (text: string) => {
    const userMsg: Message = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    addMessage(userMsg)
    setThinking(true)

    try {
      let result: ChatResponse

      if (!caseId) {
        result = await casesApi.startChat(text)
        setCaseId(result.case_id)
      } else {
        result = await casesApi.sendMessage(caseId, text)
      }

      addMessage({
        role: 'assistant',
        content: result.response,
        timestamp: new Date().toISOString(),
      })

      if (result.ready_to_generate) {
        setReadyToGenerate(true)
        setSuggestedDocType(result.suggested_document_type ?? null)
      }
    } catch (err: unknown) {
      addMessage({
        role: 'assistant',
        content: 'Sorry, I encountered a technical issue. Please try again in a moment.',
        timestamp: new Date().toISOString(),
      })
    } finally {
      setThinking(false)
    }
  }

  const handleGenerate = async () => {
    if (!caseId) return
    setGenerating(true)
    setStreamedText('')

    const docType: DocumentType = suggestedDocType ?? 'demand_letter'

    try {
      // Use SSE streaming so user sees document being written in real time
      const es = await casesApi.streamGenerate(caseId, docType)

      es.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          if (data.chunk) {
            setStreamedText((prev) => prev + data.chunk)
          } else if (data.done) {
            es.close()
            setGeneratedDocId(data.document_id)
            // Small delay so user sees the completed doc before redirect
            setTimeout(() => {
              router.push(`/cases/${caseId}`)
            }, 1200)
          } else if (data.error) {
            es.close()
            addMessage({
              role: 'assistant',
              content: `Document generation failed: ${data.error}. Please try again.`,
              timestamp: new Date().toISOString(),
            })
            setGenerating(false)
            setStreamedText('')
          }
        } catch {
          // Non-JSON chunk, append as-is
        }
      }

      es.onerror = () => {
        es.close()
        // Fall back to synchronous generation
        casesApi
          .generateDocument(caseId, docType)
          .then((result) => {
            router.push(`/cases/${caseId}`)
          })
          .catch(() => {
            addMessage({
              role: 'assistant',
              content: 'Document generation failed. Please try again.',
              timestamp: new Date().toISOString(),
            })
            setGenerating(false)
            setStreamedText('')
          })
      }
    } catch {
      // SSE not available — fall back to sync
      try {
        await casesApi.generateDocument(caseId, docType)
        router.push(`/cases/${caseId}`)
      } catch {
        addMessage({
          role: 'assistant',
          content: 'Document generation failed. Please try again.',
          timestamp: new Date().toISOString(),
        })
        setGenerating(false)
      }
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      {/* Header */}
      <div className="flex-shrink-0 px-4 sm:px-6 py-4 border-b border-[#0f0f0f]">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-white font-semibold text-base">New Case</h1>
            <p className="text-[#444] text-xs mt-0.5">Powered by Google Gemini AI</p>
          </div>
          {caseId && (
            <span className="text-[10px] font-mono text-[#333] bg-[#0a0a0a] border border-[#111] px-2 py-1 rounded">
              #{caseId.slice(0, 8)}
            </span>
          )}
        </div>
      </div>

      {/* Messages + streamed document */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-6 flex flex-col gap-5">
          {messages.map((msg, i) => (
            <ChatMessage
              key={i}
              role={msg.role}
              content={msg.content}
              timestamp={msg.timestamp}
            />
          ))}

          {thinking && <TypingIndicator />}

          {/* Generate document CTA */}
          {readyToGenerate && !generating && suggestedDocType && (
            <div className="mx-auto text-center py-4">
              <p className="text-sm text-[#666] mb-4">
                I have enough information to draft your{' '}
                <strong className="text-white capitalize">
                  {suggestedDocType.replace(/_/g, ' ')}
                </strong>
                .
              </p>
              <button
                onClick={handleGenerate}
                className="inline-flex items-center gap-2 px-6 py-3 btn-shiny text-black rounded-xl font-semibold text-sm hover:opacity-90 transition-opacity"
              >
                Generate Document →
              </button>
            </div>
          )}

          {/* Live streaming document preview */}
          {generating && (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <Spinner size="sm" />
                <span className="text-xs text-[#444]">
                  {streamedText ? 'Writing document…' : 'Researching Indian law…'}
                </span>
              </div>
              {streamedText && (
                <div className="bg-[#040404] border border-[#111] rounded-xl p-4 text-xs text-[#666] whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto font-mono">
                  {streamedText}
                  <span className="animate-pulse ml-0.5">▋</span>
                </div>
              )}
              {generatedDocId && (
                <p className="text-xs text-emerald-400 text-center">
                  ✓ Document saved — redirecting…
                </p>
              )}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input — hidden once document is generating */}
      {!generating && (
        <div className="flex-shrink-0 max-w-2xl mx-auto w-full">
          <ChatInput
            onSend={handleSend}
            disabled={thinking || readyToGenerate}
            placeholder={
              readyToGenerate
                ? 'Click "Generate Document" above to proceed'
                : 'Describe your legal issue…'
            }
          />
        </div>
      )}
    </div>
  )
}
