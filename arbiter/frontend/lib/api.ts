/**
 * Typed API client for the Arbiter backend.
 * Automatically attaches Firebase JWT to every request.
 * All methods throw ApiError on non-2xx responses.
 */
import { auth } from './firebase'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── Error class ──────────────────────────────────────────────────────────────────
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

// ── Core fetch wrapper ───────────────────────────────────────────────────────────
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

// ── Domain types ───────────────────────────────────────────────────────────────
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
  | 'complete'
  | 'paid'
  | 'tracking'
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
  content?: string          // null if not paid
  preview?: string          // first 300 chars
  citations: Citation[]
  disclaimer: string
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded'
  gcs_url?: string
  created_at?: string
  amount_paise: number
  // Confidence & grounding
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

// ── Cases API ──────────────────────────────────────────────────────────────────
export const casesApi = {
  /** List all cases for the authenticated user. */
  list: () => req<{ cases: ArbiterCase[]; total: number }>('/api/cases/'),

  /** Fetch a single case by ID. */
  get: (id: string) => req<ArbiterCase>(`/api/cases/${id}`),

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

  /** Trigger synchronous document generation for a case. */
  generateDocument: (caseId: string, documentType: DocumentType = 'demand_letter') =>
    req<{ document_id: string; case_id: string; status: string }>(
      `/api/cases/${caseId}/generate`,
      {
        method: 'POST',
        body: JSON.stringify({ document_type: documentType }),
      },
    ),

  /**
   * Record the outcome of a case (what happened after sending the document).
   * Returns the updated case.
   */
  updateOutcome: (
    caseId: string,
    outcome: CaseOutcome,
    outcomeNotes?: string,
  ) =>
    req<ArbiterCase>(`/api/cases/${caseId}/outcome`, {
      method: 'PATCH',
      body: JSON.stringify({ outcome, outcome_notes: outcomeNotes }),
    }),

  /**
   * Open an SSE stream to watch document generation in real time.
   * Returns an EventSource. The caller must add onmessage + onerror handlers.
   *
   * Message format:
   *   { chunk: string }          → append to document draft
   *   { done: true, document_id: string } → generation complete
   *   { error: string }          → generation failed
   */
  streamGenerate: async (
    caseId: string,
    documentType: DocumentType = 'demand_letter',
  ): Promise<EventSource> => {
    const token = auth.currentUser ? await auth.currentUser.getIdToken() : ''
    // EventSource doesn't support custom headers; pass token as query param
    const url = `${BASE}/api/cases/${caseId}/generate/stream?document_type=${documentType}&token=${token}`
    return new EventSource(url)
  },
}

// ── Documents API ─────────────────────────────────────────────────────────────────
export const documentsApi = {
  /** Fetch a document by ID. */
  get: (id: string) => req<ArbiterDocument>(`/api/documents/${id}`),

  /** Fetch all documents for a case (uses cases list endpoint). */
  getByCaseId: async (caseId: string): Promise<ArbiterDocument[]> => {
    // The backend doesn't have a filter endpoint yet — fetch case and use doc ID
    // This will be enhanced once document list endpoint exists
    return []
  },

  /**
   * Revise a paid document with natural language instructions.
   * Example: "Make the tone more assertive"
   * Returns the updated document (max 3 revisions per document).
   */
  revise: (documentId: string, instructions: string) =>
    req<ArbiterDocument>(`/api/documents/${documentId}/revise`, {
      method: 'POST',
      body: JSON.stringify({ instructions }),
    }),

  /** Create a Razorpay payment order for a document. */
  createOrder: (documentId: string) =>
    req<PaymentOrder>(`/api/documents/${documentId}/create-order`, {
      method: 'POST',
    }),

  /** Verify payment after Razorpay checkout. */
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

  /** Get signed GCS download URL (paid only). */
  getDownloadUrl: (documentId: string) =>
    req<{ download_url: string; expires_in_minutes: number }>(
      `/api/documents/${documentId}/download-url`,
    ),
}

// ── Payments API (legacy — kept for compatibility) ────────────────────────────────
export const paymentsApi = {
  /** Create a Razorpay order for a document. */
  createOrder: (documentId: string) => documentsApi.createOrder(documentId),
}
