// Arbiter | Powered by Google Gemini 2.0 Pro | XPRIZE Build with Gemini
/**
 * Protected app shell layout.
 * AuthGuard ensures only authenticated users can access these pages.
 * Session 8: Added nav links for legal updates, public cases, and lawyer pages.
 */
import { AuthGuard } from '@/components/auth/AuthGuard'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-black">
        <AppTopBar />
        <main>{children}</main>
      </div>
    </AuthGuard>
  )
}

function AppTopBar() {
  return (
    <header className="sticky top-0 z-40 bg-black/80 backdrop-blur-xl border-b border-[#0f0f0f]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
        <a
          href="/"
          className="text-white font-bold text-lg tracking-tight hover:opacity-80 transition-opacity flex-shrink-0"
        >
          Arbiter
        </a>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-1 text-xs text-white/50">
          <a href="/cases" className="px-2.5 py-1.5 rounded-lg hover:bg-white/8 hover:text-white transition-all">
            My Cases
          </a>
          <a href="/legal-updates" className="px-2.5 py-1.5 rounded-lg hover:bg-white/8 hover:text-white transition-all">
            Law Updates
          </a>
          <a href="/public-cases" className="px-2.5 py-1.5 rounded-lg hover:bg-white/8 hover:text-white transition-all">
            Case Showcase
          </a>
          <a href="/lawyer/dashboard" className="px-2.5 py-1.5 rounded-lg hover:bg-white/8 hover:text-white transition-all">
            For Lawyers
          </a>
        </nav>

        <div className="flex items-center gap-2 flex-shrink-0">
          <a
            href="/cases/new"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 btn-shiny text-black rounded-lg text-xs font-semibold hover:opacity-90 transition-opacity"
          >
            + New Case
          </a>
          <UserMenu />
        </div>
      </div>
    </header>
  )
}

import { UserMenuClient } from '@/components/auth/UserMenuClient'
function UserMenu() {
  return <UserMenuClient />
}
