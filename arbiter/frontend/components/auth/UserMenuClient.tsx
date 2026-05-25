'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

/**
 * User avatar + dropdown menu — sign out + account info.
 * Separated into a client component so AppLayout stays a Server Component.
 */
export function UserMenuClient() {
  const { user, signOut } = useAuth()
  const router = useRouter()
  const [open, setOpen] = useState(false)

  const handleSignOut = async () => {
    await signOut()
    router.push('/')
  }

  const initial = user?.email?.[0]?.toUpperCase() ?? 'U'

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
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          {/* Dropdown */}
          <div className="absolute right-0 top-10 z-50 w-56 rounded-xl border border-[#1a1a1a] bg-[#080808] shadow-2xl p-1">
            <div className="px-3 py-2.5 border-b border-[#111] mb-1">
              <p className="text-xs font-medium text-white truncate">
                {user?.email}
              </p>
              <p className="text-[10px] text-[#444] mt-0.5">Free plan</p>
            </div>

            <a
              href="/cases"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#888] hover:text-white hover:bg-white/5 transition-all"
              onClick={() => setOpen(false)}
            >
              My Cases
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
