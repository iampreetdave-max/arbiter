'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { NAVBAR_LINKS } from '@/lib/constants'

/**
 * Fixed top navigation bar.
 * Becomes opaque + blurred on scroll. Has mobile hamburger menu.
 */
export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Close mobile menu on route change / resize
  useEffect(() => {
    const close = () => setMenuOpen(false)
    window.addEventListener('resize', close)
    return () => window.removeEventListener('resize', close)
  }, [])

  return (
    <nav
      className={[
        'fixed top-0 left-0 right-0 z-50',
        'transition-all duration-300',
        scrolled
          ? 'bg-black/80 backdrop-blur-xl border-b border-[#111]'
          : 'bg-transparent',
      ].join(' ')}
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 text-white font-bold text-xl tracking-tight hover:opacity-80 transition-opacity"
          >
            Arbiter <span aria-hidden="true">⚖️</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden sm:flex items-center gap-6">
            {NAVBAR_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-[#888] hover:text-white text-sm font-medium transition-colors"
                {...(link.href.startsWith('http')
                  ? { target: '_blank', rel: 'noopener noreferrer' }
                  : {})}
              >
                {link.label}
              </a>
            ))}
            <Link
              href="/cases/new"
              className="btn-shiny text-black px-4 py-2 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              Start Free →
            </Link>
          </div>

          {/* Mobile hamburger */}
          <button
            className="sm:hidden p-2 text-[#888] hover:text-white transition-colors rounded-md"
            onClick={() => setMenuOpen((o) => !o)}
            aria-expanded={menuOpen}
            aria-controls="mobile-menu"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          >
            {menuOpen ? (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile menu panel */}
        {menuOpen && (
          <div
            id="mobile-menu"
            className="sm:hidden border-t border-[#111] py-4 space-y-1"
          >
            {NAVBAR_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="block text-[#888] hover:text-white text-sm py-2.5 px-1 transition-colors rounded"
                onClick={() => setMenuOpen(false)}
                {...(link.href.startsWith('http')
                  ? { target: '_blank', rel: 'noopener noreferrer' }
                  : {})}
              >
                {link.label}
              </a>
            ))}
            <div className="pt-2">
              <Link
                href="/cases/new"
                className="block w-full text-center btn-shiny text-black px-4 py-3 rounded-lg text-sm font-semibold"
                onClick={() => setMenuOpen(false)}
              >
                Start Free →
              </Link>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
