'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { casesApi, documentsApi, type ArbiterCase, type ArbiterDocument } from '@/lib/api'
import { Badge, statusVariant, statusLabel } from '@/components/ui/Badge'
import { DocumentPreview } from '@/components/cases/DocumentPreview'
import { Spinner } from '@/components/ui/Spinner'

const PROBLEM_ICONS: Record<string, string> = {
  tenant_dispute:  '🏠',
  employment:      '💼',
  consumer:        '🛒',
  rti:             '📋',
  harassment:      '🛡️',
  debt_recovery:   '💰',
}

/**
 * Case detail page — shows case info, AI document preview, and payment CTA.
 */
export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()

  const [caseData, setCaseData]     = useState<ArbiterCase | null>(null)
  const [document, setDocument]     = useState<ArbiterDocument | null>(null)
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState('')

  const load = async () => {
    try {
      const [c, docs] = await Promise.all([
        casesApi.get(id),
        documentsApi.getByCaseId(id),
      ])
      setCaseData(c)
      setDocument(docs[0] ?? null)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load case')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  const handlePaymentSuccess = async () => {
    // Reload case + document after payment
    await load()
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
  const date = new Date(caseData.created_at).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'long', year: 'numeric',
  })

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
            <h1 className="text-xl font-bold text-white">{caseData.title}</h1>
            <Badge variant={statusVariant(caseData.status)}>
              {statusLabel(caseData.status)}
            </Badge>
          </div>
          <p className="text-[#555] text-sm leading-relaxed mb-3">
            {caseData.description}
          </p>
          <div className="flex flex-wrap gap-4 text-xs text-[#333]">
            <span className="capitalize">{caseData.problem_type.replace(/_/g, ' ')}</span>
            {caseData.jurisdiction && <span>{caseData.jurisdiction}</span>}
            <span>{date}</span>
          </div>
        </div>
      </div>

      {/* Document section */}
      {document ? (
        <DocumentPreview
          document={document}
          caseData={caseData}
          onPaymentSuccess={handlePaymentSuccess}
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
            The document hasn't been generated yet.
          </p>
        </>
      )}
    </div>
  )
}
