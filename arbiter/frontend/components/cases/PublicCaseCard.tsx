/**
 * PublicCaseCard — showcases an interesting public legal case.
 */

const CATEGORY_LABELS: Record<string, string> = {
  consumer:    'Consumer Rights',
  employment:  'Employment',
  tenant:      'Tenant Rights',
  civil_rights:'Civil Rights',
  landmark:    '⚖️ Landmark Case',
  cyber:       'Cyber Law',
  corporate:   'Corporate',
}

const COUNTRY_FLAGS: Record<string, string> = {
  IN: '🇮🇳', US: '🇺🇸', GB: '🇬🇧', CA: '🇨🇦', AU: '🇦🇺'
}

interface PublicCase {
  id: string
  country_code: string
  country_name: string
  title: string
  parties: string
  court: string
  year: number
  category: string
  summary: string
  legal_lesson: string
  citizen_impact: string
  is_landmark: boolean
  source_hint: string
  view_count: number
}

interface PublicCaseCardProps {
  case_: PublicCase
  onClick?: (caseId: string) => void
}

export function PublicCaseCard({ case_, onClick }: PublicCaseCardProps) {
  return (
    <article
      className={`bg-white/5 border rounded-xl p-5 space-y-3 transition-all ${
        onClick ? 'cursor-pointer hover:border-white/30 hover:bg-white/8' : ''
      } ${case_.is_landmark ? 'border-white/25' : 'border-white/10'}`}
      onClick={() => onClick?.(case_.id)}
    >
      {/* Badges */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs text-white/40">
          {COUNTRY_FLAGS[case_.country_code] || '🌍'} {case_.country_name}
        </span>
        <span className="text-white/20">·</span>
        <span className="text-xs text-white/40">{CATEGORY_LABELS[case_.category] ?? case_.category}</span>
        <span className="text-white/20">·</span>
        <span className="text-xs text-white/40">{case_.year}</span>
        {case_.is_landmark && (
          <span className="ml-auto text-[10px] px-2 py-0.5 bg-white/10 text-white/80 rounded-full font-medium">
            Landmark
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="font-semibold text-white text-sm leading-snug">{case_.title}</h3>

      {/* Parties + Court */}
      {case_.parties && (
        <div className="text-xs text-white/40 italic">{case_.parties}</div>
      )}

      {/* Summary */}
      <p className="text-white/55 text-xs leading-relaxed line-clamp-3">{case_.summary}</p>

      {/* Legal Lesson */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-3 space-y-1">
        <div className="text-[10px] text-white/40 uppercase tracking-wider">Key Legal Lesson</div>
        <p className="text-white/75 text-xs leading-relaxed">{case_.legal_lesson}</p>
      </div>

      {/* Citizen impact */}
      {case_.citizen_impact && (
        <p className="text-white/40 text-[11px] leading-relaxed border-t border-white/8 pt-2">
          💡 {case_.citizen_impact}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-[10px] text-white/25">
        <span>{case_.court}</span>
        <span>{case_.view_count > 0 ? `${case_.view_count} views` : ''}</span>
      </div>
    </article>
  )
}
