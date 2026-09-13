# 🎙️ Aicalling: Enterprise AI Voice Agent SaaS Platform

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Platform: Production-Ready](https://img.shields.io/badge/Platform-Production--Ready-brightgreen)](https://github.com/your-repo)
[![Security: Hardened](https://img.shields.io/badge/Security-Hardened-blue)](https://github.com/your-repo)
[![OWASP: Verified](https://img.shields.io/badge/OWASP-API--10--Compliant-success)](https://owasp.org)

A production-grade, multi-tenant SaaS platform enabling businesses to deploy autonomous AI voice employees. Aicalling delivers sub-500ms voice latency, real-time knowledge retrieval (RAG), secure tool[...]

---

## 🏗️ System Architecture

The platform utilizes a **Zero-Transcode Passthrough** architecture to minimize latency, bridging the gap between telephony providers and cutting-edge Realtime AI models.

### Core Voice Pipeline
`Caller (Phone)` $\rightarrow$ `Twilio Voice Network` $\rightarrow$ `VoiceBridge (FastAPI WebSockets)` $\rightarrow$ `OpenAI Realtime API`

### Key Technical Highlights
* **Ultra-Low Latency:** Direct audio passthrough of G.711 $\mu$-law frames eliminates transcoding overhead.
* **Intelligent Barge-In:** Native interruption handling that truncates AI audio in real-time when user speech is detected.
* **Usage Enforcement:** Real-time monitoring and enforcement of monthly voice minute limits per tenant.
* **Secure Tool Pipeline:** Rigorous execution pipeline with verified caller identity and strict tenant context.
* **Authoritative RAG:** Integrated `pgvector` similarity search with SSRF-protected document ingestion.
* **Async Background Workers:** Distributed Celery worker tier handling post-call analysis, document embeddings, and campaign dialing out-of-band.

### 🛡️ 5-Layer Security & Defense
The platform is hardened for enterprise multi-tenancy and verified against the **OWASP Top 10 API Security Risks**:
1. **JWT & Identity Verification:** Cryptographically verified tokens with algorithm pinning (`HS256`) and Argon2 password hashing.
2. **Telephony & Webhook Protection:** Cryptographic HMAC signature verification (`X-Twilio-Signature` and `Stripe-Signature`).
3. **SSRF Defense:** Comprehensive IP resolution blocking loopback, link-local, and private CIDR ranges across all redirect hops for knowledge docs and webhooks.
4. **Privilege Escalation Prevention:** Strict role assignment guards preventing unauthorized creation of `PLATFORM_ADMIN` or `TENANT_OWNER` accounts.
5. **PostgreSQL Row-Level Security (RLS):** Database-level enforcement of tenant isolation using `SET LOCAL app.current_tenant_id`.

---

## 👥 User Roles & Multi-Tenancy

| User Type | Access Point | Scope & Permissions |
| :--- | :--- | :--- |
| **Platform Super-Admin** | `/login` | Global root operator. Manages all tenants, billing plans, platform analytics, and tenant suspension. |
| **Tenant Owner** | `/register` or `/login` | Business owner. Full control over their company's AI agents, phone numbers, team members, and billing. |
| **Tenant Admin / Manager** | `/login` | Manages AI agents, call campaigns, phone numbers, and contacts for their company. |
| **Supervisor / Analyst** | `/login` | Views live call dashboards, call transcripts, sentiment analytics, and reports. |

> [!NOTE]
> Every customer workspace is completely isolated. When Customer A logs in, all database queries automatically filter by `tenant_id = 'customer-a-id'`. It is technically impossible for one company[...]

---

## 📋 Prerequisites

| Component | Version | Purpose |
| :--- | :--- | :--- |
| **Docker** | 24+ | Container runtime (Recommended) |
| **Docker Compose** | v2.20+ | Multi-container orchestration |
| **Python** | 3.12+ | Backend API & Celery worker |
| **Node.js** | 20+ LTS | Management Dashboard (Next.js) |
| **PostgreSQL** | 16+ | Primary database with `pgvector` |
| **Redis** | 7+ | Session cache, rate limiting & Celery broker |

---

## ⚙️ Setup & Configuration

### 1. Environment Configuration
Copy the example environment file to `.env` (or use the pre-generated `.env`):
```bash
cp .env.example .env
```

### 2. Essential API Keys
Edit `.env` and fill in your credentials:
* **OpenAI:** `OPENAI_API_KEY` (Required for Realtime Voice & Embeddings)
* **Twilio:** `TWILIO_ACCOUNT_SID` & `TWILIO_AUTH_TOKEN` (For voice calls & SMS)
* **Twilio Webhook:** `TWILIO_WEBHOOK_BASE_URL` (Your public domain or ngrok tunnel)
* **Stripe:** `STRIPE_SECRET_KEY` & `STRIPE_WEBHOOK_SECRET` (For subscriptions/billing)
* **SendGrid:** `SENDGRID_API_KEY` (Optional for transactional emails; falls back to dev logging)
* **Application Secrets:** `APP_SECRET_KEY` & `JWT_SECRET_KEY` (Pre-generated 64-character secure strings)

---

## 🚀 Quickstart Deployment Guide

### Option A: Quickstart with Podman (Linux / Rootless)

You can run the automated launcher script:
```bash
chmod +x scripts/quickstart-podman.sh
./scripts/quickstart-podman.sh
```

Or run the commands manually:
```bash
# 1. Build and start containers in the background
podman compose up -d --build
# (or: podman-compose up -d --build)

# 2. Apply database migrations
podman compose exec api python -m alembic upgrade head

# 3. Create your Master Platform Admin
podman compose exec api python scripts/create_platform_admin.py --email admin@yourcompany.com --password "YourStrongPassword"
```

---

### Option B: Quickstart with Docker

> Make sure you've completed [Step 1](#1-environment-configuration) (`cp .env.example .env`) first — `docker compose` will fail with an "env file not found" error if `.env` doesn't exist yet.

The fastest way to launch the API, Worker, Web Dashboard, Postgres, and Redis:

```bash
docker compose up -d --build
```

Verify service health:
```bash
docker compose ps
```

### Step 2: Apply Database Schema & Migrations
Set up database tables, pgvector extensions, and PostgreSQL Row-Level Security:

```bash
docker compose exec api python -m alembic upgrade head
```

### Step 3: Create Your Master Platform Admin Account
Provision your private root `PLATFORM_ADMIN` super-user:

```bash
docker compose exec api python scripts/create_platform_admin.py --email admin@yourcompany.com --password "YourStrongMasterPassword"
```

### Step 4: Access the Platform
* **Web Dashboard:** `http://localhost:3000`
* **API Documentation (Swagger):** `http://localhost:8000/api/docs`
* **Health Check:** `http://localhost:8000/health`

---

## 📞 Telephony & AI Live Setup

### 1. Public Exposure for Twilio Webhooks
Twilio requires a public HTTPS/WSS endpoint to stream audio.

* **For Local Development (ngrok):**
  ```bash
  ngrok http 8000
  ```
  Copy the HTTPS URL (e.g. `https://xyz.ngrok.app`) and set `TWILIO_WEBHOOK_BASE_URL=https://xyz.ngrok.app` in `.env`.

* **For Production:**
  Point your live domain with SSL (e.g. `https://api.yourcompany.com`) to your server via Nginx, Caddy, or Cloudflare with WebSocket upgrade headers enabled.

### 2. Configure Twilio Phone Number
1. Log in to [Twilio Console](https://console.twilio.com) $\rightarrow$ **Phone Numbers** $\rightarrow$ **Active Numbers**.
2. Select your number and scroll to **Voice Configuration**.
3. Under **A CALL COMES IN**, select `Webhook`:
   * **URL:** `https://<your-domain>/api/v1/voice/inbound/<agent-uuid>`
   * **HTTP Method:** `HTTP POST`
4. Save the configuration. Your AI voice agent is now live and accepting calls!

---

## ⚙️ Background Workers & Tasks

The platform includes a dedicated Celery worker container (`apps.api.worker.celery_app`) for asynchronous, out-of-band processing:

| Task Name | Description | Trigger |
| :--- | :--- | :--- |
| `tasks.post_call_processing` | Generates dialogue summaries, analyzes sentiment, and dispatches webhooks. | Immediately upon call completion |
| `tasks.process_document` | Extracts text from PDF/Docx/CSV/URLs, chunks text, and computes 1536-dim vectors. | On document upload |
| `tasks.campaign_dialer` | Paces outbound promotional and reminder calls respecting concurrency limits. | Campaign launch |

To run the worker manually outside Docker:
```bash
python -m celery -A apps.api.worker.celery_app worker --loglevel=info
```

---

## 🔐 Password Reset & Email Delivery

* **Password Reset:** Utilizes an ephemeral one-time token stored in Redis with an automatic **15-minute expiration (TTL)**.
* **Email Service:** `EmailService` automatically detects SendGrid credentials:
  * In **Production**, it delivers branded HTML emails via the SendGrid API.
  * In **Development**, it safely logs rich email previews to console without failing or requiring third-party credentials.

---

## 🧪 Testing & Verification

Run the automated test suite inside Docker:

```bash
# Run all unit and integration tests
docker compose exec api pytest tests/ -v

# Run multi-tenant isolation tests
docker compose exec api pytest tests/unit/test_tenant_isolation.py -v

# Run authentication and authorization tests
docker compose exec api pytest tests/unit/test_authorization.py -v
```

### Running tests against isolated test containers

`docker-compose.test.yml` is an override file that spins up a **separate** Postgres (port `5433`) and Redis (port `6380`) so tests never touch your dev data. It's driven by `.env.test` (already includ[...]

```bash
# Starts only the test postgres/redis containers, then runs pytest on the host
make test

# Or run the full stack (api + worker included) against the test DB
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.test.yml exec api python -m alembic upgrade head
```

---

## 📄 License
Apache License 2.0. See [LICENSE](LICENSE) for details.
