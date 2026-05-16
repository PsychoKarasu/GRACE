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

    for f in findings:
        src = (f.get("language") or "en").lower()
        if src == language:
            continue
        cached = get_finding_translation(f["finding_id"], language)
        if cached:
            f["description"]          = cached["description"]
            f["recommended_action"]   = cached["recommended_action"]
            f["regulatory_reference"] = cached["regulatory_reference"]
        else:
            translated = translate_finding_fields(
                f.get("description", ""),
                f.get("recommended_action", ""),
                f.get("regulatory_reference", ""),
                language,
            )
            save_finding_translation(
                f["finding_id"], language,
                translated["description"],
                translated["recommended_action"],
                translated["regulatory_reference"],
            )
            f["description"]          = translated["description"]
            f["recommended_action"]   = translated["recommended_action"]
            f["regulatory_reference"] = translated["regulatory_reference"]
        f["language"] = language

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
