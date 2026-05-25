'use client'

/**
 * DocumentPreview — renders the generated legal document text.
 *
 * Features:
 *   - Confidence badge (green ≥80%, yellow ≥50%, red <50%)
 *   - Verified citations count
 *   - Paywall blur overlay until payment
 *   - "Request Revision" modal (paid users only, max 3 revisions)
 *   - Download PDF button after payment
 */
import { useState } from 'react'
import type { ArbiterDocument, ArbiterCase } from '@/lib/api'
import { documentsApi } from '@/lib/api'
import { Spinner } from '@/components/ui/Spinner'

interface DocumentPreviewProps {
  document: ArbiterDocument
  caseData: ArbiterCase
  onPaymentSuccess?: () => void
  onRevisionComplete?: (updated: ArbiterDocument) => void
}

declare global {
  interface Window {
    Razorpay: new (options: Record<string, unknown>) => { open(): void }
  }
}

// ── Confidence badge ────────────────────────────────────────────────────────────

function ConfidenceBadge({
  score,
  verifiedCitations,
  sources,
}: {
  score: number
  verifiedCitations: number
  sources: string[]
}) {
  const [showSources, setShowSources] = useState(false)

  const label =
    score >= 80 ? 'High confidence' : score >= 50 ? 'Medium confidence' : 'Low confidence'

  const color =
    score >= 80
      ? 'text-emerald-400 border-emerald-900/40 bg-emerald-950/30'
      : score >= 50
      ? 'text-yellow-400 border-yellow-900/40 bg-yellow-950/30'
      : 'text-red-400 border-red-900/40 bg-red-950/20'

  const dot =
    score >= 80 ? 'bg-emerald-400' : score >= 50 ? 'bg-yellow-400' : 'bg-red-400'

  return (
    <div className="flex flex-col gap-1.5">
      <button
        onClick={() => setShowSources((v) => !v)}
        className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border transition-opacity hover:opacity-80 ${color}`}
        title="Click to see sources"
      >
        <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
        {Math.round(score)}% — {label}
        {verifiedCitations > 0 && (
          <span className="opacity-70">· {verifiedCitations} verified citation{verifiedCitations !== 1 ? 's' : ''}</span>
        )}
        {sources.length > 0 && (
          <span className="opacity-50 ml-0.5">{showSources ? '▲' : '▼'}</span>
        )}
      </button>

      {showSources && sources.length > 0 && (
        <div className="flex flex-col gap-1 pl-2 border-l border-[#1a1a1a]">
          {sources.slice(0, 5).map((url, i) => (
            <a
              key={i}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-[#444] hover:text-[#888] truncate underline transition-colors"
            >
              {url}
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Revision modal ───────────────────────────────────────────────────────────────

function RevisionModal({
  documentId,
  revisionCount,
  onClose,
  onSuccess,
}: {
  documentId: string
  revisionCount: number
  onClose: () => void
  onSuccess: (doc: ArbiterDocument) => void
}) {
  const [instructions, setInstructions] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const remaining = 3 - revisionCount

  const handleSubmit = async () => {
    if (!instructions.trim()) return
    setError('')
    setLoading(true)
    try {
      const updated = await documentsApi.revise(documentId, instructions)
      onSuccess(updated)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Revision failed. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-[#080808] border border-[#1a1a1a] rounded-2xl p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-semibold">Request Revision</h3>
          <button
            onClick={onClose}
            className="text-[#444] hover:text-white text-lg leading-none transition-colors"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <p className="text-xs text-[#555]">
          {remaining} revision{remaining !== 1 ? 's' : ''} remaining.
          Tell Arbiter how to improve this document.
        </p>

        <div className="flex flex-col gap-2">
          <label className="text-xs text-[#666] font-medium" htmlFor="revision-instructions">
            Instructions
          </label>
          <textarea
            id="revision-instructions"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder={
              'Examples:\n• Make the tone more assertive\n• Increase compensation demand to ₹75,000\n• Add a paragraph about mental harassment\n• Translate the document to Hindi'
            }
            rows={5}
            className="w-full bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl px-3 py-2.5 text-sm text-white placeholder-[#333] resize-none focus:outline-none focus:border-[#333] transition-colors"
          />
        </div>

        {error && (
          <p className="text-xs text-red-400 bg-red-950/20 border border-red-900/20 rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm text-[#555] hover:text-white transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !instructions.trim()}
            className="inline-flex items-center gap-2 px-4 py-2 btn-shiny text-black rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading && <Spinner size="sm" />}
            {loading ? 'Revising…' : 'Apply Revision'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────────

export function DocumentPreview({
  document: initialDocument,
  caseData,
  onPaymentSuccess,
  onRevisionComplete,
}: DocumentPreviewProps) {
  const [doc, setDoc] = useState(initialDocument)
  const [paying, setPaying] = useState(false)
  const [payError, setPayError] = useState('')
  const [showRevision, setShowRevision] = useState(false)

  const isPaid = doc.payment_status === 'paid'
  const canRevise = isPaid && doc.revision_count < 3

  const handlePay = async () => {
    setPayError('')
    setPaying(true)
    try {
      const order = await documentsApi.createOrder(doc.id)
      await loadRazorpay()

      const options = {
        key:         order.razorpay_key_id || process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
        amount:      order.amount_paise,
        currency:    order.currency,
        name:        'Arbiter ⚖️',
        description: `Legal document — ${doc.type.replace(/_/g, ' ')}`,
        order_id:    order.order_id,
        theme:       { color: '#ffffff' },
        handler: async (response: {
          razorpay_order_id: string
          razorpay_payment_id: string
          razorpay_signature: string
        }) => {
          try {
            await documentsApi.verifyPayment(
              doc.id,
              response.razorpay_order_id,
              response.razorpay_payment_id,
              response.razorpay_signature,
            )
            onPaymentSuccess?.()
          } catch {
            setPayError('Payment verified by gateway but server confirmation failed. Please contact support.')
            setPaying(false)
          }
        },
        modal: {
          ondismiss: () => setPaying(false),
        },
      }

      const rzp = new window.Razorpay(options)
      rzp.open()
    } catch (err: unknown) {
      setPayError(err instanceof Error ? err.message : 'Payment failed. Please try again.')
      setPaying(false)
    }
  }

  const handleRevisionSuccess = (updated: ArbiterDocument) => {
    setDoc(updated)
    setShowRevision(false)
    onRevisionComplete?.(updated)
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Document header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-semibold text-white">
            {doc.title}
          </h2>
          <div className="flex flex-wrap items-center gap-3">
            {doc.word_count !== undefined && doc.word_count > 0 && (
              <span className="text-xs text-[#444]">
                {doc.word_count.toLocaleString()} words
              </span>
            )}
            {doc.revision_count > 0 && (
              <span className="text-xs text-[#333]">
                Rev. {doc.revision_count}
              </span>
            )}
            {doc.language === 'hi' && (
              <span className="text-xs text-[#444] border border-[#1a1a1a] px-1.5 py-0.5 rounded">
                हिंदी
              </span>
            )}
          </div>
          {/* Confidence badge — always visible */}
          <ConfidenceBadge
            score={doc.confidence_score}
            verifiedCitations={doc.verified_citations}
            sources={doc.grounding_sources}
          />
        </div>

        <div className="flex gap-2 flex-wrap">
          {canRevise && (
            <button
              onClick={() => setShowRevision(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-[#1f1f1f] text-[#888] hover:text-white hover:border-[#333] rounded-lg text-xs font-medium transition-colors"
            >
              ✏️ Request Revision
            </button>
          )}

          {isPaid && doc.gcs_url && (
            <a
              href={doc.gcs_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 btn-shiny text-black rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              ↓ Download PDF
            </a>
          )}

          {!isPaid && (
            <button
              onClick={handlePay}
              disabled={paying}
              className="inline-flex items-center gap-2 px-4 py-2 btn-shiny text-black rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {paying ? <Spinner size="sm" /> : null}
              {paying ? 'Processing…' : 'Pay ₹299 to Download'}
            </button>
          )}
        </div>
      </div>

      {payError && (
        <p className="text-sm text-red-400 bg-red-900/10 border border-red-900/20 rounded-lg px-3 py-2" role="alert">
          {payError}
        </p>
      )}

      {/* Citations list — shown only when paid */}
      {isPaid && doc.citations.length > 0 && (
        <div className="flex flex-col gap-1 bg-[#030303] border border-[#0f0f0f] rounded-xl px-4 py-3">
          <p className="text-xs text-[#444] font-medium mb-1.5">Legal Citations</p>
          {doc.citations.map((citation, i) => (
            <div key={i} className="flex items-start gap-2">
              <span className={`mt-0.5 text-[10px] ${citation.verified ? 'text-emerald-500' : 'text-[#333]'}`}>
                {citation.verified ? '✓' : '◦'}
              </span>
              <div>
                <span className="text-xs text-[#666] font-medium">
                  {citation.act}, {citation.section}
                </span>
                {citation.source_url ? (
                  <a
                    href={citation.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-1 text-[10px] text-[#333] hover:text-[#666] underline"
                  >
                    ↗
                  </a>
                ) : null}
                <p className="text-[10px] text-[#333] mt-0.5">{citation.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Document text — blurred if not paid */}
      <div className="relative">
        <div
          className={`bg-[#050505] border border-[#111] rounded-xl p-6 legal-text whitespace-pre-wrap leading-relaxed text-sm ${!isPaid ? 'select-none' : ''}`}
          style={!isPaid ? { filter: 'blur(3px)', userSelect: 'none' } : undefined}
          aria-label={isPaid ? 'Legal document content' : 'Document preview (pay to unlock)'}
        >
          {isPaid ? doc.content : doc.preview}
        </div>

        {/* Paywall overlay */}
        {!isPaid && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-b from-transparent via-black/60 to-black rounded-xl">
            <p className="text-white font-semibold text-lg mb-2">Document ready</p>
            <p className="text-[#666] text-sm mb-2 text-center px-4">
              Pay once to download your document as a PDF with full legal citations.
            </p>
            <div className="mb-6">
              <ConfidenceBadge
                score={doc.confidence_score}
                verifiedCitations={doc.verified_citations}
                sources={[]}
              />
            </div>
            <button
              onClick={handlePay}
              disabled={paying}
              className="inline-flex items-center gap-2 px-6 py-3 btn-shiny text-black rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-60"
            >
              {paying ? <Spinner size="sm" /> : null}
              Pay ₹299 — Download PDF
            </button>
          </div>
        )}
      </div>

      {/* Legal disclaimer */}
      <p className="text-xs text-[#333] leading-relaxed border-t border-[#0f0f0f] pt-4">
        <strong className="text-[#444]">Disclaimer:</strong> This document is AI-generated for
        informational and self-help purposes only. It does not constitute legal advice and does
        not create an attorney-client relationship. Consult a qualified lawyer for complex matters.
      </p>

      {/* Revision modal */}
      {showRevision && (
        <RevisionModal
          documentId={doc.id}
          revisionCount={doc.revision_count}
          onClose={() => setShowRevision(false)}
          onSuccess={handleRevisionSuccess}
        />
      )}
    </div>
  )
}

function loadRazorpay(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window.Razorpay !== 'undefined') return resolve()
    const script = window.document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.onload  = () => resolve()
    script.onerror = () => reject(new Error('Failed to load payment gateway.'))
    window.document.head.appendChild(script)
  })
}
