// ⚖️ Arbiter | Powered by Google Gemini 2.0 Pro | XPRIZE Build with Gemini
/**
 * Typed API client for the Arbiter backend.
 * Automatically attaches Firebase JWT to every request.
 * All methods throw ApiError on non-2xx responses.
 *
 * Updated (Session 7): Added lawyers, legal updates, public cases APIs.
 */
import { auth } from './firebase'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── Error class ───────────────────────────────────────────────────────────────
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

// ── Core fetch wrapper ────────────────────────────────────────────────────────
async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = auth.currentUser ? await auth.currentUser.getIdToken() : null
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, body.detail ?? 'Unknown error')
  }
  return res.json() as Promise<T>
}

/** Public request — no auth token attached. */
async function pubReq<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, body.detail ?? 'Unknown error')
  }
  return res.json() as Promise<T>
}

// ── Domain types ──────────────────────────────────────────────────────────────
export type CountryCode = 'IN' | 'US' | 'GB' | 'CA' | 'AU'

export type ProblemType =
  | 'tenant_dispute'
  | 'employment'
  | 'consumer'
  | 'rti'
  | 'harassment'
  | 'debt_recovery'
  | 'other'

export type CaseStatus =
  | 'intake'
  | 'research'
  | 'drafting'
  | 'draft_ready'
  | 'complete'
  | 'paid'
  | 'tracking'
  | 'escalated'
  | 'closed'

export type CaseOutcome =
  | 'pending'
  | 'resolved'
  | 'partial'
  | 'escalated'
  | 'no_response'

export type DocumentType =
  | 'demand_letter'
  | 'legal_notice'
  | 'rti_application'
  | 'consumer_complaint'
  | 'cease_desist'
  | 'employment_complaint'
  | 'small_claims_filing'
  | 'data_subject_access_request'

export type LawyerSpecialty =
  | 'consumer' | 'employment' | 'tenant' | 'criminal' | 'family'
  | 'corporate' | 'immigration' | 'property' | 'civil' | 'cyber'
  | 'rti' | 'debt_recovery' | 'other'

export type LawyerStatus = 'pending' | 'verified' | 'suspended' | 'rejected'

export type LegalUpdateCategory = 'legislation' | 'judgment' | 'regulation' | 'advisory'

export type CaseShowcaseCategory =
  | 'consumer' | 'employment' | 'tenant' | 'civil_rights'
  | 'landmark' | 'cyber' | 'corporate'

// ── Existing domain interfaces ─────────────────────────────────────────────
export interface GroundingSource {
  title: string
  url: string
}

export interface ArbiterCase {
  id: string
  user_id: string
  problem_type: ProblemType
  title?: string
  description?: string
  status: CaseStatus
  country_code?: CountryCode
  jurisdiction?: string
  intake_complete?: boolean
  outcome?: CaseOutcome
  outcome_notes?: string
  created_at: string
  updated_at?: string
  next_message?: string
}

export interface Citation {
  act: string
  section: string
  description: string
  verified: boolean
  source_url?: string
}

export interface ArbiterDocument {
  id: string
  case_id: string
  type: DocumentType
  title: string
  content?: string
  preview?: string
  citations: Citation[]
  disclaimer: string
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded'
  gcs_url?: string
  created_at?: string
  amount_paise: number
  confidence_score: number
  grounding_sources: string[]
  verified_citations: number
  revision_count: number
  language: string
}

export interface ChatResponse {
  response: string
  case_id: string
  ready_to_generate: boolean
  suggested_document_type?: DocumentType
  updated_case?: Partial<ArbiterCase>
}

export interface PaymentOrder {
  order_id: string
  amount_paise: number
  currency: string
  razorpay_key_id: string
  document_id: string
}

// ── New domain interfaces (Session 7) ──────────────────────────────────────
export interface Country {
  code: CountryCode
  name: string
  flag: string
}

export interface Lawyer {
  id: string
  full_name: string
  country_code: CountryCode
  jurisdiction: string
  specialties: LawyerSpecialty[]
  years_of_experience: number
  available_for_pro_bono: boolean
  status: LawyerStatus
  bio: string
  cases_resolved: number
  rating: number
  rating_count: number
  languages: string[]
  created_at?: string
}

export interface LawyerRegisterPayload {
  full_name: string
  bar_registration_number: string
  country_code: CountryCode
  jurisdiction: string
  specialties: LawyerSpecialty[]
  years_of_experience: number
  available_for_pro_bono: boolean
  bio: string
  contact_email: string
  contact_phone?: string
  website_url?: string
  languages?: string[]
}

export interface LawyerMatch {
  id: string
  lawyer_id: string
  case_id: string
  case_title: string
  case_problem_type: ProblemType
  case_country_code: CountryCode
  case_jurisdiction: string
  match_score: number
  status: 'pending' | 'accepted' | 'declined' | 'completed'
  lawyer_notes?: string
  created_at?: string
}

export interface LawyerMatchResult {
  matched: boolean
  lawyer?: Lawyer
  match_id?: string
  message: string
}

export interface LegalUpdate {
  id: string
  country_code: CountryCode
  country_name: string
  category: LegalUpdateCategory
  title: string
  summary: string
  impact: string
  effective_date: string
  source_hint: string
  fetched_at: string
  week_number: number
  year: number
}

export interface PublicCase {
  id: string
  country_code: CountryCode
  country_name: string
  title: string
  parties: string
  court: string
  year: number
  category: CaseShowcaseCategory
  summary: string
  legal_lesson: string
  citizen_impact: string
  is_landmark: boolean
  source_hint: string
  fetched_at: string
  view_count: number
}

// ── Cases API ─────────────────────────────────────────────────────────────────
export const casesApi = {
  list: () => req<{ cases: ArbiterCase[]; total: number }>('/api/cases/'),

  get: (id: string) => req<ArbiterCase>(`/api/cases/${id}`),

  startChat: (message: string, countryCode?: CountryCode) =>
    req<ChatResponse>('/cases/chat', {
      method: 'POST',
      body: JSON.stringify({ message, country_code: countryCode }),
    }),

  sendMessage: (caseId: string, message: string) =>
    req<ChatResponse>(`/cases/${caseId}/message`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),

  generateDocument: (caseId: string, documentType: DocumentType = 'demand_letter') =>
    req<{ document_id: string; case_id: string; status: string }>(
      `/api/cases/${caseId}/generate`,
      { method: 'POST', body: JSON.stringify({ document_type: documentType }) },
    ),

  updateOutcome: (caseId: string, outcome: CaseOutcome, outcomeNotes?: string) =>
    req<ArbiterCase>(`/api/cases/${caseId}/outcome`, {
      method: 'PATCH',
      body: JSON.stringify({ outcome, outcome_notes: outcomeNotes }),
    }),

  streamGenerate: async (caseId: string, documentType: DocumentType = 'demand_letter') => {
    const token = auth.currentUser ? await auth.currentUser.getIdToken() : ''
    const url = `${BASE}/api/cases/${caseId}/generate/stream?document_type=${documentType}&token=${token}`
    return new EventSource(url)
  },

  /** Request lawyer escalation for a case. */
  escalateToLawyer: (caseId: string) =>
    req<LawyerMatchResult>(`/api/cases/${caseId}/escalate-to-lawyer`, { method: 'POST' }),
}

// ── Documents API ─────────────────────────────────────────────────────────────
export const documentsApi = {
  get: (id: string) => req<ArbiterDocument>(`/api/documents/${id}`),

  getByCaseId: async (_caseId: string): Promise<ArbiterDocument[]> => [],

  revise: (documentId: string, instructions: string) =>
    req<ArbiterDocument>(`/api/documents/${documentId}/revise`, {
      method: 'POST',
      body: JSON.stringify({ instructions }),
    }),

  createOrder: (documentId: string) =>
    req<PaymentOrder>(`/api/documents/${documentId}/create-order`, { method: 'POST' }),

  verifyPayment: (
    documentId: string,
    razorpayOrderId: string,
    razorpayPaymentId: string,
    razorpaySignature: string,
  ) =>
    req<{ status: string; document_id: string }>(
      `/api/documents/${documentId}/verify-payment`,
      {
        method: 'POST',
        body: JSON.stringify({
          razorpay_order_id: razorpayOrderId,
          razorpay_payment_id: razorpayPaymentId,
          razorpay_signature: razorpaySignature,
        }),
      },
    ),

  getDownloadUrl: (documentId: string) =>
    req<{ download_url: string; expires_in_minutes: number }>(
      `/api/documents/${documentId}/download-url`,
    ),
}

// ── Lawyers API (Session 7) ───────────────────────────────────────────────────
export const lawyersApi = {
  /** Browse verified lawyers publicly (no auth needed). */
  list: (params?: {
    country_code?: CountryCode
    specialty?: LawyerSpecialty
    pro_bono_only?: boolean
    limit?: number
  }) => {
    const qs = new URLSearchParams()
    if (params?.country_code) qs.set('country_code', params.country_code)
    if (params?.specialty) qs.set('specialty', params.specialty)
    if (params?.pro_bono_only) qs.set('pro_bono_only', 'true')
    if (params?.limit) qs.set('limit', String(params.limit))
    return pubReq<{ lawyers: Lawyer[]; total: number }>(`/api/lawyers?${qs}`)
  },

  /** Get a specific lawyer's public profile. */
  get: (lawyerId: string) => pubReq<Lawyer>(`/api/lawyers/${lawyerId}`),

  /** Register as a lawyer. */
  register: (payload: LawyerRegisterPayload) =>
    req<Lawyer & { message: string }>('/api/lawyers/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  /** Get own lawyer profile (auth required). */
  getMyProfile: () => req<Lawyer>('/api/lawyers/me'),

  /** Update own lawyer profile. */
  updateMyProfile: (updates: Partial<Pick<LawyerRegisterPayload, 'specialties' | 'available_for_pro_bono' | 'bio' | 'contact_phone' | 'website_url' | 'languages'>>) =>
    req<Lawyer>('/api/lawyers/me', {
      method: 'PUT',
      body: JSON.stringify(updates),
    }),

  /** Get cases matched to this lawyer (lawyer dashboard). */
  getMyMatches: (statusFilter?: string, limit?: number) => {
    const qs = new URLSearchParams()
    if (statusFilter) qs.set('status_filter', statusFilter)
    if (limit) qs.set('limit', String(limit))
    return req<{ matches: LawyerMatch[]; total: number; lawyer_id: string }>(
      `/api/lawyers/me/cases?${qs}`,
    )
  },

  /** Accept or decline a case match. */
  respondToMatch: (matchId: string, action: 'accept' | 'decline', notes?: string) =>
    req<LawyerMatch>(`/api/lawyers/me/cases/${matchId}/respond`, {
      method: 'POST',
      body: JSON.stringify({ action, notes }),
    }),
}

// ── Legal Updates API (Session 7) ────────────────────────────────────────────
export const legalUpdatesApi = {
  /** Get recent legal updates (public, no auth needed). */
  list: (params?: {
    country_code?: CountryCode | ''
    category?: LegalUpdateCategory | ''
    days_back?: number
    limit?: number
  }) => {
    const qs = new URLSearchParams()
    if (params?.country_code) qs.set('country_code', params.country_code)
    if (params?.category) qs.set('category', params.category)
    if (params?.days_back) qs.set('days_back', String(params.days_back))
    if (params?.limit) qs.set('limit', String(params.limit))
    return pubReq<{ updates: LegalUpdate[]; total: number; supported_countries: Country[] }>(
      `/api/legal-updates?${qs}`,
    )
  },

  /** Get list of supported countries. */
  getSupportedCountries: () =>
    pubReq<{ countries: Country[] }>('/api/legal-updates/countries'),
}

// ── Public Cases API (Session 7) ──────────────────────────────────────────────
export const publicCasesApi = {
  /** Browse public case showcase (no auth needed). */
  list: (params?: {
    country_code?: CountryCode | ''
    category?: CaseShowcaseCategory | ''
    landmark_only?: boolean
    limit?: number
  }) => {
    const qs = new URLSearchParams()
    if (params?.country_code) qs.set('country_code', params.country_code)
    if (params?.category) qs.set('category', params.category)
    if (params?.landmark_only) qs.set('landmark_only', 'true')
    if (params?.limit) qs.set('limit', String(params.limit))
    return pubReq<{ cases: PublicCase[]; total: number; categories: string[] }>(
      `/api/public-cases?${qs}`,
    )
  },

  /** Get a specific public case (also increments view count). */
  get: (caseId: string) => pubReq<PublicCase>(`/api/public-cases/${caseId}`),
}

// ── Payments API (legacy — kept for compatibility) ────────────────────────────
export const paymentsApi = {
  createOrder: (documentId: string) => documentsApi.createOrder(documentId),
}
