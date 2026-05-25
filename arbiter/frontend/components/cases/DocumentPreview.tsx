'use client'

/**
 * DocumentPreview — renders the generated legal document text.
 * Shows a "Download PDF" button if a PDF URL is available.
 * Shows a "Pay to Unlock" button if the case is draft_ready but not paid.
 */
import { useState } from 'react'
import type { ArbiterDocument, ArbiterCase } from '@/lib/api'
import { paymentsApi } from '@/lib/api'
import { Spinner } from '@/components/ui/Spinner'

interface DocumentPreviewProps {
  document: ArbiterDocument
  caseData: ArbiterCase
  onPaymentSuccess?: () => void
}

/** Extend the global Window to include Razorpay */
declare global {
  interface Window {
    Razorpay: new (options: Record<string, unknown>) => { open(): void }
  }
}

export function DocumentPreview({
  document,
  caseData,
  onPaymentSuccess,
}: DocumentPreviewProps) {
  const [paying, setPaying] = useState(false)
  const [payError, setPayError] = useState('')

  const isPaid = caseData.status === 'paid'

  const handlePay = async () => {
    setPayError('')
    setPaying(true)
    try {
      const order = await paymentsApi.createOrder(caseData.id)

      // Load Razorpay checkout script dynamically
      await loadRazorpay()

      const options = {
        key:         process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
        amount:      order.amount,
        currency:    order.currency,
        name:        'Arbiter ⚖️',
        description: `Legal document — ${document.document_type.replace(/_/g, ' ')}`,
        order_id:    order.order_id,
        theme:       { color: '#ffffff' },
        handler: () => {
          onPaymentSuccess?.()
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

  return (
    <div className="flex flex-col gap-4">
      {/* Document header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white capitalize">
            {document.document_type.replace(/_/g, ' ')}
          </h2>
          {document.word_count && (
            <p className="text-xs text-[#444] mt-0.5">
              {document.word_count.toLocaleString()} words
            </p>
          )}
        </div>

        <div className="flex gap-2">
          {isPaid && document.pdf_url && (
            <a
              href={document.pdf_url}
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

      {/* Document text — blurred if not paid */}
      <div className="relative">
        <div
          className={`bg-[#050505] border border-[#111] rounded-xl p-6 legal-text whitespace-pre-wrap leading-relaxed text-sm ${!isPaid ? 'select-none' : ''}`}
          style={!isPaid ? { filter: 'blur(3px)', userSelect: 'none' } : undefined}
          aria-label={isPaid ? 'Legal document content' : 'Document preview (pay to unlock)'}
        >
          {document.content}
        </div>

        {/* Paywall overlay */}
        {!isPaid && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-b from-transparent via-black/60 to-black rounded-xl">
            <p className="text-white font-semibold text-lg mb-2">Document ready</p>
            <p className="text-[#666] text-sm mb-6 text-center px-4">
              Pay once to download your document as a PDF with full legal citations.
            </p>
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
