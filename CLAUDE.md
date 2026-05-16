# GRACE — Governance, Risk, Assurance & Compliance Engine
## Project context for Claude Code

This is the GRACE prototype — a working GRC automation system.

## Quick start
```bash
export ANTHROPIC_API_KEY=sk-ant-...
./start.sh          # Docker Compose
# OR
cd backend && pip install -r requirements.txt
uvicorn main:app --reload &
cd ../frontend && pip install -r requirements.txt
streamlit run app.py
```

## Architecture
- **Frontend**: Streamlit (frontend/app.py) — simulates Microsoft Copilot
- **Backend**: FastAPI (backend/main.py) — the GRC Engine REST API
- **Database**: SQLite at backend/data/grace.db
- **AI**: Anthropic Claude via SDK (ANTHROPIC_API_KEY env var)
- **Packaging**: Docker Compose (infrastructure/docker-compose.yml)

## Architectural invariants (never violate)
- I-1: Frontend (Streamlit) contains ZERO GRC logic — only API calls + UI
- I-2: Backend is the only writer to the SQLite database
- I-3: All Claude calls go through backend/modules/grc_engine.py ONLY
- I-4: Assessment sync is idempotent (dedup on file_hash)
- I-5: API versioned /api/v1/ from day one
- I-6: compliance_status (immutable) ≠ operational_status (mutable)
- I-7: All LLM output is schema-validated before persistence

## Key files
- `backend/modules/grc_engine.py` — Claude integration, gap analysis, doc generation
- `backend/modules/database.py`   — All DB operations, canonical schema
- `backend/main.py`               — FastAPI routes
- `frontend/app.py`               — Streamlit UI (5 pages)
- `prompt-library/frameworks/`    — Framework-specific YAML prompts
- `prompt-library/outputs/`       — Output schema prompts
- `backend/data/frameworks/`      — Control catalog JSON

## Framework coverage
- P0 (active): ISO27001:2022, GDPR, SOC2
- P0 (stubs):  NISTCSF2.0, PCI-DSS4.0.1, HIPAA
- P1 (stubs):  DORA, NIS2, ISO42001, EU AI Act

## Adding a new framework
1. Create `backend/data/frameworks/{framework_id}.json` with control catalog
2. Create `prompt-library/frameworks/{framework_id}.yaml` with system prompt
3. Add to `list_supported_frameworks()` in grc_engine.py
4. Add to `load_framework()` mapping in grc_engine.py

## Dev rules
- pytest for all tests: `cd backend && pytest tests/`
- No secrets in code — ANTHROPIC_API_KEY via environment only
- Structured logging on all errors
- Never break the /health endpoint

## Migration to Azure (future)
- SQLite → PostgreSQL: change connection string in database.py
- Anthropic API → Azure AI Foundry: set CLAUDE_CODE_USE_FOUNDRY=1, change client init
- File storage → Azure Blob: replace Path operations with azure-storage-blob SDK
- Deploy: `az containerapp update` with same Docker image
