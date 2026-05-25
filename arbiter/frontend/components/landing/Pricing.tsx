import { PRICING_PLANS } from '@/lib/constants'
import { cn } from '@/lib/utils'

/**
 * Pricing section — Per Document vs Monthly Unlimited.
 * Mobile: stacked cards. Desktop: side-by-side.
 */
export function Pricing() {
  return (
    <section
      id="pricing"
      className="py-24 sm:py-32 bg-[#050505]"
      aria-labelledby="pricing-heading"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12 sm:mb-16">
          <p className="text-[#555] text-xs font-medium uppercase tracking-[0.2em] mb-4">
            Simple pricing
          </p>
          <h2
            id="pricing-heading"
            className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-white"
          >
            Less than a single
            <br />
            <span className="text-[#333]">lawyer consultation</span>
          </h2>
          <p className="mt-4 text-[#555] max-w-md mx-auto text-sm sm:text-base">
            A single lawyer consultation in India costs ₹2,000–₹10,000 and
            takes days to schedule. Arbiter drafts your document for ₹299 in
            30 minutes.
          </p>
        </div>

        {/* Pricing cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 max-w-3xl mx-auto">
          {PRICING_PLANS.map((plan) => (
            <div
              key={plan.name}
              className={cn(
                'relative flex flex-col p-6 sm:p-8 rounded-2xl border transition-all duration-200',
                plan.featured
                  ? 'border-white bg-black'
                  : 'border-[#1a1a1a] bg-black hover:border-[#333]'
              )}
            >
              {/* Best value badge */}
              {plan.featured && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="px-3 py-1 text-xs font-semibold bg-white text-black rounded-full whitespace-nowrap">
                    Best Value
                  </span>
                </div>
              )}

              {/* Plan name */}
              <p
                className={cn(
                  'text-xs font-medium uppercase tracking-[0.15em] mb-4',
                  plan.featured ? 'text-white' : 'text-[#666]'
                )}
              >
                {plan.name}
              </p>

              {/* Price */}
              <div className="flex items-end gap-1.5 mb-2">
                <span className="text-4xl sm:text-5xl font-bold text-white tracking-tight">
                  {plan.price}
                </span>
                <span className="text-[#555] mb-1.5 text-sm">/ {plan.period}</span>
              </div>

              {/* Description */}
              <p className="text-[#555] text-sm mb-6">{plan.description}</p>

              {/* Feature list */}
              <ul className="space-y-3 mb-8 flex-1" role="list">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3 text-sm">
                    <span className="text-white mt-px flex-shrink-0" aria-hidden="true">✓</span>
                    <span className={plan.featured ? 'text-[#aaa]' : 'text-[#666]'}>
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <a
                href="/cases/new"
                className={cn(
                  'block w-full py-3 text-center rounded-lg text-sm font-semibold transition-all duration-200 active:scale-[0.98]',
                  plan.featured
                    ? 'btn-shiny text-black hover:opacity-90'
                    : 'border border-[#222] text-white hover:border-[#555] hover:bg-white/5'
                )}
              >
                {plan.cta}
              </a>
            </div>
          ))}
        </div>

        {/* Footer note */}
        <p className="text-center text-[#444] text-xs mt-8">
          Prices exclusive of GST. No lock-in contract. Cancel anytime.
          14-day money-back guarantee on monthly plans.
        </p>
      </div>
    </section>
  )
}
