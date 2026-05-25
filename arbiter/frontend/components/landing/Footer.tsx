/**
 * Site footer with CTA banner, nav links, and legal disclaimer.
 */
export function Footer() {
  const year = new Date().getFullYear()

  const footerLinks = {
    Product: [
      { label: 'How It Works', href: '#how-it-works' },
      { label: 'Pricing',      href: '#pricing' },
      { label: 'Problem Types',href: '#problem-types' },
      { label: 'GitHub',       href: 'https://github.com/iampreetdave-max/arbiter', external: true },
    ],
    Legal: [
      { label: 'Privacy Policy',   href: '/privacy' },
      { label: 'Terms of Service', href: '/terms' },
      { label: 'Disclaimer',       href: '/disclaimer' },
    ],
    Hackathon: [
      { label: 'XPRIZE Devpost',   href: 'https://xprize.devpost.com/', external: true },
      { label: 'Gemini API',       href: 'https://aistudio.google.com/apikey', external: true },
      { label: 'Built with Gemini',href: '#', external: false },
    ],
  }

  return (
    <footer className="bg-black border-t border-[#0f0f0f]">
      {/* CTA Banner */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-8">
        <div className="text-center mb-20">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
            Your legal rights
            <br />
            <span className="text-[#333]">deserve to be enforced.</span>
          </h2>
          <p className="text-[#555] mb-8 max-w-md mx-auto text-sm sm:text-base">
            Thousands of Indians win their disputes every year with the right
            legal document. Arbiter gives you that document — instantly.
          </p>
          <a
            href="/cases/new"
            className="inline-flex items-center gap-2 px-8 py-4 btn-shiny text-black rounded-xl font-semibold text-lg hover:opacity-90 transition-opacity active:scale-[0.98]"
          >
            Start Your Case Free
            <span aria-hidden="true">→</span>
          </a>
          <p className="mt-4 text-[#444] text-xs">
            No credit card required. First document free.
          </p>
        </div>

        {/* Nav links grid */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-8 border-t border-[#0f0f0f] pt-12">
          {/* Brand column */}
          <div className="sm:col-span-1">
            <div className="text-white font-bold text-xl mb-3">Arbiter ⚖️</div>
            <p className="text-[#444] text-sm leading-relaxed max-w-xs">
              AI-powered legal documents for everyday Indians. Powered by Google
              Gemini. Built for the XPRIZE hackathon.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <p className="text-[#666] text-xs font-medium uppercase tracking-[0.15em] mb-4">
                {category}
              </p>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-[#444] hover:text-white text-sm transition-colors"
                      {...('external' in link && link.external
                        ? { target: '_blank', rel: 'noopener noreferrer' }
                        : {})}
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Legal disclaimer */}
        <div className="mt-12 pt-8 border-t border-[#0f0f0f]">
          <p className="text-[#333] text-xs leading-relaxed text-center max-w-3xl mx-auto">
            <strong className="text-[#444]">Legal Disclaimer:</strong> Arbiter
            generates AI-powered legal documents for informational and self-help
            purposes only. This is not legal advice and does not create an
            attorney-client relationship. Laws vary by jurisdiction and change
            over time. For complex legal matters, consult a qualified legal
            professional licensed in your jurisdiction.
          </p>
          <p className="text-[#222] text-xs text-center mt-4">
            © {year} Arbiter. Built for XPRIZE Build with Gemini Hackathon.
            Powered by Google Gemini AI.
          </p>
        </div>
      </div>
    </footer>
  )
}
