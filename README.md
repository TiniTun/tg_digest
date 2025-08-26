# 📬 Telegram Digest Generator

This project automatically collects messages from Telegram channels, groups them by topics, summarizes them using GPT, and sends a daily digest to a Telegram chat.

It is deployed as a FastAPI application on Google Cloud Run and triggered by Cloud Scheduler.

---

## 🔧 Features

- ✅ Fetch messages from multiple Telegram channels
- ✅ Group by predefined topics (e.g., technology, news)
- ✅ Topic-wise summarization with GPT-4o
- ✅ Caching in Google Cloud Storage
- ✅ Deployment on Cloud Run and triggering via Cloud Scheduler
- ✅ Local debugging and Telegram authorization via Telethon

---

## 🧱 Project Structure
```
telegram_digest/
├── app/
│ ├── main.py # FastAPI app
│ ├── authorize.py # One-time Telegram authorization
│ ├── config.py # Loads environment variables
│ ├── digest_pipeline.py # Main logic
├── .env # local secrets (do not commit)
├── Dockerfile
├── requirements.txt
└── README.md
```
---

## 🚀 Quick Start (Locally)

```bash
git clone https://github.com/TiniTun/tg_digest.git
cd tg_digest
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r dev-requirements.txt  # tooling
```

### 🔑 Telegram Authorization

```bash
python app/authorize.py
```

### ▶️ Run Locally

```bash
uvicorn app.main:app --reload
```

### 🔁 Environments (dev/prod)

The app switches Telegram session source by `APP_ENV`:

- `APP_ENV=dev` (default): use local `digest_session.session` file.
- `APP_ENV=prod`: download `digest_session.session` from GCS on startup.

Usage:

```bash
export APP_ENV=dev   # or prod
uvicorn app.main:app --reload
```

### 🧹 Lint & Format (Ruff)

Install tooling if not yet installed:

```bash
pip install -r dev-requirements.txt
```

Run Ruff (lint + fix imports + format):

```bash
# Check only
ruff check .

# Auto-fix issues where safe
ruff check . --fix

# Format code (Black-compatible formatter in Ruff)
ruff format .
```

Ruff is configured via `pyproject.toml`.

---

## ☁️ Deploy to Cloud Run

```bash
gcloud run deploy telegram-digest \\
  --source . \\
  --region asia-southeast1 \\
  --allow-unauthenticated \\
  --memory=2Gi \\
  --set-secrets TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest \\
  --set-secrets TELEGRAM_CHAT_ID=TELEGRAM_CHAT_ID:latest \\
  --set-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest \\
  --set-secrets API_ID=API_ID:latest \\
  --set-secrets API_HASH=API_HASH:latest \\
  --set-secrets GCS_BUCKET_NAME=GCS_BUCKET_NAME:latest
```

---

## 🔄 CI/CD: GitHub Actions → Cloud Run (via Workload Identity Federation)

Follow these steps once per project to enable deploys from GitHub Actions without storing long‑lived keys.

### 1) Enable required APIs

```bash
gcloud services enable iam.googleapis.com iamcredentials.googleapis.com run.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com
```

### 2) Create a deploy Service Account

```bash
gcloud iam service-accounts create github-cloud-run-deployer \
  --display-name="GitHub Cloud Run Deployer"

SA_EMAIL="github-cloud-run-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# Minimal roles for deploy + access to secrets and GCS session file
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/run.admin"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/storage.objectViewer"
```

### 3) Configure Workload Identity Federation for GitHub

```bash
POOL_ID="github-pool"
PROVIDER_ID="github-provider"
REPO="TiniTun/tg_digest"  # change to your repo

gcloud iam workload-identity-pools create "$POOL_ID" \
  --project="$PROJECT_ID" --location="global" \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
  --project="$PROJECT_ID" --location="global" \
  --workload-identity-pool="$POOL_ID" \
  --display-name="GitHub OIDC" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  --issuer-uri="https://token.actions.githubusercontent.com"

PROVIDER_RESOURCE="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"

# Allow the GitHub repo to impersonate the SA (limit to main branch)
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${REPO}"
```

If you want to restrict to a branch, add condition in the workflow or map `attribute.ref` and use a more specific member with conditions.

### 4) Set GitHub repository variables and secrets

- Variables (Repository → Settings → Variables → Actions):
  - `GCP_PROJECT_ID`: your GCP project ID
  - `GCP_REGION`: e.g. `asia-southeast1`
  - `CLOUD_RUN_SERVICE`: e.g. `telegram-digest`

- Secrets (Repository → Settings → Secrets → Actions):
  - `GCP_WORKLOAD_IDENTITY_PROVIDER`: value of `${PROVIDER_RESOURCE}`
  - `GCP_SERVICE_ACCOUNT_EMAIL`: value of `${SA_EMAIL}`

### 5) Workflow

This repo includes a workflow at `.github/workflows/deploy.yml` that:

1. Authenticates to GCP via WIF
2. Sets gcloud defaults
3. Runs the deploy command identical to manual one above

Trigger: push to `main` or manual dispatch.

### 6) Secrets in Cloud Run

Create the following GCP Secret Manager secrets with latest versions:

```bash
for S in TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID OPENAI_API_KEY API_ID API_HASH GCS_BUCKET_NAME; do
  echo "<value>" | gcloud secrets create "$S" --data-file=- || \
  echo "Secret $S already exists";
done
```

The workflow uses `--set-secrets` to mount them into environment variables inside the service.

---

## 📦 Technologies Used

[FastAPI](https://fastapi.tiangolo.com/)

[Telethon](https://github.com/LonamiWebs/Telethon)

[SentenceTransformers](https://www.sbert.net/)

[OpenAI GPT-4o](https://platform.openai.com/docs/)

[Google Cloud Run](https://cloud.google.com/run)

[Google Cloud Storage](https://cloud.google.com/storage)

[Cloud Scheduler](https://cloud.google.com/scheduler)

---

## 📄 License

MIT — feel free to use and adapt for your own projects.
