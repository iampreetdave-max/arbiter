'use client'

/**
 * Client-side providers wrapper.
 * Keep the root layout (layout.tsx) as a Server Component by isolating
 * all client context providers here.
 */
import { AuthProvider } from '@/contexts/AuthContext'

export function Providers({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}
