import { Navbar }       from '@/components/landing/Navbar'
import { Hero }         from '@/components/landing/Hero'
import { HowItWorks }  from '@/components/landing/HowItWorks'
import { ProblemTypes } from '@/components/landing/ProblemTypes'
import { Pricing }     from '@/components/landing/Pricing'
import { Footer }      from '@/components/landing/Footer'

/**
 * Arbiter landing page.
 * Server component — all heavy work happens on the server.
 * Only Navbar and TypewriterText are client components.
 */
export default function Home() {
  return (
    <main className="bg-black">
      <Navbar />
      <Hero />
      <HowItWorks />
      <ProblemTypes />
      <Pricing />
      <Footer />
    </main>
  )
}
