/** Arbiter frontend constants — single source of truth for UI copy */

export const PROBLEM_TYPES = [
  {
    id: 'tenant_dispute',
    label: 'Tenant Disputes',
    icon: '🏠',
    description: 'Deposit not returned, illegal eviction, maintenance ignored',
    documents: ['Demand Letter', 'Legal Notice'],
    tag: 'Most common',
  },
  {
    id: 'employment',
    label: 'Unpaid Wages',
    icon: '💼',
    description: 'Salary withheld, wrongful termination, PF not paid',
    documents: ['Demand Letter', 'Employment Complaint'],
    tag: null,
  },
  {
    id: 'consumer',
    label: 'Consumer Fraud',
    icon: '🛒',
    description: 'E-commerce scam, defective product, service not delivered',
    documents: ['Consumer Complaint', 'Demand Letter'],
    tag: 'Popular',
  },
  {
    id: 'rti',
    label: 'RTI Applications',
    icon: '📋',
    description: 'Right to Information requests to government departments',
    documents: ['RTI Application'],
    tag: null,
  },
  {
    id: 'harassment',
    label: 'Workplace Harassment',
    icon: '🛡️',
    description: 'Harassment, discrimination, toxic work environment',
    documents: ['Cease & Desist', 'Complaint Letter'],
    tag: null,
  },
  {
    id: 'debt_recovery',
    label: 'Debt Recovery',
    icon: '💰',
    description: 'Money owed by individuals or companies, cheque bounce',
    documents: ['Demand Letter', 'Legal Notice'],
    tag: null,
  },
] as const

export const TYPEWRITER_PHRASES = [
  'tenant disputes.',
  'unpaid wages.',
  'consumer fraud.',
  'RTI applications.',
  'workplace harassment.',
  'debt recovery.',
]

export const STATS = [
  { value: '30 min', label: 'Average drafting time' },
  { value: '₹299',  label: 'Per document' },
  { value: '6+',    label: 'Document types' },
  { value: '100%',  label: 'AI-powered' },
] as const

export const HOW_IT_WORKS_STEPS = [
  {
    number: '01',
    title: 'Describe your problem',
    description:
      'Tell Arbiter what happened in plain English or Hindi. Our AI asks the right questions — jurisdiction, parties involved, evidence, outcome you want.',
  },
  {
    number: '02',
    title: 'AI researches your rights',
    description:
      'Arbiter looks up applicable Indian laws in real time — Consumer Protection Act, RTI Act, tenancy laws, labour codes — and identifies your strongest legal position.',
  },
  {
    number: '03',
    title: 'Get your legal document',
    description:
      'Download a professionally drafted demand letter, RTI application, or consumer complaint with legal citations, ready to send.',
  },
] as const

export const PRICING_PLANS = [
  {
    name: 'Per Document',
    price: '₹299',
    period: 'per document',
    description: 'Perfect for a single dispute',
    featured: false,
    cta: 'Get Started',
    features: [
      'One legal document',
      'AI-powered drafting',
      'Legal citations included',
      'PDF download',
      '48-hour revision window',
    ],
  },
  {
    name: 'Monthly Unlimited',
    price: '₹799',
    period: 'per month',
    description: 'Best for ongoing legal matters',
    featured: true,
    cta: 'Start Free Trial →',
    features: [
      'Unlimited documents',
      'All 6 document types',
      'Priority AI processing',
      'Case deadline tracking',
      'Lawyer referral network',
      '30-day money back',
    ],
  },
] as const

export const NAVBAR_LINKS = [
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Pricing',      href: '#pricing' },
  { label: 'GitHub',       href: 'https://github.com/iampreetdave-max/arbiter' },
] as const
