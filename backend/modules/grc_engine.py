"""
GRACE Prototype — GRC Engine Core
Orchestrates: document chunking, framework mapping, Claude call, output validation.
"""
import json
import re
import yaml
import hashlib
from pathlib import Path
from typing import Optional
import anthropic

PROMPT_DIR = Path("/prompt-library") if Path("/prompt-library").exists() \
             else Path(__file__).parent.parent.parent / "prompt-library"
FRAMEWORK_DIR = Path(__file__).parent.parent / "data" / "frameworks"

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
        {"id": "NISTCSF2.0",    "name": "NIST CSF 2.0",           "category": "Cybersecurity",           "controls": 106, "priority": "P0", "coming_soon": True},
        {"id": "PCI-DSS4.0.1",  "name": "PCI DSS v4.0.1",        "category": "Financial Services",      "controls": 264, "priority": "P0", "coming_soon": True},
        {"id": "HIPAA",         "name": "HIPAA Security Rule",     "category": "Privacy & Data Protection","controls": 54,  "priority": "P0", "coming_soon": True},
        {"id": "DORA",          "name": "DORA 2022/2554",          "category": "Financial Services",      "controls": 64,  "priority": "P1", "coming_soon": True},
        {"id": "ISO42001",      "name": "ISO/IEC 42001:2023",      "category": "AI & Governance",         "controls": 38,  "priority": "P1", "coming_soon": True},
        {"id": "EUAIACT",       "name": "EU AI Act 2024/1689",     "category": "AI & Governance",         "controls": 4,   "priority": "P1", "coming_soon": True},
    ]


# ─── Prompt Library ────────────────────────────────────────────────

def load_framework_prompt(framework_id: str) -> str:
    mapping = {
        "ISO27001:2022": "iso27001_2022.yaml",
        "GDPR":          "gdpr.yaml",
        "SOC2":          "soc2.yaml",
        "NIS2":          "nis2.yaml",
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
                     progress_callback=None) -> dict:
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
    system      = fw_prompt + "\n\n" + out_prompt

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

    data.setdefault("framework", framework_id)
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


# ─── Explain a control ────────────────────────────────────────────

def explain_control(framework_id: str, control_id: str) -> str:
    """Plain-language explanation of a specific control."""
    framework = load_framework(framework_id)
    ctrl = next((c for c in framework.get("controls",[]) if c["control_id"] == control_id), None)
    if not ctrl:
        return f"Control {control_id} not found in framework {framework_id}."

    fw_prompt = load_framework_prompt(framework_id)
    system = fw_prompt + "\nRespond in plain, accessible English. No JSON output needed here — just a clear explanation."
    user = (
        f"Explain {framework_id} control {control_id} — '{ctrl['title']}' "
        f"in plain language for a compliance manager with no deep technical background. "
        f"Cover: what it requires, why it matters, what good implementation looks like, "
        f"and the 3 most common gaps you see in practice. Keep it practical and concrete."
    )
    client = get_client()
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": user}]
    ) as stream:
        for _ in stream.text_stream:
            pass
        response = stream.get_final_message()
    return response.content[0].text
