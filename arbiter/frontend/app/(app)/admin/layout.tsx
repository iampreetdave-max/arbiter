'use client'
import { useState, useEffect, createContext, useContext } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

// ── Admin Key Context ─────────────────────────────────────────────────────────
export const AdminKeyContext = createContext<string>('')
export function useAdminKey() { return useContext(AdminKeyContext) }

// ── Nav items ─────────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { href: '/admin', label: '📊 Dashboard', exact: true },
  { href: '/admin/lawyers', label: '⚖️ Lawyers' },
  { href: '/admin/users', label: '👥 Users' },
  { href: '/admin/security', label: '🛡️ Security' },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const pathname = usePathname()
  const [adminKey, setAdminKey] = useState<string | null>(null)
  const [keyInput, setKeyInput] = useState('')
  const [keyError, setKeyError] = useState('')

  useEffect(() => {
    const stored = sessionStorage.getItem('arbiter_admin_key')
    if (stored) setAdminKey(stored)
  }, [])

  const handleKeySubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!keyInput.trim()) { setKeyError('Enter admin key'); return }
    sessionStorage.setItem('arbiter_admin_key', keyInput.trim())
    setAdminKey(keyInput.trim())
    setKeyError('')
  }

  // ── Loading state ─────────────────────────────────────────────────────────
  if (loading) return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
    </div>
  )

  // ── Admin key gate ────────────────────────────────────────────────────────
  if (!adminKey) return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center px-4">
      <div className="w-full max-w-sm rounded-2xl border border-[#1a1a1a] bg-[#050505] p-8">
        <div className="text-2xl mb-1">🔐</div>
        <h1 className="text-lg font-bold text-white mb-1">Admin Access</h1>
        <p className="text-[#555] text-sm mb-6">Enter your X-Admin-Key to continue.</p>
        <form onSubmit={handleKeySubmit} className="space-y-4">
          <input
            type="password"
            value={keyInput}
            onChange={e => setKeyInput(e.target.value)}
            placeholder="Admin key"
            autoComplete="off"
            className="w-full bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-4 py-3 text-white text-sm placeholder-[#333] focus:outline-none focus:border-[#444] transition-colors"
          />
          {keyError && <p className="text-red-400 text-xs">{keyError}</p>}
          <button
            type="submit"
            className="w-full bg-white text-black py-3 rounded-lg text-sm font-semibold hover:bg-white/90 transition-colors"
          >
            Enter Admin Panel
          </button>
        </form>
      </div>
    </div>
  )

  // ── Active link helper ────────────────────────────────────────────────────
  const isActive = (item: typeof NAV_ITEMS[0]) =>
    item.exact ? pathname === item.href : pathname.startsWith(item.href)

  return (
    <div className="min-h-screen bg-[#050505]">
      <div className="max-w-7xl mx-auto px-4 py-6 flex gap-6">

        {/* ── Desktop Sidebar ──────────────────────────────────────────────── */}
        <aside className="hidden md:flex flex-col w-48 flex-shrink-0">
          <div className="sticky top-6">
            <p className="text-[10px] text-[#444] uppercase tracking-widest font-semibold mb-4 px-3">
              Admin Panel
            </p>
            <nav className="space-y-0.5">
              {NAV_ITEMS.map(item => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
                    isActive(item)
                      ? 'bg-white/10 text-white font-medium'
                      : 'text-[#666] hover:text-white hover:bg-white/5'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>

            <div className="mt-6 border-t border-[#111] pt-4">
              <button
                onClick={() => {
                  sessionStorage.removeItem('arbiter_admin_key')
                  setAdminKey(null)
                }}
                className="w-full text-left px-3 py-2 rounded-lg text-xs text-[#444] hover:text-red-400 transition-colors"
              >
                🔓 Lock admin
              </button>
            </div>
          </div>
        </aside>

        {/* ── Mobile Top Tabs ───────────────────────────────────────────────── */}
        <div className="flex md:hidden gap-1 mb-4 overflow-x-auto w-full">
          {NAV_ITEMS.map(item => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs transition-all ${
                isActive(item) ? 'bg-white/10 text-white' : 'text-[#666] hover:text-white'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>

        {/* ── Main content ──────────────────────────────────────────────────── */}
        <main className="flex-1 min-w-0">
          <AdminKeyContext.Provider value={adminKey}>
            {children}
          </AdminKeyContext.Provider>
        </main>

      </div>
    </div>
  )
}
