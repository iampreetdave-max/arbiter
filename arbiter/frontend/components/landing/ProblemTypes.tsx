import { PROBLEM_TYPES } from '@/lib/constants'

/**
 * Problem types grid — 6 categories of legal problems Arbiter handles.
 * 3 columns on desktop → 2 on tablet → 1 on mobile.
 */
export function ProblemTypes() {
  return (
    <section
      id="problem-types"
      className="py-24 sm:py-32 bg-black"
      aria-labelledby="problem-types-heading"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12 sm:mb-16">
          <p className="text-[#555] text-xs font-medium uppercase tracking-[0.2em] mb-4">
            What we handle
          </p>
          <h2
            id="problem-types-heading"
            className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-white"
          >
            Six categories of
            <br />
            <span className="text-[#333]">legal problems</span>
          </h2>
          <p className="mt-4 text-[#555] max-w-xl mx-auto text-sm sm:text-base">
            Arbiter handles the most common disputes faced by everyday Indians
            — without requiring any legal knowledge from you.
          </p>
        </div>

        {/* Problem type cards grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          {PROBLEM_TYPES.map((type) => (
            <div
              key={type.id}
              className="group relative p-5 sm:p-6 rounded-xl border border-[#111] bg-[#050505] hover:border-[#2a2a2a] hover:bg-[#0a0a0a] transition-all duration-300 cursor-default"
            >
              {/* Optional tag badge */}
              {type.tag && (
                <span className="absolute top-4 right-4 px-2 py-0.5 rounded text-[10px] font-medium border border-[#222] text-[#666] uppercase tracking-wider">
                  {type.tag}
                </span>
              )}

              {/* Icon */}
              <div className="text-2xl sm:text-3xl mb-4 leading-none" aria-hidden="true">
                {type.icon}
              </div>

              {/* Title */}
              <h3 className="text-base sm:text-lg font-semibold text-white mb-2">
                {type.label}
              </h3>

              {/* Description */}
              <p className="text-sm text-[#555] mb-4 leading-relaxed">
                {type.description}
              </p>

              {/* Document type chips */}
              <div className="flex flex-wrap gap-1.5">
                {type.documents.map((doc) => (
                  <span
                    key={doc}
                    className="inline-block text-[11px] px-2 py-0.5 rounded border border-[#1a1a1a] text-[#444] font-mono tracking-tight"
                  >
                    {doc}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
