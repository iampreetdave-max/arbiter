/**
 * Typed API client for the Arbiter backend.
 * Automatically attaches Firebase JWT to every request.
 * All methods throw ApiError on non-2xx responses.
 */
import { auth } from './firebase'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── Error class ───────────────────────────────────────────────────────────────────────────
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

// ── Core fetch wrapper ────────────────────────────────────────────────────────────────────
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

// ── Domain types ───────────────────────────────────────────────────────────────────────
export type ProblemType =
  | 'tenant_dispute'
  | 'employment'
  | 'consumer'
  | 'rti'
  | 'harassment'
  | 'debt_recovery'

export type CaseStatus =
  | 'intake'
  | 'research'
  | 'drafting'
  | 'draft_ready'
  | 'paid'
  | 'closed'

export type DocumentType =
  | 'demand_letter'
  | 'legal_notice'
  | 'rti_application'
  | 'consumer_complaint'
  | 'cease_and_desist'
  | 'employment_complaint'

export interface ArbiterCase {
  id: string
  user_id: string
  problem_type: ProblemType
  title: string
  description: string
  status: CaseStatus
  jurisdiction?: string
  facts?: string
  opposing_party?: string
  relief_sought?: string
  created_at: string
  updated_at: string
}

export interface ArbiterDocument {
  id: string
  case_id: string
  document_type: DocumentType
  content: string
  pdf_url?: string
  word_count?: number
  citations?: string[]
  created_at: string
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
  amount: number       // in paise
  currency: string
  case_id: string
}

// ── Cases API ─────────────────────────────────────────────────────────────────────────
export const casesApi = {
  /** List all cases for the authenticated user. */
  list: () => req<ArbiterCase[]>('/cases'),

  /** Fetch a single case by ID. */
  get: (id: string) => req<ArbiterCase>(`/cases/${id}`),

  /** Create a case from the intake form (non-chat path). */
  create: (data: {
    problem_type: ProblemType
    title: string
    description: string
    jurisdiction?: string
  }) => req<ArbiterCase>('/cases', { method: 'POST', body: JSON.stringify(data) }),

  /** Start an intake chat — creates a case and returns the AI's first response. */
  startChat: (message: string) =>
    req<ChatResponse>('/cases/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),

  /** Send a follow-up message in an existing case's intake conversation. */
  sendMessage: (caseId: string, message: string) =>
    req<ChatResponse>(`/cases/${caseId}/message`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
}

// ── Documents API ─────────────────────────────────────────────────────────────────────
export const documentsApi = {
  /** Trigger AI document generation for a case. */
  generate: (caseId: string, documentType: DocumentType) =>
    req<ArbiterDocument>('/documents/generate', {
      method: 'POST',
      body: JSON.stringify({ case_id: caseId, document_type: documentType }),
    }),

  /** Fetch a document by ID. */
  get: (id: string) => req<ArbiterDocument>(`/documents/${id}`),

  /** Fetch all documents for a case. */
  getByCaseId: (caseId: string) =>
    req<ArbiterDocument[]>(`/documents?case_id=${caseId}`),
}

// ── Payments API ──────────────────────────────────────────────────────────────────────
export const paymentsApi = {
  /** Create a Razorpay order for a case. Returns order details for checkout. */
  createOrder: (caseId: string) =>
    req<PaymentOrder>('/payments/order', {
      method: 'POST',
      body: JSON.stringify({ case_id: caseId }),
    }),
}
