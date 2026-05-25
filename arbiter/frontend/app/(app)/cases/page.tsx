'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { casesApi, type ArbiterCase } from '@/lib/api'
import { CaseCard } from '@/components/cases/CaseCard'
import { Spinner } from '@/components/ui/Spinner'

/**
 * Cases dashboard — lists all of the user's legal cases.
 */
export default function CasesPage() {
  const [cases, setCases]   = useState<ArbiterCase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState('')

  useEffect(() => {
    casesApi.list()
      .then(setCases)
      .catch((err) => setError(err.message ?? 'Failed to load cases'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">My Cases</h1>
          <p className="text-[#555] text-sm mt-1">
            {cases.length === 0 && !loading
              ? 'No cases yet'
              : `${cases.length} case${cases.length === 1 ? '' : 's'}`}
          </p>
        </div>
        <Link
          href="/cases/new"
          className="inline-flex items-center gap-2 px-5 py-2.5 btn-shiny text-black rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity"
        >
          + New Case
        </Link>
      </div>

      {/* States */}
      {loading && (
        <div className="flex justify-center py-20">
          <Spinner size="lg" label="Loading your cases…" />
        </div>
      )}

      {!loading && error && (
        <div className="text-center py-16">
          <p className="text-red-400 text-sm">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 text-xs text-[#555] hover:text-white transition-colors underline"
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && cases.length === 0 && (
        <EmptyState />
      )}

      {!loading && !error && cases.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cases.map((c) => (
            <CaseCard key={c.id} caseData={c} />
          ))}
        </div>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="text-center py-20 border border-[#0f0f0f] rounded-2xl bg-[#030303]">
      <div className="text-5xl mb-4" aria-hidden="true">⚖️</div>
      <h2 className="text-lg font-semibold text-white mb-2">No cases yet</h2>
      <p className="text-[#444] text-sm mb-8 max-w-xs mx-auto">
        Describe your legal problem and Arbiter will draft the right document for you.
      </p>
      <Link
        href="/cases/new"
        className="inline-flex items-center gap-2 px-6 py-3 btn-shiny text-black rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity"
      >
        Start your first case
        <span aria-hidden="true">→</span>
      </Link>
    </div>
  )
}
