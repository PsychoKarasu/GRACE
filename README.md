# 🛡️ GRACE — Governance, Risk, Assurance & Compliance Engine
### Prototype v1.0 · Brightstar Security Operations

> **AI-powered GRC automation** · Copilot-first simulation · XSOAR-governed

---

## ⚠️ Usage notice — All rights reserved

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

## What this prototype demonstrates

| Capability | Description |
|------------|-------------|
| 🔍 Gap Analysis | Upload a policy or procedure document → get a structured compliance assessment against ISO 27001, GDPR, or SOC 2 with 🔴🟡🟢 ratings per control |
| 📄 Document Generation | Generate audit-ready documents: Information Security Policy, GDPR Art.28 DPA, ISO 27001 SoA |
| 📊 Governance Dashboard | Live KPI view: open findings, coverage by framework, severity distribution (simulates XSOAR) |
| 🗂️ Finding Registry | Browse and update all findings, track operational status (simulates XSOAR incident queue) |
| 📚 Framework Library | Browse the control catalog, get plain-language explanations of any control |

## Architecture (prototype vs production)

| Component | Prototype | Production (GRACE full) |
|-----------|-----------|------------------------|
| Frontend | Streamlit | Microsoft Copilot Studio |
| AI layer | Anthropic API | Azure AI Foundry |
| Backend | FastAPI | FastAPI on Azure Container Apps |
| Database | SQLite | PostgreSQL 16 (Azure) |
| Governance | Dashboard in UI | Cortex XSOAR on-prem |
| Auth | None (demo) | Entra ID + Managed Identity |

**The backend logic, prompts, data model and API contract are production-equivalent.**

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Docker Desktop | ≥ 4.25 | [docker.com](https://docker.com) — free |
| Anthropic API key | — | [console.anthropic.com](https://console.anthropic.com) |

---

## Quickstart — Docker (recommended, fully portable)

```bash
# 1. Clone or unzip the package
cd grace-prototype

# 2. Set your API key (or it will prompt you)
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# 3. Start everything
./start.sh
```

Open **http://localhost:8501** in your browser.

API documentation at **http://localhost:8000/docs**.

To stop:
```bash
docker compose -f infrastructure/docker-compose.yml down
```

---

## Quickstart — Local Python (no Docker needed)

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-your-key-here
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## Deploy to Railway (public URL for presentations)

1. Push this folder to a GitHub repository
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Set environment variable: `ANTHROPIC_API_KEY=sk-ant-...`
4. Railway gives you a public HTTPS URL — share with anyone

---

## Project structure

```
grace-prototype/
├── backend/
│   ├── main.py                  FastAPI REST API (/api/v1/*)
│   ├── modules/
│   │   ├── grc_engine.py        Claude AI integration + gap analysis engine
│   │   └── database.py          SQLite operations (production schema)
│   ├── data/
│   │   ├── grace.db             SQLite database (auto-created)
│   │   └── frameworks/          Control catalogs JSON
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py                   Streamlit UI (5 pages)
│   ├── Dockerfile
│   └── requirements.txt
├── prompt-library/
│   ├── frameworks/              System prompts per framework (YAML)
│   └── outputs/                 Output schema prompts (YAML)
├── infrastructure/
│   ├── docker-compose.yml       Portable container setup
│   └── railway.toml             One-click cloud deploy
├── CLAUDE.md                    Context file for Claude Code sessions
├── start.sh                     One-command startup script
└── README.md                    This file
```

---

## Supported frameworks (prototype)

| Framework | Status | Controls loaded |
|-----------|--------|----------------|
| ISO 27001:2022 | ✅ Active | 18 (representative) |
| GDPR | ✅ Active | 12 (representative) |
| SOC 2 TSC | ✅ Active | 13 (representative) |
| NIST CSF 2.0 | 🚧 Phase 3 | — |
| PCI DSS v4.0.1 | 🚧 Phase 3 | — |
| HIPAA | 🚧 Phase 3 | — |
| + 19 more | 🚧 Phase 3-4 | — |

> Production GRACE covers all 25 frameworks across 7 categories.

---

## Migrating to production Azure

The prototype backend is production-equivalent. Migration requires:

1. **SQLite → PostgreSQL**: change connection string in `database.py`
2. **Anthropic API → Azure AI Foundry**: set `CLAUDE_CODE_USE_FOUNDRY=1` + update client init
3. **Docker Compose → Azure Container Apps**: same Dockerfile, `az containerapp create`
4. **Streamlit → Copilot Studio**: the backend REST API is unchanged
5. **Dashboard → XSOAR**: the XSOAR sync agent (Flusso C/D) connects via Service Bus

---

*GRACE Prototype v1.0 · Brightstar Security Operations · Confidential*

---

© 2026 [@PsychoKarasu](https://github.com/PsychoKarasu). All rights reserved.
Unauthorised use, reproduction or distribution is prohibited. See the
**Usage notice** at the top of this README.
