/**
 * LegalUpdateCard — displays a single legal update in the feed.
 */

const CATEGORY_STYLES: Record<string, { label: string; dot: string }> = {
  legislation: { label: 'New Legislation', dot: 'bg-white' },
  judgment:    { label: 'Court Judgment',  dot: 'bg-white/60' },
  regulation:  { label: 'Regulation',      dot: 'bg-white/40' },
  advisory:    { label: 'Advisory',        dot: 'bg-white/20' },
}

const COUNTRY_FLAGS: Record<string, string> = {
  IN: '🇮🇳', US: '🇺🇸', GB: '🇬🇧', CA: '🇨🇦', AU: '🇦🇺'
}

interface LegalUpdate {
  id: string
  country_code: string
  country_name: string
  category: string
  title: string
  summary: string
  impact: string
  effective_date: string
  source_hint: string
  fetched_at: string
}

interface LegalUpdateCardProps {
  update: LegalUpdate
}

export function LegalUpdateCard({ update }: LegalUpdateCardProps) {
  const style = CATEGORY_STYLES[update.category] ?? { label: update.category, dot: 'bg-white/20' }
  const date = new Date(update.fetched_at).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric'
  })

  return (
    <article className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-3 hover:border-white/20 transition-all">
      {/* Meta */}
      <div className="flex items-center gap-2 text-xs text-white/40">
        <span>{COUNTRY_FLAGS[update.country_code] || '🌍'} {update.country_name}</span>
        <span>·</span>
        <span className="flex items-center gap-1">
          <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
          {style.label}
        </span>
        <span>·</span>
        <span>{date}</span>
      </div>

      {/* Title */}
      <h3 className="font-semibold text-white text-sm leading-snug">{update.title}</h3>

      {/* Summary */}
      <p className="text-white/55 text-xs leading-relaxed">{update.summary}</p>

      {/* Impact */}
      {update.impact && (
        <div className="bg-white/5 border border-white/10 rounded-lg p-3">
          <div className="text-[10px] text-white/40 uppercase tracking-wider mb-1">What This Means For You</div>
          <p className="text-white/70 text-xs leading-relaxed">{update.impact}</p>
        </div>
      )}

      {/* Footer */}
      {(update.source_hint || update.effective_date) && (
        <div className="flex items-center justify-between pt-2 border-t border-white/10 text-[10px] text-white/30">
          {update.source_hint && <span>Source: {update.source_hint}</span>}
          {update.effective_date && <span>Effective: {update.effective_date}</span>}
        </div>
      )}
    </article>
  )
}
