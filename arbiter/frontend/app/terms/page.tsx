import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'Arbiter Terms of Service.',
}

export default function TermsPage() {
  return (
    <main className="bg-black min-h-screen">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-20">
        <a href="/" className="text-[#444] hover:text-white text-sm transition-colors mb-8 inline-block">
          ← Back to home
        </a>
        <h1 className="text-3xl font-bold text-white mb-2">Terms of Service</h1>
        <p className="text-[#444] text-sm mb-12">Last updated: May 2026</p>

        <div className="space-y-8 legal-text">
          <section>
            <h2 className="text-white font-semibold text-base mb-3">1. Acceptance</h2>
            <p>By using Arbiter, you agree to these Terms of Service. If you do not agree, do not use the service.</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">2. Not Legal Advice</h2>
            <p>Arbiter generates AI-powered legal documents for informational and self-help purposes only. Nothing on this platform constitutes legal advice, and no attorney-client relationship is created by using our service. For complex legal matters, consult a licensed attorney.</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">3. Payments and Refunds</h2>
            <p>Per-document payments are ₹299 + GST. Monthly plans are ₹799 + GST with a 14-day money-back guarantee. Refunds for per-document purchases are available within 48 hours if the document is unsatisfactory.</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">4. Acceptable Use</h2>
            <p>You may not use Arbiter to generate documents intended to harass, defraud, or harm others. We reserve the right to terminate accounts that violate this policy.</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">5. Accuracy</h2>
            <p>While Arbiter uses Google Gemini AI with real-time legal research, AI can make errors. Always review your document before sending it. Arbiter is not liable for any outcomes resulting from documents generated on this platform.</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">6. Contact</h2>
            <p>For questions: <a href="mailto:agilitytechai@gmail.com" className="text-white hover:text-[#aaa] underline">agilitytechai@gmail.com</a></p>
          </section>
        </div>
      </div>
    </main>
  )
}
