'use client'
import { useState, useEffect, useCallback, useMemo } from 'react'
import { useAdminKey } from '../layout'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function UsersAdminPage() {
  const adminKey = useAdminKey()
  const [users, setUsers] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [totalRevenue, setTotalRevenue] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<'cases' | 'revenue'>('cases')

  const fetchUsers = useCallback(async () => {
    if (!adminKey) return
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/users?limit=500`, {
        headers: { 'X-Admin-Key': adminKey },
      })
      if (res.status === 403) { setError('Invalid admin key'); return }
      const data = await res.json()
      setUsers(data.users ?? [])
      setTotal(data.total ?? 0)
      setTotalRevenue(data.total_revenue_inr ?? 0)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }, [adminKey])

  useEffect(() => { fetchUsers() }, [fetchUsers])

  const filtered = useMemo(() => {
    let result = [...users]
    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter(
        u => u.user_id?.toLowerCase().includes(q) || u.email?.toLowerCase().includes(q)
      )
    }
    result.sort((a, b) =>
      sort === 'cases'
        ? (b.total_cases ?? 0) - (a.total_cases ?? 0)
        : (b.revenue_inr ?? 0) - (a.revenue_inr ?? 0)
    )
    return result
  }, [users, search, sort])

  const avgRevenue = total > 0 ? Math.round(totalRevenue / total) : 0

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">User Management</h1>
          <p className="text-[#555] text-sm mt-0.5">
            {total} total users · ₹{totalRevenue.toLocaleString()} revenue
          </p>
        </div>
        <button
          onClick={fetchUsers}
          className="text-xs text-[#555] hover:text-white border border-[#1a1a1a] rounded-lg px-3 py-1.5 transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-white">{total}</div>
          <div className="text-xs text-[#555] mt-1">Total Users</div>
        </div>
        <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-white">₹{totalRevenue.toLocaleString()}</div>
          <div className="text-xs text-[#555] mt-1">Total Revenue</div>
        </div>
        <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-white">₹{avgRevenue.toLocaleString()}</div>
          <div className="text-xs text-[#555] mt-1">Avg Revenue / User</div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search by user ID or email…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-white placeholder-[#333] focus:outline-none focus:border-[#333] transition-colors"
        />
        <select
          value={sort}
          onChange={e => setSort(e.target.value as 'cases' | 'revenue')}
          className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#333] transition-colors"
        >
          <option value="cases">Sort: Most Cases</option>
          <option value="revenue">Sort: Most Revenue</option>
        </select>
      </div>

      {error && (
        <div className="text-red-400 text-sm bg-red-900/10 border border-red-900/20 rounded-lg p-3">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-[#555] text-sm">Loading users…</div>
      ) : (
        <>
          {search.trim() && (
            <p className="text-xs text-[#444]">
              {filtered.length} of {users.length} users matching "{search}"
            </p>
          )}
          <div className="bg-[#050505] border border-[#1a1a1a] rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#111] text-[#444] text-xs">
                  <th className="text-left px-4 py-3">User</th>
                  <th className="text-right px-4 py-3">Cases</th>
                  <th className="text-right px-4 py-3">Paid</th>
                  <th className="text-right px-4 py-3">Revenue</th>
                  <th className="text-right px-4 py-3 hidden sm:table-cell">Countries</th>
                  <th className="text-right px-4 py-3 hidden md:table-cell">Last Active</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-[#444]">
                      No users found.
                    </td>
                  </tr>
                ) : (
                  filtered.map((user, i) => (
                    <tr
                      key={user.user_id}
                      className={`border-b border-[#0a0a0a] hover:bg-white/[0.02] transition-colors ${
                        i % 2 === 0 ? '' : 'bg-[#030303]'
                      }`}
                    >
                      <td className="px-4 py-3">
                        <div className="text-white text-xs font-mono truncate max-w-[140px]">
                          {user.user_id?.length > 12
                            ? `${user.user_id.slice(0, 12)}…`
                            : user.user_id ?? '—'}
                        </div>
                        {user.email && (
                          <div className="text-[#555] text-[10px] truncate max-w-[140px]">
                            {user.email}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-white">
                        {user.total_cases ?? 0}
                      </td>
                      <td className="px-4 py-3 text-right text-white">
                        {user.paid_cases ?? 0}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={(user.revenue_inr ?? 0) > 0 ? 'text-emerald-400' : 'text-[#444]'}>
                          ₹{(user.revenue_inr ?? 0).toLocaleString()}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right hidden sm:table-cell text-[#666] text-xs">
                        {(user.countries || []).join(', ') || '—'}
                      </td>
                      <td className="px-4 py-3 text-right hidden md:table-cell text-[#555] text-xs">
                        {user.latest_case_at
                          ? new Date(user.latest_case_at).toLocaleDateString()
                          : '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
