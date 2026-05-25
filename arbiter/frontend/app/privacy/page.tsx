import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'Arbiter Privacy Policy — how we handle your data.',
}

export default function PrivacyPage() {
  return (
    <main className="bg-black min-h-screen">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-20">
        <a href="/" className="text-[#444] hover:text-white text-sm transition-colors mb-8 inline-block">
          ← Back to home
        </a>
        <h1 className="text-3xl font-bold text-white mb-2">Privacy Policy</h1>
        <p className="text-[#444] text-sm mb-12">Last updated: May 2026</p>

        <div className="space-y-8 legal-text">
          <section>
            <h2 className="text-white font-semibold text-base mb-3">1. Information We Collect</h2>
            <p>Arbiter collects the information you provide when describing your legal issue, your email address for account creation, and payment information processed securely through Razorpay. We do not store payment card details.</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">2. How We Use Your Information</h2>
            <p>Your information is used solely to generate your legal documents using Google Gemini AI, to manage your account, and to process payments. We do not sell your data to third parties.</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">3. Data Storage</h2>
            <p>Your case data is stored in Google Firebase Firestore and Google Cloud Storage, both of which are located in the asia-south1 (Mumbai) region. Your data is encrypted in transit and at rest.</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">4. Third-Party Services</h2>
            <p>We use Google Gemini AI for document generation, Firebase for authentication and storage, and Razorpay for payment processing. Each service has its own privacy policy governing how they handle data.</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">5. Your Rights</h2>
            <p>You may request deletion of your account and all associated data at any time by emailing us. We will process deletion requests within 30 days.</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">6. Contact</h2>
            <p>For privacy-related questions, email: <a href="mailto:agilitytechai@gmail.com" className="text-white hover:text-[#aaa] underline">agilitytechai@gmail.com</a></p>
          </section>
        </div>
      </div>
    </main>
  )
}
