'use client'
import { useState, useEffect, useCallback } from 'react'
import { useAdminKey } from '../layout'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const STATUS_TABS = ['all', 'pending', 'verified', 'rejected'] as const
type StatusTab = typeof STATUS_TABS[number]

const SPECIALTY_LABELS: Record<string, string> = {
  tenant_disputes: 'Tenant', employment_law: 'Employment', consumer_protection: 'Consumer',
  criminal_law: 'Criminal', family_law: 'Family', corporate_law: 'Corporate',
  intellectual_property: 'IP', immigration: 'Immigration', tax_law: 'Tax',
  constitutional_law: 'Constitutional', civil_rights: 'Civil Rights',
  environmental_law: 'Environmental', real_estate: 'Real Estate',
}

export default function LawyersAdminPage() {
  const adminKey = useAdminKey()
  const [lawyers, setLawyers] = useState<any[]>([])
  const [filter, setFilter] = useState<StatusTab>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState<{msg: string, ok: boolean} | null>(null)
  const [rejecting, setRejecting] = useState<{id: string, name: string} | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [acting, setActing] = useState<string | null>(null)

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok })
    setTimeout(() => setToast(null), 3000)
  }

  const fetchLawyers = useCallback(async () => {
    if (!adminKey) return
    setLoading(true)
    try {
      const params = filter !== 'all' ? `?status_filter=${filter}` : ''
      const res = await fetch(`${API_URL}/api/admin/lawyers${params}`, {
        headers: { 'X-Admin-Key': adminKey },
      })
      const data = await res.json()
      if (res.status === 403) { setError('Invalid admin key'); return }
      setLawyers(data.lawyers ?? [])
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }, [adminKey, filter])

  useEffect(() => { fetchLawyers() }, [fetchLawyers])

  const updateStatus = async (id: string, status: string, reason?: string) => {
    setActing(id)
    try {
      const res = await fetch(`${API_URL}/api/admin/lawyers/${id}/verify`, {
        method: 'PUT',
        headers: { 'X-Admin-Key': adminKey, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, ...(reason ? { rejection_reason: reason } : {}) }),
      })
      if (res.ok) {
        showToast(`Lawyer ${status === 'verified' ? 'approved' : 'rejected'} ✓`)
        setRejecting(null)
        setRejectReason('')
        fetchLawyers()
      } else {
        showToast('Action failed. Try again.', false)
      }
    } catch { showToast('Network error.', false) }
    finally { setActing(null) }
  }

  // Count per status (counts from the full unfiltered list aren't always available,
  // so we show counts only for whatever is currently loaded)
  const counts = lawyers.reduce((acc: Record<string, number>, l) => {
    acc[l.status] = (acc[l.status] || 0) + 1
    return acc
  }, {})

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Lawyer Management</h1>
          <p className="text-[#555] text-sm mt-0.5">Review and approve lawyer applications</p>
        </div>
        <button
          onClick={fetchLawyers}
          className="text-xs text-[#555] hover:text-white border border-[#1a1a1a] rounded-lg px-3 py-1.5 transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1.5 flex-wrap">
        {STATUS_TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize ${
              filter === tab
                ? 'bg-white text-black'
                : 'border border-[#1a1a1a] text-[#666] hover:text-white'
            }`}
          >
            {tab}
            {tab !== 'all' && counts[tab]
              ? <span className="ml-1 opacity-60">({counts[tab]})</span>
              : null}
          </button>
        ))}
      </div>

      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2.5 rounded-lg text-sm font-medium shadow-xl ${
          toast.ok
            ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-800'
            : 'bg-red-900/80 text-red-300 border border-red-800'
        }`}>
          {toast.msg}
        </div>
      )}

      {error && (
        <div className="text-red-400 text-sm bg-red-900/10 border border-red-900/20 rounded-lg p-3">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-[#555] text-sm">Loading lawyers…</div>
      ) : lawyers.length === 0 ? (
        <div className="text-center py-12 text-[#444]">No lawyers in this category.</div>
      ) : (
        <div className="space-y-3">
          {lawyers.map(lawyer => (
            <div key={lawyer.id} className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-5">
              <div className="flex items-start justify-between gap-4">
                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-white font-semibold">
                      {lawyer.full_name || lawyer.name || 'Unknown'}
                    </h3>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium border ${
                      lawyer.status === 'verified'
                        ? 'bg-emerald-900/30 text-emerald-400 border-emerald-900/40'
                        : lawyer.status === 'pending'
                        ? 'bg-yellow-900/30 text-yellow-400 border-yellow-900/40'
                        : 'bg-red-900/30 text-red-400 border-red-900/40'
                    }`}>
                      {lawyer.status}
                    </span>
                    {lawyer.pro_bono && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-900/30 text-blue-400 border border-blue-900/40">
                        Pro Bono
                      </span>
                    )}
                  </div>

                  <p className="text-[#555] text-xs mt-1">{lawyer.email}</p>

                  {/* Specialties */}
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {(lawyer.specialties || []).slice(0, 4).map((s: string) => (
                      <span
                        key={s}
                        className="text-[10px] px-2 py-0.5 rounded-md bg-[#111] text-[#888] border border-[#1a1a1a]"
                      >
                        {SPECIALTY_LABELS[s] || s}
                      </span>
                    ))}
                    {(lawyer.specialties || []).length > 4 && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-[#111] text-[#555] border border-[#1a1a1a]">
                        +{lawyer.specialties.length - 4} more
                      </span>
                    )}
                  </div>

                  {/* Meta */}
                  <div className="flex flex-wrap gap-4 mt-2 text-xs text-[#444]">
                    {lawyer.country_code && <span>🌍 {lawyer.country_code}</span>}
                    {lawyer.years_experience && <span>📅 {lawyer.years_experience}y exp</span>}
                    {lawyer.rating && <span>⭐ {lawyer.rating}/5</span>}
                    {lawyer.cases_count !== undefined && <span>📁 {lawyer.cases_count} cases</span>}
                    {lawyer.registration_date && (
                      <span>Registered {new Date(lawyer.registration_date).toLocaleDateString()}</span>
                    )}
                  </div>

                  {/* Rejection reason */}
                  {lawyer.rejection_reason && (
                    <p className="text-xs text-red-400/80 mt-2 italic">
                      Rejection reason: {lawyer.rejection_reason}
                    </p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2 flex-shrink-0">
                  {/* Approve — shown for pending + rejected */}
                  {lawyer.status !== 'verified' && (
                    <button
                      disabled={acting === lawyer.id}
                      onClick={() => updateStatus(lawyer.id, 'verified')}
                      className="px-3 py-1.5 text-xs font-medium border border-emerald-800 text-emerald-400 rounded-lg hover:bg-emerald-900/20 transition-colors disabled:opacity-40"
                    >
                      ✓ {lawyer.status === 'rejected' ? 'Re-approve' : 'Approve'}
                    </button>
                  )}

                  {/* Reject / Revoke — shown for pending + verified */}
                  {lawyer.status !== 'rejected' && (
                    rejecting?.id === lawyer.id ? (
                      <div className="space-y-1.5">
                        <textarea
                          value={rejectReason}
                          onChange={e => setRejectReason(e.target.value)}
                          placeholder="Reason (optional)"
                          rows={2}
                          className="w-40 bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg px-2 py-1.5 text-xs text-white placeholder-[#333] resize-none focus:outline-none focus:border-[#444]"
                        />
                        <div className="flex gap-1">
                          <button
                            onClick={() => updateStatus(lawyer.id, 'rejected', rejectReason)}
                            disabled={acting === lawyer.id}
                            className="flex-1 px-2 py-1 text-[10px] border border-red-800 text-red-400 rounded-lg hover:bg-red-900/20 disabled:opacity-40"
                          >
                            Confirm
                          </button>
                          <button
                            onClick={() => { setRejecting(null); setRejectReason('') }}
                            className="px-2 py-1 text-[10px] border border-[#222] text-[#666] rounded-lg hover:text-white"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        disabled={acting === lawyer.id}
                        onClick={() => setRejecting({ id: lawyer.id, name: lawyer.full_name || lawyer.name })}
                        className="px-3 py-1.5 text-xs font-medium border border-red-900 text-red-400 rounded-lg hover:bg-red-900/20 transition-colors disabled:opacity-40"
                      >
                        ✗ {lawyer.status === 'verified' ? 'Revoke' : 'Reject'}
                      </button>
                    )
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
