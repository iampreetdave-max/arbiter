'use client'

/**
 * Public Cases — educational showcase of interesting real legal cases.
 */
import { useState, useEffect } from 'react'
import { PublicCaseCard } from '@/components/cases/PublicCaseCard'

const COUNTRIES = [
  { code: '', name: 'All Countries', flag: '🌍' },
  { code: 'IN', name: 'India', flag: '🇮🇳' },
  { code: 'US', name: 'USA', flag: '🇺🇸' },
  { code: 'GB', name: 'UK', flag: '🇬🇧' },
  { code: 'CA', name: 'Canada', flag: '🇨🇦' },
  { code: 'AU', name: 'Australia', flag: '🇦🇺' },
]

const CATEGORIES = [
  { value: '', label: 'All' },
  { value: 'landmark', label: '⚖️ Landmark' },
  { value: 'consumer', label: 'Consumer' },
  { value: 'employment', label: 'Employment' },
  { value: 'tenant', label: 'Tenant' },
  { value: 'civil_rights', label: 'Civil Rights' },
  { value: 'cyber', label: 'Cyber' },
  { value: 'corporate', label: 'Corporate' },
]

export default function PublicCasesPage() {
  const [cases, setCases] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [country, setCountry] = useState('')
  const [category, setCategory] = useState('')
  const [landmarkOnly, setLandmarkOnly] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  useEffect(() => {
    const fetchCases = async () => {
      setLoading(true)
      setError(null)
      try {
        const params = new URLSearchParams()
        if (country) params.set('country_code', country)
        if (category) params.set('category', category)
        if (landmarkOnly) params.set('landmark_only', 'true')
        params.set('limit', '24')

        const res = await fetch(`${BASE}/api/public-cases?${params}`)
        const data = await res.json()
        setCases(data.cases ?? [])
      } catch {
        setError('Failed to load cases.')
      } finally {
        setLoading(false)
      }
    }
    fetchCases()
  }, [country, category, landmarkOnly])

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Case Showcase</h1>
        <p className="text-white/50 text-sm mt-1">
          Learn from real legal cases. Know your rights through precedent.
        </p>
      </div>

      {/* Filters */}
      <div className="space-y-3">
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

        <div className="flex flex-wrap items-center gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.value}
              onClick={() => { setCategory(cat.value); setLandmarkOnly(false) }}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                category === cat.value && !landmarkOnly
                  ? 'bg-white text-black border-white'
                  : 'bg-transparent text-white/40 border-white/10 hover:border-white/30'
              }`}
            >
              {cat.label}
            </button>
          ))}
          <button
            onClick={() => { setLandmarkOnly(!landmarkOnly); setCategory('') }}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
              landmarkOnly
                ? 'bg-white text-black border-white'
                : 'bg-transparent text-white/40 border-white/10 hover:border-white/30'
            }`}
          >
            Landmark Only
          </button>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1,2,3,4,5,6].map((i) => (
            <div key={i} className="h-72 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-16">
          <p className="text-white/50 text-sm">{error}</p>
        </div>
      ) : cases.length === 0 ? (
        <div className="text-center py-16 border border-white/10 rounded-xl">
          <div className="text-4xl mb-3">🏙️</div>
          <p className="text-white/50 text-sm">No cases found for this filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cases.map((c: any) => (
            <PublicCaseCard key={c.id} case_={c} />
          ))}
        </div>
      )}

      <p className="text-center text-white/20 text-xs pb-4">
        All cases are publicly documented. Content is AI-curated and should not be relied upon as legal advice.
      </p>
    </div>
  )
}
