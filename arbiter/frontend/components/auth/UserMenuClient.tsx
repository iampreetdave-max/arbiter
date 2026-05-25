'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

/**
 * User avatar + dropdown menu.
 * Session 8: Added nav links, Account Settings, verified badge.
 */
export function UserMenuClient() {
  const { user, signOut } = useAuth()
  const router = useRouter()
  const [open, setOpen] = useState(false)

  const handleSignOut = async () => {
    await signOut()
    router.push('/')
  }

  const initial = user?.displayName?.[0]?.toUpperCase() ?? user?.email?.[0]?.toUpperCase() ?? 'U'
  const displayName = user?.displayName ?? user?.email ?? 'User'

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-8 h-8 rounded-full bg-[#111] border border-[#222] flex items-center justify-center text-white text-xs font-bold hover:border-[#444] transition-colors"
        aria-label="User menu"
        aria-expanded={open}
      >
        {initial}
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute right-0 top-10 z-50 w-56 rounded-xl border border-[#1a1a1a] bg-[#080808] shadow-2xl p-1">
            <div className="px-3 py-2.5 border-b border-[#111] mb-1">
              <p className="text-xs font-medium text-white truncate">
                {displayName}
              </p>
              {user?.displayName && (
                <p className="text-[10px] text-[#444] truncate">{user.email}</p>
              )}
              <div className="flex items-center gap-1.5 mt-1">
                <span className="text-[10px] text-[#444]">Free plan</span>
                {user?.emailVerified && (
                  <span className="text-[9px] bg-emerald-900/30 text-emerald-400 border border-emerald-900/40 px-1.5 py-0.5 rounded-full">
                    Verified
                  </span>
                )}
              </div>
            </div>

            <div className="px-3 py-2 border-b border-[#111] mb-1 space-y-0.5">
              <p className="text-[10px] text-[#444] uppercase tracking-widest font-semibold mb-1">Navigation</p>
              <a
                href="/cases"
                className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm text-[#888] hover:text-white hover:bg-white/5 transition-all"
                onClick={() => setOpen(false)}
              >
                My Cases
              </a>
              <a
                href="/legal-updates"
                className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm text-[#888] hover:text-white hover:bg-white/5 transition-all"
                onClick={() => setOpen(false)}
              >
                Law Updates
              </a>
              <a
                href="/public-cases"
                className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm text-[#888] hover:text-white hover:bg-white/5 transition-all"
                onClick={() => setOpen(false)}
              >
                Case Showcase
              </a>
            </div>

            <a
              href="/account"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#888] hover:text-white hover:bg-white/5 transition-all"
              onClick={() => setOpen(false)}
            >
              Account Settings
            </a>

            <button
              onClick={handleSignOut}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#888] hover:text-red-400 hover:bg-red-900/10 transition-all"
            >
              Sign out
            </button>
          </div>
        </>
      )}
    </div>
  )
}
