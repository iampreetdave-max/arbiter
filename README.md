# Arbiter ⚖️
> AI-powered legal agent for everyday people. Demand letters, rights guidance & court filings in minutes — not thousands in lawyer fees.

## 🏆 XPRIZE Hackathon Submission
**Competition:** [Build with Gemini XPRIZE](https://xprize.devpost.com/) — $2,000,000 prize pool  
**Category:** Professional Services Access  
**Deadline:** August 17, 2026  

## 🎯 What Arbiter Does
Arbiter is a fully AI-operated legal agent that helps everyday Indians who can't afford lawyers:

1. **Listens** — Describe your problem in plain English or Hindi
2. **Researches** — AI looks up applicable Indian laws in real-time
3. **Drafts** — Generates demand letters, RTI applications, consumer court complaints
4. **Tracks** — Sets deadlines and follows up automatically
5. **Escalates** — Refers complex cases to verified pro-bono lawyers

## 💰 Pricing
- ₹299 per document
- ₹799/month unlimited

## 🛠️ Tech Stack
- **AI:** Google Gemini 2.0 Pro + Google Agent Development Kit (ADK)
- **Backend:** Python 3.11 + FastAPI on Google Cloud Run
- **Database:** Firebase Firestore + Google Cloud Storage
- **Auth:** Firebase Authentication
- **Payments:** Razorpay
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Cloud account with Gemini API enabled
- Firebase project
- Razorpay account

### Backend Setup
```bash
cd arbiter/backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env   # Fill in your keys
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd arbiter/frontend
npm install
cp .env.local.example .env.local  # Fill in your keys
npm run dev
```

## 📁 Project Structure
```
arbiter/
├── backend/          # Python FastAPI + Gemini agents
│   ├── agents/       # AI agent pipeline
│   ├── api/          # REST endpoints
│   ├── core/         # Config + security
│   ├── models/       # Pydantic models
│   └── services/     # Gemini, Firebase, Razorpay
├── frontend/         # Next.js app
└── infrastructure/   # Google Cloud configs
```

## 🤝 For Judges
- **GitHub access:** Repo is public
- **Demo:** [Coming soon]
- **Category:** Professional Services Access

---
*Built with ❤️ for the Build with Gemini XPRIZE hackathon*  
*Powered by Google Gemini API + Google Cloud*
