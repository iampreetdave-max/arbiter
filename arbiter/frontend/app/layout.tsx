import type { Metadata, Viewport } from 'next'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import './globals.css'

export const metadata: Metadata = {
  title: {
    default: 'Arbiter — AI Legal Documents for Everyday Indians',
    template: '%s | Arbiter',
  },
  description:
    'Get professionally drafted demand letters, RTI applications, and consumer complaints in 30 minutes. Powered by Google Gemini AI. No lawyer fees.',
  keywords: [
    'legal documents India',
    'demand letter',
    'RTI application',
    'consumer complaint',
    'AI legal assistant India',
    'legal help India',
    'tenant dispute',
    'unpaid wages',
    'consumer fraud India',
  ],
  authors: [{ name: 'Arbiter' }],
  creator: 'Arbiter',
  openGraph: {
    title: 'Arbiter — AI Legal Documents for Everyday Indians',
    description:
      'Demand letters, RTI applications, consumer complaints — drafted by AI in 30 minutes. No lawyer needed.',
    type: 'website',
    siteName: 'Arbiter',
    locale: 'en_IN',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Arbiter — AI Legal Documents',
    description: 'AI-powered legal documents for everyday Indians. No lawyer fees.',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: '#000000',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable}`}
      suppressHydrationWarning
    >
      <body className="bg-black text-white antialiased min-h-screen">
        {children}
      </body>
    </html>
  )
}
