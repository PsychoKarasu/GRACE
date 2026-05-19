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

        -- ── Phase 1: business-ready GRC modules ──────────────────────
        CREATE TABLE IF NOT EXISTS risks (
            risk_id          TEXT PRIMARY KEY,
            title            TEXT NOT NULL,
            description      TEXT,
            category         TEXT,
            likelihood       INTEGER CHECK(likelihood BETWEEN 1 AND 5),
            impact           INTEGER CHECK(impact BETWEEN 1 AND 5),
            inherent_score   INTEGER,
            residual_score   INTEGER,
            treatment_plan   TEXT,
            treatment_notes  TEXT,
            owner            TEXT,
            status           TEXT DEFAULT 'open',
            linked_controls  TEXT,
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_risks_status   ON risks(status);
        CREATE INDEX IF NOT EXISTS idx_risks_category ON risks(category);
        CREATE INDEX IF NOT EXISTS idx_risks_owner    ON risks(owner);

        CREATE TABLE IF NOT EXISTS vendors (
            vendor_id        TEXT PRIMARY KEY,
            name             TEXT NOT NULL,
            category         TEXT,
            contact_email    TEXT,
            contract_url     TEXT,
            risk_score       INTEGER,
            risk_tier        TEXT,
            last_assessed_at TEXT,
            questionnaire    TEXT,
            ai_summary       TEXT,
            status           TEXT DEFAULT 'active',
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_vendors_tier     ON vendors(risk_tier);
        CREATE INDEX IF NOT EXISTS idx_vendors_category ON vendors(category);

        CREATE TABLE IF NOT EXISTS policies (
            policy_id        TEXT PRIMARY KEY,
            title            TEXT NOT NULL,
            version          TEXT NOT NULL,
            summary          TEXT,
            content          TEXT,
            effective_date   TEXT,
            review_date      TEXT,
            owner            TEXT,
            status           TEXT DEFAULT 'active',
            linked_controls  TEXT,
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_policies_status ON policies(status);

        CREATE TABLE IF NOT EXISTS policy_assignments (
            assignment_id    TEXT PRIMARY KEY,
            policy_id        TEXT REFERENCES policies(policy_id),
            user_id          TEXT NOT NULL,
            assigned_at      TEXT NOT NULL,
            acknowledged_at  TEXT,
            status           TEXT DEFAULT 'pending',
            signature_note   TEXT,
            UNIQUE(policy_id, user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_pa_user   ON policy_assignments(user_id);
        CREATE INDEX IF NOT EXISTS idx_pa_policy ON policy_assignments(policy_id);

        CREATE TABLE IF NOT EXISTS incidents (
            incident_id                    TEXT PRIMARY KEY,
            title                          TEXT NOT NULL,
            description                    TEXT,
            severity                       TEXT NOT NULL,
            status                         TEXT DEFAULT 'open',
            category                       TEXT,
            reported_at                    TEXT NOT NULL,
            reported_by                    TEXT,
            resolved_at                    TEXT,
            breach_notification_required   INTEGER DEFAULT 0,
            breach_notified_at             TEXT,
            regulatory_deadline            TEXT,
            impact_assessment              TEXT,
            root_cause                     TEXT,
            remediation                    TEXT,
            linked_controls                TEXT,
            linked_findings                TEXT,
            created_at                     TEXT NOT NULL,
            updated_at                     TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_incidents_status   ON incidents(status);
        CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
        CREATE INDEX IF NOT EXISTS idx_incidents_category ON incidents(category);
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
    # Normalise any legacy findings/runs that were saved with Claude's
    # human-readable framework name (e.g. "NIST CSF 2.0") instead of the
    # canonical ID ("NISTCSF2.0") — these break the Registry filter.
    _LEGACY_FW_REMAP = {
        "NIST CSF 2.0":                 "NISTCSF2.0",
        "NIST Cybersecurity Framework": "NISTCSF2.0",
        "PCI DSS 4.0.1":                "PCI-DSS4.0.1",
        "PCI DSS v4.0.1":               "PCI-DSS4.0.1",
        "PCI-DSS 4.0.1":                "PCI-DSS4.0.1",
        "ISO 42001":                    "ISO42001",
        "ISO/IEC 42001":                "ISO42001",
        "ISO/IEC 42001:2023":           "ISO42001",
        "EU AI Act":                    "EUAIACT",
        "EU AI Act 2024/1689":          "EUAIACT",
        "ISO 27001":                    "ISO27001:2022",
        "ISO/IEC 27001":                "ISO27001:2022",
        "ISO/IEC 27001:2022":           "ISO27001:2022",
    }
    for legacy, canonical in _LEGACY_FW_REMAP.items():
        conn.execute("UPDATE findings SET framework = ? WHERE framework = ?",
                     (canonical, legacy))
        conn.execute("UPDATE assessment_runs SET framework = ? WHERE framework = ?",
                     (canonical, legacy))
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


# ─── Risks (Risk Register) ────────────────────────────────────────

def _risk_score(likelihood: int, impact: int) -> int:
    try:
        return int(likelihood) * int(impact)
    except Exception:
        return 0


def create_risk(data: dict) -> dict:
    """Insert a new risk. `data` must include title, likelihood, impact."""
    risk_id = new_id()
    likelihood = int(data.get("likelihood", 1) or 1)
    impact = int(data.get("impact", 1) or 1)
    inherent = _risk_score(likelihood, impact)
    residual = data.get("residual_score")
    residual = int(residual) if residual is not None else inherent
    linked = data.get("linked_controls") or []
    if not isinstance(linked, str):
        linked = json.dumps(linked)
    ts = now_utc()
    conn = get_db()
    conn.execute("""
        INSERT INTO risks
        (risk_id, title, description, category, likelihood, impact,
         inherent_score, residual_score, treatment_plan, treatment_notes,
         owner, status, linked_controls, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (risk_id, data.get("title", "").strip(), data.get("description", ""),
          data.get("category", "operational"), likelihood, impact,
          inherent, residual,
          data.get("treatment_plan", "mitigate"),
          data.get("treatment_notes", ""),
          data.get("owner", ""),
          data.get("status", "open"),
          linked, ts, ts))
    conn.commit()
    conn.close()
    return get_risk(risk_id)


def get_risk(risk_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM risks WHERE risk_id = ?", (risk_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["linked_controls"] = json.loads(d.get("linked_controls") or "[]")
    except Exception:
        d["linked_controls"] = []
    return d


def list_risks(status: str = None, category: str = None, owner: str = None,
               min_score: int = None, limit: int = 500) -> list:
    conn = get_db()
    q = "SELECT * FROM risks WHERE 1=1"
    params = []
    if status:
        q += " AND status = ?"
        params.append(status)
    if category:
        q += " AND category = ?"
        params.append(category)
    if owner:
        q += " AND owner = ?"
        params.append(owner)
    if min_score is not None:
        q += " AND residual_score >= ?"
        params.append(int(min_score))
    q += " ORDER BY residual_score DESC, updated_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["linked_controls"] = json.loads(d.get("linked_controls") or "[]")
        except Exception:
            d["linked_controls"] = []
        out.append(d)
    return out


def update_risk(risk_id: str, data: dict) -> Optional[dict]:
    existing = get_risk(risk_id)
    if not existing:
        return None
    merged = dict(existing)
    for k in ("title", "description", "category", "likelihood", "impact",
              "residual_score", "treatment_plan", "treatment_notes",
              "owner", "status", "linked_controls"):
        if k in data and data[k] is not None:
            merged[k] = data[k]
    likelihood = int(merged.get("likelihood", 1) or 1)
    impact = int(merged.get("impact", 1) or 1)
    inherent = _risk_score(likelihood, impact)
    residual = merged.get("residual_score")
    residual = int(residual) if residual is not None else inherent
    linked = merged.get("linked_controls") or []
    if not isinstance(linked, str):
        linked = json.dumps(linked)
    conn = get_db()
    conn.execute("""
        UPDATE risks
           SET title=?, description=?, category=?, likelihood=?, impact=?,
               inherent_score=?, residual_score=?, treatment_plan=?,
               treatment_notes=?, owner=?, status=?, linked_controls=?,
               updated_at=?
         WHERE risk_id=?
    """, (merged.get("title", ""), merged.get("description", ""),
          merged.get("category", "operational"), likelihood, impact,
          inherent, residual,
          merged.get("treatment_plan", "mitigate"),
          merged.get("treatment_notes", ""),
          merged.get("owner", ""),
          merged.get("status", "open"),
          linked, now_utc(), risk_id))
    conn.commit()
    conn.close()
    return get_risk(risk_id)


def delete_risk(risk_id: str) -> bool:
    conn = get_db()
    cur = conn.execute("DELETE FROM risks WHERE risk_id = ?", (risk_id,))
    conn.commit()
    deleted = cur.rowcount or 0
    conn.close()
    return deleted > 0


# ─── Vendors (Third-Party Risk) ───────────────────────────────────

DEFAULT_VENDOR_QUESTIONS = [
    {"question_id": "Q1",  "question": "Is customer data processed only within the EU/EEA?",                                  "weight": 10},
    {"question_id": "Q2",  "question": "Is data encrypted at rest AND in transit (TLS 1.2+, AES-256)?",                       "weight": 15},
    {"question_id": "Q3",  "question": "Does the vendor hold ISO 27001 or SOC 2 Type II certification?",                      "weight": 12},
    {"question_id": "Q4",  "question": "Is there a written breach notification SLA of 72h or less?",                          "weight": 10},
    {"question_id": "Q5",  "question": "Are all subprocessors disclosed and contractually bound?",                            "weight": 8},
    {"question_id": "Q6",  "question": "Does the contract grant audit/inspection rights?",                                    "weight": 8},
    {"question_id": "Q7",  "question": "Is there a tested BCDR plan with documented RTO/RPO?",                                "weight": 10},
    {"question_id": "Q8",  "question": "Is MFA enforced on all admin and customer-facing accounts?",                          "weight": 10},
    {"question_id": "Q9",  "question": "Is a signed GDPR DPA / Article 28 agreement in place?",                               "weight": 9},
    {"question_id": "Q10", "question": "Has the vendor had any reportable breaches in the last 24 months?",                   "weight": 8},
]

_ANSWER_VALUE = {"yes": 1.0, "partial": 0.5, "no": 0.0, "unknown": 0.3}


def _score_questionnaire(answers: list) -> int:
    """Sum(weight × answer_value) / sum(weight) × 100 → 0–100 integer."""
    if not answers:
        return 0
    total_w = sum(int(a.get("weight", 0) or 0) for a in answers) or 1
    earned = 0.0
    for a in answers:
        v = _ANSWER_VALUE.get((a.get("answer") or "unknown").lower(), 0.3)
        earned += int(a.get("weight", 0) or 0) * v
    return int(round((earned / total_w) * 100))


def _tier_for_score(score: int) -> str:
    if score <= 40:
        return "critical"
    if score <= 60:
        return "high"
    if score <= 80:
        return "medium"
    return "low"


def _default_questionnaire() -> list:
    return [
        {**q, "answer": "unknown", "notes": ""} for q in DEFAULT_VENDOR_QUESTIONS
    ]


def create_vendor(data: dict) -> dict:
    vendor_id = new_id()
    q = data.get("questionnaire") or _default_questionnaire()
    if not isinstance(q, str):
        q_text = json.dumps(q)
    else:
        q_text = q
    # Initial score from defaults (mostly 'unknown' → ~30)
    try:
        answers = json.loads(q_text) if isinstance(q_text, str) else q
    except Exception:
        answers = _default_questionnaire()
    score = _score_questionnaire(answers)
    tier = _tier_for_score(score)
    ts = now_utc()
    conn = get_db()
    conn.execute("""
        INSERT INTO vendors
        (vendor_id, name, category, contact_email, contract_url,
         risk_score, risk_tier, last_assessed_at, questionnaire, ai_summary,
         status, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (vendor_id, data.get("name", "").strip(),
          data.get("category", "saas"),
          data.get("contact_email", ""),
          data.get("contract_url", ""),
          score, tier, None, q_text, None,
          data.get("status", "active"), ts, ts))
    conn.commit()
    conn.close()
    return get_vendor(vendor_id)


def get_vendor(vendor_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM vendors WHERE vendor_id = ?", (vendor_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["questionnaire"] = json.loads(d.get("questionnaire") or "[]")
    except Exception:
        d["questionnaire"] = []
    return d


def list_vendors(risk_tier: str = None, category: str = None,
                 status: str = None, limit: int = 500) -> list:
    conn = get_db()
    q = "SELECT * FROM vendors WHERE 1=1"
    params = []
    if risk_tier:
        q += " AND risk_tier = ?"
        params.append(risk_tier)
    if category:
        q += " AND category = ?"
        params.append(category)
    if status:
        q += " AND status = ?"
        params.append(status)
    q += " ORDER BY (risk_score IS NULL) ASC, risk_score ASC, updated_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["questionnaire"] = json.loads(d.get("questionnaire") or "[]")
        except Exception:
            d["questionnaire"] = []
        out.append(d)
    return out


def update_vendor(vendor_id: str, data: dict) -> Optional[dict]:
    existing = get_vendor(vendor_id)
    if not existing:
        return None
    merged = dict(existing)
    for k in ("name", "category", "contact_email", "contract_url", "status"):
        if k in data and data[k] is not None:
            merged[k] = data[k]
    conn = get_db()
    conn.execute("""
        UPDATE vendors
           SET name=?, category=?, contact_email=?, contract_url=?,
               status=?, updated_at=?
         WHERE vendor_id=?
    """, (merged.get("name", ""), merged.get("category", "saas"),
          merged.get("contact_email", ""), merged.get("contract_url", ""),
          merged.get("status", "active"), now_utc(), vendor_id))
    conn.commit()
    conn.close()
    return get_vendor(vendor_id)


def save_vendor_assessment(vendor_id: str, answers: list,
                            ai_summary: str = "") -> Optional[dict]:
    """Persist a completed questionnaire: recompute score, tier and stamp
    last_assessed_at. `answers` is the full questionnaire list (questions
    plus user-provided answer/notes)."""
    existing = get_vendor(vendor_id)
    if not existing:
        return None
    if not isinstance(answers, list):
        return None
    score = _score_questionnaire(answers)
    tier = _tier_for_score(score)
    ts = now_utc()
    conn = get_db()
    conn.execute("""
        UPDATE vendors
           SET questionnaire=?, risk_score=?, risk_tier=?,
               last_assessed_at=?, ai_summary=?, updated_at=?
         WHERE vendor_id=?
    """, (json.dumps(answers), score, tier, ts,
          ai_summary or existing.get("ai_summary") or "", ts, vendor_id))
    conn.commit()
    conn.close()
    return get_vendor(vendor_id)


def delete_vendor(vendor_id: str) -> bool:
    conn = get_db()
    cur = conn.execute("DELETE FROM vendors WHERE vendor_id = ?", (vendor_id,))
    conn.commit()
    deleted = cur.rowcount or 0
    conn.close()
    return deleted > 0


# ─── Policies & Acknowledgments ───────────────────────────────────

def create_policy(data: dict) -> dict:
    policy_id = new_id()
    linked = data.get("linked_controls") or []
    if not isinstance(linked, str):
        linked = json.dumps(linked)
    ts = now_utc()
    conn = get_db()
    conn.execute("""
        INSERT INTO policies
        (policy_id, title, version, summary, content, effective_date,
         review_date, owner, status, linked_controls, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (policy_id, data.get("title", "").strip(),
          data.get("version", "1.0"),
          data.get("summary", ""),
          data.get("content", ""),
          data.get("effective_date", ""),
          data.get("review_date", ""),
          data.get("owner", ""),
          data.get("status", "active"),
          linked, ts, ts))
    conn.commit()
    conn.close()
    return get_policy(policy_id)


def get_policy(policy_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM policies WHERE policy_id = ?", (policy_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["linked_controls"] = json.loads(d.get("linked_controls") or "[]")
    except Exception:
        d["linked_controls"] = []
    return d


def list_policies(status: str = None, limit: int = 500) -> list:
    conn = get_db()
    q = "SELECT * FROM policies WHERE 1=1"
    params = []
    if status:
        q += " AND status = ?"
        params.append(status)
    q += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["linked_controls"] = json.loads(d.get("linked_controls") or "[]")
        except Exception:
            d["linked_controls"] = []
        out.append(d)
    return out


def update_policy(policy_id: str, data: dict) -> Optional[dict]:
    existing = get_policy(policy_id)
    if not existing:
        return None
    merged = dict(existing)
    for k in ("title", "version", "summary", "content", "effective_date",
              "review_date", "owner", "status", "linked_controls"):
        if k in data and data[k] is not None:
            merged[k] = data[k]
    linked = merged.get("linked_controls") or []
    if not isinstance(linked, str):
        linked = json.dumps(linked)
    conn = get_db()
    conn.execute("""
        UPDATE policies
           SET title=?, version=?, summary=?, content=?, effective_date=?,
               review_date=?, owner=?, status=?, linked_controls=?,
               updated_at=?
         WHERE policy_id=?
    """, (merged.get("title", ""), merged.get("version", ""),
          merged.get("summary", ""), merged.get("content", ""),
          merged.get("effective_date", ""), merged.get("review_date", ""),
          merged.get("owner", ""), merged.get("status", "active"),
          linked, now_utc(), policy_id))
    conn.commit()
    conn.close()
    return get_policy(policy_id)


def assign_policy(policy_id: str, user_ids: list) -> dict:
    """Bulk-assign a policy to N users (upsert — re-assigning is a no-op).
    Returns {assigned: n, skipped: n}."""
    if not get_policy(policy_id):
        return {"error": "policy_not_found"}
    ts = now_utc()
    conn = get_db()
    assigned = 0
    skipped = 0
    for uid in user_ids or []:
        uid_s = (uid or "").strip()
        if not uid_s:
            continue
        existing = conn.execute(
            "SELECT assignment_id FROM policy_assignments "
            "WHERE policy_id = ? AND user_id = ?", (policy_id, uid_s)
        ).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute("""
            INSERT INTO policy_assignments
            (assignment_id, policy_id, user_id, assigned_at, status)
            VALUES (?,?,?,?,?)
        """, (new_id(), policy_id, uid_s, ts, "pending"))
        assigned += 1
    conn.commit()
    conn.close()
    return {"assigned": assigned, "skipped": skipped}


def list_policy_assignments(user_id: str = None, status: str = None,
                             policy_id: str = None, limit: int = 500) -> list:
    conn = get_db()
    q = """
        SELECT pa.*, p.title AS policy_title, p.version AS policy_version,
               p.summary AS policy_summary, p.content AS policy_content,
               p.status AS policy_status
        FROM policy_assignments pa
        LEFT JOIN policies p ON p.policy_id = pa.policy_id
        WHERE 1=1
    """
    params = []
    if user_id:
        q += " AND pa.user_id = ?"
        params.append(user_id)
    if status:
        q += " AND pa.status = ?"
        params.append(status)
    if policy_id:
        q += " AND pa.policy_id = ?"
        params.append(policy_id)
    q += " ORDER BY pa.assigned_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def acknowledge_assignment(assignment_id: str, signature_note: str = "") -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM policy_assignments WHERE assignment_id = ?",
        (assignment_id,)
    ).fetchone()
    if not row:
        conn.close()
        return None
    ts = now_utc()
    conn.execute("""
        UPDATE policy_assignments
           SET acknowledged_at=?, status='acknowledged', signature_note=?
         WHERE assignment_id=?
    """, (ts, signature_note or "", assignment_id))
    conn.commit()
    out = conn.execute(
        "SELECT * FROM policy_assignments WHERE assignment_id = ?",
        (assignment_id,)
    ).fetchone()
    conn.close()
    return dict(out) if out else None


# ─── Incidents (Incident Management) ──────────────────────────────

def _compute_regulatory_deadline(severity: str, category: str,
                                  reported_at: str) -> Optional[str]:
    """Hard-coded demo rule:
      - security_breach OR data_loss + (high|critical) → 72h from reported_at (GDPR Art.33)
      - everything else → None
    """
    if not reported_at:
        return None
    sev = (severity or "").lower()
    cat = (category or "").lower()
    if cat in ("security_breach", "data_loss") and sev in ("high", "critical"):
        from datetime import timedelta
        try:
            dt = datetime.fromisoformat(reported_at.replace("Z", "+00:00"))
            return (dt + timedelta(hours=72)).isoformat()
        except Exception:
            return None
    return None


def create_incident(data: dict) -> dict:
    incident_id = new_id()
    ts = now_utc()
    reported_at = data.get("reported_at") or ts
    severity = data.get("severity", "medium")
    category = data.get("category", "other")
    breach_required = 1 if data.get("breach_notification_required") else 0
    # Auto-flag breach notification when the regulatory deadline applies.
    deadline = _compute_regulatory_deadline(severity, category, reported_at)
    if deadline and not breach_required:
        breach_required = 1
    linked_c = data.get("linked_controls") or []
    if not isinstance(linked_c, str):
        linked_c = json.dumps(linked_c)
    linked_f = data.get("linked_findings") or []
    if not isinstance(linked_f, str):
        linked_f = json.dumps(linked_f)
    conn = get_db()
    conn.execute("""
        INSERT INTO incidents
        (incident_id, title, description, severity, status, category,
         reported_at, reported_by, resolved_at,
         breach_notification_required, breach_notified_at, regulatory_deadline,
         impact_assessment, root_cause, remediation,
         linked_controls, linked_findings, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (incident_id,
          data.get("title", "").strip(), data.get("description", ""),
          severity, data.get("status", "open"), category,
          reported_at, data.get("reported_by", ""), None,
          breach_required, None, deadline,
          data.get("impact_assessment", ""),
          data.get("root_cause", ""),
          data.get("remediation", ""),
          linked_c, linked_f, ts, ts))
    conn.commit()
    conn.close()
    return get_incident(incident_id)


def get_incident(incident_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM incidents WHERE incident_id = ?",
                       (incident_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for k in ("linked_controls", "linked_findings"):
        try:
            d[k] = json.loads(d.get(k) or "[]")
        except Exception:
            d[k] = []
    return d


def list_incidents(status: str = None, severity: str = None,
                    category: str = None, limit: int = 500) -> list:
    conn = get_db()
    q = "SELECT * FROM incidents WHERE 1=1"
    params = []
    if status:
        q += " AND status = ?"
        params.append(status)
    if severity:
        q += " AND severity = ?"
        params.append(severity)
    if category:
        q += " AND category = ?"
        params.append(category)
    q += " ORDER BY reported_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        for k in ("linked_controls", "linked_findings"):
            try:
                d[k] = json.loads(d.get(k) or "[]")
            except Exception:
                d[k] = []
        out.append(d)
    return out


def update_incident(incident_id: str, data: dict) -> Optional[dict]:
    existing = get_incident(incident_id)
    if not existing:
        return None
    merged = dict(existing)
    for k in ("title", "description", "severity", "status", "category",
              "reported_by", "breach_notification_required",
              "breach_notified_at", "impact_assessment", "root_cause",
              "remediation", "linked_controls", "linked_findings",
              "resolved_at"):
        if k in data and data[k] is not None:
            merged[k] = data[k]
    # Auto-stamp resolved_at when status transitions to resolved/closed
    if (merged.get("status") in ("resolved", "closed")
            and not merged.get("resolved_at")):
        merged["resolved_at"] = now_utc()
    linked_c = merged.get("linked_controls") or []
    if not isinstance(linked_c, str):
        linked_c = json.dumps(linked_c)
    linked_f = merged.get("linked_findings") or []
    if not isinstance(linked_f, str):
        linked_f = json.dumps(linked_f)
    breach_required = 1 if merged.get("breach_notification_required") else 0
    conn = get_db()
    conn.execute("""
        UPDATE incidents
           SET title=?, description=?, severity=?, status=?, category=?,
               reported_by=?, resolved_at=?,
               breach_notification_required=?, breach_notified_at=?,
               impact_assessment=?, root_cause=?, remediation=?,
               linked_controls=?, linked_findings=?, updated_at=?
         WHERE incident_id=?
    """, (merged.get("title", ""), merged.get("description", ""),
          merged.get("severity", "medium"),
          merged.get("status", "open"),
          merged.get("category", "other"),
          merged.get("reported_by", ""),
          merged.get("resolved_at"),
          breach_required,
          merged.get("breach_notified_at"),
          merged.get("impact_assessment", ""),
          merged.get("root_cause", ""),
          merged.get("remediation", ""),
          linked_c, linked_f, now_utc(), incident_id))
    conn.commit()
    conn.close()
    return get_incident(incident_id)


def delete_incident(incident_id: str) -> bool:
    conn = get_db()
    cur = conn.execute("DELETE FROM incidents WHERE incident_id = ?", (incident_id,))
    conn.commit()
    deleted = cur.rowcount or 0
    conn.close()
    return deleted > 0


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
