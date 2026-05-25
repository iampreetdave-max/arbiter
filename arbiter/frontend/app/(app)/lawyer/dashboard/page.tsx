'use client'

/**
 * Lawyer Dashboard — shows matched cases for verified lawyers.
 */
import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending:   { label: 'Awaiting Response', color: 'text-white/60' },
  accepted:  { label: 'Accepted',          color: 'text-green-400' },
  declined:  { label: 'Declined',          color: 'text-white/30' },
  completed: { label: 'Completed',         color: 'text-white/80' },
}

const PROBLEM_LABELS: Record<string, string> = {
  tenant_dispute: 'Tenant Dispute',
  employment:     'Employment',
  consumer:       'Consumer',
  rti:            'RTI',
  harassment:     'Harassment',
  debt_recovery:  'Debt Recovery',
  other:          'Other',
}

export default function LawyerDashboardPage() {
  const { user } = useAuth()
  const [matches, setMatches] = useState<any[]>([])
  const [profile, setProfile] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [responding, setResponding] = useState<string | null>(null)

  const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  const getToken = async () => {
    const { auth } = await import('@/lib/firebase')
    return auth.currentUser ? await auth.currentUser.getIdToken() : ''
  }

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const token = await getToken()
        const headers = { Authorization: `Bearer ${token}` }

        // Fetch profile
        const profileRes = await fetch(`${BASE}/api/lawyers/me`, { headers })
        if (profileRes.status === 404) {
          setError('no_profile')
          return
        }
        const profileData = await profileRes.json()
        setProfile(profileData)

        // Fetch matches
        const params = new URLSearchParams()
        if (statusFilter) params.set('status_filter', statusFilter)
        const matchesRes = await fetch(`${BASE}/api/lawyers/me/cases?${params}`, { headers })
        const matchesData = await matchesRes.json()
        setMatches(matchesData.matches ?? [])
      } catch {
        setError('Failed to load dashboard.')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [statusFilter])

  const respond = async (matchId: string, action: 'accept' | 'decline') => {
    setResponding(matchId)
    try {
      const token = await getToken()
      await fetch(`${BASE}/api/lawyers/me/cases/${matchId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ action }),
      })
      setMatches((prev) =>
        prev.map((m) =>
          m.id === matchId ? { ...m, status: action === 'accept' ? 'accepted' : 'declined' } : m
        )
      )
    } catch { }
    finally { setResponding(null) }
  }

  if (error === 'no_profile') {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center space-y-4">
        <div className="text-4xl">⚖️</div>
        <h2 className="text-xl font-bold text-white">Not Registered Yet</h2>
        <p className="text-white/50 text-sm">Register as a lawyer to start receiving cases.</p>
        <a href="/lawyer/register" className="inline-block mt-4 px-6 py-2.5 bg-white text-black rounded-lg font-semibold text-sm">
          Register as Lawyer
        </a>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Lawyer Dashboard</h1>
          {profile && (
            <p className="text-white/50 text-sm mt-0.5">
              {profile.full_name} · Status: <span className={profile.status === 'verified' ? 'text-green-400' : 'text-amber-400'}>{profile.status}</span>
            </p>
          )}
        </div>
        <a href="/lawyer/register" className="text-xs text-white/40 border border-white/15 px-3 py-1.5 rounded-lg hover:border-white/40">
          Edit Profile
        </a>
      </div>

      {profile?.status === 'pending' && (
        <div className="bg-white/5 border border-white/20 rounded-xl p-4 text-sm text-white/60">
          ⏳ Your profile is pending verification. You'll receive matched cases once verified (24–48 hours).
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {[['', 'All'], ['pending', 'Pending'], ['accepted', 'Accepted'], ['declined', 'Declined']].map(([val, label]) => (
          <button
            key={val}
            onClick={() => setStatusFilter(val)}
            className={`px-3 py-1 rounded-full text-xs border transition-all ${
              statusFilter === val ? 'bg-white text-black border-white' : 'text-white/50 border-white/15 hover:border-white/35'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1,2,3].map((i) => <div key={i} className="h-32 bg-white/5 rounded-xl animate-pulse" />)}
        </div>
      ) : matches.length === 0 ? (
        <div className="text-center py-16 border border-white/10 rounded-xl">
          <div className="text-3xl mb-2">📭</div>
          <p className="text-white/40 text-sm">No matched cases yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {matches.map((match: any) => {
            const s = STATUS_LABELS[match.status] ?? { label: match.status, color: 'text-white/50' }
            return (
              <div key={match.id} className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-white font-medium text-sm">{match.case_title}</h3>
                    <div className="text-white/40 text-xs mt-0.5">
                      {PROBLEM_LABELS[match.case_problem_type] ?? match.case_problem_type}
                      {' · '}{match.case_jurisdiction}
                    </div>
                  </div>
                  <span className={`text-xs font-medium ${s.color}`}>{s.label}</span>
                </div>

                <div className="flex items-center gap-2 text-[10px] text-white/30">
                  <span>Match score: {Math.round(match.match_score * 100)}%</span>
                  <span>·</span>
                  <span>{new Date(match.created_at).toLocaleDateString()}</span>
                </div>

                {match.status === 'pending' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => respond(match.id, 'accept')}
                      disabled={responding === match.id}
                      className="flex-1 py-2 bg-white text-black rounded-lg text-xs font-semibold disabled:opacity-50"
                    >
                      {responding === match.id ? '…' : 'Accept Case'}
                    </button>
                    <button
                      onClick={() => respond(match.id, 'decline')}
                      disabled={responding === match.id}
                      className="flex-1 py-2 border border-white/20 text-white/60 rounded-lg text-xs font-medium"
                    >
                      Decline
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
