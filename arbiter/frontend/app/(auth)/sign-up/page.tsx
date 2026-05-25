'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'

export default function SignUpPage() {
  const { signUp, signInWithGoogle, sendVerification } = useAuth()
  const router = useRouter()

  const [name, setName]         = useState('')
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [googleLoad, setGoogleLoad] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (password !== confirm) { setError('Passwords do not match.'); return }
    if (password.length < 8) { setError('Password must be at least 8 characters.'); return }
    setLoading(true)
    try {
      await signUp(email, password)
      try {
        if (name.trim()) {
          const { updateProfile } = await import('firebase/auth')
          const { auth } = await import('@/lib/firebase')
          if (auth.currentUser) await updateProfile(auth.currentUser, { displayName: name.trim() })
        }
        await sendVerification()
      } catch { /* non-blocking */ }
      router.push('/cases')
    } catch (err: unknown) {
      setError(friendlyError(err))
    } finally {
      setLoading(false)
    }
  }

  const handleGoogle = async () => {
    setError('')
    setGoogleLoad(true)
    try { await signInWithGoogle(); router.push('/cases') }
    catch (err: unknown) { setError(friendlyError(err)) }
    finally { setGoogleLoad(false) }
  }

  return (
    <div className="rounded-2xl border border-[#1a1a1a] bg-[#050505] p-8">
      <h1 className="text-xl font-bold text-white mb-1">Create account</h1>
      <p className="text-[#555] text-sm mb-6">First document free. No credit card required.</p>

      <button type="button" onClick={handleGoogle} disabled={googleLoad || loading}
        className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg border border-[#222] text-white text-sm font-medium hover:border-[#444] hover:bg-white/5 transition-all disabled:opacity-50 disabled:cursor-not-allowed mb-6">
        {googleLoad ? <Spinner size="sm" /> : (
          <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24" aria-hidden="true">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
        )}
        Continue with Google
      </button>

      <div className="relative mb-6">
        <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-[#111]" /></div>
        <div className="relative flex justify-center text-xs"><span className="px-3 bg-[#050505] text-[#444]">or email</span></div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input label="Full name" type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" autoComplete="name" />
        <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required />
        <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min. 8 characters" autoComplete="new-password" hint="At least 8 characters" required />
        <Input label="Confirm password" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="••••••••" autoComplete="new-password" required />
        {error && <p className="text-sm text-red-400 bg-red-900/10 border border-red-900/20 rounded-lg px-3 py-2" role="alert">{error}</p>}
        <button type="submit" disabled={loading || googleLoad}
          className="w-full btn-shiny text-black py-3 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
          {loading ? <Spinner size="sm" label="Creating account…" /> : 'Create account'}
        </button>
      </form>

      <p className="text-center text-[#444] text-xs mt-4">
        Already have an account?{' '}
        <Link href="/sign-in" className="text-white hover:text-[#aaa] transition-colors underline underline-offset-2">Sign in</Link>
      </p>
    </div>
  )
}

function friendlyError(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message
    if (msg.includes('email-already-in-use')) return 'An account with this email already exists.'
    if (msg.includes('invalid-email')) return 'Please enter a valid email address.'
    if (msg.includes('weak-password')) return 'Password is too weak. Use at least 8 characters.'
    if (msg.includes('network')) return 'Network error. Check your internet connection.'
  }
  return 'Sign up failed. Please try again.'
}
