'use client'

import { useEffect, useState, useMemo } from 'react'
import Link from 'next/link'
import { casesApi, type ArbiterCase } from '@/lib/api'
import { CaseCard } from '@/components/cases/CaseCard'
import { Spinner } from '@/components/ui/Spinner'

const STATUS_FILTERS = [
  { value: '', label: 'All' },
  { value: 'intake', label: 'Intake' },
  { value: 'draft_ready', label: 'Ready' },
  { value: 'paid', label: 'Paid' },
  { value: 'complete', label: 'Complete' },
  { value: 'closed', label: 'Closed' },
]

const COUNTRY_FILTERS = [
  { value: '', label: 'All Countries' },
  { value: 'IN', label: 'India' },
  { value: 'US', label: 'USA' },
  { value: 'GB', label: 'UK' },
  { value: 'CA', label: 'Canada' },
  { value: 'AU', label: 'Australia' },
]

export default function CasesPage() {
  const [cases, setCases]     = useState<ArbiterCase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')
  const [search, setSearch]   = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [countryFilter, setCountryFilter] = useState('')
  const [sort, setSort]       = useState<'newest' | 'oldest'>('newest')

  useEffect(() => {
    casesApi.list()
      .then((res) => setCases(res.cases ?? (res as any) ?? []))
      .catch((err) => setError(err.message ?? 'Failed to load cases'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    let result = [...cases]
    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter(
        (c) => c.title?.toLowerCase().includes(q) || c.description?.toLowerCase().includes(q) ||
               c.jurisdiction?.toLowerCase().includes(q) || c.problem_type?.toLowerCase().includes(q)
      )
    }
    if (statusFilter) result = result.filter((c) => c.status === statusFilter)
    if (countryFilter) result = result.filter((c) => c.country_code === countryFilter)
    result.sort((a, b) => {
      const da = new Date(a.created_at ?? 0).getTime()
      const db = new Date(b.created_at ?? 0).getTime()
      return sort === 'newest' ? db - da : da - db
    })
    return result
  }, [cases, search, statusFilter, countryFilter, sort])

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">My Cases</h1>
          <p className="text-white/40 text-sm mt-0.5">
            {loading ? '…' : `${cases.length} total · ${filtered.length} shown`}
          </p>
        </div>
        <Link href="/cases/new" className="inline-flex items-center gap-2 px-5 py-2.5 btn-shiny text-black rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity">
          + New Case
        </Link>
      </div>

      {!loading && cases.length > 0 && (
        <div className="space-y-3 mb-6">
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search cases by title, type, or location…"
            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm placeholder:text-white/25 focus:outline-none focus:border-white/35" />
          <div className="flex flex-wrap gap-2 items-center">
            <div className="flex gap-1 flex-wrap">
              {STATUS_FILTERS.map((f) => (
                <button key={f.value} onClick={() => setStatusFilter(f.value)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
                    statusFilter === f.value ? 'bg-white text-black border-white' : 'text-white/40 border-white/15 hover:border-white/35'
                  }`}>
                  {f.label}
                </button>
              ))}
            </div>
            <div className="w-px h-4 bg-white/10 hidden sm:block" />
            <select value={countryFilter} onChange={(e) => setCountryFilter(e.target.value)}
              className="bg-black border border-white/15 text-white/60 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-white/40">
              {COUNTRY_FILTERS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
            <select value={sort} onChange={(e) => setSort(e.target.value as 'newest' | 'oldest')}
              className="bg-black border border-white/15 text-white/60 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-white/40 ml-auto">
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
            </select>
          </div>
        </div>
      )}

      {loading && <div className="flex justify-center py-20"><Spinner size="lg" label="Loading your cases…" /></div>}
      {!loading && error && <div className="text-center py-16"><p className="text-red-400 text-sm">{error}</p></div>}
      {!loading && !error && cases.length === 0 && <EmptyState />}
      {!loading && !error && cases.length > 0 && filtered.length === 0 && (
        <div className="text-center py-16 border border-white/8 rounded-2xl">
          <p className="text-white/40 text-sm">No cases match your filters.</p>
          <button onClick={() => { setSearch(''); setStatusFilter(''); setCountryFilter('') }}
            className="mt-3 text-xs text-white/30 hover:text-white underline">Clear filters</button>
        </div>
      )}
      {!loading && !error && filtered.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((c) => <CaseCard key={c.id} caseData={c} />)}
        </div>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="text-center py-20 border border-white/8 rounded-2xl bg-white/[0.01]">
      <div className="text-5xl mb-4">&#x2696;&#xFE0F;</div>
      <h2 className="text-lg font-semibold text-white mb-2">No cases yet</h2>
      <p className="text-white/30 text-sm mb-8 max-w-xs mx-auto">Describe your legal problem and Arbiter will draft the right document for you.</p>
      <Link href="/cases/new" className="inline-flex items-center gap-2 px-6 py-3 btn-shiny text-black rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity">
        Start your first case
      </Link>
    </div>
  )
}
