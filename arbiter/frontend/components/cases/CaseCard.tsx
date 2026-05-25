import Link from 'next/link'
import { Badge, statusVariant, statusLabel } from '@/components/ui/Badge'
import type { ArbiterCase } from '@/lib/api'

const PROBLEM_ICONS: Record<string, string> = {
  tenant_dispute:  '🏠',
  employment:      '💼',
  consumer:        '🛒',
  rti:             '📋',
  harassment:      '🛡️',
  debt_recovery:   '💰',
}

interface CaseCardProps {
  caseData: ArbiterCase
}

/**
 * Dashboard card showing a single case summary.
 * Links to the case detail page.
 */
export function CaseCard({ caseData }: CaseCardProps) {
  const icon = PROBLEM_ICONS[caseData.problem_type] ?? '⚖️'
  const date = new Date(caseData.created_at).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })

  return (
    <Link
      href={`/cases/${caseData.id}`}
      className="group flex flex-col gap-3 p-5 rounded-xl border border-[#111] bg-[#050505] hover:border-[#2a2a2a] hover:bg-[#0a0a0a] transition-all duration-200"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-2xl flex-shrink-0" aria-hidden="true">{icon}</span>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-white truncate">
              {caseData.title}
            </h3>
            <p className="text-xs text-[#444] mt-0.5">{date}</p>
          </div>
        </div>
        <Badge variant={statusVariant(caseData.status)}>
          {statusLabel(caseData.status)}
        </Badge>
      </div>

      <p className="text-xs text-[#555] line-clamp-2 leading-relaxed">
        {caseData.description}
      </p>

      <div className="flex items-center justify-between text-xs text-[#333]">
        <span className="capitalize">{caseData.problem_type.replace(/_/g, ' ')}</span>
        <span className="group-hover:text-white transition-colors">
          View →
        </span>
      </div>
    </Link>
  )
}
