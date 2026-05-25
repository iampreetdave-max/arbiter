/**
 * Auth layout — centered card, no navbar.
 * Used for /sign-in and /sign-up.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <a href="/" className="flex items-center justify-center gap-2 mb-8 group">
          <span className="text-white font-bold text-2xl tracking-tight group-hover:opacity-80 transition-opacity">
            Arbiter <span aria-hidden="true">⚖️</span>
          </span>
        </a>

        {children}
      </div>
    </div>
  )
}
