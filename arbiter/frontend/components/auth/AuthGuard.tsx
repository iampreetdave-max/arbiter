'use client'

/**
 * AuthGuard — wraps protected app pages.
 * Redirects to /sign-in if no authenticated user.
 * Shows a full-screen spinner while auth state is resolving.
 */
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Spinner } from '@/components/ui/Spinner'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/sign-in')
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Spinner size="lg" label="Checking authentication…" />
      </div>
    )
  }

  if (!user) {
    // Will redirect via the useEffect above; render nothing in the meantime
    return null
  }

  return <>{children}</>
}
