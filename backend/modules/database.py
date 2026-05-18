"""
GRACE Prototype — Database Layer
SQLite with full canonical schema matching the production PostgreSQL model.
"""
import sqlite3
import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "db" / "grace.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id     TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            source_uri      TEXT,
            file_hash       TEXT NOT NULL,
            document_type   TEXT,
            owner           TEXT,
            business_unit   TEXT,
            content_text    TEXT,
            registered_at   TEXT NOT NULL,
            registered_by   TEXT,
            deleted_at      TEXT,
            UNIQUE(file_hash)
        );

        CREATE TABLE IF NOT EXISTS assessment_runs (
            run_id          TEXT PRIMARY KEY,
            document_id     TEXT REFERENCES documents(document_id),
            framework       TEXT NOT NULL,
            mode            TEXT DEFAULT 'gap_analysis',
            channel         TEXT DEFAULT 'web',
            requested_by    TEXT,
            status          TEXT DEFAULT 'pending',
            started_at      TEXT NOT NULL,
            completed_at    TEXT,
            error_message   TEXT,
            controls_scope  TEXT
        );

        CREATE TABLE IF NOT EXISTS findings (
            finding_id          TEXT PRIMARY KEY,
            run_id              TEXT REFERENCES assessment_runs(run_id),
            document_id         TEXT REFERENCES documents(document_id),
            framework           TEXT NOT NULL,
            control_id          TEXT NOT NULL,
            control_title       TEXT NOT NULL,
            compliance_status   TEXT NOT NULL,
            severity            TEXT NOT NULL,
            coverage_score      INTEGER,
            confidence          INTEGER DEFAULT 80,
            operational_status  TEXT DEFAULT 'new',
            owner               TEXT,
            due_date            TEXT,
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL,
            language            TEXT DEFAULT 'en'
        );

        CREATE TABLE IF NOT EXISTS gaps (
            gap_id              TEXT PRIMARY KEY,
            finding_id          TEXT UNIQUE REFERENCES findings(finding_id),
            description         TEXT NOT NULL,
            evidence_found      TEXT,
            evidence_required   TEXT,
            recommended_action  TEXT NOT NULL,
            effort              TEXT,
            regulatory_reference TEXT
        );

        CREATE TABLE IF NOT EXISTS output_documents (
            document_out_id TEXT PRIMARY KEY,
            document_type   TEXT NOT NULL,
            framework_id    TEXT,
            related_run_id  TEXT REFERENCES assessment_runs(run_id),
            requested_by    TEXT,
            channel         TEXT DEFAULT 'web',
            language        TEXT DEFAULT 'en',
            format          TEXT DEFAULT 'markdown',
            content_text    TEXT,
            content_json    TEXT,
            quality_score   REAL,
            created_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_events (
            event_id    TEXT PRIMARY KEY,
            actor       TEXT,
            channel     TEXT,
            event_type  TEXT NOT NULL,
            entity_type TEXT,
            entity_id   TEXT,
            details     TEXT,
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS finding_translations (
            finding_id           TEXT NOT NULL,
            language             TEXT NOT NULL,
            description          TEXT,
            recommended_action   TEXT,
            regulatory_reference TEXT,
            control_title        TEXT,
            created_at           TEXT NOT NULL,
            PRIMARY KEY (finding_id, language)
        );

        CREATE TABLE IF NOT EXISTS control_mappings (
            mapping_id           TEXT PRIMARY KEY,
            source_framework     TEXT NOT NULL,
            source_control_id    TEXT NOT NULL,
            target_framework     TEXT NOT NULL,
            target_control_id    TEXT NOT NULL,
            target_control_title TEXT,
            confidence           TEXT NOT NULL CHECK(confidence IN ('high','medium','low')),
            rationale            TEXT,
            generated_at         TEXT NOT NULL,
            UNIQUE(source_framework, source_control_id, target_framework, target_control_id)
        );
        CREATE INDEX IF NOT EXISTS idx_mapping_src
            ON control_mappings(source_framework, source_control_id);
    """)
    # Idempotent migrations for older DBs
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(findings)").fetchall()}
    if "language" not in cols:
        conn.execute("ALTER TABLE findings ADD COLUMN language TEXT DEFAULT 'en'")
    # finding_translations: add success flag (1 = real translation we can
    # trust, 0/NULL = produced by a failed/legacy code path and must be
    # retranslated on next view). Default 0 invalidates ALL pre-existing
    # rows, which is desired — earlier builds (pre PR #28) saved the
    # ORIGINAL fields when the Claude call failed, so those rows would
    # otherwise leave individual findings stuck in their source language.
    ft_cols = {r["name"] for r in conn.execute("PRAGMA table_info(finding_translations)").fetchall()}
    if ft_cols and "success" not in ft_cols:
        conn.execute("ALTER TABLE finding_translations ADD COLUMN success INTEGER DEFAULT 0")
    if ft_cols and "control_title" not in ft_cols:
        # control_title was added later — existing rows have NULL for it.
        # When NULL is read, the caller falls back to the finding's
        # original title (still readable, just not localised).
        conn.execute("ALTER TABLE finding_translations ADD COLUMN control_title TEXT")
    conn.commit()
    conn.close()


def new_id() -> str:
    return str(uuid.uuid4())


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


# ─── Document operations ────────────────────────────────────────────

def register_document(title: str, content: str, owner: str = "demo",
                       business_unit: str = "Security", source_uri: str = "") -> dict:
    file_hash = compute_hash(content)
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT document_id, title FROM documents WHERE file_hash = ?", (file_hash,)
        ).fetchone()
        if existing:
            conn.close()
            return {"document_id": existing["document_id"], "title": existing["title"], "is_new": False}

        doc_id = new_id()
        conn.execute("""
            INSERT INTO documents (document_id, title, source_uri, file_hash,
                                   document_type, owner, business_unit, content_text,
                                   registered_at, registered_by)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (doc_id, title, source_uri or f"upload://{title}", file_hash,
              "policy", owner, business_unit, content,
              now_utc(), "demo_user"))
        conn.commit()
        _log_event("demo_user", "web", "document_registered", "document", doc_id)
        return {"document_id": doc_id, "title": title, "is_new": True}
    finally:
        conn.close()


def get_document(document_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_documents() -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT document_id, title, document_type, owner, business_unit, registered_at "
        "FROM documents WHERE deleted_at IS NULL ORDER BY registered_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Assessment run operations ────────────────────────────────────────

def create_run(document_id: str, framework: str, controls_scope: Optional[list] = None,
               channel: str = "web") -> str:
    run_id = new_id()
    conn = get_db()
    conn.execute("""
        INSERT INTO assessment_runs
        (run_id, document_id, framework, channel, requested_by, status, started_at, controls_scope)
        VALUES (?,?,?,?,?,?,?,?)
    """, (run_id, document_id, framework, channel, "demo_user", "pending",
          now_utc(), json.dumps(controls_scope) if controls_scope else None))
    conn.commit()
    conn.close()
    return run_id


def complete_run(run_id: str, status: str = "completed", error: str = None):
    conn = get_db()
    conn.execute(
        "UPDATE assessment_runs SET status=?, completed_at=?, error_message=? WHERE run_id=?",
        (status, now_utc(), error, run_id)
    )
    conn.commit()
    conn.close()


def get_run(run_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM assessment_runs WHERE run_id = ?", (run_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_runs(limit: int = 20) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT r.run_id, r.framework, r.status, r.started_at, r.completed_at,
               d.title as document_title
        FROM assessment_runs r
        LEFT JOIN documents d ON r.document_id = d.document_id
        ORDER BY r.started_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Finding operations ────────────────────────────────────────────

def save_findings(run_id: str, document_id: str, assessment_result: dict,
                  language: str = "en") -> list:
    """Persist structured findings from LLM output."""
    conn = get_db()
    saved_ids = []
    for ctrl in assessment_result.get("controls", []):
        fid = new_id()
        conn.execute("""
            INSERT INTO findings
            (finding_id, run_id, document_id, framework, control_id, control_title,
             compliance_status, severity, coverage_score, confidence, created_at, updated_at,
             language)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (fid, run_id, document_id,
              assessment_result.get("framework", ""),
              ctrl.get("control_id", ""),
              ctrl.get("control_title", ""),
              ctrl.get("status", "no_evidence"),
              ctrl.get("severity", "medium"),
              ctrl.get("coverage_score", 0),
              80, now_utc(), now_utc(), language))

        gap_id = new_id()
        conn.execute("""
            INSERT INTO gaps
            (gap_id, finding_id, description, evidence_found, evidence_required,
             recommended_action, effort, regulatory_reference)
            VALUES (?,?,?,?,?,?,?,?)
        """, (gap_id, fid,
              ctrl.get("finding", ""),
              json.dumps(ctrl.get("evidence_found", [])),
              json.dumps(ctrl.get("evidence_required", [])),
              ctrl.get("remediation", ""),
              ctrl.get("effort", "medium"),
              ctrl.get("regulatory_reference", "")))
        saved_ids.append(fid)
    conn.commit()
    conn.close()
    return saved_ids


def list_findings(framework: str = None, status: str = None, limit: int = 100,
                  operational_status: str = None) -> list:
    conn = get_db()
    q = """
        SELECT f.finding_id, f.framework, f.control_id, f.control_title,
               f.compliance_status, f.severity, f.coverage_score,
               f.operational_status, f.created_at, f.language,
               g.description, g.recommended_action, g.regulatory_reference,
               g.evidence_required,
               d.title as document_title, d.document_id, r.run_id
        FROM findings f
        LEFT JOIN gaps g ON g.finding_id = f.finding_id
        LEFT JOIN documents d ON d.document_id = f.document_id
        LEFT JOIN assessment_runs r ON r.run_id = f.run_id
        WHERE 1=1
    """
    params = []
    if framework:
        q += " AND f.framework = ?"
        params.append(framework)
    if status:
        q += " AND f.compliance_status = ?"
        params.append(status)
    if operational_status:
        q += " AND f.operational_status = ?"
        params.append(operational_status)
    q += " ORDER BY f.created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_finding(finding_id: str) -> Optional[dict]:
    """Return a single finding row (joined with gaps + documents) or None."""
    conn = get_db()
    row = conn.execute("""
        SELECT f.finding_id, f.framework, f.control_id, f.control_title,
               f.compliance_status, f.severity, f.coverage_score,
               f.operational_status, f.created_at, f.language,
               g.description, g.recommended_action, g.regulatory_reference,
               g.evidence_required,
               d.title as document_title, d.document_id, r.run_id
        FROM findings f
        LEFT JOIN gaps g ON g.finding_id = f.finding_id
        LEFT JOIN documents d ON d.document_id = f.document_id
        LEFT JOIN assessment_runs r ON r.run_id = f.run_id
        WHERE f.finding_id = ?
    """, (finding_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_operational_status(finding_id: str, new_status: str, actor: str = "demo_user"):
    conn = get_db()
    conn.execute(
        "UPDATE findings SET operational_status=?, updated_at=? WHERE finding_id=?",
        (new_status, now_utc(), finding_id)
    )
    conn.commit()
    _log_event(actor, "web", "status_updated", "finding", finding_id,
               {"new_status": new_status})
    conn.close()


# ─── KPI aggregation ────────────────────────────────────────────

def get_finding_translation(finding_id: str, language: str) -> dict | None:
    """Return a cached, TRUSTED translation for the finding or None.

    Rows with success != 1 are treated as a cache miss — they were
    written by an earlier code path that persisted the original fields
    when the Claude call failed.
    """
    conn = get_db()
    row = conn.execute(
        "SELECT description, recommended_action, regulatory_reference, control_title "
        "FROM finding_translations "
        "WHERE finding_id=? AND language=? AND success = 1",
        (finding_id, language),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_finding_translation(finding_id: str, language: str,
                             description: str, recommended_action: str,
                             regulatory_reference: str,
                             success: bool = True,
                             control_title: str = "") -> None:
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO finding_translations "
        "(finding_id, language, description, recommended_action, "
        " regulatory_reference, control_title, created_at, success) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (finding_id, language, description, recommended_action,
         regulatory_reference, control_title, now_utc(),
         1 if success else 0),
    )
    conn.commit()
    conn.close()


def get_kpi_summary() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as n FROM findings WHERE operational_status != 'closed'").fetchone()["n"]
    by_status = {}
    for row in conn.execute("""
        SELECT compliance_status, COUNT(*) as n FROM findings
        WHERE operational_status != 'closed' GROUP BY compliance_status
    """).fetchall():
        by_status[row["compliance_status"]] = row["n"]
    by_severity = {}
    for row in conn.execute("""
        SELECT severity, COUNT(*) as n FROM findings
        WHERE operational_status != 'closed' GROUP BY severity
    """).fetchall():
        by_severity[row["severity"]] = row["n"]
    by_framework = {}
    for row in conn.execute("""
        SELECT framework, COUNT(*) as n,
               ROUND(AVG(coverage_score),1) as avg_score
        FROM findings WHERE operational_status != 'closed'
        GROUP BY framework
    """).fetchall():
        by_framework[row["framework"]] = {"count": row["n"], "avg_score": row["avg_score"]}
    avg_score = conn.execute("SELECT ROUND(AVG(coverage_score),1) as s FROM findings").fetchone()["s"] or 0
    docs = conn.execute("SELECT COUNT(*) as n FROM documents WHERE deleted_at IS NULL").fetchone()["n"]
    runs = conn.execute("SELECT COUNT(*) as n FROM assessment_runs").fetchone()["n"]
    conn.close()
    return {
        "total_open_findings": total,
        "documents_registered": docs,
        "assessment_runs": runs,
        "avg_coverage_score": avg_score,
        "by_status": by_status,
        "by_severity": by_severity,
        "by_framework": by_framework,
    }


# ─── Saved generated documents ────────────────────────────────────

def save_output_document(doc_type: str, framework: str, run_id: Optional[str],
                          content_text: str, quality_score: float = 90.0) -> str:
    doc_id = new_id()
    conn = get_db()
    conn.execute("""
        INSERT INTO output_documents
        (document_out_id, document_type, framework_id, related_run_id,
         requested_by, content_text, quality_score, created_at)
        VALUES (?,?,?,?,?,?,?,?)
    """, (doc_id, doc_type, framework, run_id, "demo_user",
          content_text, quality_score, now_utc()))
    conn.commit()
    conn.close()
    return doc_id


def list_output_documents(limit: int = 20) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT document_out_id, document_type, framework_id,
               quality_score, created_at
        FROM output_documents
        ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Cross-framework control mappings ────────────────────────────

_CONFIDENCE_RANK = {"high": 0, "medium": 1, "low": 2}


def has_mappings(source_framework: str, source_control_id: str) -> bool:
    """Fast existence check: does the cache already contain at least one
    mapping row for this source control? Used to decide whether to invoke
    Claude or just hit the cache."""
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM control_mappings "
        "WHERE source_framework = ? AND source_control_id = ? LIMIT 1",
        (source_framework, source_control_id),
    ).fetchone()
    conn.close()
    return row is not None


def get_mappings_for_control(source_framework: str, source_control_id: str) -> list:
    """Return cached cross-framework mappings for one source control,
    ordered by confidence (high → low) then framework asc."""
    conn = get_db()
    rows = conn.execute("""
        SELECT target_framework, target_control_id, target_control_title,
               confidence, rationale, generated_at
        FROM control_mappings
        WHERE source_framework = ? AND source_control_id = ?
    """, (source_framework, source_control_id)).fetchall()
    conn.close()
    items = [dict(r) for r in rows]
    items.sort(key=lambda m: (_CONFIDENCE_RANK.get(m["confidence"], 99),
                              m["target_framework"]))
    return items


def save_mappings(source_framework: str, source_control_id: str,
                  mappings: list) -> int:
    """Bulk-insert mappings via INSERT OR IGNORE — duplicates (same
    source × target pair) are silently skipped. Returns the number of
    rows actually written. An empty list is still a valid 'we computed
    this and found nothing' answer, so the caller is expected to write
    a sentinel row separately if needed."""
    if not mappings:
        return 0
    conn = get_db()
    inserted = 0
    ts = now_utc()
    for m in mappings:
        conf = (m.get("confidence") or "").lower()
        if conf not in ("high", "medium", "low"):
            conf = "low"
        try:
            cur = conn.execute("""
                INSERT OR IGNORE INTO control_mappings
                (mapping_id, source_framework, source_control_id,
                 target_framework, target_control_id, target_control_title,
                 confidence, rationale, generated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                new_id(),
                source_framework, source_control_id,
                m.get("target_framework", ""),
                m.get("target_control_id", ""),
                m.get("target_control_title", ""),
                conf,
                m.get("rationale", ""),
                ts,
            ))
            inserted += cur.rowcount or 0
        except Exception:
            # never let one bad row sabotage the whole batch
            continue
    conn.commit()
    conn.close()
    return inserted


def count_mappings(source_framework: str, source_control_id: str) -> int:
    """Cheap count of cached mappings — used to populate the
    cross_framework_count badge on each finding without touching Claude."""
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as n FROM control_mappings "
        "WHERE source_framework = ? AND source_control_id = ?",
        (source_framework, source_control_id),
    ).fetchone()
    conn.close()
    return int(row["n"]) if row else 0


# ─── Audit log ────────────────────────────────────────────────────

def _log_event(actor: str, channel: str, event_type: str,
                entity_type: str = None, entity_id: str = None, details: dict = None):
    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO audit_events
            (event_id, actor, channel, event_type, entity_type, entity_id, details, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (new_id(), actor, channel, event_type, entity_type, entity_id,
              json.dumps(details) if details else None, now_utc()))
        conn.commit()
        conn.close()
    except Exception:
        pass  # audit failures must never break the main flow
