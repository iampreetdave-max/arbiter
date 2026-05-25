'use client'

/**
 * Legal Updates — weekly feed of new laws, court judgments, and regulatory changes.
 */
import { useState, useEffect } from 'react'
import { LegalUpdateCard } from '@/components/updates/LegalUpdateCard'

const COUNTRIES = [
  { code: '', name: 'All Countries', flag: '🌍' },
  { code: 'IN', name: 'India', flag: '🇮🇳' },
  { code: 'US', name: 'USA', flag: '🇺🇸' },
  { code: 'GB', name: 'UK', flag: '🇬🇧' },
  { code: 'CA', name: 'Canada', flag: '🇨🇦' },
  { code: 'AU', name: 'Australia', flag: '🇦🇺' },
]

const CATEGORIES = [
  { value: '', label: 'All Types' },
  { value: 'legislation', label: 'Legislation' },
  { value: 'judgment', label: 'Court Judgments' },
  { value: 'regulation', label: 'Regulations' },
  { value: 'advisory', label: 'Advisories' },
]

export default function LegalUpdatesPage() {
  const [updates, setUpdates] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [country, setCountry] = useState('')
  const [category, setCategory] = useState('')
  const [error, setError] = useState<string | null>(null)

  const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  useEffect(() => {
    const fetch_updates = async () => {
      setLoading(true)
      setError(null)
      try {
        const params = new URLSearchParams()
        if (country) params.set('country_code', country)
        if (category) params.set('category', category)
        params.set('limit', '30')

        const res = await fetch(`${BASE}/api/legal-updates?${params}`)
        const data = await res.json()
        setUpdates(data.updates ?? [])
      } catch {
        setError('Failed to load updates. Please try again.')
      } finally {
        setLoading(false)
      }
    }
    fetch_updates()
  }, [country, category])

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Legal Updates</h1>
        <p className="text-white/50 text-sm mt-1">
          Weekly summaries of new laws, court judgments, and regulatory changes across 5 countries.
        </p>
      </div>

      {/* Filters */}
      <div className="space-y-3">
        {/* Country filter */}
        <div className="flex flex-wrap gap-2">
          {COUNTRIES.map((c) => (
            <button
              key={c.code}
              onClick={() => setCountry(c.code)}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                country === c.code
                  ? 'bg-white text-black border-white'
                  : 'bg-white/5 text-white/60 border-white/15 hover:border-white/40'
              }`}
            >
              {c.flag} {c.name}
            </button>
          ))}
        </div>

        {/* Category filter */}
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setCategory(cat.value)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                category === cat.value
                  ? 'bg-white text-black border-white'
                  : 'bg-transparent text-white/40 border-white/10 hover:border-white/30'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-16">
          <div className="text-white/30 text-4xl mb-3">⚠️</div>
          <p className="text-white/50 text-sm">{error}</p>
        </div>
      ) : updates.length === 0 ? (
        <div className="text-center py-16 border border-white/10 rounded-xl">
          <div className="text-4xl mb-3">📰</div>
          <p className="text-white/50 text-sm">No updates found for this filter.</p>
          <p className="text-white/30 text-xs mt-1">Updates are refreshed weekly.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {updates.map((update: any) => (
            <LegalUpdateCard key={update.id} update={update} />
          ))}
        </div>
      )}
    </div>
  )
}
