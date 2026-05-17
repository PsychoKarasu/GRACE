#!/usr/bin/env python3
"""
GRACE — Synthetic Assessment Document Generator

Generates realistic-but-fictional compliance documents for ISO 27001:2022,
GDPR, SOC 2, NIS2, HIPAA, NIST CSF 2.0 and PCI DSS 4.0.1. Output is
markdown files written to backend/data/synthetic/, ready to be uploaded
via POST /api/v1/documents/upload.

NO REAL DATA. NO PII. NO REAL ORGANIZATIONS. Every output begins with a
SYNTHETIC watermark; all persons, addresses, customers are fictional.

Usage examples:
  python tools/synth_assessments.py --framework iso27001_2022 --count 3
  python tools/synth_assessments.py --framework all --count 1 --coverage mixed
  python tools/synth_assessments.py --framework gdpr --persona medicloud --upload
  python tools/synth_assessments.py --framework all --count 1 --dry-run
"""
import argparse
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
# Invariant I-3: all Claude calls go through backend/modules/grc_engine.py.
# This tool is a thin CLI wrapper around generate_synthetic_document().
sys.path.insert(0, str(REPO_ROOT / "backend"))
from modules.grc_engine import generate_synthetic_document  # noqa: E402

OUTPUT_DIR = REPO_ROOT / "backend" / "data" / "synthetic"

# Framework keys mapped to (engine framework_id, primary document type).
# Only frameworks whose catalogs are loadable by grc_engine.load_framework()
# on the current branch are listed here. When HIPAA/NIST-CSF/PCI-DSS land
# (see branch claude/p0-frameworks-hipaa-nist-pci), extend this dict and
# also extend load_framework() in grc_engine.py.
FRAMEWORKS = {
    "iso27001_2022": ("ISO27001:2022", "Information Security Management System (ISMS) Policy"),
    "gdpr":          ("GDPR",          "Privacy Notice and Personal Data Processing Procedure"),
    "soc2":          ("SOC2",          "Trust Services Security Policy and System Description"),
    "nis2":          ("NIS2",          "NIS2 Cybersecurity Risk Management Programme"),
}

PERSONAS = [
    {
        "id": "novapay",
        "name": "NovaPay Solutions S.r.l.",
        "sector": "Fintech — Payment Initiation Service Provider (PSD2 PISP)",
        "size": "210 employees, offices in Milan, Lisbon and Dublin",
        "scope": "EU/EEA payment initiation and account information services for SMB merchants",
        "tech_stack": "AWS Frankfurt, microservices on Kubernetes, PostgreSQL, Kafka",
        "maturity": "Series B, ISO 27001 certified ~2 years ago, GDPR-mature, expanding into SOC 2",
    },
    {
        "id": "medicloud",
        "name": "MediCloud Health Systems GmbH",
        "sector": "Healthcare SaaS — Electronic Health Record and patient portal for clinics",
        "size": "480 employees, offices in Berlin and Vienna",
        "scope": "EU+CH operations, processing special category health data under GDPR Art.9(2)(h)",
        "tech_stack": "Azure West Europe, .NET, Azure SQL, Azure Kubernetes Service",
        "maturity": "Series C, ISO 27001 + ISO 27799, EU MDR-aware, evaluating HIPAA for US expansion",
    },
    {
        "id": "voltmfg",
        "name": "VoltMfg Industries S.p.A.",
        "sector": "Industrial Manufacturing — power electronics and EV components",
        "size": "1240 employees across 4 plants (Bologna, Lyon, Bratislava, Porto)",
        "scope": "OT/IT hybrid environment, NIS2 essential entity in energy supply chain",
        "tech_stack": "On-prem SCADA (Siemens), SAP S/4HANA, hybrid Azure tenancy, MES on the shop floor",
        "maturity": "Family-owned, ISO 9001/14001 mature, security maturing, NIS2 programme in progress",
    },
    {
        "id": "datalink",
        "name": "DataLink Marketing Services S.r.l.",
        "sector": "Digital Marketing Agency — programmatic ad-tech",
        "size": "52 employees, headquarters in Milan, distributed remote team",
        "scope": "EU clients, processes personal data on behalf of clients as data processor (GDPR Art.28)",
        "tech_stack": "GCP, BigQuery, Looker, Salesforce CDP",
        "maturity": "Bootstrapped, small, no formal ISMS, GDPR processor obligations being formalized",
    },
    {
        "id": "aerologistics",
        "name": "AeroLogistics Operations Ltd.",
        "sector": "Logistics — air cargo handling and freight forwarding",
        "size": "810 employees, hubs in London, Amsterdam and Singapore",
        "scope": "Global operations, EU GDPR + UK GDPR primary, cargo-related personal data of shippers/consignees",
        "tech_stack": "Oracle ERP, custom TMS, AWS Ireland, partial on-prem in EU hubs",
        "maturity": "Established 30+ years, mid-maturity, recently breached, ISMS overhaul under way",
    },
]

COVERAGE_PROFILES = {
    "well-prepared": {
        "description": "mature organization with most controls partially-to-fully covered; few but meaningful gaps remain",
        "target_coverage": "70-85%",
        "gap_density": "low — 2 to 4 specific control gaps mentioned",
        "tone": "confident, structured, formal; references specific procedures and named roles",
    },
    "mixed": {
        "description": "realistic mid-maturity; policy intent is solid but procedures and evidence are uneven",
        "target_coverage": "40-65%",
        "gap_density": "medium — 5 to 8 control areas with partial or absent coverage",
        "tone": "aspirational where coverage exists, vague where gaps live; some sections feel templated",
    },
    "gaps-heavy": {
        "description": "early-stage or audit-failable; policy statements present but implementation absent",
        "target_coverage": "15-35%",
        "gap_density": "high — most controls only superficially addressed; markers like 'TBD', 'to be defined', 'in progress'",
        "tone": "well-intentioned but immature; mentions controls without describing implementation or evidence",
    },
}

DEFAULT_MODEL = "claude-haiku-4-5"

# USD per 1M tokens, as of 2026. Used only for pre-flight cost estimate
# and post-run reporting — not for billing or hard limits.
PRICING = {
    "claude-haiku-4-5":  {"input": 1.00, "output": 5.00,  "cache_write": 1.25, "cache_read": 0.10},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30},
}


def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.lower())
    return s.strip("_")[:48] or "doc"


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate synthetic compliance documents for GRACE demo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--framework",
        default="iso27001_2022",
        help="framework key or 'all'. Available: " + ", ".join(FRAMEWORKS) + ", all",
    )
    p.add_argument("--count", type=int, default=3,
                   help="documents per framework (capped at number of personas: %d)" % len(PERSONAS))
    p.add_argument("--coverage", default="mixed",
                   choices=["well-prepared", "mixed", "gaps-heavy", "random"])
    p.add_argument("--persona", default=None,
                   help="single persona id (overrides random selection). Available: "
                        + ", ".join(p_["id"] for p_ in PERSONAS))
    p.add_argument("--language", default="en", choices=["en", "it"])
    p.add_argument("--model", default=DEFAULT_MODEL, choices=list(PRICING.keys()))
    p.add_argument("--output-dir", default=str(OUTPUT_DIR))
    p.add_argument("--force", action="store_true",
                   help="overwrite existing files (default: skip)")
    p.add_argument("--upload", action="store_true",
                   help="also upload generated docs to a running GRACE backend")
    p.add_argument("--backend-url", default="http://localhost:8000")
    p.add_argument("--dry-run", action="store_true",
                   help="show plan and cost estimate, no API calls")
    p.add_argument("--yes", action="store_true",
                   help="skip the cost confirmation prompt")
    p.add_argument("--seed", type=int, default=None,
                   help="random seed for reproducible persona/coverage selection")
    return p.parse_args()


def select_personas(persona_arg: Optional[str], count: int) -> list:
    if persona_arg:
        chosen = [p for p in PERSONAS if p["id"] == persona_arg]
        if not chosen:
            raise SystemExit(f"Unknown persona '{persona_arg}'. Available: "
                             f"{[p['id'] for p in PERSONAS]}")
        return chosen
    if count >= len(PERSONAS):
        return list(PERSONAS)
    return random.sample(PERSONAS, count)


def pick_coverage(coverage_arg: str) -> dict:
    if coverage_arg == "random":
        key = random.choice(["well-prepared", "mixed", "gaps-heavy"])
        return COVERAGE_PROFILES[key]
    return COVERAGE_PROFILES[coverage_arg]


def build_plan(args) -> list:
    if args.framework == "all":
        framework_keys = list(FRAMEWORKS.keys())
    else:
        if args.framework not in FRAMEWORKS:
            raise SystemExit(f"Unknown framework '{args.framework}'. "
                             f"Available: {list(FRAMEWORKS) + ['all']}")
        framework_keys = [args.framework]

    plan = []
    for fw_key in framework_keys:
        fw_id, doc_type = FRAMEWORKS[fw_key]
        personas = select_personas(args.persona, args.count)
        for persona in personas:
            plan.append((fw_key, fw_id, persona, doc_type))
    return plan


def confirm_cost(plan: list, model: str, yes: bool) -> bool:
    # Rough per-doc estimate. Caching cuts subsequent calls per-framework
    # by ~80% on the cached input block, so this is an upper bound.
    rough_per_doc_usd = {
        "claude-haiku-4-5":  0.025,
        "claude-sonnet-4-6": 0.070,
    }.get(model, 0.05)
    total = rough_per_doc_usd * len(plan)
    print("\n=== Generation plan ===")
    for i, (fw_key, _, persona, doc_type) in enumerate(plan, 1):
        print(f"  {i:>2}. [{fw_key:>16}]  {persona['name']:<38}  → {doc_type}")
    print(f"\nModel:         {model}")
    print(f"Docs:          {len(plan)}")
    print(f"Cost estimate: ~${total:.2f} USD (upper bound — prompt caching reduces "
          "subsequent calls per framework)")
    if yes:
        return True
    ans = input("\nProceed? [y/N] ").strip().lower()
    return ans in ("y", "yes")


def upload_to_backend(path: Path, backend_url: str) -> Optional[str]:
    try:
        import httpx
    except ImportError:
        print("    upload skipped — install httpx to enable")
        return None
    try:
        with open(path, "rb") as f:
            r = httpx.post(
                f"{backend_url.rstrip('/')}/api/v1/documents/upload",
                files={"file": (path.name, f, "text/markdown")},
                data={"owner": "synth", "business_unit": "Demo"},
                timeout=30.0,
            )
        if r.status_code in (200, 201):
            doc_id = r.json().get("document_id")
            print(f"    uploaded → document_id={doc_id}")
            return doc_id
        print(f"    upload failed: HTTP {r.status_code} — {r.text[:200]}")
    except Exception as e:
        print(f"    upload error: {e}")
    return None


def estimate_actual_cost(totals: dict, model: str) -> float:
    p = PRICING.get(model, PRICING[DEFAULT_MODEL])
    return (
        totals["input"]       * p["input"]
        + totals["output"]      * p["output"]
        + totals["cache_write"] * p["cache_write"]
        + totals["cache_read"]  * p["cache_read"]
    ) / 1_000_000


def main():
    args = parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    plan = build_plan(args)
    if not plan:
        raise SystemExit("Nothing to generate.")

    if args.dry_run:
        confirm_cost(plan, args.model, yes=True)
        print("\nDry run complete — no API calls made.")
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ERROR: ANTHROPIC_API_KEY not set. Export it before generating.")

    if not confirm_cost(plan, args.model, args.yes):
        print("Aborted.")
        return

    output_dir = Path(args.output_dir)
    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    generated = 0

    for i, (fw_key, fw_id, persona, doc_type) in enumerate(plan, 1):
        fw_dir = output_dir / fw_key
        fw_dir.mkdir(parents=True, exist_ok=True)
        out_path = fw_dir / f"{persona['id']}_{slugify(doc_type)}.md"

        if out_path.exists() and not args.force:
            print(f"[{i:>2}/{len(plan)}] skip (exists): {out_path.relative_to(REPO_ROOT)}")
            continue

        coverage = pick_coverage(args.coverage)
        print(f"[{i:>2}/{len(plan)}] {fw_key:<16} / {persona['id']:<14} / "
              f"{coverage['target_coverage']:<7} ... ", end="", flush=True)
        t0 = time.time()
        try:
            result = generate_synthetic_document(
                framework_id=fw_id,
                persona=persona,
                coverage_profile=coverage,
                doc_type_name=doc_type,
                language=args.language,
                model=args.model,
            )
        except Exception as e:
            print(f"FAILED — {e}")
            continue

        elapsed = time.time() - t0
        usage = result.get("usage", {}) or {}
        totals["input"]       += usage.get("input_tokens") or 0
        totals["output"]      += usage.get("output_tokens") or 0
        totals["cache_read"]  += usage.get("cache_read_input_tokens") or 0
        totals["cache_write"] += usage.get("cache_creation_input_tokens") or 0

        out_path.write_text(result["markdown_content"], encoding="utf-8")
        print(f"ok ({elapsed:4.1f}s, {len(result['markdown_content']):,} chars)")
        generated += 1

        if args.upload:
            upload_to_backend(out_path, args.backend_url)

    cost = estimate_actual_cost(totals, args.model)
    print("\n=== Summary ===")
    print(f"Generated: {generated} document(s)")
    print(f"Tokens:    input={totals['input']:,}  output={totals['output']:,}  "
          f"cache_read={totals['cache_read']:,}  cache_write={totals['cache_write']:,}")
    print(f"Cost:      ~${cost:.4f} USD")
    print(f"Output:    {output_dir.relative_to(REPO_ROOT)}/")


if __name__ == "__main__":
    main()
