# Synthetic Compliance Documents — Demo Dataset

**All files in this directory are AI-generated and entirely fictional.**

## Purpose

This directory holds synthetic compliance documents (ISMS policies, GDPR
privacy notices, SOC 2 policies, NIS2 programmes, etc.) used as a
playground dataset for the GRACE prototype. They let an analyst exercise
the upload → gap analysis → report flow against documents that look and
feel like real organizational artefacts, **without ever touching real
organizational data**.

## What these files are NOT

- They are **not** real policies of any real organization.
- They are **not** approved by any compliance team.
- They must **never** be used as templates for actual policy writing.
- They contain no real personal data, no real customer names, no real
  addresses, no real systems.

Every file is watermarked at the top with:

> **SYNTHETIC DEMO DOCUMENT — FICTIONAL ORGANIZATION — NOT REAL DATA**

All persons named in the documents are obvious placeholders. Any
resemblance to real organizations is coincidental.

## How they are generated

See `tools/synth_assessments.py`. The generator builds documents by
combining a fictional organization persona (NovaPay, MediCloud, VoltMfg,
DataLink, AeroLogistics) with a coverage profile (well-prepared, mixed,
gaps-heavy) and submitting them to Claude via the GRACE engine
(`backend/modules/grc_engine.py`).

Example regenerate of the full dataset:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python tools/synth_assessments.py --framework all --count 3 --coverage random
```

## Why this exists

The GRACE prototype must demonstrate value on realistic-looking
documents, but the project author is not authorized to upload real
organizational documents to any environment that lacks a formal Data
Processing Agreement, registry-of-processing update and CISO/DPO
approval. Synthetic data is the compliant way to demo the system on
plausible content. Real organizational data may only be used once the
deployment moves to officially sanctioned company infrastructure.
