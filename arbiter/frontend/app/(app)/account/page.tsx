'use client'

/**
 * Account Settings page — /account
 * Protected by AuthGuard via the (app) layout group.
 * Allows users to update display name, verify email, and change password.
 */
import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'

// ── Helpers ───────────────────────────────────────────────────────────────────

function friendlyError(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message
    if (msg.includes('wrong-password') || msg.includes('invalid-credential'))
      return 'Current password is incorrect.'
    if (msg.includes('weak-password'))
      return 'New password is too weak. Use at least 8 characters.'
    if (msg.includes('requires-recent-login'))
      return 'Please sign out and sign back in before changing your password.'
    if (msg.includes('too-many-requests'))
      return 'Too many attempts. Please wait a few minutes and try again.'
    if (msg.includes('network'))
      return 'Network error. Check your internet connection.'
  }
  return 'Something went wrong. Please try again.'
}

// ── Profile Section ───────────────────────────────────────────────────────────

function ProfileSection() {
  const { user, updateDisplayName, sendVerification } = useAuth()

  const [displayName, setDisplayName] = useState(user?.displayName ?? '')
  const [nameLoading, setNameLoading] = useState(false)
  const [nameSuccess, setNameSuccess] = useState(false)
  const [nameError, setNameError]     = useState('')

  const [verifyLoading, setVerifyLoading]   = useState(false)
  const [verifySent, setVerifySent]         = useState(false)
  const [verifyError, setVerifyError]       = useState('')

  const handleSaveName = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!displayName.trim()) return
    setNameError('')
    setNameSuccess(false)
    setNameLoading(true)
    try {
      await updateDisplayName(displayName.trim())
      setNameSuccess(true)
      setTimeout(() => setNameSuccess(false), 3000)
    } catch (err) {
      setNameError(friendlyError(err))
    } finally {
      setNameLoading(false)
    }
  }

  const handleSendVerification = async () => {
    setVerifyError('')
    setVerifyLoading(true)
    try {
      await sendVerification()
      setVerifySent(true)
    } catch (err) {
      setVerifyError(friendlyError(err))
    } finally {
      setVerifyLoading(false)
    }
  }

  return (
    <section aria-labelledby="profile-heading">
      <h2
        id="profile-heading"
        className="text-sm font-semibold text-[#888] uppercase tracking-widest mb-4"
      >
        Profile
      </h2>

      <div className="bg-[#050505] border border-[#1a1a1a] rounded-2xl p-6 mb-6 space-y-6">
        {/* Email row */}
        <div>
          <p className="text-xs text-[#555] mb-1 font-medium">Email address</p>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-white">{user?.email ?? '—'}</span>
            {user?.emailVerified ? (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-green-400 bg-green-400/10 border border-green-400/20 rounded-full px-2.5 py-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
                Verified
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-yellow-400 bg-yellow-400/10 border border-yellow-400/20 rounded-full px-2.5 py-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 inline-block" />
                Not verified
              </span>
            )}
          </div>

          {!user?.emailVerified && (
            <div className="mt-3">
              {verifySent ? (
                <p className="text-sm text-green-400">
                  Verification email sent! Check your inbox.
                </p>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={handleSendVerification}
                    disabled={verifyLoading}
                    className="border border-[#222] text-white rounded-lg text-sm py-2 px-4 hover:border-[#444] hover:bg-white/5 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {verifyLoading ? <Spinner size="sm" /> : null}
                    Send verification email
                  </button>
                  {verifyError && (
                    <p className="mt-2 text-xs text-red-400">{verifyError}</p>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        {/* Display name row */}
        <form onSubmit={handleSaveName} className="space-y-3">
          <Input
            label="Display name"
            type="text"
            value={displayName}
            onChange={(e) => {
              setDisplayName(e.target.value)
              setNameSuccess(false)
              setNameError('')
            }}
            placeholder="Your name"
            autoComplete="name"
          />

          {nameError && (
            <p className="text-xs text-red-400 bg-red-900/10 border border-red-900/20 rounded-lg px-3 py-2" role="alert">
              {nameError}
            </p>
          )}

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={nameLoading || !displayName.trim()}
              className="btn-shiny text-black rounded-lg text-sm font-semibold py-2.5 px-5 hover:opacity-90 transition-opacity active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {nameLoading ? <Spinner size="sm" /> : null}
              Save name
            </button>
            {nameSuccess && (
              <span className="text-sm text-green-400 transition-opacity">
                Name updated ✓
              </span>
            )}
          </div>
        </form>
      </div>
    </section>
  )
}

// ── Change Password Section ───────────────────────────────────────────────────

function ChangePasswordSection() {
  const { updateUserPassword } = useAuth()

  const [current, setCurrent]     = useState('')
  const [next, setNext]           = useState('')
  const [confirm, setConfirm]     = useState('')
  const [loading, setLoading]     = useState(false)
  const [success, setSuccess]     = useState(false)
  const [error, setError]         = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    if (next.length < 8) {
      setError('New password must be at least 8 characters.')
      return
    }
    if (next !== confirm) {
      setError('New passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await updateUserPassword(current, next)
      setSuccess(true)
      setCurrent('')
      setNext('')
      setConfirm('')
      setTimeout(() => setSuccess(false), 4000)
    } catch (err) {
      setError(friendlyError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section aria-labelledby="password-heading">
      <h2
        id="password-heading"
        className="text-sm font-semibold text-[#888] uppercase tracking-widest mb-4"
      >
        Change Password
      </h2>

      <div className="bg-[#050505] border border-[#1a1a1a] rounded-2xl p-6 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <Input
            label="Current password"
            type="password"
            value={current}
            onChange={(e) => { setCurrent(e.target.value); setError(''); setSuccess(false) }}
            placeholder="••••••••"
            autoComplete="current-password"
            required
          />
          <Input
            label="New password"
            type="password"
            value={next}
            onChange={(e) => { setNext(e.target.value); setError(''); setSuccess(false) }}
            placeholder="Min. 8 characters"
            autoComplete="new-password"
            hint="At least 8 characters"
            required
          />
          <Input
            label="Confirm new password"
            type="password"
            value={confirm}
            onChange={(e) => { setConfirm(e.target.value); setError(''); setSuccess(false) }}
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

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={loading || !current || !next || !confirm}
              className="btn-shiny text-black rounded-lg text-sm font-semibold py-2.5 px-5 hover:opacity-90 transition-opacity active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? <Spinner size="sm" /> : null}
              Update password
            </button>
            {success && (
              <span className="text-sm text-green-400">
                Password updated ✓
              </span>
            )}
          </div>
        </form>
      </div>
    </section>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AccountPage() {
  const { user } = useAuth()

  const hasEmailProvider = user?.providerData.some(
    (p) => p.providerId === 'password'
  ) ?? false

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Back link */}
      <Link
        href="/cases"
        className="inline-flex items-center gap-1.5 text-xs text-[#555] hover:text-white transition-colors mb-8 group"
      >
        <svg
          className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back to cases
      </Link>

      {/* Page heading */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Account settings</h1>
        <p className="text-sm text-[#555] mt-1">
          Manage your profile and security preferences.
        </p>
      </div>

      {/* Profile section */}
      <ProfileSection />

      {/* Password section — only for email/password accounts */}
      {hasEmailProvider && <ChangePasswordSection />}

      {/* Footer note */}
      <p className="text-xs text-[#333] mt-2">
        This is an AI-generated document service. Arbiter is not a law firm and
        does not provide legal advice.
      </p>
    </div>
  )
}
