'use client'

/**
 * LawyerCard — displays a lawyer's public profile in a card format.
 */

const SPECIALTY_LABELS: Record<string, string> = {
  consumer: 'Consumer',
  employment: 'Employment',
  tenant: 'Tenant / Property',
  criminal: 'Criminal',
  family: 'Family',
  corporate: 'Corporate',
  immigration: 'Immigration',
  property: 'Property',
  civil: 'Civil',
  cyber: 'Cyber / IT',
  rti: 'RTI',
  debt_recovery: 'Debt Recovery',
  other: 'Other',
}

interface Lawyer {
  id: string
  full_name: string
  country_code: string
  jurisdiction: string
  specialties: string[]
  years_of_experience: number
  available_for_pro_bono: boolean
  bio: string
  rating: number
  rating_count: number
  cases_resolved: number
  languages: string[]
}

interface LawyerCardProps {
  lawyer: Lawyer
  onContact?: (lawyerId: string) => void
  showContactButton?: boolean
}

const COUNTRY_FLAGS: Record<string, string> = {
  IN: '🇮🇳', US: '🇺🇸', GB: '🇬🇧', CA: '🇨🇦', AU: '🇦🇺'
}

export function LawyerCard({ lawyer, onContact, showContactButton = true }: LawyerCardProps) {
  const initials = lawyer.full_name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-4 hover:border-white/25 transition-all">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="w-11 h-11 rounded-full bg-white/10 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-white text-sm">{lawyer.full_name}</h3>
            {lawyer.available_for_pro_bono && (
              <span className="text-[10px] px-1.5 py-0.5 bg-white/10 text-white/60 rounded font-medium">
                Pro Bono
              </span>
            )}
          </div>
          <div className="text-white/50 text-xs mt-0.5">
            {COUNTRY_FLAGS[lawyer.country_code] || '🌍'} {lawyer.jurisdiction}
            {' · '}{lawyer.years_of_experience}y exp
          </div>
        </div>

        {/* Rating */}
        {lawyer.rating_count > 0 && (
          <div className="text-right flex-shrink-0">
            <div className="text-white font-semibold text-sm">★ {lawyer.rating.toFixed(1)}</div>
            <div className="text-white/40 text-[10px]">{lawyer.rating_count} reviews</div>
          </div>
        )}
      </div>

      {/* Specialties */}
      <div className="flex flex-wrap gap-1.5">
        {lawyer.specialties.slice(0, 4).map((s) => (
          <span
            key={s}
            className="text-[10px] px-2 py-0.5 border border-white/20 text-white/60 rounded-full"
          >
            {SPECIALTY_LABELS[s] ?? s}
          </span>
        ))}
      </div>

      {/* Bio */}
      <p className="text-white/50 text-xs leading-relaxed line-clamp-2">{lawyer.bio}</p>

      {/* Footer */}
      <div className="flex items-center justify-between pt-1 border-t border-white/10">
        <div className="text-white/40 text-xs">
          {lawyer.cases_resolved > 0 ? `${lawyer.cases_resolved} cases resolved` : 'New to platform'}
        </div>
        {showContactButton && onContact && (
          <button
            onClick={() => onContact(lawyer.id)}
            className="text-xs px-3 py-1.5 bg-white text-black rounded-lg font-semibold hover:opacity-90 transition-opacity"
          >
            Request Consultation
          </button>
        )}
      </div>
    </div>
  )
}
