# Frontend Design System — Arbiter
# Read this before building ANY frontend component.

## Theme: MONOCHROME
Arbiter uses a strict monochrome color palette. No color except for critical states.

### Color Palette
```css
/* Background */
--bg-primary: #000000;      /* Main app background */
--bg-secondary: #0a0a0a;    /* Cards, panels */
--bg-tertiary: #111111;     /* Input fields, hover states */
--bg-elevated: #1a1a1a;     /* Modals, dropdowns */

/* Text */
--text-primary: #ffffff;     /* Main text */
--text-secondary: #a0a0a0;   /* Subtext, placeholders */
--text-muted: #555555;       /* Disabled, very subtle */

/* Borders */
--border-default: #222222;   /* Default borders */
--border-hover: #444444;     /* Hover state borders */
--border-focus: #ffffff;     /* Focused input borders */

/* Only use color for critical states */
--color-success: #22c55e;    /* Payment success, document ready */
--color-error: #ef4444;      /* Errors only */
--color-warning: #f59e0b;    /* Deadlines approaching */
```

## 21st.dev Component Library
Install components: npx shadcn@latest add "https://21st.dev/r/[component-name]"

### Components to use in Arbiter:
- Text animations: https://21st.dev/r/typewriter-effect
- Button animations: https://21st.dev/r/shiny-button
- Card hover effects: https://21st.dev/r/card-with-noise-pattern
- Loading states: https://21st.dev/r/animated-circular-progress-bar
- Background: https://21st.dev/r/dot-pattern (dark dots on black)
- Gradient text: https://21st.dev/r/animated-gradient-text
- Border glow: https://21st.dev/r/border-beam
- Shimmer: https://21st.dev/r/shimmer-button

### Typography
```
Font: Geist (from next/font/google) -- clean, modern, technical
Heading: font-bold tracking-tight
Body: font-normal leading-relaxed
Code/Legal text: font-mono (for document content)
```

## Key UI Screens

### 1. Landing Page
- Hero: Big white bold text on black "Legal help. No lawyer fees."
- Animated typewriter showing problem types: "Tenant disputes. Unpaid wages. Consumer fraud."
- CTA button: Shiny white button "Get Started Free"
- Dot pattern background

### 2. Intake Chat Screen
- Chat interface, dark theme
- Arbiter messages: dark gray bubbles
- User messages: white bubbles with black text
- Typing indicator: 3 dots animation
- Bottom input: minimal, white border on focus

### 3. Document Viewer
- Document shown in monospace font on dark background
- "Unlock Full Document" CTA if not paid
- Legal citations shown as monochrome badges
- Download button: ghost button with border beam animation

### 4. Dashboard
- Case cards: dark cards with subtle border
- Status badges: monochrome (INTAKE, RESEARCHING, READY, TRACKING)
- Deadline indicator: thin progress bar, turns amber when close

## Component Rules
1. NEVER use colored backgrounds except for success/error/warning
2. ALL cards use border + subtle shadow, never color fills
3. Hover states: border gets brighter (#444 -> #888)
4. Focus states: pure white border (#ffffff)
5. Animations: subtle, purposeful -- not decorative
6. Loading states: shimmer/skeleton in dark grays
