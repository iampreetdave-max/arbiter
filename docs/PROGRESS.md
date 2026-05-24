# PROGRESS.md — Arbiter Build Tracker
> Update whenever a feature is started, completed, or blocked.

---

## 🗓️ Timeline

| Week | Dates | Goal | Status |
|---|---|---|---|
| Week 1 | May 24–31 | Framework + Backend skeleton + Core agents | 🔨 In Progress |
| Week 2 | Jun 1–7 | Document generation end-to-end | ⬜ |
| Week 3 | Jun 8–14 | Frontend + Auth + Payments | ⬜ |
| Week 4 | Jun 15–21 | Deploy Cloud Run, first 5 free users | ⬜ |
| Week 5 | Jun 22–28 | First 5 PAYING customers | ⬜ |
| Week 6 | Jun 29–Jul 5 | 15 paying customers + testimonials | ⬜ |
| Week 7 | Jul 6–12 | 30 paying customers + Hindi intake | ⬜ |
| Week 8 | Jul 13–19 | WhatsApp integration | ⬜ |
| Week 9 | Jul 20–26 | 50+ customers + agent log collection | ⬜ |
| Week 10 | Jul 27–Aug 2 | Polish + submission prep | ⬜ |
| Week 11 | Aug 3–9 | Record demo video | ⬜ |
| Week 12 | Aug 10–17 | Final submission | ⬜ |

---

## 📦 Feature Tracker

### Phase 1 — Backend MVP
| Feature | File | Status |
|---|---|---|
| FastAPI skeleton | `backend/main.py` | ⬜ |
| Config management | `backend/core/config.py` | ⬜ |
| Firebase connection | `backend/services/firebase_service.py` | ⬜ |
| Gemini client | `backend/services/gemini_service.py` | ⬜ |
| IntakeAgent | `backend/agents/intake_agent.py` | ⬜ |
| ResearchAgent | `backend/agents/research_agent.py` | ⬜ |
| DraftingAgent | `backend/agents/drafting_agent.py` | ⬜ |
| TrackingAgent | `backend/agents/tracking_agent.py` | ⬜ |
| Case API routes | `backend/api/cases.py` | ⬜ |
| Document API routes | `backend/api/documents.py` | ⬜ |
| Razorpay service | `backend/services/razorpay_service.py` | ⬜ |
| GCS storage service | `backend/services/storage_service.py` | ⬜ |
| Pydantic models | `backend/models/` | ⬜ |
| Unit tests | `arbiter/tests/` | ⬜ |

### Phase 2 — Frontend
| Feature | File | Status |
|---|---|---|
| App shell | `frontend/app/layout.tsx` | ⬜ |
| Landing page | `frontend/app/page.tsx` | ⬜ |
| Auth pages | `frontend/app/auth/` | ⬜ |
| Dashboard | `frontend/app/dashboard/` | ⬜ |
| Case intake flow | `frontend/app/case/new/` | ⬜ |
| Document viewer | `frontend/app/document/[id]/` | ⬜ |
| Payment flow | `frontend/app/payment/` | ⬜ |
| API client | `frontend/lib/api.ts` | ⬜ |

### Phase 3 — Infrastructure
| Feature | Status |
|---|---|
| Cloud Run Dockerfiles | ⬜ |
| Cloud Build CI/CD | ⬜ |
| Firestore rules | ⬜ |
| GCS bucket | ⬜ |

### Phase 4 — Customers
| Milestone | Status |
|---|---|
| Landing page live | ⬜ |
| First free user | ⬜ |
| First paying user | ⬜ |
| 10 paying users | ⬜ |
| 30 paying users | ⬜ |

---

## 🐛 Known Issues
*(none yet)*

---

## 💰 Revenue Tracker
| Date | Customers | MRR (₹) | Notes |
|---|---|---|---|
| May 24 | 0 | 0 | Project start |

---

## 📝 Submission Evidence
| Evidence | Collected |
|---|---|
| Agent execution logs | ❌ |
| Razorpay revenue export | ❌ |
| Customer testimonials | ❌ |
| Customer contact info | ❌ |
| Demo video | ❌ |
| Written narrative | ❌ |
