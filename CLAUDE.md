# CLAUDE.md — Arbiter Project Bible
> This file is the single source of truth for Claude. Read this FIRST every session before doing anything.

---

## 🚨 MANDATORY RULES — NEVER SKIP THESE

1. **READ HANDOFF.md FIRST** — Before every single response, read `HANDOFF.md` to know the current state. Never assume. Always verify.
2. **UPDATE HANDOFF.md LAST** — After every response where code was written or decisions made — update `HANDOFF.md`. No exceptions.
3. **NO HALLUCINATIONS** — If unsure about a file, function, API, or decision — READ the file first. Never invent code referencing things you haven't verified exist.
4. **CHECK BEFORE CREATING** — Always check if a file/function/module already exists before creating. Use Glob/Grep to verify.
5. **ONE TECH DECISION AT A TIME** — Never change the tech stack without updating ARCHITECTURE.md and flagging it in HANDOFF.md.
6. **REAL CODE ONLY** — No placeholder code, no untracked TODOs, no fake implementations.
7. **ALWAYS PARALLELIZE** — Never do sequentially what can be done in parallel. Use subagents aggressively.
8. **ALWAYS VERIFY + GIT** — After every coding session, ALWAYS spawn a Verifier Agent AND a Git Agent (see Parallel Working section below).

---

## ⚡ PARALLEL WORKING — MANDATORY

### The Golden Rule
**If two tasks don't depend on each other → they run in parallel via subagents. Always.**

### When to ALWAYS Parallelize

| Situation | Parallel Pattern |
|---|---|
| Writing a module + its tests | Agent 1: code, Agent 2: tests — simultaneously |
| Writing multiple independent files | One agent per file — simultaneously |
| Backend feature + docs update | Agent 1: code, Agent 2: update PROGRESS.md — simultaneously |
| Any 2+ independent subtasks | Identify dependencies → parallelize everything that's independent |

### Standard Session Ending — ALWAYS Run These 2 in Parallel

After EVERY session where ANY code was written, ALWAYS spawn these two agents simultaneously:

#### 🔍 Agent: VERIFIER
```
subagent_type: Explore
description: "Verify files written this session"
prompt: |
  Read HANDOFF.md to get the list of files written/modified this session.
  Then read each of those files and run the full checklist in .claude/VERIFICATION_PROTOCOL.md.
  Report either VERIFICATION PASSED or ISSUES FOUND with file:line specifics.
```

#### 🚀 Agent: GIT PUSHER
```
subagent_type: general-purpose
description: "Commit and push changes to GitHub"
prompt: |
  You are the Git Agent for the Arbiter project.
  Repo: https://github.com/iampreetdave-max/arbiter
  Working directory: C:\Users\PREET\OneDrive\Desktop\HACKATHON
  
  Use the GitHub MCP tool (mcp__github-personal__push_files) to push all changed files.
  Owner: iampreetdave-max | Repo: arbiter | Branch: main
  
  Steps:
  1. Read HANDOFF.md to know which files changed this session
  2. Read each changed file
  3. Push all using mcp__github-personal__push_files in one commit
  4. Commit message format: "feat: <what was built> — Arbiter XPRIZE"
  5. Report: PUSHED commit with list of files
```

**These two agents run IN PARALLEL. Launch both simultaneously. Wait for both results before updating HANDOFF.md.**

### Parallel Code Writing Pattern

```
Step 1 — PLAN: Identify all files needed. Map dependencies.
Step 2 — PARALLELIZE: Spawn one agent per independent file simultaneously.
Step 3 — VERIFY: Spawn Verifier Agent.
Step 4 — PUSH: Spawn Git Agent (uses GitHub MCP).
Step 5 — UPDATE: Claude updates HANDOFF.md and PROGRESS.md.
```

### Example: Building IntakeAgent

✅ RIGHT:
```
Simultaneously:
  Agent 1 → Write intake_agent.py
  Agent 2 → Write test_intake.py
  Agent 3 → Update PROGRESS.md
Wait for all 3 →
Simultaneously:
  Agent 4 (Verifier) → Check all files
  Agent 5 (Git MCP)  → Commit and push
Wait for both → Claude updates HANDOFF.md
```

---

## 🏆 Project Overview

**Name:** Arbiter  
**GitHub:** https://github.com/iampreetdave-max/arbiter  
**Tagline:** AI-powered legal agent for everyday people — demand letters, rights guidance & court filings in minutes, not thousands in lawyer fees.  
**Hackathon:** Build with Gemini XPRIZE ($2M prize pool)  
**Category:** Professional Services Access ($50K category prize)  
**Submission Deadline:** August 17, 2026 @ 11:30 PM IST  
**Finals:** September 25, 2026 — Los Angeles (live)  
**Devpost:** https://xprize.devpost.com/  
**Builder:** iampreetdave-max (India — fully eligible)

---

## 🎯 What Arbiter Does

1. **Listens** — User describes problem in plain English or Hindi
2. **Researches** — Gemini agents look up Indian laws (IPC, CPC, Consumer Protection Act, Tenancy, Labour law)
3. **Drafts** — Generates demand letters, RTI applications, consumer court complaints, cease & desist
4. **Tracks** — Deadline reminders, follow-up scheduling
5. **Escalates** — Refers complex cases to verified pro-bono lawyers

**Target Users:** Working-class Indians who can't afford lawyers (₹5K–₹50K/consultation)  
**Pricing:** ₹299 per document OR ₹799/month unlimited  
**Payment:** Razorpay  

---

## 🛠️ Tech Stack — LOCKED

| Layer | Technology | Why |
|---|---|---|
| **AI Core** | Google Gemini 2.0 Pro API | Required by hackathon, best reasoning |
| **Agent Framework** | Google Agent Development Kit (ADK) | Official Google agents |
| **Backend** | Python 3.11 + FastAPI | Fast, async, great for agents |
| **Frontend** | Next.js 14 + TypeScript + Tailwind CSS | Fast to build, modern |
| **Database** | Firebase Firestore | Real-time, free tier, easy auth |
| **File Storage** | Google Cloud Storage | Required Google Cloud product |
| **Auth** | Firebase Authentication | Email + Google OAuth |
| **Payments** | Razorpay | India-native, easy integration |
| **Deployment** | Google Cloud Run | Serverless, auto-scales |
| **Legal DB** | Vertex AI Search | Search Indian statutes & judgements |
| **Monitoring** | Google Cloud Logging | Agent execution logs for submission |

---

## 📁 Project Structure

```
HACKATHON/
├── CLAUDE.md
├── HANDOFF.md
├── README.md
├── .gitignore
├── .claude/
│   ├── settings.json
│   ├── VERIFICATION_PROTOCOL.md
│   └── hooks/
│       ├── stop_guard.ps1
│       ├── post_write.ps1
│       └── git_verify.ps1
├── docs/
│   ├── ARCHITECTURE.md
│   └── PROGRESS.md
└── arbiter/
    ├── backend/
    │   ├── main.py
    │   ├── agents/
    │   │   ├── intake_agent.py
    │   │   ├── research_agent.py
    │   │   ├── drafting_agent.py
    │   │   └── tracking_agent.py
    │   ├── api/
    │   │   ├── cases.py
    │   │   ├── documents.py
    │   │   └── payments.py
    │   ├── core/
    │   │   ├── config.py
    │   │   └── security.py
    │   ├── models/
    │   │   ├── case.py
    │   │   └── document.py
    │   └── services/
    │       ├── gemini_service.py
    │       ├── firebase_service.py
    │       ├── razorpay_service.py
    │       └── storage_service.py
    ├── frontend/
    │   ├── app/
    │   ├── components/
    │   └── lib/
    ├── infrastructure/
    └── tests/
```

---

## 🔑 Environment Variables (NEVER hardcode)

```
GEMINI_API_KEY=
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_REGION=asia-south1
FIREBASE_PROJECT_ID=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
GCS_BUCKET_NAME=arbiter-documents
VERTEX_AI_SEARCH_ID=
```

---

## 📋 Hackathon Submission Checklist

- [ ] GitHub repo shared with testing@devpost.com AND judging@hacker.fund
- [ ] 3-min video (YouTube/Vimeo) showing AI running in production
- [ ] Written narrative 500–1000 words
- [ ] Revenue evidence (Razorpay export)
- [ ] Expense documentation
- [ ] Agent execution logs (Cloud Logging screenshots)
- [ ] Customer evidence (name, email, phone, testimonial)
- [ ] Category selected: Professional Services Access

---

## 🧠 Key Decisions

1. India-first — Hindi support, Razorpay, Indian law focus
2. Document drafting ONLY — not legal advice
3. Disclaimer on every output
4. Grounded generation — every claim must cite a statute/section
5. WhatsApp integration — Phase 2
6. GitHub MCP used for all pushes (not local git CLI)

---

## ⚠️ What Claude Must NEVER Do

- Change tech stack without user approval + ARCHITECTURE.md update
- Commit API keys or secrets
- Create duplicate files without checking first
- Write placeholder code without tracking in PROGRESS.md
- Skip HANDOFF.md update after coding
- Invent library APIs — always verify against existing code or docs
- Push directly via git CLI — always use GitHub MCP tool
