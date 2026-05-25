# 🤖 GEMINI.md — How Arbiter Uses Google Gemini 2.0 Pro

> This document is for XPRIZE Build with Gemini judges. It maps every Gemini API call in the codebase.

---

## Model in Use

| Setting | Value |
|---|---|
| **Model ID** | `gemini-2.0-pro-exp` |
| **API** | `google.generativeai` (Python SDK) |
| **Framework** | Google Agent Development Kit (ADK) |
| **Grounding** | Google Search via Gemini grounding API |

---

## Where Gemini Is Called

### 1. `arbiter/backend/services/gemini_service.py`
The central Gemini wrapper. All AI calls route through here.

| Method | Gemini Feature Used |
|---|---|
| `generate()` | Standard text generation |
| `generate_structured()` | JSON-mode generation with schema |
| `generate_with_grounding()` | Google Search grounding — verifies real statutes |
| `stream_generate()` | Streaming generation for live document drafting |
| `chat()` | Multi-turn conversation with history |

---

### 2. `arbiter/backend/agents/intake_agent.py`
**IntakeAgent** — Multi-turn Gemini conversation to collect legal problem details.
- Drives conversational intake flow
- Asks for jurisdiction, parties, amounts, dates, desired outcome
- Returns structured `IntakeData` when complete

---

### 3. `arbiter/backend/agents/research_agent.py`
**ResearchAgent** — Gemini + Google Search grounding for real-time legal research.
- Looks up applicable statutes for user's jurisdiction (IN/US/GB/CA/AU)
- Uses `generate_with_grounding()` — every cited law is verified against real sources
- Sources: indiankanoon.org, legislative.gov.in, congress.gov, legislation.gov.uk
- Returns `ResearchData` with confidence score based on grounding hits

---

### 4. `arbiter/backend/agents/drafting_agent.py`
**DraftingAgent** — Gemini streaming generation for legal document creation.
- Generates demand letters, RTI applications, consumer complaints, cease & desist
- Every legal claim cites a specific act and section number
- Supports English and Hindi (`detect_language()` → Hindi system prompt)
- `stream_draft()` streams tokens live to frontend

---

### 5. `arbiter/backend/agents/tracking_agent.py`
**TrackingAgent** — Gemini for deadline analysis and follow-up strategy.
- Analyzes case urgency
- Generates follow-up message templates
- Sets Firestore reminders via `schedule_deadlines()`

---

### 6. `arbiter/backend/api/chat.py`
**Chat API** — Main user-facing AI conversation endpoint.
- 3-layer jailbreak defense
- Identity lock: "I am Arbiter" — never reveals Gemini/Google
- Country-aware system prompt: injects jurisdiction-specific laws
- Calls `enhance_if_needed()` before every intake message
- Multi-turn history passed to Gemini on every turn

---

### 7. `arbiter/backend/core/prompt_enhancer.py`
**Prompt Enhancer** — Gemini pre-processes raw casual user messages.
- Raw: "my landlord wont give me deposit back its been 6 months"
- Enhanced: "I am seeking legal remedies for wrongful retention of security deposit by landlord for 6 months. Applicable statutes: Tenancy Act s.X, Consumer Protection Act s.Y."

---

### 8. `arbiter/backend/services/legal_update_service.py`
**Legal Update Service** — Gemini + Google Search grounding, weekly scheduled.
- Fetches new legislation, judgments, regulations per country
- Uses Google Search grounding to verify recency
- Triggered by Cloud Scheduler every Monday

---

### 9. `arbiter/backend/services/case_showcase_service.py`
**Case Showcase Service** — Gemini curates interesting public cases.
- Identifies landmark judgments and instructive cases per country
- Extracts legal lessons for public display
- Powered by Gemini + Google Search grounding

---

## Total Gemini Calls in a Typical User Journey

```
User describes problem
  → Prompt Enhancement (1 Gemini call)
  → IntakeAgent follow-up questions (2–4 Gemini calls)
  → ResearchAgent legal lookup (1 Gemini call + grounding)
  → DraftingAgent document creation (1 streaming Gemini call)
  → TrackingAgent deadline analysis (1 Gemini call)
─────────────────────────────────────────────────────
  Total: 6–8 Gemini API calls per document generated
```

---

## Gemini-Specific Features Used

- ✅ **Google Search Grounding** — real-time statute verification
- ✅ **Streaming generation** — live document drafting
- ✅ **Structured JSON output** — schema-validated agent responses
- ✅ **Multi-turn chat** — conversational intake flow
- ✅ **System prompts** — jurisdiction-aware legal AI persona
- ✅ **Grounding confidence scores** — legal citation quality metric

---

*Arbiter is an XPRIZE "Build with Gemini 2026" submission.*  
*Every AI-powered feature in this product is built on Google Gemini 2.0 Pro.*
