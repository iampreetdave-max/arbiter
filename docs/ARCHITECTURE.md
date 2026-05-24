# ARCHITECTURE.md — Arbiter Technical Decisions
> Every tech decision lives here. Update this when architecture changes.

---

## System Overview

```
User (Web / WhatsApp)
        │
        ▼
┌─────────────────────┐
│   Next.js Frontend  │  ← User talks to Arbiter here
│   (Cloud Run)       │
└─────────┬───────────┘
          │ HTTPS API calls
          ▼
┌─────────────────────┐
│   FastAPI Backend   │  ← Orchestrates everything
│   (Cloud Run)       │
└──┬──────┬──────┬────┘
   │      │      │
   ▼      ▼      ▼
Gemini  Firebase  GCS
 API    Firestore Storage
   │
   ▼
Google ADK Agent Pipeline:
1. IntakeAgent    → Understands the user's problem
2. ResearchAgent  → Finds applicable laws
3. DraftingAgent  → Writes the legal document
4. TrackingAgent  → Manages deadlines & follow-ups
```

---

## Agent Architecture

```
User Input
    │
    ▼
IntakeAgent (Gemini 2.0 Pro)
  - Asks clarifying questions
  - Extracts: problem_type, jurisdiction, parties, dates, desired_outcome
    │
    ▼
ResearchAgent (Gemini 2.0 Pro + Vertex AI Search)
  - Searches Indian legal database
  - Returns: relevant_laws[], case_law[], applicable_sections[]
    │
    ▼
DraftingAgent (Gemini 2.0 Pro)
  - Generates legal document
  - MUST cite every legal claim
  - Returns: document_text, citations[]
    │
    ▼
TrackingAgent (Gemini 2.0 Pro)
  - Sets response deadline (30 days)
  - Schedules reminders
  - Suggests next steps if no response
```

---

## Database Schema (Firestore)

```
/users/{userId}
  - email, name, phone
  - plan: "pay_per_doc" | "monthly"
  - created_at, razorpay_customer_id

/cases/{caseId}
  - user_id, status, problem_type, jurisdiction
  - intake_data, research_data
  - created_at, updated_at

/documents/{documentId}
  - case_id, type, content, citations[]
  - gcs_url, payment_status, razorpay_payment_id
  - created_at

/reminders/{reminderId}
  - case_id, user_id, remind_at, message, sent
```

---

## API Endpoints (FastAPI)

```
POST   /api/cases/start
GET    /api/cases/{id}
POST   /api/cases/{id}/message
POST   /api/cases/{id}/generate
GET    /api/cases/

GET    /api/documents/{id}
GET    /api/documents/{id}/pdf
POST   /api/documents/{id}/pay
POST   /payments/webhook

GET    /health
GET    /health/agents
```

---

## Security

1. No legal advice — every output has disclaimer
2. Grounded generation — every claim cites a statute
3. Firebase Auth JWT on every request
4. .env / Secret Manager — no hardcoded secrets
5. DPDP Act compliance — 30-day retention for free users

---

## Deployment

```
Dev:  uvicorn local (8000) + next dev (3000) + Firebase emulator
Prod: Cloud Run asia-south1 + Firestore + GCS + Cloud Logging
```

---

## Cost at 50 Customers/Month

| Service | Est. Cost |
|---|---|
| Gemini API | ~$20–50 |
| Cloud Run | ~$5–15 |
| Firebase | ~$2–5 |
| GCS | ~$1–3 |
| Vertex AI Search | ~$10–20 |
| **Total** | **~$38–93** |

Revenue at 50 customers: ₹25,000/month (~$300) → ~70% margin ✅
