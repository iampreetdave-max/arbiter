# VERIFICATION PROTOCOL
# Used by the Verifier subagent after every coding session.

## HOW TO RUN
You are the Verifier Agent. Read HANDOFF.md to get files modified this session.
Run ALL checks below on those files.

---

## CHECKLIST

### 🐍 Python Files (.py)
- [ ] No syntax errors
- [ ] All imports reference modules that exist (internal: verify file exists; third-party: verify in requirements.txt)
- [ ] No hardcoded API keys, passwords, tokens
- [ ] All functions/classes have docstrings
- [ ] Environment variables via os.getenv() or config.py
- [ ] No print() in production code (use logging)
- [ ] Pydantic models for all request/response schemas
- [ ] Async functions use await correctly

### 📘 TypeScript/TSX Files
- [ ] All imported components/functions exist
- [ ] No `any` types without explanation comment
- [ ] API calls use typed client in frontend/lib/api.ts
- [ ] No hardcoded API URLs

### 📄 All Files
- [ ] No .env with real secrets
- [ ] No duplicate logic
- [ ] TODOs tracked in docs/PROGRESS.md
- [ ] File location matches CLAUDE.md structure

### 🏗️ Architecture Compliance
- [ ] Agents → arbiter/backend/agents/
- [ ] API routes → arbiter/backend/api/
- [ ] Services → arbiter/backend/services/
- [ ] Models → arbiter/backend/models/
- [ ] Pages → arbiter/frontend/app/
- [ ] Components → arbiter/frontend/components/

### 🔗 Cross-File Integrity
- [ ] If A imports from B, B exists and exports what A needs
- [ ] API routes reference services that exist
- [ ] Agent prompts are coherent

---

## OUTPUT FORMAT

Pass: `✅ VERIFICATION PASSED — Files checked: [...] All checks clean.`

Fail: `❌ VERIFICATION FAILED — Issues: 1. file:line — description`

## RULES
- Be STRICT. Don't pass broken code.
- Be SPECIFIC. file:line references required.
- Mark unverifiable items as UNVERIFIABLE.
