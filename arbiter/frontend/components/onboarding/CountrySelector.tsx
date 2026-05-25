'use client'

/**
 * CountrySelector — lets users pick their country for jurisdiction-aware AI.
 * Shows 5 supported countries as visual cards. Optional (can skip).
 */

interface Country {
  code: string
  name: string
  flag: string
}

const COUNTRIES: Country[] = [
  { code: 'IN', name: 'India', flag: '🇮🇳' },
  { code: 'US', name: 'United States', flag: '🇺🇸' },
  { code: 'GB', name: 'United Kingdom', flag: '🇬🇧' },
  { code: 'CA', name: 'Canada', flag: '🇨🇦' },
  { code: 'AU', name: 'Australia', flag: '🇦🇺' },
]

interface CountrySelectorProps {
  selected: string | null
  onChange: (code: string) => void
  onSkip?: () => void
  compact?: boolean
}

export function CountrySelector({ selected, onChange, onSkip, compact = false }: CountrySelectorProps) {
  if (compact) {
    return (
      <div className="flex flex-wrap gap-2">
        {COUNTRIES.map((c) => (
          <button
            key={c.code}
            onClick={() => onChange(c.code)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
              selected === c.code
                ? 'bg-white text-black border-white'
                : 'bg-transparent text-white/60 border-white/20 hover:border-white/50 hover:text-white'
            }`}
          >
            <span>{c.flag}</span>
            <span>{c.name}</span>
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="text-center space-y-1">
        <h2 className="text-xl font-semibold text-white">Where are you located?</h2>
        <p className="text-white/50 text-sm">
          This helps Arbiter apply the right laws to your case.{' '}
          {onSkip && (
            <button onClick={onSkip} className="text-white/40 underline hover:text-white/70 transition-colors">
              Skip for now
            </button>
          )}
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {COUNTRIES.map((c) => (
          <button
            key={c.code}
            onClick={() => onChange(c.code)}
            className={`group relative p-4 rounded-xl border transition-all text-left ${
              selected === c.code
                ? 'bg-white text-black border-white'
                : 'bg-white/5 text-white border-white/10 hover:border-white/40 hover:bg-white/10'
            }`}
          >
            <div className="text-3xl mb-2">{c.flag}</div>
            <div className="font-medium text-sm">{c.name}</div>
            {selected === c.code && (
              <div className="absolute top-2 right-2 w-2 h-2 bg-black rounded-full" />
            )}
          </button>
        ))}
      </div>

      {selected && (
        <p className="text-center text-white/50 text-xs">
          ✓ Laws and documents will be tailored for <strong className="text-white">{COUNTRIES.find(c => c.code === selected)?.name}</strong>
        </p>
      )}
    </div>
  )
}
