"""
GRACE Prototype — Cross-Framework Control Mapper

Given a source control (e.g. ISO27001:2022 A.5.23), discover semantically
equivalent controls in every OTHER active framework GRACE supports. Used
to surface "fixing this one gap closes 5 gaps across 5 frameworks" on the
Findings Registry.

Architecture invariants:
- I-3: this module is only ever invoked from grc_engine.py — the engine
       owns orchestration and caching; we just do the LLM call.
- I-7: the LLM response is Pydantic-validated before it ever reaches
       the database layer.

Cost model: the heavy bit of the prompt is the concatenation of the OTHER
9 frameworks' control catalogs (~50k tokens). We send those as a single
ephemeral-cached system block so subsequent mapping calls share the prefix
and pay the read price (~0.1×) instead of the full input price.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Literal, Optional

from pydantic import BaseModel, ValidationError, field_validator

from . import grc_engine

logger = logging.getLogger(__name__)


# ─── Output schema (Pydantic v2 — invariant I-7) ─────────────────────

class MappingEntry(BaseModel):
    target_framework:     str
    target_control_id:    str
    target_control_title: str
    confidence:           Literal["high", "medium", "low"]
    rationale:            str  # 1-2 sentences

    @field_validator("confidence", mode="before")
    @classmethod
    def _normalise_confidence(cls, v):
        if isinstance(v, str):
            v = v.strip().lower()
            if v in ("high", "medium", "low"):
                return v
        return "low"


class MappingResponse(BaseModel):
    mappings: list[MappingEntry] = []


# ─── Catalog packaging ───────────────────────────────────────────────

def _compact_control(c: dict) -> dict:
    """Strip the catalog entry down to just what's useful for semantic
    matching. Keeping descriptions short keeps the cached prefix lean."""
    desc = (c.get("description") or "")[:280]
    return {
        "control_id": c.get("control_id", ""),
        "title":      c.get("title", ""),
        "description": desc,
    }


def _serialize_target_catalogs(source_framework: str) -> tuple[str, list[str]]:
    """Build the cached catalog block — all OTHER active frameworks with
    their controls, in a stable order. Returns (serialized_blob,
    [target_framework_ids])."""
    targets: list[tuple[str, dict]] = []
    for fw_meta in grc_engine.list_supported_frameworks():
        fw_id = fw_meta["id"]
        if fw_id == source_framework:
            continue
        fw = grc_engine.load_framework(fw_id)
        if not fw or not fw.get("controls"):
            # framework stub not yet activated — skip so the prompt stays accurate
            continue
        targets.append((fw_id, fw))

    blocks = []
    target_ids = []
    for fw_id, fw in targets:
        target_ids.append(fw_id)
        compact = [_compact_control(c) for c in fw.get("controls", [])]
        blocks.append(
            f"=== FRAMEWORK: {fw_id} — {fw.get('name', fw_id)} "
            f"({len(compact)} controls) ===\n"
            + json.dumps(compact, ensure_ascii=False, indent=2)
        )
    return "\n\n".join(blocks), target_ids


# ─── LLM call ────────────────────────────────────────────────────────

_SYSTEM_INTRO = (
    "You are a GRC (Governance, Risk, Compliance) expert specialised in "
    "cross-framework control rationalisation. Your task is to identify "
    "controls in target frameworks that are semantically equivalent to a "
    "given source control — i.e. controls that address the SAME underlying "
    "control objective, not just thematically related ones.\n\n"
    "Confidence levels:\n"
    "- high:   identical requirement wording / clear 1:1 mapping\n"
    "- medium: substantially the same objective with minor scope or "
    "          phrasing difference\n"
    "- low:    partially overlapping objective; useful but not a full "
    "          substitute\n\n"
    "Skip a target framework entirely if no genuine equivalent exists. "
    "Do NOT force a mapping just to fill the slot. Quality over coverage."
)


def _build_user_prompt(source_framework: str, src_ctrl: dict,
                       target_ids: list[str]) -> str:
    return (
        f"SOURCE CONTROL ({source_framework}):\n"
        f"- control_id: {src_ctrl.get('control_id', '')}\n"
        f"- title: {src_ctrl.get('title', '')}\n"
        f"- description: {src_ctrl.get('description', '')}\n\n"
        f"TARGET FRAMEWORKS (search these only): {', '.join(target_ids)}\n\n"
        f"Find the semantically equivalent control(s) in each target "
        f"framework where they exist. For each match, provide a 1-2 "
        f"sentence rationale explaining WHY the source and target "
        f"controls address the same objective.\n\n"
        f"Return STRICT JSON only — no preamble, no markdown fences, "
        f"no commentary. Schema:\n"
        f'{{"mappings": [{{"target_framework": "...", '
        f'"target_control_id": "...", "target_control_title": "...", '
        f'"confidence": "high|medium|low", "rationale": "..."}}]}}\n\n'
        f"If no genuine equivalents exist in any target framework, "
        f'return {{"mappings": []}}.'
    )


def _parse_response_text(text: str) -> dict:
    """Strip optional markdown fences and return the parsed JSON dict."""
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("no JSON object found in mapper response")
    return json.loads(cleaned[start:end])


def find_equivalent_controls(source_framework: str,
                              source_control_id: str) -> list[dict]:
    """Discover semantically equivalent controls in every OTHER active
    framework. Returns a list of dicts ready for `database.save_mappings`.

    Empty list is a valid answer: "we asked Claude and there are no
    genuine cross-framework equivalents for this control".

    Raises on transport / parse / validation failure so the caller can
    decide whether to swallow + degrade or retry.
    """
    fw = grc_engine.load_framework(source_framework)
    if not fw:
        raise ValueError(f"Source framework {source_framework} not loaded")
    src_ctrl = next(
        (c for c in fw.get("controls", []) if c.get("control_id") == source_control_id),
        None,
    )
    if not src_ctrl:
        raise ValueError(
            f"Control {source_control_id} not found in {source_framework}")

    catalogs_blob, target_ids = _serialize_target_catalogs(source_framework)
    if not target_ids:
        # nothing to map against — degenerate but valid
        return []

    # Cached system: stable intro + heavy catalog blob. Putting the cache
    # breakpoint on the LAST text block of `system` caches everything up
    # through it (intro + catalogs). The source control goes in `user`
    # content, which varies per call and stays cheap.
    system = [
        {"type": "text", "text": _SYSTEM_INTRO},
        {
            "type": "text",
            "text": f"=== TARGET CONTROL CATALOGS ===\n\n{catalogs_blob}",
            "cache_control": {"type": "ephemeral"},
        },
    ]
    user_prompt = _build_user_prompt(source_framework, src_ctrl, target_ids)

    client = grc_engine.get_client()
    # Match the streaming pattern used by run_gap_analysis — keeps long
    # responses safe under the SDK's HTTP timeout.
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for _ in stream.text_stream:
            pass
        response = stream.get_final_message()

    raw = response.content[0].text if response.content else ""
    parsed = _parse_response_text(raw)

    try:
        validated = MappingResponse.model_validate(parsed)
    except ValidationError as e:
        # Surface the validation error — get_or_compute_mappings in the
        # engine will catch it and degrade gracefully.
        raise ValueError(f"mapper response failed schema validation: {e}") from e

    # Drop any mapping pointing at a framework outside the target set —
    # the model occasionally invents a synonym (e.g. "ISO/IEC 27001" vs
    # "ISO27001:2022"). We deliberately don't try to rescue those: if
    # the framework ID isn't an exact match for one we know, the row is
    # useless downstream.
    target_set = set(target_ids)
    out: list[dict] = []
    for m in validated.mappings:
        if m.target_framework not in target_set:
            logger.info(
                "discarding mapping to unknown target_framework=%r "
                "(source=%s/%s)",
                m.target_framework, source_framework, source_control_id,
            )
            continue
        out.append(m.model_dump())

    # Log cache effectiveness once per call — helps confirm caching is
    # actually firing across the ~530-control precompute run.
    try:
        usage = response.usage
        logger.info(
            "control_mapper usage source=%s/%s cache_creation=%s "
            "cache_read=%s input=%s output=%s mappings=%d",
            source_framework, source_control_id,
            getattr(usage, "cache_creation_input_tokens", None),
            getattr(usage, "cache_read_input_tokens", None),
            getattr(usage, "input_tokens", None),
            getattr(usage, "output_tokens", None),
            len(out),
        )
    except Exception:  # noqa: BLE001 — telemetry only, never break the call
        pass

    return out
