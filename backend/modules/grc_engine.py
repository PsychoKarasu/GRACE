"""
GRACE Prototype — GRC Engine Core
Orchestrates: document chunking, framework mapping, Claude call, output validation.
"""
import json
import re
import yaml
import hashlib
import logging
from pathlib import Path
from typing import Optional
import anthropic

logger = logging.getLogger(__name__)

PROMPT_DIR = Path("/prompt-library") if Path("/prompt-library").exists() \
             else Path(__file__).parent.parent.parent / "prompt-library"
FRAMEWORK_DIR = Path(__file__).parent.parent / "data" / "frameworks"


LANGUAGE_NAME = {
    "en": "English",
    "it": "Italian",
}


def _language_instruction(language: str, mode: str = "structured") -> str:
    """
    Build an instruction line that forces the model to respond in `language`,
    INDEPENDENTLY of the source document's language. mode='structured' is
    for JSON output where enum values and control IDs must stay in English.
    mode='prose' is for free text (policies, explanations).
    """
    lang_name = LANGUAGE_NAME.get(language, "English")
    # NB: this instruction MUST fire even for language == 'en'. Without it,
    # an Italian source document would lead Claude to mirror the document's
    # language in its output, ignoring the user's language toggle.
    if mode == "structured":
        return (
            f"\n\nOUTPUT LANGUAGE: All free-text fields (executive_summary, "
            f"finding, evidence_found, evidence_required, remediation, "
            f"regulatory_reference where it is descriptive) MUST be written "
            f"in {lang_name}, regardless of the language of the source "
            f"document. Schema enum values (compliant, partial, "
            f"non_compliant, no_evidence, not_applicable, critical, high, "
            f"medium, low) and control IDs MUST remain in English."
        )
    return (
        f"\n\nOUTPUT LANGUAGE: Respond entirely in {lang_name}, "
        f"regardless of the language of the source document."
    )

# Anthropic client — reads ANTHROPIC_API_KEY from environment
_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


# ─── Framework Library ────────────────────────────────────────────

def load_framework(framework_id: str) -> dict:
    """Load control catalog JSON for a given framework."""
    mapping = {
        "ISO27001:2022": "iso27001_2022.json",
        "GDPR":          "gdpr.json",
        "SOC2":          "soc2.json",
        "NIS2":          "nis2.json",
        "NISTCSF2.0":    "nistcsf2_0.json",
        "PCI-DSS4.0.1":  "pci_dss_4_0_1.json",
        "HIPAA":         "hipaa.json",
        "DORA":          "dora.json",
        "ISO42001":      "iso42001.json",
        "EUAIACT":       "eu_ai_act.json",
    }
    fname = mapping.get(framework_id)
    if not fname:
        return {}
    path = FRAMEWORK_DIR / fname
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def list_supported_frameworks() -> list:
    return [
        {"id": "ISO27001:2022", "name": "ISO/IEC 27001:2022",     "category": "Information Security",    "controls": 93,  "priority": "P0"},
        {"id": "GDPR",          "name": "GDPR 2016/679",          "category": "Privacy & Data Protection","controls": 99,  "priority": "P0"},
        {"id": "SOC2",          "name": "SOC 2 TSC 2017",         "category": "Information Security",    "controls": 35,  "priority": "P0"},
        {"id": "NIS2",          "name": "NIS2 Directive 2022/2555","category": "Cybersecurity Regulation","controls": 10,  "priority": "P1"},
        {"id": "NISTCSF2.0",    "name": "NIST CSF 2.0",           "category": "Cybersecurity",           "controls": 106, "priority": "P0"},
        {"id": "PCI-DSS4.0.1",  "name": "PCI DSS v4.0.1",        "category": "Financial Services",      "controls": 264, "priority": "P0"},
        {"id": "HIPAA",         "name": "HIPAA Security Rule",     "category": "Privacy & Data Protection","controls": 54,  "priority": "P0"},
        {"id": "DORA",          "name": "DORA 2022/2554",          "category": "Financial Services",      "controls": 64,  "priority": "P1"},
        {"id": "ISO42001",      "name": "ISO/IEC 42001:2023",      "category": "AI & Governance",         "controls": 38,  "priority": "P1"},
        {"id": "EUAIACT",       "name": "EU AI Act 2024/1689",     "category": "AI & Governance",         "controls": 4,   "priority": "P1"},
    ]


# ─── Prompt Library ────────────────────────────────────────────────

def load_framework_prompt(framework_id: str) -> str:
    mapping = {
        "ISO27001:2022": "iso27001_2022.yaml",
        "GDPR":          "gdpr.yaml",
        "SOC2":          "soc2.yaml",
        "NIS2":          "nis2.yaml",
        "NISTCSF2.0":    "nistcsf2_0.yaml",
        "PCI-DSS4.0.1":  "pci_dss_4_0_1.yaml",
        "HIPAA":         "hipaa.yaml",
        "DORA":          "dora.yaml",
        "ISO42001":      "iso42001.yaml",
        "EUAIACT":       "eu_ai_act.yaml",
    }
    fname = mapping.get(framework_id, "")
    path = PROMPT_DIR / "frameworks" / fname
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f)
        return data.get("system_prompt", "")
    # Fallback generic prompt
    return f"You are an expert {framework_id} compliance auditor. Assess the document and return a structured gap assessment JSON."


def load_output_prompt(output_type: str) -> str:
    path = PROMPT_DIR / "outputs" / f"{output_type}.yaml"
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f)
        return data.get("output_schema_prompt", "")
    return ""


# ─── Document Chunking ────────────────────────────────────────────

def chunk_document(text: str, chunk_size: int = 3000) -> list[str]:
    """Simple sentence-boundary chunking for prototype."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current, current_len = [], [], 0
    for sent in sentences:
        if current_len + len(sent) > chunk_size and current:
            chunks.append(" ".join(current))
            current, current_len = [], 0
        current.append(sent)
        current_len += len(sent)
    if current:
        chunks.append(" ".join(current))
    return chunks if chunks else [text[:chunk_size]]


def select_relevant_controls(document_text: str, framework: dict, max_controls: int = 12) -> list:
    """Keyword-based relevance scoring to select controls for deep analysis."""
    doc_lower = document_text.lower()
    scored = []
    for ctrl in framework.get("controls", []):
        score = 0
        for kw in ctrl.get("keywords", []):
            if kw.lower() in doc_lower:
                score += 1
        scored.append((score, ctrl))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [ctrl for _, ctrl in scored[:max_controls]]


# ─── Core Assessment Engine ───────────────────────────────────────

def run_gap_analysis(document_text: str, document_title: str,
                     framework_id: str, controls_scope: Optional[list] = None,
                     progress_callback=None, language: str = "en") -> dict:
    """
    Full gap analysis pipeline:
    1. Load framework and prompt
    2. Select relevant controls
    3. Call Claude with structured prompt
    4. Parse and validate output
    """
    framework = load_framework(framework_id)
    if not framework:
        raise ValueError(f"Framework {framework_id} not loaded. Supported: ISO27001:2022, GDPR, SOC2")

    all_controls = framework.get("controls", [])
    if controls_scope:
        controls = [c for c in all_controls if c["control_id"] in controls_scope]
    else:
        controls = select_relevant_controls(document_text, framework, max_controls=10)

    if progress_callback:
        progress_callback(f"Selected {len(controls)} controls for analysis...")

    fw_prompt   = load_framework_prompt(framework_id)
    out_prompt  = load_output_prompt("gap_assessment")
    system      = fw_prompt + "\n\n" + out_prompt + _language_instruction(language, "structured")

    controls_str = json.dumps([{
        "control_id":    c["control_id"],
        "control_title": c["title"],
        "description":   c["description"],
        "keywords":      c["keywords"][:5],
    } for c in controls], indent=2)

    doc_excerpt = document_text[:60000]  # ~20K tokens, well within 200K context

    user_content = f"""Analyze the following document for compliance with {framework_id}.

DOCUMENT TITLE: {document_title}

DOCUMENT CONTENT:
{doc_excerpt}

CONTROLS TO ASSESS:
{controls_str}

For each control listed above, assess the document and produce the structured gap assessment JSON.
Remember: find what IS present AND what is MISSING. Be specific to this document's actual content."""

    if progress_callback:
        progress_callback("Calling Claude AI for compliance analysis...")

    client = get_client()
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=32768,
        system=system,
        messages=[{"role": "user", "content": user_content}]
    ) as stream:
        for _ in stream.text_stream:
            pass
        response = stream.get_final_message()

    raw = response.content[0].text
    result = _parse_and_validate(raw, framework_id, document_title)

    if progress_callback:
        progress_callback("Validating structured output...")

    return result


def _parse_and_validate(raw: str, framework_id: str, document_title: str) -> dict:
    """Parse LLM output, extract JSON, validate schema."""
    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

    # Find first { ... } block
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in LLM response")

    candidate = cleaned[start:end]
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        # LLM output may be truncated mid-array (max_tokens hit). Try to
        # recover by closing the last complete control entry.
        data = _try_recover_truncated_json(candidate)
        if data is None:
            raise ValueError("JSON parse error and recovery failed")

    # Validate required fields and normalise
    if "controls" not in data:
        data["controls"] = []

    # Always force the canonical framework_id — Claude sometimes echoes
    # back a human-readable name like "NIST CSF 2.0" which then breaks
    # downstream filters that key off the canonical ID (e.g. the
    # Findings Registry framework dropdown).
    data["framework"] = framework_id
    data.setdefault("document_analyzed", document_title)
    data.setdefault("overall_coverage_score", _compute_overall_score(data["controls"]))
    data.setdefault("overall_status", _compute_overall_status(data["overall_coverage_score"]))
    data.setdefault("executive_summary", "Assessment completed.")

    # Normalise each control
    valid_statuses   = {"compliant","partial","non_compliant","no_evidence","not_applicable"}
    valid_severities = {"critical","high","medium","low"}
    valid_efforts    = {"low","medium","high"}
    for ctrl in data["controls"]:
        if ctrl.get("status") not in valid_statuses:
            ctrl["status"] = "no_evidence"
        if ctrl.get("severity") not in valid_severities:
            ctrl["severity"] = "medium"
        if ctrl.get("effort") not in valid_efforts:
            ctrl["effort"] = "medium"
        ctrl.setdefault("coverage_score", _status_to_score(ctrl["status"]))
        ctrl.setdefault("finding", "No specific finding recorded.")
        ctrl.setdefault("evidence_found", [])
        ctrl.setdefault("evidence_required", [])
        ctrl.setdefault("remediation", "Review and address the identified gap.")

    return data


def _try_recover_truncated_json(candidate: str) -> Optional[dict]:
    """
    Attempt to parse JSON that was truncated mid-output (e.g. max_tokens hit).
    Strategy: walk the JSON tracking bracket depth, then trim back to the
    last position where the outer object/array can be closed cleanly.
    """
    depth_curly = 0
    depth_square = 0
    in_string = False
    escape = False
    # Track the position just after each `},` at depth 2 inside a "controls" array
    # (a finished control entry). Last such position is our safe cut point.
    safe_cut = -1
    for i, c in enumerate(candidate):
        if escape:
            escape = False
            continue
        if in_string:
            if c == "\\":
                escape = True
            elif c == '"':
                in_string = False
            continue
        if c == '"':
            in_string = True
        elif c == '{':
            depth_curly += 1
        elif c == '}':
            depth_curly -= 1
            # finished a control entry if we're back to depth 1 (inside the
            # outer object) and inside the controls array (depth_square == 1)
            if depth_curly == 1 and depth_square == 1:
                safe_cut = i + 1
        elif c == '[':
            depth_square += 1
        elif c == ']':
            depth_square -= 1

    if safe_cut == -1:
        return None
    # Trim and close: ... },  →  ... } ] }
    trimmed = candidate[:safe_cut].rstrip().rstrip(",")
    repaired = trimmed + "]}"
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        return None


def _compute_overall_score(controls: list) -> int:
    if not controls:
        return 0
    return round(sum(c.get("coverage_score", _status_to_score(c.get("status","no_evidence")))
                     for c in controls) / len(controls))


def _compute_overall_status(score: int) -> str:
    if score >= 80:
        return "compliant"
    elif score >= 40:
        return "partial"
    return "non_compliant"


def _status_to_score(status: str) -> int:
    return {"compliant":100,"partial":60,"non_compliant":20,
            "no_evidence":10,"not_applicable":100}.get(status, 10)


# ─── Finding translation (lazy, cached) ──────────────────────────

_LANG_LABEL = {"en": "English", "it": "Italian"}


def translate_finding_fields(description: str, recommended_action: str,
                              regulatory_reference: str,
                              target_lang: str,
                              control_title: str = "") -> dict:
    """Translate the user-facing fields of a finding to `target_lang`.

    Retries up to 3 times with exponential back-off to absorb transient
    cold-start failures — the first parallel worker in main.py used to
    fail repeatedly because of pool warm-up, persistently leaving its
    finding untranslated even though the same prompt succeeded for the
    next sibling.

    Returns the four translated fields plus 'ok' (bool). The caller
    must check 'ok' before persisting — caching a failed call would
    serve the originals back on every subsequent view.
    """
    import time as _time
    target_name = _LANG_LABEL.get(target_lang, "English")
    payload = json.dumps({
        "control_title": control_title or "",
        "description": description or "",
        "recommended_action": recommended_action or "",
        "regulatory_reference": regulatory_reference or "",
    }, ensure_ascii=False)

    prompt = (
        f"You are translating a GRC (Governance, Risk, Compliance) finding "
        f"into {target_name}. Translate the natural-language portions of "
        f"every field. Preserve every regulatory reference, control "
        f"identifier (e.g. 'IAM-02', 'Art.21.2.j'), framework name "
        f"(ISO27001, GDPR, NIS2, SOC2…), product name, acronym and "
        f"quoted clause verbatim. Maintain a professional auditor tone.\n\n"
        f"Return ONLY a valid JSON object with exactly these keys: "
        f"\"control_title\", \"description\", \"recommended_action\", "
        f"\"regulatory_reference\". No prose around the JSON.\n\n"
        f"Input JSON:\n{payload}"
    )

    last_error = None
    for attempt in range(3):
        try:
            msg = get_client().messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1800,
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:].strip()
            translated = json.loads(text)
            return {
                "control_title":        translated.get("control_title") or control_title,
                "description":          translated.get("description") or description,
                "recommended_action":   translated.get("recommended_action") or recommended_action,
                "regulatory_reference": translated.get("regulatory_reference") or regulatory_reference,
                "ok":                   True,
            }
        except Exception as e:
            last_error = e
            if attempt < 2:
                _time.sleep(0.4 * (attempt + 1))  # 0.4 s, 0.8 s
                continue

    logger.warning("Translation to %s failed after 3 attempts (%s); "
                   "returning originals, NOT caching",
                   target_lang, last_error)
    return {
        "control_title":        control_title,
        "description":          description,
        "recommended_action":   recommended_action,
        "regulatory_reference": regulatory_reference,
        "ok":                   False,
    }


# ─── Document Generation ─────────────────────────────────────────

def generate_document(doc_type: str, framework_id: str,
                       context: dict, language: str = "en") -> str:
    """
    Generate a structured compliance document.
    doc_type: policy | dpa | soa | risk_register | control_narrative
    """
    prompts = {
        "policy": _policy_prompt,
        "dpa":    _dpa_prompt,
        "soa":    _soa_prompt,
    }
    builder = prompts.get(doc_type, _generic_doc_prompt)
    system, user = builder(framework_id, context, language)
    system = system + _language_instruction(language, "prose")

    client = get_client()
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        system=system,
        messages=[{"role": "user", "content": user}]
    ) as stream:
        for _ in stream.text_stream:
            pass
        response = stream.get_final_message()
    return response.content[0].text


def _policy_prompt(fw: str, ctx: dict, lang: str):
    system = (
        f"You are an expert {fw} compliance consultant. Generate a professional, "
        "audit-ready information security policy document. Use markdown formatting. "
        "Include: document control block (version, date, owner, approver, review date), "
        "purpose, scope, objectives, policy statements mapped to controls, "
        "roles and responsibilities, enforcement, review cycle."
    )
    user = (
        f"Generate an Information Security Policy for:\n"
        f"Organization: {ctx.get('organization','[Organization Name]')}\n"
        f"Framework: {fw}\n"
        f"Scope: {ctx.get('scope','All information assets')}\n"
        f"Language: {lang}"
    )
    return system, user


def _dpa_prompt(fw: str, ctx: dict, lang: str):
    system = (
        "You are an expert GDPR Data Protection Officer and legal counsel. "
        "Generate a complete Data Processing Agreement (DPA) compliant with GDPR Art.28. "
        "Include all mandatory clauses: subject matter, nature and purpose of processing, "
        "type of personal data, categories of data subjects, controller obligations, "
        "processor obligations, sub-processor provisions, security measures, "
        "data subject rights assistance, audit rights, deletion/return of data, "
        "international transfer safeguards. Use formal legal language."
    )
    user = (
        f"Generate a GDPR Art.28 DPA between:\n"
        f"Controller: {ctx.get('controller','[Controller Name]')}\n"
        f"Processor: {ctx.get('processor','[Processor Name]')}\n"
        f"Processing purpose: {ctx.get('purpose','IT services and data processing')}\n"
        f"Data categories: {ctx.get('data_categories','contact data, usage data')}"
    )
    return system, user


def _soa_prompt(fw: str, ctx: dict, lang: str):
    system = (
        "You are an expert ISO 27001:2022 Lead Auditor. "
        "Generate a Statement of Applicability (SoA) document. "
        "For each of the 93 Annex A controls, provide: control ID, control title, "
        "applicable (Yes/No), justification for inclusion/exclusion, "
        "implementation status (Implemented/Partial/Planned/N/A), responsible party. "
        "Format as a structured markdown table."
    )
    org = ctx.get("organization","[Organization Name]")
    user = (
        f"Generate an ISO 27001:2022 Statement of Applicability for {org}.\n"
        f"ISMS Scope: {ctx.get('scope','All IT systems and data processing activities')}\n"
        f"Include all 93 Annex A controls. Mark controls related to physical locations "
        f"as applicable if the organization has physical premises."
    )
    return system, user


def _generic_doc_prompt(fw: str, ctx: dict, lang: str):
    system = f"You are an expert {fw} compliance consultant. Generate professional, audit-ready compliance documentation."
    user   = f"Generate a {ctx.get('doc_type','compliance document')} for {fw}. Context: {json.dumps(ctx)}"
    return system, user


# ─── Cross-framework control mapping (orchestrator) ───────────────

def get_or_compute_mappings(source_framework: str,
                             source_control_id: str) -> list[dict]:
    """Return the list of semantically equivalent controls in other
    active frameworks for the given source control.

    Cache-on-demand:
    - if the cache already has rows for this (framework, control_id),
      we return them straight from SQLite — no Claude call;
    - otherwise we ask Claude via control_mapper.find_equivalent_controls,
      persist the result, and return it.

    Empty list is a valid 'we computed this and found nothing' answer.
    Any failure (Claude transport, JSON parse, Pydantic validation,
    unknown framework) is swallowed and logged — the caller, typically
    the Findings Registry, should never crash because a mapping call
    failed. The DB stays empty so the next view tries again.
    """
    # Lazy import keeps grc_engine importable in environments where the
    # database isn't initialised yet (e.g. unit tests for prompt builders).
    from . import database, control_mapper

    try:
        if database.has_mappings(source_framework, source_control_id):
            return database.get_mappings_for_control(
                source_framework, source_control_id)
    except Exception as e:  # noqa: BLE001
        logger.warning("mapping cache lookup failed for %s/%s: %s",
                       source_framework, source_control_id, e)
        # fall through and try to compute — at worst we'll fail the same way

    try:
        mappings = control_mapper.find_equivalent_controls(
            source_framework, source_control_id)
    except Exception as e:  # noqa: BLE001
        logger.warning("control mapping failed for %s/%s: %s",
                       source_framework, source_control_id, e)
        return []

    try:
        database.save_mappings(source_framework, source_control_id, mappings)
    except Exception as e:  # noqa: BLE001
        # persistence failed but we still have a valid result — return it
        # so the current view isn't degraded; next view will retry the save.
        logger.warning("mapping persistence failed for %s/%s: %s",
                       source_framework, source_control_id, e)
        return mappings

    # Re-read through the same accessor so the caller always sees the
    # canonical ordering (confidence desc, framework asc) and the
    # generated_at timestamp the DB just stamped.
    try:
        return database.get_mappings_for_control(
            source_framework, source_control_id)
    except Exception:
        return mappings


# ─── Explain a control ────────────────────────────────────────────

def explain_control(framework_id: str, control_id: str, language: str = "en") -> str:
    """Plain-language explanation of a specific control."""
    framework = load_framework(framework_id)
    ctrl = next((c for c in framework.get("controls",[]) if c["control_id"] == control_id), None)
    if not ctrl:
        return f"Control {control_id} not found in framework {framework_id}."

    fw_prompt = load_framework_prompt(framework_id)
    system = (fw_prompt + "\nRespond in plain, accessible language. No JSON output needed here — just a clear explanation."
              + _language_instruction(language, "prose"))
    user = (
        f"Explain {framework_id} control {control_id} — '{ctrl['title']}' "
        f"in plain language for a compliance manager with no deep technical background. "
        f"Cover: what it requires, why it matters, what good implementation looks like, "
        f"and the 3 most common gaps you see in practice. Keep it practical and concrete."
    )
    # Non-streaming call — we don't yield tokens to the frontend (the
    # whole result is rendered at once via st.markdown), so streaming
    # only added latency before. Haiku is plenty for an explanation
    # and replies in 2-3 s vs Sonnet's 15-20 s, which used to time out
    # the frontend's 10 s api_get and leave the UI 'spinning then
    # nothing'.
    try:
        msg = get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text
    except Exception as e:
        logger.warning("explain_control failed for %s/%s: %s", framework_id, control_id, e)
        return f"_Could not generate explanation — {e}_"


# ─── Vendor risk assessment summary (Phase 1) ─────────────────────

def generate_vendor_assessment_summary(vendor_name: str, category: str,
                                        questionnaire: list) -> str:
    """Generate a 3-paragraph qualitative summary of a completed vendor
    questionnaire — strengths, key risks, recommended next step. Used by
    POST /api/v1/vendors/{id}/assess. Haiku 4.5 keeps latency low so the
    UI can render the summary inline right after the form submission."""
    if not questionnaire:
        return "_No questionnaire provided — cannot generate a summary._"
    lines = []
    for a in questionnaire:
        lines.append(
            f"- [{a.get('question_id','?')}] (weight={a.get('weight','?')}) "
            f"{a.get('question','')} → answer: {a.get('answer','unknown')}"
            + (f" · notes: {a.get('notes','')}" if a.get('notes') else "")
        )
    user = (
        f"Vendor: {vendor_name}\n"
        f"Category: {category or 'unspecified'}\n\n"
        f"Completed questionnaire:\n" + "\n".join(lines)
    )
    system = (
        "You are a vendor risk analyst. Summarise the key strengths, key "
        "risks and recommended next step in 3 short paragraphs based on "
        "this completed vendor questionnaire. Use markdown with three "
        "bolded paragraph labels: **Strengths**, **Key risks**, "
        "**Recommended next step**. Be concrete and reference the most "
        "important answers verbatim."
    )
    try:
        msg = get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=700,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = (msg.content[0].text or "").strip()
        # Minimal schema validation: must include at least one of the
        # expected section markers; otherwise treat as malformed and fall
        # back to a safe sentinel string.
        if not text or not any(k in text.lower() for k in
                                ("strength", "risk", "recommend")):
            return "_AI summary returned without expected sections._"
        return text
    except Exception as e:
        logger.warning("generate_vendor_assessment_summary failed: %s", e)
        return f"_Could not generate vendor summary — {e}_"


# ─── Synthetic Document Generation (demo dataset) ─────────────────

def generate_synthetic_document(
    framework_id: str,
    persona: dict,
    coverage_profile: dict,
    doc_type_name: str,
    language: str = "en",
    model: str = "claude-haiku-4-5",
) -> dict:
    """
    Generate a SYNTHETIC realistic-but-fictional compliance document for demo
    and testing purposes. The output is watermarked, fictional, and must NEVER
    be used as a real organizational policy.

    Uses prompt caching on the control catalog block, so batch generations
    against the same framework reuse the heavy input cheaply.
    """
    framework = load_framework(framework_id)
    if not framework:
        raise ValueError(f"Framework {framework_id} not loaded")

    framework_name = framework.get("name", framework_id)
    controls_view = [
        {
            "control_id": c["control_id"],
            "title":       c.get("title", ""),
            "description": (c.get("description") or "")[:240],
        }
        for c in framework.get("controls", [])
    ]
    controls_json = json.dumps(controls_view, indent=2)

    base_system = (
        f"You are an expert {framework_name} compliance consultant who has authored "
        "hundreds of audit-ready compliance documents across sectors. You write "
        "documents that read as produced by a real internal compliance team — not "
        "generated boilerplate.\n\n"
        "Given a fictional organization persona, a coverage profile, and a document "
        "type, produce a single compliance document in Markdown with this structure:\n"
        "1. Header banner (mandatory first line): "
        "**SYNTHETIC DEMO DOCUMENT — FICTIONAL ORGANIZATION — NOT REAL DATA**\n"
        "2. Document control block: version, effective date, classification, owner, "
        "approver, next review date\n"
        "3. Body with framework-appropriate sections (purpose, scope, roles, control "
        "statements, references, enforcement, review cycle)\n"
        "4. Explicit references to control IDs from the provided catalog\n\n"
        "CRITICAL RULES (violations require regeneration):\n"
        "- NEVER use real personal names. Use obvious placeholders only (\"[CISO TBD]\", "
        "\"Mario Rossi — CISO\", \"Jane Smith — DPO\").\n"
        "- NEVER use real customer names, real addresses, real phone numbers. Use "
        "@example.com for any email.\n"
        "- Reference controls by their real IDs from the catalog. Depth of reference "
        "MUST match the coverage profile.\n"
        "- Target 1800–2800 words. The document must feel realistic, not toy-sized.\n"
        "- Vary style by persona: a fintech ISMS reads different from a manufacturing one.\n"
        "- Where coverage profile demands gaps, leave them realistically (\"TBD\", missing "
        "procedures, vague timelines, controls referenced but not implemented).\n\n"
        "OUTPUT: Return ONLY the markdown text. No preamble, no code fences."
    )
    if language != "en":
        lang_name = LANGUAGE_NAME.get(language, "English")
        base_system += (
            f"\n\nLANGUAGE: Write the entire document in {lang_name}. Keep control IDs "
            f"and standard names in their original form (e.g. 'ISO/IEC 27001:2022 A.5.15')."
        )

    system = [
        {"type": "text", "text": base_system},
        {
            "type": "text",
            "text": f"=== CONTROL CATALOG ({framework_id}) ===\n{controls_json}",
            "cache_control": {"type": "ephemeral"},
        },
    ]

    user_content = (
        f"Generate a \"{doc_type_name}\" document for the following scenario.\n\n"
        "FICTIONAL ORGANIZATION:\n"
        f"- Name: {persona['name']}\n"
        f"- Sector: {persona['sector']}\n"
        f"- Size: {persona['size']}\n"
        f"- Operational scope: {persona['scope']}\n"
        f"- Technology stack: {persona['tech_stack']}\n"
        f"- Compliance maturity: {persona['maturity']}\n\n"
        f"TARGET FRAMEWORK: {framework_name} ({framework_id})\n\n"
        f"COVERAGE PROFILE: {coverage_profile['description']}\n"
        f"- Target overall coverage: {coverage_profile['target_coverage']}\n"
        f"- Gap density: {coverage_profile['gap_density']}\n"
        f"- Tone: {coverage_profile['tone']}\n\n"
        f"DOCUMENT TYPE: {doc_type_name}\n\n"
        "Produce the document now. Remember: SYNTHETIC banner first line, fictional "
        "names only, real control IDs."
    )

    client = get_client()
    with client.messages.stream(
        model=model,
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        for _ in stream.text_stream:
            pass
        response = stream.get_final_message()

    markdown = response.content[0].text or ""
    if "SYNTHETIC DEMO DOCUMENT" not in markdown[:600]:
        markdown = (
            "**SYNTHETIC DEMO DOCUMENT — FICTIONAL ORGANIZATION — NOT REAL DATA**\n\n"
            + markdown
        )

    usage = response.usage
    return {
        "title": f"{persona['name']} — {doc_type_name} (synthetic)",
        "markdown_content": markdown,
        "framework_id": framework_id,
        "persona_id": persona.get("id"),
        "doc_type": doc_type_name,
        "model": model,
        "usage": {
            "input_tokens":  getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", None),
            "cache_read_input_tokens":     getattr(usage, "cache_read_input_tokens", None),
        },
    }
