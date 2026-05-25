/**
 * Protected app shell layout.
 * AuthGuard ensures only authenticated users can access these pages.
 * Includes a minimal top bar with user menu.
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
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <a
          href="/"
          className="text-white font-bold text-lg tracking-tight hover:opacity-80 transition-opacity"
        >
          Arbiter ⚖️
        </a>

        <div className="flex items-center gap-3">
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

// Extracted as a client-only component to avoid making the whole layout a client component
import { UserMenuClient } from '@/components/auth/UserMenuClient'
function UserMenu() {
  return <UserMenuClient />
}
