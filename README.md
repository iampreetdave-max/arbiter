<div align="center">

# ⚖️ Arbiter

### AI-powered legal agent for everyday people

[![Built with Google Gemini](https://img.shields.io/badge/Built%20with-Google%20Gemini%202.0%20Pro-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com/)
[![XPRIZE Build with Gemini](https://img.shields.io/badge/XPRIZE-Build%20with%20Gemini-orange?style=for-the-badge)](https://xprize.devpost.com/)
[![Google ADK](https://img.shields.io/badge/Framework-Google%20ADK-34A853?style=for-the-badge&logo=google&logoColor=white)](https://google.github.io/adk-docs/)
[![Cloud Run](https://img.shields.io/badge/Deploy-Google%20Cloud%20Run-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/run)

> Demand letters, rights guidance & court filings in minutes — not thousands in lawyer fees.  
> **India · United States · United Kingdom · Canada · Australia**

</div>

> **XPRIZE Build with Gemini 2026** — Professional Services Access category  
> AI-powered demand letters, RTI applications, and consumer complaints — drafted in 30 minutes, not weeks.

[![Built with Gemini](https://img.shields.io/badge/Built%20with-Google%20Gemini-blue)](https://aistudio.google.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)](https://fastapi.tiangolo.com)

---

## 🎯 What Arbiter Does

Arbiter is an AI legal agent that helps working-class Indians resolve disputes without paying ₹5,000–₹50,000 in lawyer fees.

1. **Listen** — User describes their problem in plain English or Hindi
2. **Research** — Gemini agents look up applicable Indian laws in real time (IPC, CPC, Consumer Protection Act, Tenancy laws, Labour codes)
3. **Draft** — Generates demand letters, RTI applications, consumer court complaints, cease & desist notices with legal citations
4. **Pay** — ₹299 per document, ₹799/month unlimited

---

## 🤖 AI Stack — Powered by Google Gemini

| Component | Technology |
|---|---|
| **Core AI Model** | Google Gemini 2.0 Pro (`gemini-2.0-pro-exp`) |
| **Agent Framework** | Google Agent Development Kit (ADK) |
| **Search Grounding** | Google Search via Gemini grounding API |
| **Legal Research** | Gemini + real-time Google Search |
| **Document Drafting** | Gemini streaming generation |
| **Prompt Enhancement** | Gemini pre-processing pipeline |
| **Weekly Updates** | Gemini + Google Search grounding |
| **Deployment** | Google Cloud Run (asia-south1) |
| **Database** | Google Firebase Firestore |
| **File Storage** | Google Cloud Storage |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **AI Core** | Google Gemini 2.0 Pro API |
| **Agent Framework** | Google Agent Development Kit (ADK) |
| **Backend** | Python 3.11 + FastAPI |
| **Frontend** | Next.js 14 + TypeScript + Tailwind CSS |
| **Database** | Firebase Firestore |
| **Auth** | Firebase Authentication |
| **Storage** | Google Cloud Storage (PDFs) |
| **Payments** | Razorpay |
| **Deployment** | Google Cloud Run |

---

## 📁 Project Structure

```
HACKATHON/
├── arbiter/
│   ├── backend/               ← FastAPI + Gemini agents
│   │   ├── agents/            ← intake, research, drafting, tracking
│   │   ├── api/               ← cases, documents, payments, chat
│   │   ├── core/              ← config, security
│   │   ├── models/            ← Pydantic models
│   │   ├── services/          ← Gemini, Firebase, Razorpay, GCS
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── frontend/              ← Next.js 14 app
│   │   ├── app/               ← App Router pages
│   │   │   ├── (auth)/        ← sign-in, sign-up
│   │   │   ├── (app)/         ← protected pages (cases dashboard, chat, detail)
│   │   │   └── page.tsx       ← landing page
│   │   ├── components/        ← UI, auth, chat, cases
│   │   ├── contexts/          ← AuthContext
│   │   ├── lib/               ← firebase.ts, api.ts, constants.ts
│   │   └── Dockerfile
│   └── tests/                 ← pytest test suite
├── infrastructure/
│   ├── cloudbuild.yaml        ← Cloud Run CI/CD
│   ├── docker-compose.yml     ← Local dev
│   └── firestore.rules
└── docs/
    ├── ARCHITECTURE.md
    └── PROGRESS.md
```

---

## ⚡ Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- Accounts: Firebase, GCP, Razorpay, Gemini API key

### 1. Clone and set up env files

```bash
git clone https://github.com/iampreetdave-max/arbiter.git
cd arbiter

# Backend
cp arbiter/backend/.env.example arbiter/backend/.env
# Edit arbiter/backend/.env and fill in your keys

# Frontend
cp arbiter/frontend/.env.local.example arbiter/frontend/.env.local
# Edit arbiter/frontend/.env.local and fill in your keys
```

### 2. Run backend

```bash
cd arbiter/backend
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs (Swagger UI)
```

### 3. Run frontend

```bash
cd arbiter/frontend
npm install
npm run dev
# → http://localhost:3000
```

### 4. Or run both with Docker Compose

```bash
cd infrastructure
docker compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## 🔑 Required Environment Variables

### Backend (`arbiter/backend/.env`)

| Variable | Where to get it |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `GOOGLE_CLOUD_PROJECT` | https://console.cloud.google.com |
| `FIREBASE_PROJECT_ID` | Firebase Console → Project Settings |
| `RAZORPAY_KEY_ID` | https://dashboard.razorpay.com |
| `RAZORPAY_KEY_SECRET` | https://dashboard.razorpay.com |
| `GCS_BUCKET_NAME` | Create bucket: `arbiter-documents` |

### Frontend (`arbiter/frontend/.env.local`)

| Variable | Where to get it |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` (dev) or Cloud Run URL (prod) |
| `NEXT_PUBLIC_FIREBASE_*` | Firebase Console → Project Settings → Your apps |
| `NEXT_PUBLIC_RAZORPAY_KEY_ID` | Razorpay Dashboard (test key for dev) |

---

## 🧪 Running Tests

```bash
# Agent tests
cd HACKATHON
pytest arbiter/tests/test_agents.py -v

# API route tests
pytest arbiter/tests/test_api.py -v

# All tests
pytest arbiter/tests/ -v
```

---

## 🚀 Deploying to Google Cloud Run

```bash
# Build and deploy backend
gcloud run deploy arbiter-backend \
  --source arbiter/backend \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=xxx,FIREBASE_PROJECT_ID=xxx,...

# Build and deploy frontend
gcloud run deploy arbiter-frontend \
  --source arbiter/frontend \
  --region asia-south1 \
  --allow-unauthenticated
```

---

## 📋 Document Types

| Type | Use Case |
|---|---|
| Demand Letter | Unpaid deposits, salary dues, debt recovery |
| Legal Notice | Formal notice before litigation |
| RTI Application | Government information requests |
| Consumer Complaint | E-commerce fraud, defective products |
| Cease & Desist | Harassment, illegal activity |
| Employment Complaint | Labour court, wrongful termination |

---

## ⚖️ Legal Disclaimer

Arbiter generates AI-powered legal documents for informational and self-help purposes only. This is **not legal advice** and does not create an attorney-client relationship. Always review documents before sending. For complex matters, consult a qualified lawyer.

---

## 🏆 Hackathon

**Competition:** XPRIZE Build with Gemini 2026  
**Category:** Professional Services Access ($50K category)  
**Submission Deadline:** August 17, 2026  
**Builder:** iampreetdave-max (India)  
**Devpost:** https://xprize.devpost.com/

---

*Built with ❤️ for everyday Indians who deserve access to justice.*  
*Powered by Google Gemini API + Google Cloud.*
