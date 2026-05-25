import { HOW_IT_WORKS_STEPS } from '@/lib/constants'

/**
 * "How It Works" section — three numbered steps with connecting line on desktop.
 */
export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="py-24 sm:py-32 bg-[#050505]"
      aria-labelledby="how-it-works-heading"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center mb-16 sm:mb-20">
          <p className="text-[#555] text-xs font-medium uppercase tracking-[0.2em] mb-4">
            The process
          </p>
          <h2
            id="how-it-works-heading"
            className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-white"
          >
            From problem to document
            <br />
            <span className="text-[#333]">in three steps</span>
          </h2>
          <p className="mt-4 text-[#555] max-w-lg mx-auto text-base sm:text-lg">
            No legal knowledge required. Arbiter guides you through the
            entire process in plain language.
          </p>
        </div>

        {/* Steps grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12 relative">
          {/* Connector line (desktop only) */}
          <div
            className="hidden md:block absolute top-7 left-[calc(33.33%_-_1rem)] right-[calc(33.33%_-_1rem)] h-px"
            style={{ background: 'linear-gradient(90deg, transparent, #222 20%, #222 80%, transparent)' }}
            aria-hidden="true"
          />

          {HOW_IT_WORKS_STEPS.map((step, index) => (
            <div
              key={step.number}
              className="relative flex flex-col items-center md:items-start text-center md:text-left"
            >
              {/* Step circle */}
              <div
                className="flex items-center justify-center w-14 h-14 rounded-full border border-[#222] bg-black text-white font-mono text-base font-bold mb-6 relative z-10 shrink-0 select-none"
                aria-label={`Step ${index + 1}`}
              >
                {step.number}
              </div>

              <h3 className="text-lg sm:text-xl font-semibold text-white mb-3">
                {step.title}
              </h3>
              <p className="text-[#555] text-sm sm:text-base leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <a
            href="/cases/new"
            className="inline-flex items-center gap-2 text-[#888] hover:text-white text-sm transition-colors border-b border-[#333] hover:border-[#666] pb-0.5"
          >
            Start your case now
            <span aria-hidden="true">→</span>
          </a>
        </div>
      </div>
    </section>
  )
}
