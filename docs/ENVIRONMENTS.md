# Arbiter — Environment Setup Guide

## Overview

Arbiter runs in three environments:

| Environment | Branch   | Trigger          | Firebase Project     | Cloud Run Service     |
|-------------|----------|------------------|----------------------|-----------------------|
| Development | any      | Local            | arbiter-dev          | localhost             |
| Staging     | develop  | Push to develop  | arbiter-staging      | arbiter-backend-staging |
| Production  | main (tag) | Push v*.*.* tag | arbiter-prod         | arbiter-backend       |

---

## Development Setup

### Backend
```bash
cd arbiter/backend
cp .env.example .env
# Edit .env with your credentials
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd arbiter/frontend
cp .env.example .env.local
# Edit .env.local with your credentials
npm install
npm run dev
```

---

## GitHub Secrets Required

### Shared secrets
| Secret | Description |
|--------|-------------|
| `GEMINI_API_KEY_TEST` | Gemini key for CI (can be test key) |

### Staging secrets (`GCP_PROJECT_ID_STAGING`, etc.)
| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID_STAGING` | GCP project ID for staging |
| `GCP_SA_KEY_STAGING` | Service account JSON (base64) for staging deployment |
| `FIREBASE_API_KEY_STAGING` | Firebase web API key (staging project) |
| `FIREBASE_AUTH_DOMAIN_STAGING` | Firebase auth domain (staging) |
| `FIREBASE_PROJECT_ID_STAGING` | Firebase project ID (staging) |
| `FIREBASE_STORAGE_BUCKET_STAGING` | Firebase storage bucket (staging) |
| `FIREBASE_SENDER_ID_STAGING` | Firebase messaging sender ID (staging) |
| `FIREBASE_APP_ID_STAGING` | Firebase app ID (staging) |
| `RAZORPAY_KEY_ID_STAGING` | Razorpay test key (staging) |

### Production secrets
Same as staging but with `_PROD` suffix. Use live Razorpay keys for production.

---

## Environment Strategy

### What differs between environments:

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| Firebase project | arbiter-dev | arbiter-staging | arbiter-prod |
| Razorpay keys | rzp_test_* | rzp_test_* | rzp_live_* |
| ENVIRONMENT var | development | staging | production |
| Min Cloud Run instances | N/A | 0 | 1 (always warm) |
| Max Cloud Run instances | N/A | 5 | 20 |
| Memory | N/A | 1Gi | 2Gi |
| Rate limits | relaxed | normal | normal |
| Sentry | disabled | enabled | enabled |
| Prompt enhancement | optional | enabled | enabled |
| Weekly updates | disabled | enabled | enabled |
| API docs (/docs) | visible | hidden | hidden |

---

## How to Deploy to Staging

1. Work on a feature branch
2. Push to `develop` branch (or merge PR into develop)
3. GitHub Actions automatically builds and deploys to staging
4. Test at the staging URL posted in the PR comment

## How to Deploy to Production

1. Ensure staging is tested and working
2. Create a version tag: `git tag v1.2.0 && git push origin v1.2.0`
3. GitHub Actions opens a manual approval gate (via GitHub Environments)
4. Approve the deployment in GitHub → Actions
5. Production deploys automatically

---

## Cloud Scheduler (Weekly Content Refresh)

Set up weekly content refresh in Google Cloud Scheduler:

```bash
# Create weekly legal updates job (every Monday 6 AM IST = 00:30 UTC)
gcloud scheduler jobs create http arbiter-legal-updates-refresh \
  --location=asia-south1 \
  --schedule="30 0 * * 1" \
  --uri="https://your-backend-url/api/admin/content/legal-updates/refresh" \
  --http-method=POST \
  --headers="X-Admin-Key=YOUR_ADMIN_SECRET_KEY" \
  --time-zone="Asia/Kolkata"

# Create weekly public cases refresh (every Monday 7 AM IST)
gcloud scheduler jobs create http arbiter-cases-refresh \
  --location=asia-south1 \
  --schedule="30 1 * * 1" \
  --uri="https://your-backend-url/api/admin/content/public-cases/refresh" \
  --http-method=POST \
  --headers="X-Admin-Key=YOUR_ADMIN_SECRET_KEY" \
  --time-zone="Asia/Kolkata"
```

---

## Firestore Security Rules

Staging and production use separate Firebase projects, so Firestore rules
are deployed independently to each. See `infrastructure/firestore.rules`.

```bash
# Deploy rules to staging
firebase use arbiter-staging
firebase deploy --only firestore:rules

# Deploy rules to production
firebase use arbiter-prod
firebase deploy --only firestore:rules
```
