'use client'
import { useState, useEffect, useCallback } from 'react'
import { useAdminKey } from '../layout'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type SecurityEvent = {
  id: string
  event_type: string
  user_id?: string
  ip_address?: string
  timestamp: string
  details?: string
  severity?: 'low' | 'medium' | 'high'
}

const EVENT_STYLES: Record<string, { label: string; color: string }> = {
  injection_attempt:    { label: 'Injection Attempt',    color: 'text-red-400 border-red-900/40 bg-red-900/10' },
  jailbreak_attempt:    { label: 'Jailbreak Attempt',    color: 'text-red-400 border-red-900/40 bg-red-900/10' },
  rate_limit_violation: { label: 'Rate Limit Violation', color: 'text-yellow-400 border-yellow-900/40 bg-yellow-900/10' },
  off_topic_spam:       { label: 'Off-Topic Spam',       color: 'text-yellow-400 border-yellow-900/40 bg-yellow-900/10' },
  invalid_auth:         { label: 'Invalid Auth',         color: 'text-orange-400 border-orange-900/40 bg-orange-900/10' },
  suspicious_pattern:   { label: 'Suspicious Pattern',  color: 'text-orange-400 border-orange-900/40 bg-orange-900/10' },
}

const getEventStyle = (type: string) =>
  EVENT_STYLES[type] ?? { label: type.replace(/_/g, ' '), color: 'text-[#888] border-[#1a1a1a] bg-[#0a0a0a]' }

export default function SecurityAdminPage() {
  const adminKey = useAdminKey()
  const [events, setEvents] = useState<SecurityEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reviewed, setReviewed] = useState<Set<string>>(new Set())
  const [typeFilter, setTypeFilter] = useState<string>('all')

  const fetchEvents = useCallback(async () => {
    if (!adminKey) return
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/security-events`, {
        headers: { 'X-Admin-Key': adminKey },
      })
      if (res.status === 403) { setError('Invalid admin key'); return }
      const data = await res.json()
      setEvents(data.events ?? data ?? [])
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }, [adminKey])

  useEffect(() => { fetchEvents() }, [fetchEvents])

  const toggleReviewed = (id: string) => {
    setReviewed(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  // Derive unique event types for the filter bar
  const eventTypes = ['all', ...Array.from(new Set(events.map(e => e.event_type)))]

  const filtered = typeFilter === 'all'
    ? events
    : events.filter(e => e.event_type === typeFilter)

  const unreviewedCount = filtered.filter(e => !reviewed.has(e.id)).length

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Security Events</h1>
          <p className="text-[#555] text-sm mt-0.5">
            Injection attempts · Off-topic spam · Rate limit violations
          </p>
        </div>
        <button
          onClick={fetchEvents}
          className="text-xs text-[#555] hover:text-white border border-[#1a1a1a] rounded-lg px-3 py-1.5 transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Summary row */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-white">{filtered.length}</div>
          <div className="text-xs text-[#555] mt-1">Total Events</div>
        </div>
        <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-red-400">{unreviewedCount}</div>
          <div className="text-xs text-[#555] mt-1">Unreviewed</div>
        </div>
        <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-emerald-400">{reviewed.size}</div>
          <div className="text-xs text-[#555] mt-1">Reviewed</div>
        </div>
      </div>

      {/* Event type filter */}
      <div className="flex gap-1.5 flex-wrap">
        {eventTypes.map(type => (
          <button
            key={type}
            onClick={() => setTypeFilter(type)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize ${
              typeFilter === type
                ? 'bg-white text-black'
                : 'border border-[#1a1a1a] text-[#666] hover:text-white'
            }`}
          >
            {type === 'all' ? 'All Types' : getEventStyle(type).label}
          </button>
        ))}
      </div>

      {error && (
        <div className="text-red-400 text-sm bg-red-900/10 border border-red-900/20 rounded-lg p-3">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-[#555] text-sm">Loading security events…</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-[#444]">No security events recorded.</div>
      ) : (
        <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#111] text-[#444] text-xs">
                <th className="text-left px-4 py-3">Event</th>
                <th className="text-left px-4 py-3 hidden sm:table-cell">User / IP</th>
                <th className="text-left px-4 py-3 hidden md:table-cell">Details</th>
                <th className="text-right px-4 py-3">Time</th>
                <th className="text-right px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((event, i) => {
                const style = getEventStyle(event.event_type)
                const isReviewed = reviewed.has(event.id)
                return (
                  <tr
                    key={event.id}
                    className={`border-b border-[#0a0a0a] transition-colors ${
                      isReviewed ? 'opacity-40' : 'hover:bg-white/[0.02]'
                    } ${i % 2 === 0 ? '' : 'bg-[#030303]'}`}
                  >
                    {/* Event type badge */}
                    <td className="px-4 py-3">
                      <span className={`text-[10px] px-2 py-0.5 rounded-md border font-medium ${style.color}`}>
                        {style.label}
                      </span>
                    </td>

                    {/* User / IP */}
                    <td className="px-4 py-3 hidden sm:table-cell">
                      <div className="text-[#666] text-xs font-mono truncate max-w-[160px]">
                        {event.user_id
                          ? event.user_id.length > 14
                            ? `${event.user_id.slice(0, 14)}…`
                            : event.user_id
                          : '—'}
                      </div>
                      {event.ip_address && (
                        <div className="text-[#444] text-[10px] font-mono">{event.ip_address}</div>
                      )}
                    </td>

                    {/* Details */}
                    <td className="px-4 py-3 hidden md:table-cell">
                      <span className="text-[#555] text-xs truncate max-w-[200px] block">
                        {event.details ?? '—'}
                      </span>
                    </td>

                    {/* Timestamp */}
                    <td className="px-4 py-3 text-right text-[#444] text-xs whitespace-nowrap">
                      {event.timestamp
                        ? new Date(event.timestamp).toLocaleString('en-IN', {
                            month: 'short', day: 'numeric',
                            hour: '2-digit', minute: '2-digit',
                          })
                        : '—'}
                    </td>

                    {/* Mark reviewed (UI-only) */}
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => toggleReviewed(event.id)}
                        className={`text-[10px] px-2 py-1 rounded-lg border transition-colors ${
                          isReviewed
                            ? 'border-emerald-900/40 text-emerald-600 hover:text-emerald-400'
                            : 'border-[#1a1a1a] text-[#444] hover:text-white hover:border-[#333]'
                        }`}
                      >
                        {isReviewed ? '✓ Reviewed' : 'Review'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Note */}
      <p className="text-[10px] text-[#333] text-center pt-2">
        "Reviewed" status is session-only — not persisted to the server.
      </p>
    </div>
  )
}
