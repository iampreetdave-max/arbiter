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
}

// Outcome buttons for tracking what happened after sending the document
const OUTCOME_OPTIONS: {
  value: CaseOutcome
  label: string
  emoji: string
  description: string
}[] = [
  {
    value: 'resolved',
    label: 'Resolved',
    emoji: '✅',
    description: 'Issue resolved in my favour',
  },
  {
    value: 'partial',
    label: 'Partial',
    emoji: '🤝',
    description: 'Partially resolved',
  },
  {
    value: 'no_response',
    label: 'No response',
    emoji: '⏳',
    description: 'No response received',
  },
  {
    value: 'escalated',
    label: 'Escalated',
    emoji: '⚖️',
    description: 'Escalated to court/authority',
  },
]

/**
 * Case detail page — shows case info, AI document, confidence badge,
 * revision feature, and outcome tracker.
 */
export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()

  const [caseData, setCaseData]   = useState<ArbiterCase | null>(null)
  const [document, setDocument]   = useState<ArbiterDocument | null>(null)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState('')
  const [recordingOutcome, setRecordingOutcome] = useState(false)
  const [outcomeError, setOutcomeError]         = useState('')

  const load = async () => {
    try {
      const c = await casesApi.get(id)
      setCaseData(c)
      // Fetch document if case has a document_id stored
      // (In current backend, documents are fetched separately)
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
        <button
          onClick={() => router.push('/cases')}
          className="text-sm text-[#555] hover:text-white underline transition-colors"
        >
          ← Back to cases
        </button>
      </div>
    )
  }

  const icon = PROBLEM_ICONS[caseData.problem_type] ?? '⚖️'
  const date = caseData.created_at
    ? new Date(caseData.created_at).toLocaleDateString('en-IN', {
        day: 'numeric', month: 'long', year: 'numeric',
      })
    : ''

  const showOutcomeTracker =
    ['complete', 'paid', 'draft_ready', 'tracking'].includes(caseData.status) &&
    !caseData.outcome

  const currentOutcome = caseData.outcome

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      {/* Back link */}
      <button
        onClick={() => router.push('/cases')}
        className="flex items-center gap-1.5 text-[#444] hover:text-white text-sm mb-6 transition-colors"
      >
        <span aria-hidden="true">←</span> All cases
      </button>

      {/* Case header */}
      <div className="flex flex-col sm:flex-row sm:items-start gap-4 mb-8 pb-8 border-b border-[#0f0f0f]">
        <span className="text-4xl" aria-hidden="true">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-3 mb-2">
            <h1 className="text-xl font-bold text-white">
              {caseData.title || caseData.problem_type?.replace(/_/g, ' ')}
            </h1>
            <Badge variant={statusVariant(caseData.status)}>
              {statusLabel(caseData.status)}
            </Badge>
          </div>
          {caseData.description && (
            <p className="text-[#555] text-sm leading-relaxed mb-3">
              {caseData.description}
            </p>
          )}
          <div className="flex flex-wrap gap-4 text-xs text-[#333]">
            <span className="capitalize">
              {caseData.problem_type?.replace(/_/g, ' ')}
            </span>
            {caseData.jurisdiction && <span>{caseData.jurisdiction}</span>}
            {date && <span>{date}</span>}
          </div>
        </div>
      </div>

      {/* Outcome tracker — shown after document is generated, before outcome recorded */}
      {showOutcomeTracker && (
        <div className="mb-8 bg-[#040404] border border-[#111] rounded-2xl p-6">
          <h3 className="text-white font-semibold text-sm mb-1">
            What happened after you sent the document?
          </h3>
          <p className="text-[#444] text-xs mb-4">
            Recording outcomes helps Arbiter improve and shows judges real-world impact.
          </p>
          {outcomeError && (
            <p className="text-xs text-red-400 mb-3">{outcomeError}</p>
          )}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {OUTCOME_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleOutcome(opt.value)}
                disabled={recordingOutcome}
                className="flex flex-col items-center gap-1.5 p-3 bg-[#060606] border border-[#111] hover:border-[#222] rounded-xl text-center transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <span className="text-2xl group-hover:scale-110 transition-transform">
                  {opt.emoji}
                </span>
                <span className="text-xs font-medium text-white">{opt.label}</span>
                <span className="text-[10px] text-[#333] leading-tight">{opt.description}</span>
              </button>
            ))}
          </div>
          {recordingOutcome && (
            <div className="flex items-center gap-2 mt-3">
              <Spinner size="sm" />
              <span className="text-xs text-[#444]">Recording outcome…</span>
            </div>
          )}
        </div>
      )}

      {/* Recorded outcome badge */}
      {currentOutcome && (
        <div className="mb-8 flex items-center gap-2 px-4 py-3 bg-[#040404] border border-[#111] rounded-xl">
          <span className="text-lg">
            {OUTCOME_OPTIONS.find((o) => o.value === currentOutcome)?.emoji ?? '📌'}
          </span>
          <div>
            <p className="text-xs text-[#444] font-medium">Outcome recorded</p>
            <p className="text-sm text-white capitalize">
              {OUTCOME_OPTIONS.find((o) => o.value === currentOutcome)?.description ??
                currentOutcome.replace(/_/g, ' ')}
            </p>
            {caseData.outcome_notes && (
              <p className="text-xs text-[#333] mt-0.5">{caseData.outcome_notes}</p>
            )}
          </div>
        </div>
      )}

      {/* Document section */}
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
  )
}

function DocumentPending({
  caseData,
  onRefresh,
}: {
  caseData: ArbiterCase
  onRefresh: () => void
}) {
  const isDrafting = ['research', 'drafting'].includes(caseData.status)

  return (
    <div className="text-center py-16 border border-[#0f0f0f] rounded-2xl bg-[#030303]">
      {isDrafting ? (
        <>
          <Spinner size="lg" className="mb-4 mx-auto" />
          <p className="text-white font-semibold mb-2">Drafting your document…</p>
          <p className="text-[#444] text-sm mb-6">
            Arbiter is researching Indian law and writing your document.
          </p>
          <button
            onClick={onRefresh}
            className="text-xs text-[#444] hover:text-white underline transition-colors"
          >
            Refresh
          </button>
        </>
      ) : (
        <>
          <div className="text-4xl mb-4" aria-hidden="true">📄</div>
          <p className="text-white font-semibold mb-2">No document yet</p>
          <p className="text-[#444] text-sm">
            The document hasn&apos;t been generated yet.
          </p>
        </>
      )}
    </div>
  )
}
