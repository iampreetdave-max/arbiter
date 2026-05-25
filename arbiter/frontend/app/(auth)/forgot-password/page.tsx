'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'

export default function ForgotPasswordPage() {
  const { resetPassword } = useAuth()
  const [email, setEmail]     = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [sent, setSent]       = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await resetPassword(email)
      setSent(true)
    } catch (err: unknown) {
      setError(friendlyError(err))
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <div className="rounded-2xl border border-[#1a1a1a] bg-[#050505] p-8">
        <div className="flex justify-center mb-6">
          <div className="w-14 h-14 rounded-full border border-[#333] flex items-center justify-center">
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
        </div>
        <h1 className="text-xl font-bold text-white mb-2 text-center">Check your email</h1>
        <p className="text-[#555] text-sm text-center mb-8">
          We sent a reset link to <span className="text-[#888]">{email}</span>. It expires in 1 hour.
        </p>
        <div className="flex flex-col gap-3 mb-6">
          <a href="https://mail.google.com" target="_blank" rel="noopener noreferrer"
            className="w-full btn-shiny text-black py-3 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity active:scale-[0.98] flex items-center justify-center gap-2">
            Open Gmail
          </a>
          <a href="https://outlook.com" target="_blank" rel="noopener noreferrer"
            className="w-full px-4 py-3 rounded-lg border border-[#222] text-white text-sm font-medium hover:border-[#444] hover:bg-white/5 transition-all flex items-center justify-center gap-2">
            Open Outlook
          </a>
        </div>
        <div className="text-center space-y-3">
          <button type="button" onClick={() => setSent(false)} className="text-xs text-[#555] hover:text-white transition-colors">
            Didn&apos;t get it? Try again
          </button>
          <p className="text-[#444] text-xs">
            <Link href="/sign-in" className="text-white hover:text-[#aaa] transition-colors underline underline-offset-2">Back to sign in</Link>
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-[#1a1a1a] bg-[#050505] p-8">
      <h1 className="text-xl font-bold text-white mb-1">Forgot password?</h1>
      <p className="text-[#555] text-sm mb-6">Enter your email and we&apos;ll send a reset link.</p>
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required />
        {error && <p className="text-sm text-red-400 bg-red-900/10 border border-red-900/20 rounded-lg px-3 py-2" role="alert">{error}</p>}
        <button type="submit" disabled={loading}
          className="w-full btn-shiny text-black py-3 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
          {loading ? <Spinner size="sm" label="Sending…" /> : 'Send reset link'}
        </button>
      </form>
      <p className="text-center text-[#444] text-xs mt-6">
        Remember it?{' '}
        <Link href="/sign-in" className="text-white hover:text-[#aaa] transition-colors underline underline-offset-2">Sign in</Link>
      </p>
    </div>
  )
}

function friendlyError(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message
    if (msg.includes('user-not-found') || msg.includes('invalid-email')) return 'No account found with that email address.'
    if (msg.includes('too-many-requests')) return 'Too many attempts. Please wait and try again.'
    if (msg.includes('network')) return 'Network error. Check your internet connection.'
  }
  return 'Failed to send reset email. Please try again.'
}
