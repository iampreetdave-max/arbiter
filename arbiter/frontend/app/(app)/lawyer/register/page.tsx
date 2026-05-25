'use client'

/**
 * Lawyer Registration — lawyers join the Arbiter network here.
 */
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { SpecialtySelector } from '@/components/lawyer/SpecialtySelector'
import { CountrySelector } from '@/components/onboarding/CountrySelector'

const STEPS = ['Profile', 'Specialties', 'Review']

export default function LawyerRegisterPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const [form, setForm] = useState({
    full_name: '',
    bar_registration_number: '',
    country_code: '',
    jurisdiction: '',
    specialties: [] as string[],
    years_of_experience: 0,
    available_for_pro_bono: false,
    bio: '',
    contact_email: user?.email ?? '',
    contact_phone: '',
    website_url: '',
    languages: ['en'],
  })

  const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)
    try {
      const { auth } = await import('@/lib/firebase')
      const token = auth.currentUser ? await auth.currentUser.getIdToken() : ''

      const res = await fetch(`${BASE}/api/lawyers/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...form, years_of_experience: Number(form.years_of_experience) }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Registration failed.')
      }

      setSuccess(true)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center space-y-4">
        <div className="text-5xl">✅</div>
        <h2 className="text-xl font-bold text-white">Registration Submitted</h2>
        <p className="text-white/50 text-sm">
          Your Bar registration number will be verified within 24–48 hours.
          Once verified, you'll start receiving matched cases.
        </p>
        <button
          onClick={() => router.push('/cases')}
          className="mt-4 px-6 py-2.5 bg-white text-black rounded-lg font-semibold text-sm"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Join as a Lawyer</h1>
        <p className="text-white/50 text-sm mt-1">
          Register to receive matched cases from users who need legal assistance.
        </p>
      </div>

      {/* Stepper */}
      <div className="flex items-center gap-2">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`flex items-center gap-1.5 text-xs font-medium ${
              i < step ? 'text-white' : i === step ? 'text-white' : 'text-white/30'
            }`}>
              <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                i < step ? 'bg-white text-black' : i === step ? 'border border-white text-white' : 'border border-white/20 text-white/30'
              }`}>
                {i < step ? '✓' : i + 1}
              </div>
              {s}
            </div>
            {i < STEPS.length - 1 && <div className="w-8 h-px bg-white/15" />}
          </div>
        ))}
      </div>

      {/* Step 0 — Profile */}
      {step === 0 && (
        <div className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm text-white/70">Full Legal Name *</label>
            <input
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              placeholder="As it appears on your Bar registration"
              className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-white text-sm placeholder:text-white/25 focus:outline-none focus:border-white/50"
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm text-white/70">Bar Registration Number *</label>
            <input
              value={form.bar_registration_number}
              onChange={(e) => setForm({ ...form, bar_registration_number: e.target.value })}
              placeholder="e.g. D/1234/2010 (India) or Bar No. 12345 (US)"
              className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-white text-sm placeholder:text-white/25 focus:outline-none focus:border-white/50"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-white/70">Country of Practice *</label>
            <CountrySelector
              selected={form.country_code}
              onChange={(code) => setForm({ ...form, country_code: code })}
              compact
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-white/70">State / Province / Jurisdiction *</label>
            <input
              value={form.jurisdiction}
              onChange={(e) => setForm({ ...form, jurisdiction: e.target.value })}
              placeholder="e.g. Delhi, California, Ontario"
              className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-white text-sm placeholder:text-white/25 focus:outline-none focus:border-white/50"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-sm text-white/70">Years of Experience *</label>
              <input
                type="number"
                min={0}
                max={70}
                value={form.years_of_experience}
                onChange={(e) => setForm({ ...form, years_of_experience: parseInt(e.target.value) || 0 })}
                className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-white/50"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm text-white/70">Contact Email *</label>
              <input
                type="email"
                value={form.contact_email}
                onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-white/50"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-sm text-white/70">Professional Bio * (min 50 characters)</label>
            <textarea
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
              rows={4}
              placeholder="Describe your practice areas, expertise, and approach to helping clients..."
              className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-white text-sm placeholder:text-white/25 focus:outline-none focus:border-white/50 resize-none"
            />
            <div className="text-right text-[10px] text-white/30">{form.bio.length}/1000</div>
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={form.available_for_pro_bono}
              onChange={(e) => setForm({ ...form, available_for_pro_bono: e.target.checked })}
              className="w-4 h-4 accent-white"
            />
            <span className="text-sm text-white/70">I'm available for pro bono cases</span>
          </label>

          <button
            onClick={() => setStep(1)}
            disabled={!form.full_name || !form.bar_registration_number || !form.country_code || !form.jurisdiction || form.bio.length < 50}
            className="w-full py-2.5 bg-white text-black rounded-lg font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
          >
            Next: Select Specialties →
          </button>
        </div>
      )}

      {/* Step 1 — Specialties */}
      {step === 1 && (
        <div className="space-y-4">
          <SpecialtySelector
            selected={form.specialties}
            onChange={(specialties) => setForm({ ...form, specialties })}
          />

          <div className="flex gap-3">
            <button
              onClick={() => setStep(0)}
              className="flex-1 py-2.5 border border-white/20 text-white/70 rounded-lg font-medium text-sm hover:border-white/40"
            >
              ← Back
            </button>
            <button
              onClick={() => setStep(2)}
              disabled={form.specialties.length === 0}
              className="flex-1 py-2.5 bg-white text-black rounded-lg font-semibold text-sm disabled:opacity-40"
            >
              Review →
            </button>
          </div>
        </div>
      )}

      {/* Step 2 — Review */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-white/50">Name</span>
              <span className="text-white font-medium">{form.full_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Bar No.</span>
              <span className="text-white">{form.bar_registration_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Jurisdiction</span>
              <span className="text-white">{form.jurisdiction}, {form.country_code}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Experience</span>
              <span className="text-white">{form.years_of_experience} years</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-white/50">Specialties</span>
              <span className="text-white text-right">{form.specialties.join(', ')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Pro Bono</span>
              <span className="text-white">{form.available_for_pro_bono ? 'Yes' : 'No'}</span>
            </div>
          </div>

          <p className="text-white/40 text-xs">
            By submitting, you confirm that all information is accurate and that you are a licensed legal practitioner. Your Bar registration number will be verified before your profile goes live.
          </p>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="flex gap-3">
            <button onClick={() => setStep(1)} className="flex-1 py-2.5 border border-white/20 text-white/70 rounded-lg font-medium text-sm">
              ← Back
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="flex-1 py-2.5 bg-white text-black rounded-lg font-semibold text-sm disabled:opacity-50"
            >
              {loading ? 'Submitting…' : 'Submit Registration'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
