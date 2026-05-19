# 🛡 GRACE — Governance, Risk, Assurance & Compliance Engine
### Prototype v1.0

> **AI-assisted GRC automation** — 10 frameworks, cross-framework mapping, risk register, vendor due diligence, policy lifecycle, incident management.

📘 **Quick links**
- [Italian user guide for GRC analysts →](docs/USER_GUIDE_IT.md)
- [Oracle Cloud Always Free deploy playbook →](infrastructure/oracle-deploy/README.md)

---

## ⚠ Usage notice — All rights reserved

**This software, its source code, design, prompts, data model and accompanying
assets are the intellectual property of the project owner ([@PsychoKarasu](https://github.com/PsychoKarasu)).**

Use, reproduction, distribution, modification, sublicensing, hosting,
commercial exploitation, derivative-work creation or any redistribution
of GRACE — in whole or in part — **is strictly prohibited without the
prior, explicit, written consent of the owner.**

This includes (non-exhaustive):
- forking and publishing the repository under another name or organisation,
- embedding GRACE (or any of its modules, prompts, schemas, datasets, or
  brand assets) into other products, demos or services,
- using GRACE in any client engagement, sales activity, training material
  or marketing communication,
- using GRACE outputs (gap assessments, generated policies, etc.) in any
  audit, certification or regulatory submission without independent review.

For any request to evaluate, license, integrate or otherwise use this
project, contact the owner via GitHub before proceeding.

> The project is shared publicly for **demonstration, review and educational
> review only**. No license — express or implied — is granted by the mere
> visibility of the source code on this repository.

---

## What GRACE does today

GRACE is a single-pane GRC workbench. Ten pages, one workflow.

| Page | What it does |
|------|--------------|
| 🤖 **Ask GRACE** | Conversational AI for GRC. Persistent chat history, optional file attachments (PDF / DOCX / TXT / XLSX / CSV), optional framework context. Never creates findings — pure exploration / Q&A / cross-mapping. |
| 📊 **Gap Analysis** | Dedicated assessment workflow: upload evidence → choose framework → run → structured findings populate the registry and dashboard. Exports the assessment report to PDF. |
| 📝 **Document Generation** | Generates audit-ready documents (Information Security Policy, GDPR Art.28 DPA, ISO 27001 SoA, DPIA, IRP) with framework alignment. Markdown + PDF + DOCX export. |
| 🛡 **Governance Dashboard** | KPIs for the manager — open findings, critical count, coverage by framework, click-through filters to the registry. |
| 🔍 **Finding Registry** | Triage queue. Filter by framework / verdict / operational status. Cross-framework impact panel shows equivalent controls across the other 9 active frameworks. |
| 📚 **Framework Library** | Browse 10 active control catalogues (530+ controls). "Explain with Claude" turns formal control text into plain language. |
| 🎲 **Risk Management** | Risk register with 5×5 likelihood × impact heatmap, inherent/residual scoring, treatment plan, owner, linked controls. |
| 🤝 **Vendor Risk** | Vendor onboarding with a standard 10-question questionnaire, weighted scoring (0-100), automatic risk tier (low/medium/high/critical), Claude-generated qualitative summary. |
| 📜 **Policies** | Policy lifecycle: create (Markdown), assign to users, collect signed acknowledgments. Two tabs — Library (admin) + My Acknowledgments (end-user). |
| 🚨 **Incidents** | Incident management with automatic GDPR Art.33 deadline countdown for security_breach / data_loss at high+ severity. MTTR KPI. |

### Standout features

- **Cross-framework mapping**: a finding on ISO 27001 A.5.23 (cloud services) automatically surfaces the semantically equivalent controls in SOC 2, NIST CSF, DORA, NIS2, HIPAA — so fixing one gap closes five. Lazy compute + permanent DB cache, optional pre-warming CLI.
- **10 active frameworks**: ISO 27001:2022 (93), GDPR (99), SOC 2 (35), NIS2 (10), NIST CSF 2.0 (106), PCI DSS v4.0.1 (51 representative), HIPAA (54), DORA (64), ISO 42001:2023 (38), EU AI Act 2024/1689 (4 risk tiers).
- **Persistent chat history**: Ask GRACE conversations survive refresh, browser restart, container rebuild — backed by SQLite.
- **Multi-language** (EN / IT): UI + LLM output. Existing findings are lazily translated on first view, then cached.
- **Document upload** in PDF, DOCX, TXT, XLSX, CSV. XLSX parsed sheet-by-sheet with all cells as tab-separated text Claude can reason over.
- **Synthetic data generator** (`tools/synth_assessments.py`) for safe demos without real organisational data.

---

## Architecture

```
                          ┌─────────────────────────┐
                          │   Streamlit (8501)      │
                          │   10 pages, EN/IT       │
                          └────────────┬────────────┘
                                       │ REST /api/v1/
                          ┌────────────▼────────────┐
                          │   FastAPI (8000)        │
                          │   60+ endpoints         │
                          └────────────┬────────────┘
                                       │
                ┌──────────────────────┼──────────────────────┐
                ▼                      ▼                      ▼
        ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
        │   SQLite     │      │  Anthropic   │      │   YAML       │
        │  /app/data/  │      │   Claude     │      │  prompts +   │
        │   db/        │      │   API        │      │  catalogs    │
        └──────────────┘      └──────────────┘      └──────────────┘
```

| Component | Prototype | Production-ready alternative |
|-----------|-----------|------------------------------|
| Frontend | Streamlit (single-process) | Same code on Azure App Service / Cloud Run |
| AI layer | Anthropic Claude SDK | Azure AI Foundry (Claude on Bedrock-compatible) — flag-switchable |
| Backend | FastAPI on uvicorn | Same image on Azure Container Apps / ECS |
| Database | SQLite (loopback-only) | PostgreSQL 16 — connection-string swap in `database.py` |
| Reverse proxy | Caddy (HTTPS + Let's Encrypt) | Azure Front Door / Cloudflare |
| Auth | Single demo user | Entra ID / SSO / SAML in Phase 2 |

**Backend logic, prompts, data model and API contract are production-equivalent.** Migration is connection-string + adapter changes, not a rewrite.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Docker Desktop | ≥ 4.25 | [docker.com](https://docker.com) — free |
| Anthropic API key | — | [console.anthropic.com](https://console.anthropic.com) |

---

## Quick start — Docker (recommended)

```bash
git clone https://github.com/PsychoKarasu/GRACE
cd GRACE

# Configure environment
cp infrastructure/.env.example infrastructure/.env
# Edit infrastructure/.env and set ANTHROPIC_API_KEY=sk-ant-...

# Start
cd infrastructure
docker compose up -d --build
```

Open **http://localhost:8501**.

API docs at **http://localhost:8000/docs**.

To stop:
```bash
docker compose down
```

To wipe local data (keeps framework catalogs):
```bash
curl -X POST http://localhost:8000/api/v1/admin/reset
```

---

## Quick start — local Python (no Docker)

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## Deploy options

### Oracle Cloud Always Free (€0/month, real persistent VM)
See [`infrastructure/oracle-deploy/README.md`](infrastructure/oracle-deploy/README.md) for a 13-step playbook: VM provisioning, Caddy HTTPS via Let's Encrypt, DuckDNS subdomain, demo password gate, synthetic dataset.

### Self-hosted with Caddy reverse proxy
The `infrastructure/docker-compose.prod.yml` overlay adds Caddy in front of Streamlit with automatic HTTPS:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Project structure

```
GRACE/
├── backend/
│   ├── main.py                       FastAPI REST API (60+ endpoints under /api/v1/)
│   ├── modules/
│   │   ├── grc_engine.py             Claude integration, gap analysis, doc generation,
│   │   │                             control mapper, vendor AI summary, explain control
│   │   ├── control_mapper.py         Cross-framework semantic mapping (prompt caching)
│   │   ├── database.py               SQLite layer — single writer (invariant I-2)
│   │   └── export.py                 Markdown → PDF (reportlab) + DOCX (python-docx)
│   ├── data/
│   │   ├── db/grace.db               SQLite — auto-created, volume-mounted in Docker
│   │   ├── frameworks/               10 control-catalog JSONs (530+ controls total)
│   │   └── synthetic/                Generated synthetic evidence (watermarked)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py                        Streamlit UI — 10 pages, EN/IT i18n
│   ├── avatar.py                     GRACE avatar state machine + messages
│   ├── Dockerfile
│   └── requirements.txt
├── prompt-library/
│   ├── frameworks/                   System prompts per framework (10 YAMLs)
│   └── outputs/                      Output schema prompts per document type
├── infrastructure/
│   ├── docker-compose.yml            Local dev (loopback-only ports)
│   ├── docker-compose.prod.yml       Caddy overlay for public deploy
│   ├── Caddyfile                     HTTPS + websocket reverse proxy
│   ├── .env.example                  Env template (ANTHROPIC_API_KEY, demo password)
│   └── oracle-deploy/
│       ├── cloud-init.yml            Oracle VM bootstrap
│       └── README.md                 Step-by-step deploy playbook
├── tools/
│   ├── precompute_mappings.py        Pre-warm cross-framework mapping cache
│   ├── synth_assessments.py          Generate watermarked synthetic evidence
│   └── README.md
├── docs/
│   └── USER_GUIDE_IT.md              GRC analyst's operational guide (Italian)
├── CLAUDE.md                         Context file for Claude Code sessions
└── README.md                         This file
```

---

## Supported frameworks

| ID | Framework | Controls | Priority |
|----|-----------|----------|----------|
| ISO27001:2022 | ISO/IEC 27001:2022 | 93 | P0 |
| GDPR | GDPR 2016/679 | 99 | P0 |
| SOC2 | SOC 2 TSC 2017 | 35 | P0 |
| NIS2 | NIS2 Directive 2022/2555 | 10 | P1 |
| NISTCSF2.0 | NIST CSF 2.0 | 106 | P0 |
| PCI-DSS4.0.1 | PCI DSS v4.0.1 | 51 (representative) | P0 |
| HIPAA | HIPAA Security Rule | 54 | P0 |
| DORA | DORA 2022/2554 | 64 | P1 |
| ISO42001 | ISO/IEC 42001:2023 | 38 | P1 |
| EUAIACT | EU AI Act 2024/1689 | 4 (risk tiers) | P1 |

Each framework ships with:
- A control catalogue JSON (`backend/data/frameworks/`)
- A system prompt YAML (`prompt-library/frameworks/`) with assessment rules, severity definitions, regulatory reference format

Adding a new framework is a 3-step process documented in `CLAUDE.md`.

---

## API at a glance

| Endpoint group | Purpose |
|----------------|---------|
| `GET /health` | Liveness + Anthropic key check |
| `GET /api/v1/frameworks` | List of 10 active frameworks |
| `GET /api/v1/frameworks/{id}/controls` | Full catalogue |
| `POST /api/v1/documents/upload` | Upload PDF / DOCX / TXT / XLSX / CSV |
| `POST /api/v1/assessments/run-sync` | Run gap analysis (multi-doc supported) |
| `GET /api/v1/findings` | List findings with filters + `cross_framework_count` |
| `GET /api/v1/findings/{id}/cross-framework-impact` | Equivalent controls in other frameworks |
| `POST /api/v1/chat/sessions` | Create persistent Ask GRACE session |
| `POST /api/v1/chat/sessions/{id}/messages` | Send a chat message |
| `POST /api/v1/risks` | Create risk in the register |
| `POST /api/v1/vendors/{id}/assess` | Submit questionnaire → Claude scoring + AI summary |
| `POST /api/v1/policies/{id}/assign` | Assign a policy to one or more users |
| `POST /api/v1/policy-assignments/{id}/acknowledge` | End-user accepts a policy |
| `POST /api/v1/incidents` | Open an incident (auto-computes GDPR deadline) |
| `POST /api/v1/admin/reset` | Wipe user data (keep framework catalogues) |

Full OpenAPI spec at `/docs` on the running backend.

---

## Cost notes (Anthropic API)

GRACE uses prompt caching aggressively for cross-framework mapping and explanations. Typical demo budget:

| Operation | Cost (cached) | Cost (uncached) |
|-----------|---------------|-----------------|
| Single gap analysis on a 10-page document | ~$0.05 | ~$0.05 |
| Cross-framework mapping for ALL 530 controls (one-shot pre-warm) | ~$2-5 | $20+ |
| Single finding's cross-framework lookup (lazy) | ~$0.01 (free after cache) | $0.01 |
| Document generation (policy) | ~$0.10 | ~$0.10 |
| Vendor AI summary (Haiku) | ~$0.001 | ~$0.001 |
| Ask GRACE message (Haiku/Sonnet depending on context) | ~$0.001-0.02 | ~$0.001-0.02 |

Pre-warm command (recommended before a live demo):
```bash
docker compose exec grace-backend python tools/precompute_mappings.py
```

---

## Architectural invariants

GRACE enforces 7 invariants (see `CLAUDE.md`):

- **I-1**: Frontend contains ZERO GRC logic — only API calls + UI
- **I-2**: Backend is the only writer to SQLite
- **I-3**: All Claude calls go through `backend/modules/grc_engine.py`
- **I-4**: Assessment ingest is idempotent (file_hash dedup)
- **I-5**: API versioned `/api/v1/` from day one
- **I-6**: `compliance_status` (immutable) ≠ `operational_status` (mutable)
- **I-7**: All LLM output is schema-validated before persistence

---

## Roadmap

**Phase 1 — Business-ready prototype** (✅ done): risk register, vendor risk, policies, incidents, cross-framework mapping, persistent chat history, 10 active frameworks, multi-language.

**Phase 2 — Production hardening**: Entra ID SSO, evidence storage on S3 / Azure Blob, control testing automation via APScheduler, continuous monitoring scheduler, multi-tenant data partitioning, audit log of every backend write.

**Phase 3 — Enterprise integration**: XSOAR hand-off, Slack / Teams webhooks, SIEM ingestion of incident events, GraphQL on top of REST, evidence collection agents for AWS / Azure / GCP.

---

## Contributing & support

GRACE is a personal prototype. Issues are welcome on the GitHub tracker. Pull requests will not be merged from third parties without prior agreement (see the Usage notice above).

For bugs, follow the conventional commits style: `fix(scope): short summary`.

---

*GRACE Prototype v1.0 · Confidential*

---

© 2026 [@PsychoKarasu](https://github.com/PsychoKarasu). All rights reserved.
Unauthorised use, reproduction or distribution is prohibited. See the
**Usage notice** at the top of this README.
