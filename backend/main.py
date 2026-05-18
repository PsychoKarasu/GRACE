"""
GRACE Prototype — FastAPI Backend
All REST endpoints — /api/v1/
"""
import json
import io
import re
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import fitz  # PyMuPDF
import docx2txt

from modules.database import (
    init_db, register_document, get_document, list_documents,
    create_run, complete_run, get_run, list_runs,
    save_findings, list_findings, update_operational_status,
    get_kpi_summary, save_output_document, list_output_documents
)
from modules.grc_engine import (
    run_gap_analysis, generate_document, explain_control,
    list_supported_frameworks, load_framework
)

app = FastAPI(
    title="GRACE API",
    description="Governance, Risk, Assurance & Compliance Engine — Prototype v1.0",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # prototype only — restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise DB on startup
@app.on_event("startup")
def on_startup():
    init_db()


# ─── Health ──────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Real liveness/readiness probe.

    - 'ok'       : DB reachable AND Anthropic API key configured
    - 'degraded' : DB reachable but API key missing (read-only)
    - 'down'     : DB unreachable (returns HTTP 503)
    """
    import os
    from fastapi import HTTPException
    from modules.database import get_db

    try:
        conn = get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    api_key_ok = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())

    if not db_ok:
        raise HTTPException(status_code=503, detail={
            "status": "down", "service": "GRACE API", "db": False,
        })

    status = "ok" if api_key_ok else "degraded"
    return {
        "status": status,
        "service": "GRACE API",
        "version": "1.0.0-prototype",
        "db": True,
        "api_key": api_key_ok,
    }


# ─── Admin (prototype only) ──────────────────────────────────────────

@app.post("/api/v1/admin/reset")
def reset_prototype_data():
    """Wipe all user-generated data — uploaded/generated documents,
    assessment runs, findings, gaps, translations and output documents.
    Framework catalogs and the schema itself are untouched. Prototype-
    only convenience endpoint, not safe for production use."""
    from modules.database import get_db
    conn = get_db()
    tables = [
        "finding_translations",
        "gaps",
        "findings",
        "audit_events",
        "assessment_runs",
        "output_documents",
        "documents",
    ]
    counts = {}
    for table in tables:
        try:
            row = conn.execute(f"SELECT COUNT(*) as n FROM {table}").fetchone()
            counts[table] = row["n"]
            conn.execute(f"DELETE FROM {table}")
        except Exception:
            counts[table] = None
    conn.commit()
    conn.close()
    return {"status": "reset_complete", "deleted": counts}


# ─── Frameworks ──────────────────────────────────────────────────────

@app.get("/api/v1/frameworks")
def get_frameworks():
    return {"frameworks": list_supported_frameworks()}


@app.get("/api/v1/frameworks/{framework_id}/controls")
def get_controls(framework_id: str):
    fw = load_framework(framework_id)
    if not fw:
        raise HTTPException(404, detail=f"Framework {framework_id} not found or not loaded")
    return {"framework_id": framework_id, "controls": fw.get("controls", [])}


@app.get("/api/v1/frameworks/{framework_id}/controls/{control_id}/explain")
def explain(framework_id: str, control_id: str, language: Optional[str] = "en"):
    explanation = explain_control(framework_id, control_id, language=language)
    return {"framework_id": framework_id, "control_id": control_id, "explanation": explanation}


# ─── Documents ───────────────────────────────────────────────────────

class DocumentText(BaseModel):
    title: str
    content: str
    owner: Optional[str] = "demo"
    business_unit: Optional[str] = "Security"


@app.post("/api/v1/documents/text", status_code=201)
def register_text_document(body: DocumentText):
    result = register_document(body.title, body.content, body.owner, body.business_unit)
    return result


@app.post("/api/v1/documents/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    owner: str = Form("demo"),
    business_unit: str = Form("Security")
):
    content_bytes = await file.read()
    fname = file.filename or "document"
    ext = Path(fname).suffix.lower()

    if ext == ".pdf":
        with fitz.open(stream=content_bytes, filetype="pdf") as doc:
            text = "\n".join(page.get_text() for page in doc)
    elif ext in (".docx", ".doc"):
        text = docx2txt.process(io.BytesIO(content_bytes))
    elif ext == ".xlsx":
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(content_bytes), read_only=True, data_only=True)
        parts = []
        for sheet in wb.worksheets:
            parts.append(f"# Sheet: {sheet.title}")
            for row in sheet.iter_rows(values_only=True):
                cells = ["" if v is None else str(v) for v in row]
                if any(cells):
                    parts.append("\t".join(cells))
        text = "\n".join(parts)
    elif ext == ".csv":
        import csv
        raw = content_bytes.decode("utf-8-sig", errors="replace")
        reader = csv.reader(io.StringIO(raw))
        text = "\n".join("\t".join(row) for row in reader)
    else:
        text = content_bytes.decode("utf-8", errors="replace")

    if not text.strip():
        raise HTTPException(400, detail="Could not extract text from document")

    result = register_document(fname, text, owner, business_unit)
    result["character_count"] = len(text)
    return result


@app.get("/api/v1/documents")
def get_documents():
    return {"documents": list_documents()}


@app.get("/api/v1/documents/output")
def get_output_documents():
    return {"documents": list_output_documents()}


@app.get("/api/v1/documents/{document_id}")
def get_doc(document_id: str):
    doc = get_document(document_id)
    if not doc:
        raise HTTPException(404, detail="Document not found")
    return doc


# ─── Assessment ──────────────────────────────────────────────────────

class AssessmentRequest(BaseModel):
    document_id: str
    framework: str
    controls_scope: Optional[list] = None
    channel: Optional[str] = "web"
    language: Optional[str] = "en"


# In-memory run status store (lightweight for prototype)
_run_results: dict = {}


def _run_assessment_bg(run_id: str, document_id: str, framework: str,
                       controls_scope: list, language: str = "en"):
    """Background task: run assessment and persist results."""
    try:
        doc = get_document(document_id)
        if not doc:
            complete_run(run_id, "error", "Document not found")
            return

        def progress(msg):
            _run_results[run_id] = {"status": "running", "message": msg}

        result = run_gap_analysis(
            document_text=doc["content_text"],
            document_title=doc["title"],
            framework_id=framework,
            controls_scope=controls_scope,
            progress_callback=progress,
            language=language,
        )
        finding_ids = save_findings(run_id, document_id, result, language=language)
        complete_run(run_id, "completed")
        _run_results[run_id] = {
            "status": "completed",
            "result": result,
            "finding_ids": finding_ids
        }
    except Exception as e:
        complete_run(run_id, "error", str(e))
        _run_results[run_id] = {"status": "error", "error": str(e)}


@app.post("/api/v1/assessments/run", status_code=202)
def start_assessment(body: AssessmentRequest, background_tasks: BackgroundTasks):
    run_id = create_run(body.document_id, body.framework, body.controls_scope, body.channel)
    _run_results[run_id] = {"status": "pending"}
    background_tasks.add_task(
        _run_assessment_bg, run_id, body.document_id, body.framework,
        body.controls_scope, body.language
    )
    return {"run_id": run_id, "status": "pending", "message": "Assessment started"}


@app.get("/api/v1/assessments/{run_id}")
def poll_run(run_id: str):
    in_memory = _run_results.get(run_id)
    if in_memory:
        return in_memory
    db_run = get_run(run_id)
    if not db_run:
        raise HTTPException(404, detail="Run not found")
    return {"status": db_run["status"]}


@app.get("/api/v1/assessments")
def get_runs():
    return {"runs": list_runs()}


# ─── Synchronous assessment (for Streamlit polling UI) ───────────────

@app.post("/api/v1/assessments/run-sync")
def run_assessment_sync(body: AssessmentRequest):
    """Run assessment synchronously and return result immediately."""
    doc = get_document(body.document_id)
    if not doc:
        raise HTTPException(404, detail="Document not found")

    run_id = create_run(body.document_id, body.framework, body.controls_scope, body.channel)
    try:
        result = run_gap_analysis(
            document_text=doc["content_text"],
            document_title=doc["title"],
            framework_id=body.framework,
            controls_scope=body.controls_scope,
            language=body.language,
        )
        finding_ids = save_findings(run_id, body.document_id, result, language=body.language or "en")
        complete_run(run_id, "completed")
        return {"run_id": run_id, "status": "completed", "result": result, "finding_ids": finding_ids}
    except Exception as e:
        complete_run(run_id, "error", str(e))
        raise HTTPException(500, detail=str(e))


# ─── Ask GRACE: unified natural-language workspace ───────────────────
#
# Single entry point that routes the request to the right downstream
# pipeline. Keeps the old endpoints intact (callers like the legacy
# Assessment widget can still hit them), but the new Ask GRACE panel
# in the UI talks ONLY to /api/v1/ask. Intent classification is a
# straightforward keyword heuristic today — well-isolated so we can
# swap it for a Claude-based router later without touching the
# dispatch logic.

class AskRequest(BaseModel):
    query: str
    document_ids: Optional[list] = None
    framework_id: Optional[str] = None
    language: Optional[str] = "en"


_INTENT_KEYWORDS = {
    "explain":         ["explain ", "spiega ", "what is ", "cosa è ", "cos'è "],
    "query_findings":  ["finding", "registr", "open", "aperti", "critical", "critici",
                        "list ", "show me", "mostra", "summari", "riassum"],
    # 'analyze_new' is inferred from STRUCTURED signals (document_ids +
    # framework_id), not keywords — see classify_intent below.
}


def classify_intent(query: str, has_docs: bool, has_framework: bool) -> str:
    """Lightweight intent router.

    Priority:
      1. analyze_new   — user attached/pasted content AND picked a framework
      2. explain       — query starts with 'explain X', 'what is X' …
      3. query_findings — query mentions findings/registry/critical/etc.
      4. free_qa       — everything else
    """
    q = (query or "").strip().lower()
    if has_docs and has_framework:
        return "analyze_new"
    for kw in _INTENT_KEYWORDS["explain"]:
        if q.startswith(kw):
            return "explain"
    for kw in _INTENT_KEYWORDS["query_findings"]:
        if kw in q:
            return "query_findings"
    return "free_qa"


def _free_qa_response(query: str, framework_id: Optional[str], language: str) -> str:
    """Generic Claude Q&A about GRC. Lightweight system prompt that
    keeps GRACE on-topic without long-context overhead."""
    from modules.grc_engine import get_client, _language_instruction
    system = (
        "You are GRACE, an AI GRC (Governance, Risk, Assurance & Compliance) "
        "analyst. Reply to the user's question concisely, with practical "
        "framing. Cite framework articles or control IDs when relevant. If "
        "the question is outside GRC scope, say so briefly and redirect to "
        "what GRACE can help with."
        + _language_instruction(language, mode="prose")
    )
    user_msg = query
    if framework_id:
        user_msg = f"(Context: user's working framework is {framework_id})\n\n{query}"
    try:
        msg = get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return msg.content[0].text
    except Exception as e:
        return f"_Couldn't reach the model: {e}_"


def _findings_summary_response(query: str, language: str) -> tuple[str, list]:
    """Summarise the findings table in the user's words via Claude.
    Returns (markdown, citations)."""
    findings = list_findings(limit=50)
    if not findings:
        return ("_No findings in the registry yet — run a Gap Analysis to populate it._", [])
    # Build a compact tabular context for Claude
    rows = []
    for f in findings[:30]:
        rows.append(
            f"- [{f.get('severity','?').upper()}] {f.get('framework','')} "
            f"{f.get('control_id','')} · {f.get('control_title','')[:80]} "
            f"(status: {f.get('compliance_status','?')}, op: {f.get('operational_status','?')})"
        )
    from modules.grc_engine import get_client, _language_instruction
    system = (
        "You are GRACE, an AI GRC analyst. You will be given a list of "
        "findings from the user's registry. Answer the user's question by "
        "summarising / filtering / explaining those findings. Be concise, "
        "highlight critical and high severity items first, and reference "
        "control IDs verbatim."
        + _language_instruction(language, mode="prose")
    )
    user_msg = (
        f"User question: {query}\n\n"
        f"Findings registry ({len(findings)} total, showing top 30):\n"
        + "\n".join(rows)
    )
    try:
        msg = get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = msg.content[0].text
    except Exception as e:
        text = f"_Couldn't reach the model: {e}_"
    citations = [
        {"type": "finding", "id": f["finding_id"],
         "label": f"{f.get('framework','')} {f.get('control_id','')}"}
        for f in findings[:8]
    ]
    return (text, citations)


@app.post("/api/v1/ask")
def ask_grace(body: AskRequest):
    """Unified Ask-GRACE dispatcher. Returns a flexible envelope:

    {
      "intent":         "analyze_new" | "explain" | "query_findings" | "free_qa",
      "response_type":  "analysis"    | "explanation" | "findings_qa" | "qa",
      "response_text":  "<markdown>",                           # for non-analysis
      "result":         {...gap_analysis result...} (optional), # for analysis
      "finding_ids":    [...] (optional),
      "citations":      [{"type": "...", "id": "...", "label": "..."}]
    }
    """
    document_ids = body.document_ids or []
    has_docs = bool(document_ids)
    has_fw   = bool(body.framework_id)
    intent   = classify_intent(body.query or "", has_docs, has_fw)
    language = body.language or "en"

    if intent == "analyze_new":
        # Concatenate text from all attached docs into one analysis input,
        # then run the existing gap_analysis pipeline.
        merged_chunks = []
        titles = []
        for did in document_ids:
            d = get_document(did)
            if d:
                merged_chunks.append(d["content_text"])
                titles.append(d["title"])
        merged_text  = "\n\n---\n\n".join(merged_chunks)
        merged_title = " + ".join(titles) if titles else "Untitled"

        run_id = create_run(document_ids[0], body.framework_id, None, "ask_grace")
        try:
            result = run_gap_analysis(
                document_text=merged_text,
                document_title=merged_title,
                framework_id=body.framework_id,
                controls_scope=None,
                language=language,
            )
            finding_ids = save_findings(run_id, document_ids[0], result, language=language)
            complete_run(run_id, "completed")
            return {
                "intent":        intent,
                "response_type": "analysis",
                "result":        result,
                "finding_ids":   finding_ids,
                "run_id":        run_id,
                "citations":     [{"type": "document", "id": did, "label": ttl}
                                  for did, ttl in zip(document_ids, titles)],
            }
        except Exception as e:
            complete_run(run_id, "error", str(e))
            return {"intent": intent, "response_type": "error",
                    "response_text": f"_Analysis failed: {e}_", "citations": []}

    if intent == "explain":
        # Try to parse 'explain CONTROL_ID' or 'spiega CONTROL_ID'.
        # Fall back to free_qa if no recognisable control ID.
        import re as _re
        m = _re.search(r"([A-Z]+\.?[A-Z0-9.\-]+|Art\.\d+(?:\.\d+)*\.?[a-z]?)", body.query or "")
        if m and body.framework_id:
            ctrl_id = m.group(1)
            from modules.grc_engine import explain_control
            text = explain_control(body.framework_id, ctrl_id, language=language)
            return {
                "intent":        intent,
                "response_type": "explanation",
                "response_text": text,
                "citations":     [{"type": "control", "id": ctrl_id,
                                   "label": f"{body.framework_id} · {ctrl_id}"}],
            }
        # No control ID matched → free Q&A
        intent = "free_qa"

    if intent == "query_findings":
        text, citations = _findings_summary_response(body.query, language)
        return {
            "intent":        intent,
            "response_type": "findings_qa",
            "response_text": text,
            "citations":     citations,
        }

    # free_qa fallback
    text = _free_qa_response(body.query, body.framework_id, language)
    return {
        "intent":        "free_qa",
        "response_type": "qa",
        "response_text": text,
        "citations":     [],
    }


# ─── Findings ────────────────────────────────────────────────────────

@app.get("/api/v1/findings")
def get_findings(framework: Optional[str] = None, status: Optional[str] = None,
                 operational_status: Optional[str] = None, limit: int = 100,
                 language: Optional[str] = None):
    """Return findings, with user-facing fields lazily translated to
    `language` when it differs from the finding's stored generation
    language. Translations are cached in the finding_translations table
    so each (finding × target_lang) pair only hits Claude once."""
    from modules.database import (
        get_finding_translation, save_finding_translation,
    )
    from modules.grc_engine import translate_finding_fields

    findings = list_findings(framework, status, limit, operational_status)

    if not language or language not in ("en", "it"):
        return {"findings": findings}

    # We deliberately do NOT short-circuit on (stored_language == requested
    # language). The stored language column reflects the language passed
    # to the run, but Claude's output can still come back in a different
    # language (e.g. if the source document was Italian and the prompt
    # only weakly steered output to English). For every (finding ×
    # ui_language) we serve from cache or ask Claude.
    #
    # The first view per pair triggers one Haiku round-trip per finding.
    # We run those Claude calls in PARALLEL via a ThreadPoolExecutor so a
    # 10-finding page costs ~one Haiku-call wall-clock, not ten — the
    # frontend no longer freezes for 30 s on the first Registry visit.
    import concurrent.futures as _cf
    from threading import Lock

    pending = []        # findings that need a Claude call
    for f in findings:
        fid = f["finding_id"]
        cached = get_finding_translation(fid, language)
        if cached:
            f["description"]          = cached["description"]
            f["recommended_action"]   = cached["recommended_action"]
            f["regulatory_reference"] = cached["regulatory_reference"]
            if cached.get("control_title"):
                f["control_title"]    = cached["control_title"]
            f["language"]             = language
        else:
            pending.append(f)

    if pending:
        def _translate_one(f):
            return f, translate_finding_fields(
                f.get("description", ""),
                f.get("recommended_action", ""),
                f.get("regulatory_reference", ""),
                language,
                control_title=f.get("control_title", ""),
            )

        with _cf.ThreadPoolExecutor(max_workers=min(8, len(pending))) as ex:
            for f, translated in ex.map(_translate_one, pending):
                # Apply the translated content in-flight regardless of
                # outcome — when ok=False the originals stay in place,
                # which is the safest fallback for the UI.
                f["description"]          = translated["description"]
                f["recommended_action"]   = translated["recommended_action"]
                f["regulatory_reference"] = translated["regulatory_reference"]
                if translated.get("control_title"):
                    f["control_title"]    = translated["control_title"]
                f["language"]             = language
                # CRITICAL: only persist to the translation cache when
                # the call actually succeeded.
                if translated.get("ok"):
                    save_finding_translation(
                        f["finding_id"], language,
                        translated["description"],
                        translated["recommended_action"],
                        translated["regulatory_reference"],
                        success=True,
                        control_title=translated.get("control_title", ""),
                    )

    return {"findings": findings}


class StatusUpdate(BaseModel):
    operational_status: str
    actor: Optional[str] = "demo_user"


@app.patch("/api/v1/findings/{finding_id}/status")
def patch_finding_status(finding_id: str, body: StatusUpdate):
    valid = {"new","acknowledged","in_progress","resolved","accepted_risk","closed","dismissed"}
    if body.operational_status not in valid:
        raise HTTPException(400, detail=f"Invalid status. Must be one of: {valid}")
    update_operational_status(finding_id, body.operational_status, body.actor)
    return {"finding_id": finding_id, "operational_status": body.operational_status}


# ─── Document Generation ─────────────────────────────────────────────

class GenerateRequest(BaseModel):
    framework_id: str
    doc_type: str
    context: dict = {}
    run_id: Optional[str] = None
    language: Optional[str] = "en"


@app.post("/api/v1/generate")
def generate(body: GenerateRequest):
    try:
        content = generate_document(body.doc_type, body.framework_id, body.context, body.language)
        doc_out_id = save_output_document(body.doc_type, body.framework_id,
                                           body.run_id, content)
        return {"document_out_id": doc_out_id, "doc_type": body.doc_type,
                "framework_id": body.framework_id, "content": content}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


class ExportRequest(BaseModel):
    content: str
    format: str  # "pdf" | "docx"
    filename: Optional[str] = "GRACE_Document"


@app.post("/api/v1/generate/export")
def export_document(body: ExportRequest):
    from modules.export import markdown_to_pdf_bytes, markdown_to_docx_bytes

    fmt = body.format.lower()
    if fmt == "pdf":
        try:
            data = markdown_to_pdf_bytes(body.content)
        except Exception as e:
            raise HTTPException(500, detail=f"PDF export failed: {e}")
        media_type = "application/pdf"
    elif fmt == "docx":
        try:
            data = markdown_to_docx_bytes(body.content)
        except Exception as e:
            raise HTTPException(500, detail=f"DOCX export failed: {e}")
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        raise HTTPException(400, detail="format must be 'pdf' or 'docx'")

    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", body.filename or "GRACE_Document")
    return StreamingResponse(
        io.BytesIO(data),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.{fmt}"'},
    )


# ─── KPI / Dashboard ─────────────────────────────────────────────────

@app.get("/api/v1/kpi/summary")
def kpi_summary():
    return get_kpi_summary()
