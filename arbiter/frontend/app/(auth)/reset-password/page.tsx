'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { verifyPasswordResetCode, confirmPasswordReset } from 'firebase/auth'
import { auth } from '@/lib/firebase'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'

// Inner component that reads search params (must be wrapped in Suspense)
function ResetPasswordForm() {
  const searchParams = useSearchParams()
  const oobCode = searchParams.get('oobCode') ?? ''

  const [password, setPassword]   = useState('')
  const [confirm, setConfirm]     = useState('')
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState('')
  const [done, setDone]           = useState(false)
  const [verifying, setVerifying] = useState(true)
  const [codeValid, setCodeValid] = useState(false)

  // Verify the oobCode on mount
  useEffect(() => {
    if (!oobCode) {
      setError('Invalid reset link. Please request a new one.')
      setVerifying(false)
      return
    }

    verifyPasswordResetCode(auth, oobCode)
      .then(() => {
        setCodeValid(true)
      })
      .catch(() => {
        setError('This reset link has expired or already been used. Request a new one.')
      })
      .finally(() => {
        setVerifying(false)
      })
  }, [oobCode])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await confirmPasswordReset(auth, oobCode, password)
      setDone(true)
    } catch (err: unknown) {
      setError(friendlyError(err))
    } finally {
      setLoading(false)
    }
  }

  // ── Loading state while verifying code ───────────────────────────────────────
  if (verifying) {
    return (
      <div className="rounded-2xl border border-[#1a1a1a] bg-[#050505] p-8 flex flex-col items-center gap-4">
        <Spinner size="sm" />
        <p className="text-[#555] text-sm">Verifying reset link…</p>
      </div>
    )
  }

  // ── Invalid / expired code ────────────────────────────────────────────────────
  if (!codeValid) {
    return (
      <div className="rounded-2xl border border-[#1a1a1a] bg-[#050505] p-8">
        <div className="flex justify-center mb-6">
          <div className="w-14 h-14 rounded-full border border-red-900/40 flex items-center justify-center">
            <svg
              className="w-7 h-7 text-red-400"
              fill="none"
              stroke="currentColor"
              strokeWidth={2.5}
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        </div>
        <h1 className="text-xl font-bold text-white mb-2 text-center">Link expired</h1>
        <p className="text-[#555] text-sm text-center mb-8">{error}</p>
        <Link
          href="/forgot-password"
          className="w-full btn-shiny text-black py-3 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity active:scale-[0.98] flex items-center justify-center"
        >
          Request new link
        </Link>
      </div>
    )
  }

  // ── Success state ─────────────────────────────────────────────────────────────
  if (done) {
    return (
      <div className="rounded-2xl border border-[#1a1a1a] bg-[#050505] p-8">
        <div className="flex justify-center mb-6">
          <div className="w-14 h-14 rounded-full border border-[#333] flex items-center justify-center">
            <svg
              className="w-7 h-7 text-white"
              fill="none"
              stroke="currentColor"
              strokeWidth={2.5}
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
        </div>
        <h1 className="text-xl font-bold text-white mb-2 text-center">Password updated!</h1>
        <p className="text-[#555] text-sm text-center mb-8">
          Your password has been changed. Sign in with your new password.
        </p>
        <Link
          href="/sign-in"
          className="w-full btn-shiny text-black py-3 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity active:scale-[0.98] flex items-center justify-center"
        >
          Sign in
        </Link>
      </div>
    )
  }

  // ── Reset password form ───────────────────────────────────────────────────────
  return (
    <div className="rounded-2xl border border-[#1a1a1a] bg-[#050505] p-8">
      <h1 className="text-xl font-bold text-white mb-1">Set new password</h1>
      <p className="text-[#555] text-sm mb-6">Choose a strong password of at least 8 characters.</p>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input
          label="New password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          autoComplete="new-password"
          minLength={8}
          required
        />
        <Input
          label="Confirm password"
          type="password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="••••••••"
          autoComplete="new-password"
          required
        />

        {error && (
          <p
            className="text-sm text-red-400 bg-red-900/10 border border-red-900/20 rounded-lg px-3 py-2"
            role="alert"
          >
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full btn-shiny text-black py-3 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? <Spinner size="sm" label="Updating…" /> : 'Update password'}
        </button>
      </form>

      <p className="text-center text-[#444] text-xs mt-6">
        <Link
          href="/sign-in"
          className="text-white hover:text-[#aaa] transition-colors underline underline-offset-2"
        >
          Back to sign in
        </Link>
      </p>
    </div>
  )
}

// Outer page wraps in Suspense (required for useSearchParams in Next.js 14)
export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="rounded-2xl border border-[#1a1a1a] bg-[#050505] p-8 flex flex-col items-center gap-4">
          <Spinner size="sm" />
          <p className="text-[#555] text-sm">Loading…</p>
        </div>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  )
}

function friendlyError(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message
    if (msg.includes('expired-action-code') || msg.includes('invalid-action-code'))
      return 'This reset link has expired or already been used. Request a new one.'
    if (msg.includes('weak-password'))
      return 'Password is too weak. Use at least 8 characters.'
    if (msg.includes('network'))
      return 'Network error. Check your internet connection.'
  }
  return 'Failed to update password. Please try again.'
}
