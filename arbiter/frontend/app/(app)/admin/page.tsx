'use client'
import { useState, useEffect, useCallback } from 'react'
import { useAdminKey } from './layout'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── Types ─────────────────────────────────────────────────────────────────────
interface Overview {
  unique_users: number
  revenue_inr: number
  cases: {
    total: number
    intake: number
    paid: number
    complete: number
    escalated: number
  }
  lawyers: {
    total: number
    pending: number
    verified: number
    rejected: number
  }
}

interface ServiceCheck {
  status: 'ok' | 'error'
  detail?: string
}

interface HealthResponse {
  status: string
  services: Record<string, ServiceCheck>
}

interface EndpointLatency {
  p50: number
  p95: number
  p99: number
  count: number
}

interface MetricsResponse {
  metrics: {
    endpoint_latencies_ms: Record<string, EndpointLatency>
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function StatCard({ icon, value, label }: { icon: string; value: string | number; label: string }) {
  return (
    <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-4">
      <div className="text-xl mb-2">{icon}</div>
      <div className="text-2xl font-bold text-white tabular-nums">{value}</div>
      <div className="text-xs text-[#555] mt-1">{label}</div>
    </div>
  )
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-[11px] font-semibold text-[#888] uppercase tracking-widest mb-4">
      {children}
    </h2>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function AdminDashboard() {
  const adminKey = useAdminKey()
  const [overview, setOverview] = useState<Overview | null>(null)
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchAll = useCallback(async () => {
    if (!adminKey) return
    setLoading(true)
    setError('')
    try {
      const headers = { 'X-Admin-Key': adminKey }
      const [overviewRes, metricsRes, healthRes] = await Promise.all([
        fetch(`${API_URL}/api/admin/overview`, { headers }),
        fetch(`${API_URL}/api/admin/metrics`, { headers }),
        fetch(`${API_URL}/api/admin/health/full`, { headers }),
      ])

      if (overviewRes.status === 403) {
        setError('Invalid admin key — please lock and re-enter.')
        setLoading(false)
        return
      }

      const [overviewData, metricsData, healthData] = await Promise.all([
        overviewRes.json(),
        metricsRes.ok ? metricsRes.json() : Promise.resolve(null),
        healthRes.ok ? healthRes.json() : Promise.resolve(null),
      ])

      setOverview(overviewData)
      setMetrics(metricsData)
      setHealth(healthData)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch dashboard data.')
    } finally {
      setLoading(false)
    }
  }, [adminKey])

  useEffect(() => { fetchAll() }, [fetchAll])

  // ── States ────────────────────────────────────────────────────────────────
  if (loading) return (
    <div className="flex items-center gap-3 text-[#555] text-sm pt-4">
      <div className="w-4 h-4 border border-white/20 border-t-white rounded-full animate-spin" />
      Loading dashboard…
    </div>
  )

  if (error) return (
    <div className="text-red-400 text-sm bg-red-900/10 border border-red-900/20 rounded-xl p-5">
      <p className="font-medium mb-1">Error</p>
      <p className="text-red-300/70">{error}</p>
      <button onClick={fetchAll} className="mt-3 text-xs underline underline-offset-2 hover:text-red-300 transition-colors">
        Retry
      </button>
    </div>
  )

  if (!overview) return null

  // ── Data ──────────────────────────────────────────────────────────────────
  const statCards = [
    { label: 'Unique Users', value: overview.unique_users ?? '—', icon: '👥' },
    { label: 'Total Cases', value: overview.cases?.total ?? '—', icon: '📁' },
    { label: 'Revenue', value: `₹${(overview.revenue_inr ?? 0).toLocaleString('en-IN')}`, icon: '💰' },
    { label: 'Lawyers Pending', value: overview.lawyers?.pending ?? '—', icon: '⚖️' },
  ]

  const caseStatuses: Array<{ key: keyof typeof overview.cases; color: string }> = [
    { key: 'intake', color: 'text-white' },
    { key: 'paid', color: 'text-blue-400' },
    { key: 'complete', color: 'text-emerald-400' },
    { key: 'escalated', color: 'text-yellow-400' },
  ]

  const lawyerStatuses: Array<{ key: keyof typeof overview.lawyers; color: string }> = [
    { key: 'pending', color: 'text-yellow-400' },
    { key: 'verified', color: 'text-emerald-400' },
    { key: 'rejected', color: 'text-red-400' },
  ]

  const serviceChecks = health?.services ?? {}
  const latencies = metrics?.metrics?.endpoint_latencies_ms

  return (
    <div className="space-y-5">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">Admin Dashboard</h1>
          <p className="text-[#555] text-sm mt-0.5">Real-time Arbiter operations</p>
        </div>
        <button
          onClick={fetchAll}
          className="flex-shrink-0 text-xs text-[#555] hover:text-white border border-[#1a1a1a] rounded-lg px-3 py-1.5 transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      {/* ── Stat cards ─────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {statCards.map(card => (
          <StatCard key={card.label} icon={card.icon} value={card.value} label={card.label} />
        ))}
      </div>

      {/* ── Case breakdown ──────────────────────────────────────────────────── */}
      <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-5">
        <SectionHeading>Case Status Breakdown</SectionHeading>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {caseStatuses.map(({ key, color }) => (
            <div key={key} className="text-center">
              <div className={`text-2xl font-bold tabular-nums ${color}`}>
                {overview.cases?.[key] ?? 0}
              </div>
              <div className="text-xs text-[#555] capitalize mt-1">{key}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Lawyer registry ─────────────────────────────────────────────────── */}
      <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-5">
        <SectionHeading>Lawyer Registry</SectionHeading>
        <div className="grid grid-cols-3 gap-4">
          {lawyerStatuses.map(({ key, color }) => (
            <div key={key} className="text-center">
              <div className={`text-2xl font-bold tabular-nums ${color}`}>
                {overview.lawyers?.[key] ?? 0}
              </div>
              <div className="text-xs text-[#555] capitalize mt-1">{key}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Service health ──────────────────────────────────────────────────── */}
      {health && (
        <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <SectionHeading>Service Health</SectionHeading>
            <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
              health.status === 'ok'
                ? 'text-emerald-400 border-emerald-400/20 bg-emerald-400/5'
                : 'text-yellow-400 border-yellow-400/20 bg-yellow-400/5'
            }`}>
              {health.status ?? '…'}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {Object.entries(serviceChecks).map(([name, check]) => (
              <div key={name} className="flex items-start gap-2.5">
                <span className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${
                  check.status === 'ok' ? 'bg-emerald-400' : 'bg-red-400'
                }`} />
                <div className="min-w-0">
                  <div className="text-xs text-white capitalize font-medium">{name}</div>
                  {check.status !== 'ok' && check.detail && (
                    <div className="text-[10px] text-red-400 truncate">{check.detail}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── API Latency table ───────────────────────────────────────────────── */}
      {latencies && Object.keys(latencies).length > 0 && (
        <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-5 overflow-x-auto">
          <SectionHeading>API Latency (ms)</SectionHeading>
          <table className="w-full text-sm min-w-[480px]">
            <thead>
              <tr className="text-[#444] text-xs border-b border-[#111]">
                <th className="text-left pb-2 font-medium">Endpoint</th>
                <th className="text-right pb-2 font-medium">P50</th>
                <th className="text-right pb-2 font-medium">P95</th>
                <th className="text-right pb-2 font-medium">P99</th>
                <th className="text-right pb-2 font-medium">Calls</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#0a0a0a]">
              {Object.entries(latencies).map(([ep, stats]) => (
                <tr key={ep} className="group">
                  <td className="py-2.5 text-[#666] font-mono text-xs truncate max-w-[200px] group-hover:text-[#888] transition-colors">
                    {ep}
                  </td>
                  <td className="py-2.5 text-right text-white tabular-nums">{Math.round(stats.p50)}</td>
                  <td className="py-2.5 text-right text-white tabular-nums">{Math.round(stats.p95)}</td>
                  <td className="py-2.5 text-right text-white tabular-nums">{Math.round(stats.p99)}</td>
                  <td className="py-2.5 text-right text-[#555] tabular-nums">{stats.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

    </div>
  )
}
