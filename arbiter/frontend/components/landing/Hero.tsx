import Link from 'next/link'
import { TypewriterText } from '@/components/ui/TypewriterText'
import { STATS } from '@/lib/constants'

/**
 * Landing page hero section.
 * Mobile-first: centered content on mobile, left-aligned on desktop.
 * Full-viewport height with dot pattern background.
 */
export function Hero() {
  return (
    <section
      className="relative min-h-screen flex flex-col justify-center dot-pattern overflow-hidden"
      aria-label="Hero"
    >
      {/* Radial gradient fade at bottom */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 80% 50% at 50% -20%, rgba(255,255,255,0.04) 0%, transparent 60%), linear-gradient(to bottom, transparent 60%, #000 100%)',
        }}
        aria-hidden="true"
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-28 pb-20">
        {/* Category badge */}
        <div className="flex justify-center sm:justify-start mb-8">
          <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#222] bg-[#0a0a0a] text-[#888] text-xs font-medium tracking-wide">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" aria-hidden="true" />
            XPRIZE Build with Gemini 2026 — Professional Services
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.5rem] font-bold tracking-[-0.03em] text-white mb-6 text-center sm:text-left leading-[1.04]">
          Legal help.
          <br />
          <span className="text-[#3a3a3a]">No lawyer fees.</span>
        </h1>

        {/* Typewriter subtitle */}
        <div className="flex justify-center sm:justify-start mb-4">
          <p className="text-xl sm:text-2xl md:text-3xl text-[#666] text-center sm:text-left">
            AI documents for{' '}
            <TypewriterText className="text-white font-semibold" />
          </p>
        </div>

        {/* Description */}
        <p className="text-base sm:text-lg text-[#555] max-w-lg mb-10 text-center sm:text-left mx-auto sm:mx-0 leading-relaxed">
          Describe your problem. Arbiter researches applicable Indian laws and
          drafts a professional document — demand letter, RTI application, or
          consumer complaint — in minutes, not months.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center sm:justify-start mb-16">
          <Link
            href="/cases/new"
            className="inline-flex items-center justify-center gap-2 px-7 py-3.5 btn-shiny text-black rounded-lg font-semibold text-base hover:opacity-90 transition-opacity active:scale-[0.98]"
          >
            Start Your Case Free
            <span aria-hidden="true">→</span>
          </Link>
          <a
            href="#how-it-works"
            className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-lg border border-[#2a2a2a] text-white text-base font-medium hover:border-[#555] hover:bg-white/5 transition-all active:scale-[0.98]"
          >
            See how it works
          </a>
        </div>

        {/* Stats bar */}
        <div className="border-t border-[#111] pt-8 grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8">
          {STATS.map((stat) => (
            <div key={stat.label} className="text-center sm:text-left">
              <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight mb-1">
                {stat.value}
              </div>
              <div className="text-xs sm:text-sm text-[#555] leading-snug">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
