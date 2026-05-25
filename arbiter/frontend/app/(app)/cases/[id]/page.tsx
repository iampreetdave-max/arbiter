'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  casesApi,
  documentsApi,
  type ArbiterCase,
  type ArbiterDocument,
  type CaseOutcome,
} from '@/lib/api'
import { Badge, statusVariant, statusLabel } from '@/components/ui/Badge'
import { DocumentPreview } from '@/components/cases/DocumentPreview'
import { Spinner } from '@/components/ui/Spinner'

const PROBLEM_ICONS: Record<string, string> = {
  tenant_dispute: '🏠',
  employment:     '💼',
  consumer:       '🛒',
  rti:            '📋',
  harassment:     '🛡️',
  debt_recovery:  '💰',
  other:          '⚖️',
}

const COUNTRY_FLAGS: Record<string, string> = {
  IN: '🇮🇳', US: '🇺🇸', GB: '🇬🇧', CA: '🇨🇦', AU: '🇦🇺'
}

const STATUS_TIMELINE = [
  { key: 'intake',      label: 'Intake',       icon: '📝', desc: 'Describing the problem' },
  { key: 'research',   label: 'Research',      icon: '🔍', desc: 'Looking up applicable laws' },
  { key: 'drafting',   label: 'Drafting',      icon: '✍️',  desc: 'Writing your document' },
  { key: 'draft_ready', label: 'Draft Ready',  icon: '📄', desc: 'Document ready for review' },
  { key: 'paid',       label: 'Paid',          icon: '✅', desc: 'Payment confirmed' },
  { key: 'complete',   label: 'Complete',      icon: '🎉', desc: 'Document downloaded' },
  { key: 'tracking',  label: 'Tracking',       icon: '📡', desc: 'Following up' },
  { key: 'escalated', label: 'Escalated',      icon: '⚖️', desc: 'Referred to lawyer' },
  { key: 'closed',    label: 'Closed',         icon: '🔒', desc: 'Case closed' },
]

const OUTCOME_OPTIONS: { value: CaseOutcome; label: string; emoji: string; description: string }[] = [
  { value: 'resolved',    label: 'Resolved',    emoji: '✅', description: 'Issue resolved in my favour' },
  { value: 'partial',     label: 'Partial',     emoji: '🤝', description: 'Partially resolved' },
  { value: 'no_response', label: 'No response', emoji: '⏳', description: 'No response received' },
  { value: 'escalated',   label: 'Escalated',   emoji: '⚖️', description: 'Escalated to court/authority' },
]

type Tab = 'overview' | 'conversation' | 'timeline'

/**
 * Case detail page — tabbed view: Overview | Conversation | Timeline.
 * Includes outcome tracker, document preview, lawyer escalation, and country flag.
 */
export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router  = useRouter()

  const [caseData, setCaseData] = useState<ArbiterCase | null>(null)
  const [document, setDocument] = useState<ArbiterDocument | null>(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')
  const [tab, setTab]           = useState<Tab>('overview')
  const [recordingOutcome, setRecordingOutcome] = useState(false)
  const [outcomeError, setOutcomeError]         = useState('')
  const [escalating, setEscalating]             = useState(false)
  const [escalationResult, setEscalationResult] = useState<string | null>(null)

  const load = async () => {
    try {
      const c = await casesApi.get(id)
      setCaseData(c)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load case')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  const handlePaymentSuccess = () => load()
  const handleRevisionComplete = (updated: ArbiterDocument) => setDocument(updated)

  const handleOutcome = async (outcome: CaseOutcome) => {
    if (!caseData) return
    setOutcomeError('')
    setRecordingOutcome(true)
    try {
      const updated = await casesApi.updateOutcome(id, outcome)
      setCaseData(updated)
    } catch (err: unknown) {
      setOutcomeError(err instanceof Error ? err.message : 'Failed to record outcome')
    } finally {
      setRecordingOutcome(false)
    }
  }

  const handleEscalate = async () => {
    setEscalating(true)
    setEscalationResult(null)
    try {
      const result = await casesApi.escalateToLawyer(id)
      setEscalationResult(result.message)
      load()
    } catch (err: unknown) {
      setEscalationResult(err instanceof Error ? err.message : 'Escalation failed. Please try again.')
    } finally {
      setEscalating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Spinner size="lg" label="Loading case…" />
      </div>
    )
  }

  if (error || !caseData) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-20 text-center">
        <p className="text-red-400 mb-4">{error || 'Case not found'}</p>
        <button onClick={() => router.push('/cases')} className="text-sm text-white/40 hover:text-white underline">
          ← Back to cases
        </button>
      </div>
    )
  }

  const icon    = PROBLEM_ICONS[caseData.problem_type] ?? '⚖️'
  const flag    = caseData.country_code ? COUNTRY_FLAGS[caseData.country_code] : null
  const date    = caseData.created_at
    ? new Date(caseData.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
    : ''
  const showOutcomeTracker = ['complete', 'paid', 'draft_ready', 'tracking'].includes(caseData.status) && !caseData.outcome
  const chatHistory: Array<{ role: string; content: string }> = (caseData as any).chat_history ?? []

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      {/* Back */}
      <button
        onClick={() => router.push('/cases')}
        className="flex items-center gap-1.5 text-white/30 hover:text-white text-sm mb-6 transition-colors"
      >
        ← All cases
      </button>

      {/* Case header */}
      <div className="flex flex-col sm:flex-row sm:items-start gap-4 mb-6 pb-6 border-b border-white/8">
        <span className="text-4xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <h1 className="text-xl font-bold text-white">
              {caseData.title || caseData.problem_type?.replace(/_/g, ' ')}
            </h1>
            <Badge variant={statusVariant(caseData.status)}>
              {statusLabel(caseData.status)}
            </Badge>
          </div>
          <div className="flex flex-wrap gap-3 text-xs text-white/35">
            {flag && <span>{flag} {caseData.country_code}</span>}
            {caseData.jurisdiction && <span>📍 {caseData.jurisdiction}</span>}
            <span className="capitalize">{caseData.problem_type?.replace(/_/g, ' ')}</span>
            {date && <span>🗓 {date}</span>}
          </div>
          {caseData.description && (
            <p className="text-white/40 text-sm mt-2 leading-relaxed line-clamp-2">{caseData.description}</p>
          )}
        </div>

        {/* Escalate button */}
        {!['escalated', 'closed'].includes(caseData.status) && (
          <button
            onClick={handleEscalate}
            disabled={escalating}
            className="flex-shrink-0 text-xs px-3 py-2 border border-white/20 text-white/60 rounded-lg hover:border-white/50 hover:text-white transition-all disabled:opacity-40"
          >
            {escalating ? '…' : '⚖️ Get a Lawyer'}
          </button>
        )}
      </div>

      {/* Escalation result */}
      {escalationResult && (
        <div className="mb-4 p-3 bg-white/5 border border-white/15 rounded-lg text-sm text-white/70">
          {escalationResult}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-white/10">
        {([
          { key: 'overview',     label: 'Overview' },
          { key: 'conversation', label: `Conversation${chatHistory.length ? ` (${chatHistory.length})` : ''}` },
          { key: 'timeline',     label: 'Timeline' },
        ] as { key: Tab; label: string }[]).map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-all ${
              tab === t.key
                ? 'border-white text-white'
                : 'border-transparent text-white/40 hover:text-white/70'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {tab === 'overview' && (
        <div className="space-y-6">
          {showOutcomeTracker && (
            <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-6">
              <h3 className="text-white font-semibold text-sm mb-1">What happened after you sent the document?</h3>
              <p className="text-white/35 text-xs mb-4">Recording outcomes helps Arbiter improve.</p>
              {outcomeError && <p className="text-xs text-red-400 mb-3">{outcomeError}</p>}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {OUTCOME_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleOutcome(opt.value)}
                    disabled={recordingOutcome}
                    className="flex flex-col items-center gap-1.5 p-3 bg-white/[0.02] border border-white/10 hover:border-white/25 rounded-xl text-center transition-all disabled:opacity-50"
                  >
                    <span className="text-2xl">{opt.emoji}</span>
                    <span className="text-xs font-medium text-white">{opt.label}</span>
                    <span className="text-[10px] text-white/30 leading-tight">{opt.description}</span>
                  </button>
                ))}
              </div>
              {recordingOutcome && (
                <div className="flex items-center gap-2 mt-3">
                  <Spinner size="sm" />
                  <span className="text-xs text-white/40">Recording outcome…</span>
                </div>
              )}
            </div>
          )}

          {caseData.outcome && (
            <div className="flex items-center gap-3 px-4 py-3 bg-white/[0.02] border border-white/10 rounded-xl">
              <span className="text-lg">{OUTCOME_OPTIONS.find((o) => o.value === caseData.outcome)?.emoji ?? '📌'}</span>
              <div>
                <p className="text-xs text-white/40 font-medium">Outcome recorded</p>
                <p className="text-sm text-white capitalize">
                  {OUTCOME_OPTIONS.find((o) => o.value === caseData.outcome)?.description ?? caseData.outcome?.replace(/_/g, ' ')}
                </p>
              </div>
            </div>
          )}

          {document ? (
            <DocumentPreview
              document={document}
              caseData={caseData}
              onPaymentSuccess={handlePaymentSuccess}
              onRevisionComplete={handleRevisionComplete}
            />
          ) : (
            <DocumentPending caseData={caseData} onRefresh={load} />
          )}
        </div>
      )}

      {/* CONVERSATION TAB */}
      {tab === 'conversation' && (
        <div className="space-y-3">
          {chatHistory.length === 0 ? (
            <div className="text-center py-16 border border-white/8 rounded-xl">
              <p className="text-white/30 text-sm">No conversation history stored yet.</p>
            </div>
          ) : (
            <>
              <p className="text-white/30 text-xs mb-4">
                Full intake conversation — {chatHistory.length} messages
              </p>
              {chatHistory.map((msg, i) => {
                const isUser = msg.role === 'user'
                return (
                  <div
                    key={i}
                    className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    {!isUser && (
                      <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
                        ⚖️
                      </div>
                    )}
                    <div
                      className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                        isUser
                          ? 'bg-white text-black rounded-br-sm'
                          : 'bg-white/8 text-white/80 rounded-bl-sm border border-white/10'
                      }`}
                    >
                      {msg.content}
                    </div>
                    {isUser && (
                      <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
                        👤
                      </div>
                    )}
                  </div>
                )
              })}
            </>
          )}
        </div>
      )}

      {/* TIMELINE TAB */}
      {tab === 'timeline' && (
        <div className="space-y-0">
          <p className="text-white/30 text-xs mb-6">Case status progression</p>
          {STATUS_TIMELINE.map((step, i) => {
            const statusOrder = STATUS_TIMELINE.map((s) => s.key)
            const currentIdx  = statusOrder.indexOf(caseData.status)
            const stepIdx     = i
            const isDone      = stepIdx < currentIdx
            const isCurrent   = step.key === caseData.status
            const isFuture    = stepIdx > currentIdx

            if (isFuture && !isCurrent) return null

            return (
              <div key={step.key} className="flex gap-4 pb-6 relative">
                {i < STATUS_TIMELINE.length - 1 && (
                  <div className="absolute left-[13px] top-7 w-px h-[calc(100%-8px)] bg-white/10" />
                )}
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-sm flex-shrink-0 z-10 ${
                  isCurrent
                    ? 'bg-white text-black'
                    : isDone
                    ? 'bg-white/20 text-white/60'
                    : 'bg-white/5 text-white/20'
                }`}>
                  {step.icon}
                </div>
                <div className="pt-0.5">
                  <div className={`text-sm font-medium ${isCurrent ? 'text-white' : isDone ? 'text-white/60' : 'text-white/20'}`}>
                    {step.label}
                    {isCurrent && (
                      <span className="ml-2 text-[10px] bg-white/10 text-white/60 px-1.5 py-0.5 rounded-full">Current</span>
                    )}
                  </div>
                  <div className={`text-xs mt-0.5 ${isCurrent ? 'text-white/50' : 'text-white/25'}`}>
                    {step.desc}
                  </div>
                  {isCurrent && caseData.updated_at && (
                    <div className="text-[10px] text-white/25 mt-1">
                      {new Date(caseData.updated_at).toLocaleString('en-GB', {
                        day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                      })}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function DocumentPending({ caseData, onRefresh }: { caseData: ArbiterCase; onRefresh: () => void }) {
  const isDrafting = ['research', 'drafting'].includes(caseData.status)
  return (
    <div className="text-center py-16 border border-white/8 rounded-2xl bg-white/[0.01]">
      {isDrafting ? (
        <>
          <Spinner size="lg" className="mb-4 mx-auto" />
          <p className="text-white font-semibold mb-2">Drafting your document…</p>
          <p className="text-white/35 text-sm mb-6">Arbiter is researching applicable laws.</p>
          <button onClick={onRefresh} className="text-xs text-white/30 hover:text-white underline">Refresh</button>
        </>
      ) : (
        <>
          <div className="text-4xl mb-4">📄</div>
          <p className="text-white font-semibold mb-2">No document yet</p>
          <p className="text-white/35 text-sm">Complete the intake to generate your document.</p>
        </>
      )}
    </div>
  )
}
