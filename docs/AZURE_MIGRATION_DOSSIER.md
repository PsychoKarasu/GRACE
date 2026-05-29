# GRACE — Production Deployment & Azure Migration Dossier

**Document type**: Technical architecture & production-readiness specification
**Audience**: Azure platform team, Cloud security, IT governance, FinOps
**Prepared by**: GRACE project owner
**Status**: For review / access request
**Classification**: Internal

---

## 0. Purpose of this document

This dossier accompanies a request for access to **Azure AI Foundry** (Anthropic Claude models) and the supporting Azure platform services required to move **GRACE** from a working local prototype to a governed, production-grade deployment in the corporate Azure tenant.

It describes, in one place:
1. What GRACE is and what business problem it solves
2. The current (prototype) architecture
3. The target production architecture on Azure
4. A phased migration plan
5. The concrete platform requirements the Azure team needs to provision
6. Security, identity, networking, data-protection and cost considerations

The intent is that an Azure platform owner, a cloud security reviewer and a FinOps reviewer can each read the relevant section and approve or scope their part without further context.

---

## 1. Executive summary

**GRACE (Governance, Risk, Assurance & Compliance Engine)** is an AI-assisted GRC workbench. It consolidates, into a single web application, activities today spread across spreadsheets, SharePoint and Word templates:

- Multi-framework compliance gap analysis (10 frameworks, ISO 27001 → EU AI Act)
- Automatic cross-framework control mapping ("fix once, close five gaps")
- Audit-ready document generation (policies, DPIA, SoA, IRP)
- Corporate risk register (5×5 heatmap, treatment plans)
- Vendor risk due diligence (questionnaire + AI scoring)
- Policy lifecycle with acknowledgment tracking
- Incident management with automatic GDPR Art.33 deadline tracking

GRACE uses **Anthropic Claude** as its reasoning engine. The prototype calls the Anthropic public API directly. **For production we require Claude served through Azure AI Foundry**, so that all inference traffic stays inside the corporate Azure tenant, under corporate data-processing terms, monitoring and cost governance.

**The application code is production-equivalent.** Migration is a matter of swapping infrastructure adapters (database connection string, model client initialization, file-storage backend) — not a rewrite. Estimated migration effort: **2–4 engineering weeks**, dominated by Azure provisioning, networking and security review rather than code.

---

## 2. What GRACE does (functional scope)

| Module | Business outcome |
|--------|------------------|
| Ask GRACE | Conversational GRC assistant — explanations, ad-hoc document analysis, cross-mapping. Persistent chat history. |
| Gap Analysis | Structured compliance assessment of evidence against a chosen framework; produces persisted findings. |
| Document Generation | First-draft generation of policies, DPIAs, SoA, incident response plans. |
| Governance Dashboard | Management KPIs: open findings, coverage by framework, severity distribution. |
| Finding Registry | Analyst triage queue with operational status workflow + cross-framework impact. |
| Framework Library | 10 control catalogues (530+ controls) with plain-language explanations. |
| Risk Management | Corporate risk register with inherent/residual scoring. |
| Vendor Risk | Third-party due diligence with weighted scoring + AI summary. |
| Policies | Policy publication + acknowledgment workflow. |
| Incidents | Incident tracking with regulatory deadline automation. |

**Frameworks covered**: ISO/IEC 27001:2022, GDPR, SOC 2, NIS2, NIST CSF 2.0, PCI DSS v4.0.1, HIPAA, DORA, ISO/IEC 42001:2023, EU AI Act 2024/1689.

---

## 3. Current architecture (prototype)

```
┌────────────────────────────────────────────────────────┐
│  Single Docker host (local dev / Oracle Free VM)        │
│                                                          │
│  ┌──────────────┐   REST    ┌──────────────┐            │
│  │  Streamlit   │──────────▶│   FastAPI    │            │
│  │  (8501)      │  /api/v1/ │   (8000)     │            │
│  └──────────────┘           └──────┬───────┘            │
│                                     │                    │
│              ┌──────────────────────┼─────────────┐     │
│              ▼                      ▼              ▼     │
│        ┌──────────┐         ┌──────────────┐  ┌───────┐ │
│        │  SQLite  │         │  Anthropic   │  │ YAML  │ │
│        │  (file)  │         │  public API  │  │ files │ │
│        └──────────┘         └──────┬───────┘  └───────┘ │
└─────────────────────────────────── │ ───────────────────┘
                                      │ HTTPS egress to
                                      ▼ api.anthropic.com
```

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Streamlit 1.40 | Python; pure presentation, zero business logic |
| Backend | FastAPI 0.115 + uvicorn | 53 REST endpoints under `/api/v1/` |
| AI | `anthropic` SDK 0.40 | Calls api.anthropic.com directly |
| Database | SQLite | 15 tables; single-writer |
| Document parsing | PyMuPDF, docx2txt, openpyxl | PDF/DOCX/XLSX/CSV ingestion |
| Document export | reportlab, python-docx | PDF/DOCX generation |
| Packaging | Docker Compose | Two containers, loopback-only ports |
| TLS (public) | Caddy 2.8 | Automatic Let's Encrypt |

**Architectural invariants already enforced in code** (relevant to a production review):

- **I-1** Frontend contains zero GRC logic — only API calls
- **I-2** Backend is the only writer to the database
- **I-3** All AI calls funnel through one module (`grc_engine.py`) — single point to swap the model provider
- **I-4** Document ingestion is idempotent (SHA-256 dedup)
- **I-5** API versioned `/api/v1/` from day one
- **I-6** Immutable compliance status vs. mutable operational status
- **I-7** All LLM output is schema-validated (Pydantic) before persistence

Invariant **I-3** is the key enabler for the Azure migration: there is exactly one place in the codebase where the model client is constructed.

---

## 4. Target production architecture (Azure)

```
                          Internet
                             │
                             ▼
                  ┌────────────────────┐
                  │  Azure Front Door  │  WAF, TLS, custom domain
                  └─────────┬──────────┘
                            │ private
                  ┌─────────▼──────────────────────────────┐
                  │   Azure Container Apps environment      │
                  │   (VNet-integrated, internal ingress)   │
                  │                                         │
                  │  ┌────────────┐      ┌──────────────┐   │
                  │  │ Streamlit  │─────▶│   FastAPI    │   │
                  │  │ container  │      │   container  │   │
                  │  └────────────┘      └──────┬───────┘   │
                  └──────────────────────────── │ ──────────┘
                          │            │         │
            Managed Identity (no secrets in app)│
                          │            │         │
              ┌───────────▼──┐ ┌───────▼─────┐ ┌─▼──────────────┐
              │ Azure DB for │ │ Azure Blob  │ │ Azure AI       │
              │ PostgreSQL   │ │ Storage     │ │ Foundry        │
              │ (Flexible)   │ │ (evidence)  │ │ (Claude)       │
              └──────────────┘ └─────────────┘ └────────────────┘
                     │                                  │
              ┌──────▼──────┐                  Private Endpoint /
              │ Key Vault   │                  VNet-restricted
              │ (secrets)   │
              └─────────────┘

   Cross-cutting: Entra ID auth, Azure Monitor + Log Analytics,
                  Microsoft Defender for Cloud, Azure Policy
```

### 4.1 Component mapping (prototype → production)

| Concern | Prototype | Production (Azure) | Code change |
|---------|-----------|--------------------|-------------|
| Compute | Docker Compose | **Azure Container Apps** (same images) | None — same Dockerfiles |
| Database | SQLite file | **Azure Database for PostgreSQL Flexible Server** | Connection string in `database.py`; SQL is standard |
| AI inference | Anthropic public API | **Azure AI Foundry (Claude)** | Client init in `grc_engine.py` (one module) |
| File/evidence storage | Local filesystem | **Azure Blob Storage** | `Path` ops → `azure-storage-blob` SDK |
| Secrets | `.env` file | **Azure Key Vault** + Managed Identity | Env var resolution at startup |
| TLS / WAF | Caddy + Let's Encrypt | **Azure Front Door** (WAF + managed certs) | None |
| AuthN/Z | Single demo user | **Entra ID** (OIDC) + app roles | New auth middleware (see §6) |
| Observability | stdout logs | **Azure Monitor + Log Analytics** | Structured logging already present |

### 4.2 Why Azure Container Apps (not AKS)

GRACE is two stateless containers plus managed backing services. Container Apps gives scale-to-zero, built-in ingress, revision-based deployment, VNet integration and Managed Identity without the operational overhead of a Kubernetes cluster. If the platform team standardises on **AKS** or **App Service**, GRACE runs unchanged on either — the images are vanilla Docker.

---

## 5. Azure AI Foundry — the critical dependency

This is the **primary access request**.

### 5.1 What we need

| Item | Requirement |
|------|-------------|
| Service | **Azure AI Foundry** with the **Anthropic Claude** model family enabled in the corporate tenant |
| Models | A current Claude model for reasoning (gap analysis, document generation, mapping) and a smaller/faster Claude model for lightweight tasks (chat Q&A, vendor summaries). GRACE selects model per-task. |
| Region | EU region (e.g. **Sweden Central** / **West Europe**) for data residency — see §7 |
| Access pattern | Application authenticates via **Managed Identity** (no API keys in code or config) |
| Networking | Foundry endpoint reachable from the Container Apps VNet via **Private Endpoint** where supported |
| Quota | Token-per-minute (TPM) and requests-per-minute (RPM) quota sized for the workload in §8 |

### 5.2 Integration impact on code

Because of invariant **I-3**, switching from the Anthropic public API to Azure AI Foundry touches **one module** (`backend/modules/grc_engine.py`), specifically the client constructor:

```python
# Prototype (today)
import anthropic
client = anthropic.Anthropic()              # reads ANTHROPIC_API_KEY

# Production (Azure AI Foundry)
# Claude on Foundry is consumed through the Foundry endpoint with
# Entra ID / Managed Identity credentials instead of an API key.
# The message-creation calls, prompt caching, system prompts and
# schema validation remain identical.
```

All prompt engineering, prompt caching, schema validation and business logic remain unchanged. This is a configuration/adapter change, not a functional change.

### 5.3 Data handling expectation

We expect that, under Azure AI Foundry, prompt and completion content:
- Stays within the selected Azure region
- Is governed by the corporate Azure / Microsoft data-processing terms (not the public Anthropic consumer terms)
- Is **not** used for model training
- Can be excluded from any abuse-monitoring human review if the tenant has that configuration

Please confirm the tenant's Foundry data-handling posture so we can document it in GRACE's own DPIA.

---

## 6. Identity & access (Entra ID)

The prototype has a single demo user. Production requires real authentication and role separation.

| Requirement | Detail |
|-------------|--------|
| Authentication | **Entra ID OIDC** in front of the Streamlit app (via Front Door / Container Apps auth or app-level middleware) |
| Authorization | App roles mapped to GRACE personas (see below) |
| Service-to-service | Backend → PostgreSQL, Blob, Foundry all via **system-assigned Managed Identity**; zero secrets in app config |
| Secrets | Any unavoidable secret in **Key Vault**, referenced by Managed Identity |

**Proposed app roles** (RBAC, to be implemented in Phase 2):

| Role | Capabilities |
|------|-------------|
| `grace.viewer` | Read dashboards, findings, library |
| `grace.analyst` | Run assessments, manage findings, risks, vendors |
| `grace.author` | Generate & publish documents/policies |
| `grace.admin` | All of the above + data reset, user assignment |

RBAC is **not** in the current prototype (single user). It is a defined Phase 2 work item; the API is already versioned and centralised, so adding an auth dependency layer is contained.

---

## 7. Data protection & compliance

GRACE processes **governance content**: policies, control evidence, vendor questionnaires, incident records. Some of this can include personal data (incident reporters, policy acknowledgers, vendor contacts) and is therefore in GDPR scope.

| Topic | Position |
|-------|----------|
| Data residency | All storage (PostgreSQL, Blob) and inference (Foundry) in an **EU region** |
| Data classification | Internal / Confidential. No special-category data by design. Customer PII must **not** be uploaded as evidence. |
| Encryption at rest | Native Azure encryption on PostgreSQL + Blob; optionally customer-managed keys (CMK) via Key Vault |
| Encryption in transit | TLS 1.2+ end to end; internal traffic over VNet |
| Retention | Findings, runs, incidents retained per corporate records policy; admin reset endpoint allows purge |
| DPIA | GRACE will carry its own DPIA. The Foundry data-handling confirmation (§5.3) is an input to it. |
| Audit trail | An `audit_events` table exists; production should ship these to Log Analytics for immutability |
| LLM output governance | All AI output is schema-validated (I-7) and treated as **draft requiring human review** — never auto-published to audits/regulators |

**Important usage constraint already enforced operationally**: the prototype is exercised only with **synthetic / fictional data**. Production onboarding of real organisational data requires the DPIA sign-off and the data-processing confirmations above.

---

## 8. Sizing & cost

### 8.1 Compute (Azure Container Apps)

| Workload | Profile | Notes |
|----------|---------|-------|
| FastAPI backend | 0.5–1 vCPU, 1–2 GB, scale 1→3 | CPU-light; spends time waiting on the model |
| Streamlit frontend | 0.5 vCPU, 1 GB, scale 1→2 | Stateless |

Scale-to-zero is viable for non-production / out-of-hours environments.

### 8.2 Managed services (order-of-magnitude, EU region)

| Service | Suggested tier | Indicative monthly |
|---------|----------------|--------------------|
| Container Apps | Consumption | €30–80 |
| PostgreSQL Flexible | Burstable B1ms/B2s | €25–60 |
| Blob Storage | Hot, < 50 GB | €5–15 |
| Key Vault | Standard | < €5 |
| Front Door + WAF | Standard | €30–40 |
| Log Analytics | Pay-as-you-go | €10–30 |
| **Platform subtotal** | | **≈ €105–230 / month** |

### 8.3 Azure AI Foundry (Claude) — usage-based

This dominates variable cost and depends on adoption. GRACE is **token-efficient by design**:
- **Prompt caching** on framework catalogues (cross-framework mapping, explanations) — large static context cached, not re-billed per call
- **Model tiering** — a smaller Claude model handles chat Q&A and vendor summaries; the larger model is reserved for gap analysis and document generation
- **Lazy + cached** cross-framework mapping — computed once per control, then served from the database forever

Indicative per-operation cost (cached where applicable):

| Operation | Indicative cost |
|-----------|-----------------|
| One gap analysis (10-page doc) | ~€0.05 |
| Pre-warm ALL cross-framework mappings (one-off, 530+ controls) | ~€2–5 |
| Single cross-framework lookup (lazy, then free) | ~€0.01 |
| Document generation (policy) | ~€0.10 |
| Vendor AI summary (small model) | ~€0.001 |
| Chat message | ~€0.001–0.02 |

For a team of ~10 analysts in steady use, a **monthly Foundry token budget of €100–300** is a reasonable starting envelope, to be refined against actual TPM quota and observed usage. A **budget alert / quota cap** is recommended from day one (FinOps ask).

---

## 9. Networking summary (Azure platform ask)

| Requirement | Detail |
|-------------|--------|
| VNet | Dedicated subnet for the Container Apps environment |
| Ingress | Internal only; public exposure exclusively via Front Door |
| Private Endpoints | PostgreSQL, Blob, Key Vault, and Foundry (where supported) |
| Egress | Restricted; only to required Azure service endpoints |
| WAF | Front Door WAF with managed rule set |
| Custom domain + TLS | Managed certificate on Front Door |

---

## 10. Observability & operations

| Capability | Implementation |
|-----------|----------------|
| Logs | Structured logging already in code → Azure Monitor / Log Analytics |
| Metrics | Container Apps + Foundry token metrics |
| Health probe | `/health` endpoint (DB reachability + model-credential check) already implemented — **must not be broken**, it's a defined invariant |
| Alerting | Budget alerts (Foundry spend), failed-run alerts, 5xx alerts |
| Backup | PostgreSQL automated backups (PITR); Blob soft-delete + versioning |
| CI/CD | Build images → push to **Azure Container Registry** → `az containerapp update` (revision-based, zero-downtime) |
| DR | Stateless app; recovery = redeploy images + restore DB. RPO/RTO to be agreed with platform team. |

---

## 11. Migration plan (phased)

### Phase 0 — Access & landing zone (Azure team)
1. Provision resource group + VNet + subnets in EU region
2. **Enable Azure AI Foundry with Claude models** (the gating dependency)
3. Create PostgreSQL Flexible Server, Blob Storage, Key Vault, ACR
4. Configure Managed Identity and RBAC assignments

### Phase 1 — Lift the backend
5. Push existing Docker images to ACR
6. Swap `database.py` connection string → PostgreSQL (schema is standard SQL; a one-time migration script ports the 15 tables)
7. Swap `grc_engine.py` client init → Azure AI Foundry (Managed Identity)
8. Swap file storage → Azure Blob SDK
9. Resolve config from Key Vault at startup

### Phase 2 — Front the app & secure it
10. Deploy both containers to Container Apps (internal ingress)
11. Front Door + WAF + custom domain
12. **Entra ID authentication + app roles (RBAC)**
13. Wire logs/metrics to Log Analytics; set budget alerts

### Phase 3 — Hardening & go-live
14. DPIA completion using the confirmed Foundry data-handling posture
15. Penetration test / Defender for Cloud review
16. Load the first real (non-synthetic) dataset after sign-off
17. Operational runbook + DR test

**Estimated effort**: 2–4 engineering weeks of application work, in parallel with the Azure team's landing-zone provisioning. The long pole is organisational (access approval, security review, DPIA), not code.

---

## 12. What we are asking the Azure team to approve

1. **Access to Azure AI Foundry with Claude models** in an EU region (the core dependency)
2. Confirmation of the **Foundry data-handling posture** (residency, no-training, abuse-monitoring) for our DPIA
3. A **landing zone**: resource group, VNet, PostgreSQL Flexible Server, Blob Storage, Key Vault, ACR, Container Apps environment
4. **Entra ID** app registration + app roles for GRACE
5. **Front Door + WAF** with a custom domain
6. A **Foundry token budget + quota** with FinOps alerting
7. Inclusion of GRACE in standard **Defender for Cloud / Azure Policy** governance

---

## 13. Risk register for the migration itself

| Risk | Impact | Mitigation |
|------|--------|------------|
| Foundry Claude not available in chosen EU region | Blocks core feature | Confirm region availability before Phase 0; fall back to nearest compliant EU region |
| Quota too low for adoption | Throttling / poor UX | Size TPM/RPM from §8; request headroom; model tiering already reduces load |
| Real PII uploaded as evidence | GDPR exposure | DPIA + user guidance + classification banner; admin purge endpoint |
| Cost overrun on Foundry | Budget | Budget alerts + quota cap + prompt caching (already implemented) |
| RBAC not ready at go-live | Over-broad access | Phase 2 gates go-live; no real data before RBAC |

---

## 14. References (in-repo)

- `CLAUDE.md` — architectural invariants and migration notes
- `README.md` — feature overview and API surface
- `docs/USER_GUIDE_IT.md` — end-user operational guide
- `backend/modules/grc_engine.py` — the single AI integration point (I-3)
- `backend/modules/database.py` — data model (15 tables)
- `infrastructure/` — Docker Compose, Caddy, deployment overlays

---

*GRACE — Production Deployment & Azure Migration Dossier · Internal · For review*
