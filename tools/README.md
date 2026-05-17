# GRACE — Developer Tooling

Auxiliary scripts for developers and demo operators. None of these are
part of the runtime path (Streamlit / FastAPI) — they are CLI utilities
that augment the prototype workflow.

## `synth_assessments.py` — Synthetic dataset generator

Generates realistic-but-fictional compliance documents (ISMS policies,
privacy notices, NIS2 programmes, etc.) for the frameworks active on
this branch: **ISO 27001:2022, GDPR, SOC 2, NIS2**. When HIPAA, NIST CSF
2.0 and PCI DSS 4.0.1 are merged in from `claude/p0-frameworks-hipaa-nist-pci`,
extend the `FRAMEWORKS` dict in `synth_assessments.py` and the matching
`load_framework()` mapping in `backend/modules/grc_engine.py`.

Output files land in `backend/data/synthetic/` and are watermarked
"SYNTHETIC DEMO DOCUMENT" on the first line. They can be uploaded to a
running GRACE backend via the existing `/api/v1/documents/upload`
endpoint (the `--upload` flag automates this).

### Quickstart

```bash
export ANTHROPIC_API_KEY=sk-ant-...

# 3 ISO27001 ISMS policies, mixed coverage, random personas
python tools/synth_assessments.py --framework iso27001_2022 --count 3

# one document per active framework, mixed coverage
python tools/synth_assessments.py --framework all --count 1 --coverage mixed

# generate AND upload to the local backend
python tools/synth_assessments.py --framework gdpr --count 2 --upload

# dry run: print the plan + cost estimate, do not call the API
python tools/synth_assessments.py --framework all --count 3 --dry-run

# reproducible run (same personas every time)
python tools/synth_assessments.py --framework all --count 2 --seed 42
```

### Key flags

| Flag | Default | Purpose |
|---|---|---|
| `--framework` | `iso27001_2022` | framework key or `all` |
| `--count` | `3` | docs per framework (capped at number of personas) |
| `--coverage` | `mixed` | `well-prepared` / `mixed` / `gaps-heavy` / `random` |
| `--persona` | _random_ | force a single persona id |
| `--language` | `en` | `en` or `it` |
| `--model` | `claude-haiku-4-5` | also accepts `claude-sonnet-4-6` |
| `--upload` | off | also POST each doc to the backend |
| `--backend-url` | `http://localhost:8000` | backend for `--upload` |
| `--dry-run` | off | plan + cost only, no API calls |
| `--yes` | off | skip the cost confirmation prompt |
| `--force` | off | overwrite existing files |
| `--seed` | _none_ | reproducible random selection |

### Cost expectations

Per document, with Haiku 4.5 and prompt caching of the framework control
catalog (active after the first call per framework):

- First doc per framework: ~$0.025 USD
- Subsequent docs same framework (cache hit): ~$0.010 USD

Generating the full demo dataset (4 frameworks × 3 personas = 12 docs)
costs roughly **$0.18 USD** with Haiku, or ~$0.50 with Sonnet.

The script prints a pre-flight estimate and asks for confirmation
(unless `--yes`).

### Architectural note

All Claude calls go through `backend/modules/grc_engine.py`
(`generate_synthetic_document`), respecting invariant **I-3** in
`CLAUDE.md`: "All Claude calls go through backend/modules/grc_engine.py
ONLY". This CLI is a thin wrapper that imports that function.
