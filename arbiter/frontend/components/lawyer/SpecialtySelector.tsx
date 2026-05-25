'use client'

/**
 * SpecialtySelector — multi-select specialty picker for lawyer registration.
 * Max 5 selections.
 */

const SPECIALTIES = [
  { value: 'consumer',      label: 'Consumer Protection',  desc: 'Product fraud, e-commerce, warranties' },
  { value: 'employment',    label: 'Employment / Labour',  desc: 'Wages, termination, workplace rights' },
  { value: 'tenant',        label: 'Tenant / Landlord',    desc: 'Deposits, eviction, lease disputes' },
  { value: 'criminal',      label: 'Criminal Defence',     desc: 'FIR, bail, criminal proceedings' },
  { value: 'family',        label: 'Family Law',           desc: 'Divorce, custody, domestic violence' },
  { value: 'corporate',     label: 'Corporate / Business', desc: 'Contracts, company disputes, IP' },
  { value: 'immigration',   label: 'Immigration',          desc: 'Visa, citizenship, deportation' },
  { value: 'property',      label: 'Property / Real Estate', desc: 'Land, RERA, title disputes' },
  { value: 'civil',         label: 'General Civil',        desc: 'Civil litigation, recovery suits' },
  { value: 'cyber',         label: 'Cyber / IT Law',       desc: 'Online fraud, defamation, data breaches' },
  { value: 'rti',           label: 'RTI (India)',          desc: 'Right to Information applications' },
  { value: 'debt_recovery', label: 'Debt Recovery',        desc: 'Cheque bounce, loan recovery' },
]

interface SpecialtySelectorProps {
  selected: string[]
  onChange: (specialties: string[]) => void
  maxSelect?: number
}

export function SpecialtySelector({ selected, onChange, maxSelect = 5 }: SpecialtySelectorProps) {
  const toggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((s) => s !== value))
    } else if (selected.length < maxSelect) {
      onChange([...selected, value])
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-white/80">Legal Specialties</label>
        <span className="text-xs text-white/40">{selected.length}/{maxSelect} selected</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {SPECIALTIES.map((s) => {
          const isSelected = selected.includes(s.value)
          const isDisabled = !isSelected && selected.length >= maxSelect

          return (
            <button
              key={s.value}
              type="button"
              onClick={() => toggle(s.value)}
              disabled={isDisabled}
              className={`text-left p-3 rounded-lg border transition-all ${
                isSelected
                  ? 'bg-white text-black border-white'
                  : isDisabled
                  ? 'bg-white/2 border-white/5 text-white/20 cursor-not-allowed'
                  : 'bg-white/5 border-white/15 text-white hover:border-white/40 hover:bg-white/10'
              }`}
            >
              <div className="font-medium text-xs">{s.label}</div>
              <div className={`text-[10px] mt-0.5 ${isSelected ? 'text-black/60' : 'text-white/40'}`}>
                {s.desc}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
