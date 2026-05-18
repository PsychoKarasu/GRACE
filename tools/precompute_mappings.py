#!/usr/bin/env python3
"""
GRACE — Cross-Framework Mapping Pre-Compute

Walks every (framework, control_id) pair across the active GRACE
framework catalogs and asks the engine for its cross-framework
mappings. Each call goes through grc_engine.get_or_compute_mappings()
which:
  1. Hits the SQLite cache first (cheap COUNT) — skips Claude on hit.
  2. Calls Claude via control_mapper on miss, validates the response
     with Pydantic, and persists the rows.

Why bother running it: the Findings Registry computes mappings lazily
on first expand, which means the first user to look at a finding pays
the ~3-6s round-trip. Running this once warms the cache so every user
gets instant lookups. With prompt caching on the target catalogs,
the ~530-control walk runs in ~$2-5 of API usage.

Examples:
  # All active frameworks
  docker compose exec grace-backend python tools/precompute_mappings.py

  # Just one framework
  docker compose exec grace-backend python tools/precompute_mappings.py \\
      --framework ISO27001:2022

  # Dry-run: print what would be mapped, no API calls
  docker compose exec grace-backend python tools/precompute_mappings.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Invariant I-3: all Claude calls go through backend/modules/grc_engine.py.
sys.path.insert(0, str(REPO_ROOT / "backend"))

from modules import database, grc_engine  # noqa: E402


def _iter_controls(framework_id: str):
    fw = grc_engine.load_framework(framework_id)
    if not fw:
        return []
    return list(fw.get("controls", []))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Pre-compute cross-framework control mappings.",
    )
    ap.add_argument(
        "--framework",
        help="Limit to a single framework ID (e.g. 'ISO27001:2022'). "
             "Default: walk every active framework.",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Re-map controls that already have cached entries.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the work plan without calling Claude or touching the DB.",
    )
    args = ap.parse_args()

    # Make sure the schema (incl. control_mappings table) exists before
    # we start writing rows. Safe to call repeatedly.
    database.init_db()

    if args.framework:
        active = [args.framework]
    else:
        active = [fw["id"] for fw in grc_engine.list_supported_frameworks()]
        # Drop any framework whose catalog isn't actually loadable —
        # e.g. an entry registered but with its JSON file missing.
        active = [fw for fw in active if grc_engine.load_framework(fw)]

    if not active:
        print("No active frameworks to walk. Nothing to do.")
        return 0

    grand_total = 0
    grand_skipped = 0
    grand_mapped = 0
    grand_failed = 0
    t0 = time.time()

    for fw_id in active:
        controls = _iter_controls(fw_id)
        if not controls:
            print(f"[{fw_id}] no controls loaded — skipping")
            continue

        print(f"\n=== {fw_id} — {len(controls)} controls ===")
        for i, ctrl in enumerate(controls, start=1):
            ctrl_id = ctrl.get("control_id", "")
            grand_total += 1

            if not args.force and database.has_mappings(fw_id, ctrl_id):
                grand_skipped += 1
                cached = database.count_mappings(fw_id, ctrl_id)
                print(f"  [{i:>3}/{len(controls)}] {ctrl_id:<14} "
                      f"cache hit ({cached} mappings) — skip")
                continue

            if args.dry_run:
                print(f"  [{i:>3}/{len(controls)}] {ctrl_id:<14} "
                      f"would map (dry-run)")
                continue

            try:
                mappings = grc_engine.get_or_compute_mappings(fw_id, ctrl_id)
            except Exception as e:  # noqa: BLE001
                grand_failed += 1
                print(f"  [{i:>3}/{len(controls)}] {ctrl_id:<14} "
                      f"FAILED — {e}")
                continue

            grand_mapped += 1
            print(f"  [{i:>3}/{len(controls)}] {ctrl_id:<14} "
                  f"{len(mappings)} equivalents found")

    elapsed = time.time() - t0
    print("\n──────────────────────────────────────────────")
    print(f"Total controls considered: {grand_total}")
    print(f"  cache hits (skipped):    {grand_skipped}")
    print(f"  newly mapped:            {grand_mapped}")
    print(f"  failures:                {grand_failed}")
    print(f"  elapsed:                 {elapsed:.1f}s")
    if args.dry_run:
        print("  (dry-run — no API calls, no DB writes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
