"""
GRACE Prototype — Streamlit Frontend
Professional GRC demo UI: Gap Analysis, Document Generation, Dashboard
"""
import os
import base64
from pathlib import Path
import streamlit as st
import requests

import streamlit.components.v1 as components
from avatar import (
    render_avatar, AvatarState, state_for_page,
    get_state as get_avatar_state, set_state as set_avatar_state,
    AVATAR_FRAME_HEIGHT,
)

# ─── Config ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GRACE — GRC Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API = os.environ.get("GRACE_API_URL", "http://localhost:8000")
DEFAULT_LANGUAGE = os.environ.get("GRACE_DEFAULT_LANGUAGE", "en")
DEFAULT_THEME = os.environ.get("GRACE_DEFAULT_THEME", "light")

# ─── Demo password gate (opt-in via env var) ─────────────────────────
# When GRACE_DEMO_PASSWORD is set, the user must enter it before the app
# renders. When unset (local dev), the gate is silently disabled so
# nothing changes about the developer experience.

_DEMO_PASSWORD = os.environ.get("GRACE_DEMO_PASSWORD", "")


def _demo_gate():
    if not _DEMO_PASSWORD:
        return
    if st.session_state.get("_grace_auth_ok"):
        return

    import hmac
    st.markdown(
        "<div style='text-align:center; padding:4rem 0 1rem 0;'>"
        "<div style='font-size:3rem; margin-bottom:0.5rem;'>🛡️</div>"
        "<h1 style='margin:0; font-weight:600;'>GRACE</h1>"
        "<p style='color:#6b7280; margin:0.5rem 0 0 0;'>"
        "Governance, Risk, Assurance &amp; Compliance Engine</p>"
        "<p style='color:#9ca3af; margin-top:1.5rem; font-size:0.9rem;'>"
        "Demo access — please enter the shared password</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        with st.form("_demo_gate", clear_on_submit=False):
            pwd = st.text_input(
                "Password", type="password",
                label_visibility="collapsed", placeholder="Demo password",
            )
            submitted = st.form_submit_button("Enter", use_container_width=True)
            if submitted:
                if hmac.compare_digest(pwd, _DEMO_PASSWORD):
                    st.session_state["_grace_auth_ok"] = True
                    st.rerun()
                else:
                    st.error("Invalid password")
    st.stop()


_demo_gate()

ASSETS = Path(__file__).parent / "assets"


@st.cache_data
def load_b64(filename: str) -> str:
    p = ASSETS / filename
    if p.exists():
        return base64.b64encode(p.read_bytes()).decode()
    return ""


LOGO_B64 = load_b64("grace-logo.png")
SYMBOL_B64 = load_b64("grace-symbol.png")


# ─── i18n ────────────────────────────────────────────────────────────

TRANSLATIONS = {
    "en": {
        "sidebar.navigation":         "Navigation",
        "sidebar.engine_online":      "GRACE Engine: Online",
        "sidebar.engine_degraded":    "GRACE Engine: Degraded",
        "sidebar.engine_offline":     "GRACE Engine: Offline",
        "sidebar.api_label":          "API: {api}",
        "sidebar.reset_section":      "Reset prototype",
        "sidebar.reset_help":         "Delete all uploaded/generated documents, assessment runs, findings and translations. The framework catalog is preserved.",
        "sidebar.reset_confirm":      "Yes, delete everything",
        "sidebar.reset_done":         "Prototype data cleared.",
        "sidebar.reset_failed":       "Reset failed: {detail}",
        "topbar.language":            "Language",
        "topbar.theme.light":         "Light",
        "topbar.theme.dark":          "Dark",
        "topbar.tagline":             "Governance · Risk · Assurance · Compliance Engine",
        "nav.ask_grace":              "🤖 Ask GRACE",
        "nav.gap_analysis":           "📊 Gap Analysis",
        "nav.doc_gen":                "📝 Document Generation",
        "nav.dashboard":              "🛡 Governance Dashboard",
        "nav.registry":               "🔍 Finding Registry",
        "nav.library":                "📚 Framework Library",
        "nav.risks":                  "🎲 Risk Management",
        "nav.vendors":                "🤝 Vendor Risk",
        "nav.policies":               "📜 Policies",
        "nav.incidents":              "🚨 Incidents",
        # ── Ask GRACE (chat) ──────────────────────────────────────
        "ask.header":                 "🤖 Ask GRACE",
        "ask.intro":                  "Conversational AI for GRC — explore, explain, map. Doesn't create findings or runs.",
        "ask.new_chat":               "+ New chat",
        "ask.delete_chat":            "Delete chat",
        "ask.delete_confirm":         "Confirm delete",
        "ask.rename_chat":            "Rename",
        "ask.save":                   "Save",
        "ask.cancel":                 "Cancel",
        "ask.history_title":          "Conversations",
        "ask.no_history":             "No conversations yet — start one below.",
        "ask.placeholder":            "Ask GRACE anything — explain a control, map two documents, summarise your findings…",
        "ask.send_button":            "Send",
        "ask.attached_files_label":   "Attached files (optional)",
        "ask.paste_label":            "Paste text (optional)",
        "ask.context_framework_label":"Framework context (optional)",
        "ask.no_framework":           "(none)",
        "ask.empty_state_title":      "Start a conversation",
        "ask.empty_state_body":       "Ask a question, attach evidence, or paste text for cross-mapping. For a structured assessment that generates findings, use **Gap Analysis** instead.",
        "ask.empty_state_cta":        "+ Start a chat",
        "ask.thinking":               "GRACE is thinking…",
        "ask.you":                    "You",
        "ask.grace":                  "GRACE",
        "ask.add_context":            "Add Context",
        "ask.no_session_yet":         "Start a new chat from the sidebar to begin.",
        "ask.untitled":               "Untitled",
        "ga.header":                  "📊 Gap Analysis",
        "ga.intro":                   "Run a structured compliance assessment. Findings are persisted and populate the Governance Dashboard.",
        # ── Gap Analysis wizard ───────────────────────────────────
        "ga.wizard_step1":            "Step 1 — Upload evidence",
        "ga.wizard_step2":            "Step 2 — Choose framework",
        "ga.wizard_step3":            "Step 3 — Optional scope",
        "ga.wizard_step4":            "Step 4 — Run analysis",
        "ga.run_button":              "▶ Run Gap Analysis",
        "ga.running":                 "Running gap analysis — this may take 30-60s…",
        "ga.results_title":           "Assessment results",
        "ga.coverage_score":          "Overall coverage score",
        "ga.open_in_registry":        "Open in Finding Registry",
        "ga.gen_report":              "📄 Generate Assessment Report",
        "ga.no_docs_yet":             "Upload at least one document to enable analysis.",
        "ga.no_fw_yet":               "Select a framework to enable analysis.",
        "ga.results_placeholder_title": "Results will appear here",
        "ga.results_placeholder_body":  "When you click Run, GRACE will:\n- Concatenate your evidence and analyse it against every control\n- Score overall coverage and list gaps with severity\n- Persist findings so they show up in the Registry and Dashboard\n- Let you export a PDF report",
        "ga.paste_label":             "Paste evidence (optional)",
        "ga.scope_label":             "Limit to specific controls",
        "ga.report_filename":         "GRACE_Gap_Analysis",
        "ga.report_failed":           "Report export failed: {detail}",
        "ga.intro_legacy":            "Analyse, ask or add context — one natural-language workspace over your GRC content.",
        "ga.input":                   "Input",
        "ga.ws.query_label":          "Ask GRACE",
        "ga.ws.query_placeholder":    "Ask GRACE to analyse a document, explain a finding, summarise results, or compare frameworks…",
        "ga.ws.query_examples":       "Try: \"Analyse this against ISO 27001\" · \"Show me critical open findings\" · \"Explain control A.5.1\"",
        "ga.ws.add_context":          "Add context (optional)",
        "ga.ws.paste_label":          "Paste policy text",
        "ga.ws.upload_label":         "Attach documents (PDF, DOCX, TXT) — multiple allowed",
        "ga.ws.active_context":       "Active context",
        "ga.ws.ctx_paste":            "Pasted text ({n} chars)",
        "ga.ws.ctx_files":            "{n} file(s) attached",
        "ga.ws.ctx_framework":        "Framework: {fw}",
        "ga.ws.no_framework":         "No framework selected",
        "ga.ws.submit":               "Ask GRACE",
        "ga.ws.uploading":            "Uploading documents…",
        "ga.ws.thinking":             "Thinking…",
        "ga.ws.no_input":             "Type a question to get started, or attach a document and pick a framework to run an analysis.",
        "ga.ws.intent_analysis":      "Analysis",
        "ga.ws.intent_explanation":   "Explanation",
        "ga.ws.intent_findings_qa":   "Findings Q&A",
        "ga.ws.intent_qa":            "Conversation",
        "ga.ws.intent_error":         "Error",
        "ga.ws.cites":                "References",
        "ga.select_framework":        "Framework",
        "ga.coming_soon_info":        "This framework will be available in Phase 3 of the GRACE rollout.",
        "ga.doc_source":              "Document source",
        "ga.opt_paste":               "Paste text",
        "ga.opt_upload":              "Upload file",
        "ga.opt_example":             "Use example policy",
        "ga.doc_title":               "Document title",
        "ga.doc_content":             "Document content",
        "ga.paste_placeholder":       "Paste your policy, procedure or standard here…",
        "ga.upload_label":            "Upload PDF, DOCX or TXT",
        "ga.choose_example":          "Choose example document",
        "ga.doc_preview":             "Document preview",
        "ga.run_button":              "Run Gap Analysis",
        "ga.copilot_response":        "Assessment",
        "ga.provide_content":         "Please provide document content.",
        "ga.registering":             "Registering document…",
        "ga.analyzing":               "Claude is analysing your document against the framework…",
        "ga.registration_failed":     "Document registration failed: {detail}",
        "ga.assessment_failed":       "Assessment failed: {detail}",
        "ga.remediation":             "Remediation",
        "ga.evidence_required":       "Evidence required for full compliance",
        "dg.header":                  "Document Generation",
        "dg.intro":                   "Generate audit-ready compliance documents and export them in three formats.",
        "dg.configure":               "Configure",
        "dg.doc_type":                "Document type",
        "dg.framework":               "Framework",
        "dg.organization":            "Organization name",
        "dg.processor":               "Processor / Vendor",
        "dg.purpose":                 "Processing purpose",
        "dg.policy_scope":            "Policy scope",
        "dg.isms_scope":              "ISMS scope",
        "dg.generate_button":         "✍️  Generate",
        "dg.generated":               "Generated Document",
        "dg.spinner":                 "Claude is generating your {kind}…",
        "dg.success":                 "Document generated and saved.",
        "dg.download_md":             "⬇️  Markdown",
        "dg.download_pdf":            "📕  PDF",
        "dg.download_docx":           "📘  Word (.docx)",
        "dg.placeholder":             "Configure the document and click Generate.",
        "dg.type_policy":             "Information Security Policy",
        "dg.type_dpa":                "Data Processing Agreement (GDPR Art.28)",
        "dg.type_soa":                "Statement of Applicability (SoA)",
        "db.header":                  "Governance Dashboard",
        "db.intro":                   "Live view of compliance posture across frameworks — simulates the XSOAR dashboard.",
        "db.no_data":                 "No data yet. Run a gap analysis to populate the dashboard.",
        "db.kpi.open_findings":       "Open Findings",
        "db.kpi.documents":           "Documents",
        "db.kpi.assessments":         "Assessments",
        "db.kpi.avg_coverage":        "Avg Coverage",
        "db.kpi.critical_open":       "Critical Open",
        "db.kpi.open":                "Open in Registry",
        "db.kpi.view":                "View",
        "db.status_distribution":     "Compliance Status",
        "db.coverage_framework":      "Coverage by Framework",
        "db.severity_breakdown":      "Severity Breakdown",
        "db.recent_docs":             "Recent Documents Analysed",
        "db.no_findings":             "No findings yet.",
        "db.no_framework_data":       "No framework data yet.",
        "db.no_severity_data":        "No severity data yet.",
        "db.no_assessments":          "No completed assessments yet.",
        "db.no_document":             "(no document)",
        "db.findings_avg":            "{count} findings · avg {score}%",
        "reg.header":                 "Finding Registry",
        "reg.intro":                  "Every finding ever generated — simulates the XSOAR incident queue.",
        "reg.framework":              "Framework",
        "reg.verdict":                "Verdict",
        "reg.operational_status":     "Operational Status",
        "reg.no_findings":            "No findings yet. Run a Gap Analysis first.",
        "reg.findings_count":         "**{n} finding(s)** across **{d} document(s)**",
        "reg.document":               "**Document:** {title}",
        "reg.unknown_doc":            "(unknown document)",
        "reg.doc_summary":            "{n} finding(s) · {framework} · {date}",
        "reg.lang_tag":               "Generated in",
        "reg.finding":                "Finding",
        "reg.remediation":            "Remediation",
        "reg.update_op_status":       "Update operational status",
        "reg.update_button":          "Update",
        "reg.status_updated":         "Status updated.",
        "reg.xframework_title":       "🔗 Cross-Framework Impact",
        "reg.xframework_show":        "🔗 Show cross-framework impact",
        "reg.xframework_hide":        "🔗 Hide cross-framework impact",
        "reg.xframework_empty":       "No equivalent controls found in other active frameworks.",
        "reg.xframework_loading":     "Mapping controls across frameworks…",
        "reg.xframework_failed":      "Could not load cross-framework mappings.",
        "reg.xframework_confidence":  "Confidence",
        "reg.xframework_badge":       "🔗 +{n}",
        "xfw.high":                   "High",
        "xfw.medium":                 "Medium",
        "xfw.low":                    "Low",
        "lib.header":                 "Framework Library",
        "lib.intro":                  "25 international frameworks — P0 frameworks active in this prototype.",
        "lib.coming_phase3":          "🚧  Coming Phase 3",
        "lib.active":                 "Active",
        "lib.category":               "Category",
        "lib.priority":               "Priority",
        "lib.controls":               "Controls",
        "lib.controls_loaded":        "{n} controls loaded in prototype",
        "lib.more_controls":          "+ {n} more controls…",
        "lib.explain_ctrl":           "Explain a control",
        "lib.explain_button":         "Explain with Claude",
        "lib.explain_spinner":        "Getting plain-language explanation…",
        "lib.cannot_reach":           "Cannot reach GRACE API",
        "lib.framework_entry":        "**{name}** — {controls} controls · {tag}",
        "verdict.compliant":          "Compliant",
        "verdict.partial":            "Partial",
        "verdict.non_compliant":      "Non-Compliant",
        "verdict.no_evidence":        "No Evidence",
        "verdict.not_applicable":     "Not Applicable",
        "verdict_emoji.compliant":    "Compliant",
        "verdict_emoji.partial":      "Partial",
        "verdict_emoji.non_compliant":"Non-Compliant",
        "verdict_emoji.no_evidence":  "No Evidence",
        "severity.critical":          "CRITICAL",
        "severity.high":              "HIGH",
        "severity.medium":            "MEDIUM",
        "severity.low":               "LOW",
        "opstatus.new":               "New",
        "opstatus.acknowledged":      "Acknowledged",
        "opstatus.in_progress":       "In Progress",
        "opstatus.resolved":          "Resolved",
        "opstatus.accepted_risk":     "Accepted Risk",
        "opstatus.closed":            "Closed",
        "opstatus.dismissed":         "Dismissed",
        "all":                        "All",
        # ── Risk Management ──────────────────────────────────────
        "risks.header":               "Risk Management",
        "risks.intro":                "Maintain the corporate risk register — likelihood × impact, treatment plans, owners.",
        "risks.kpi.total":            "Total risks",
        "risks.kpi.critical":         "Critical (score ≥ 15)",
        "risks.kpi.avg_residual":     "Avg residual score",
        "risks.kpi.open":             "Open",
        "risks.filter.status":        "Status",
        "risks.filter.category":      "Category",
        "risks.filter.owner":         "Owner",
        "risks.heatmap_title":        "5 × 5 Risk Heatmap (likelihood × impact)",
        "risks.heatmap_xaxis":        "Impact →",
        "risks.heatmap_yaxis":        "Likelihood →",
        "risks.new_button":           "+ New Risk",
        "risks.new_form_title":       "Create a new risk",
        "risks.edit_button":          "Edit",
        "risks.cancel_button":        "Cancel",
        "risks.save_button":          "Save changes",
        "risks.delete_button":        "Delete",
        "risks.delete_confirm":       "Risk deleted.",
        "risks.no_risks":             "No risks registered yet. Click '+ New Risk' to add one.",
        "risks.field.title":          "Title",
        "risks.field.description":    "Description",
        "risks.field.category":       "Category",
        "risks.field.likelihood":     "Likelihood (1–5)",
        "risks.field.impact":         "Impact (1–5)",
        "risks.field.residual":       "Residual score (0–25)",
        "risks.field.treatment":      "Treatment plan",
        "risks.field.treatment_notes":"Treatment notes",
        "risks.field.owner":          "Owner",
        "risks.field.status":         "Status",
        "risks.field.linked_controls":"Linked controls (comma-separated, e.g. ISO27001:2022:A.5.1, GDPR:Art.32)",
        "risks.create_button":        "Create risk",
        "risks.created_ok":           "Risk created.",
        "risks.updated_ok":           "Risk updated.",
        "risks.score_inherent":       "Inherent",
        "risks.score_residual":       "Residual",
        "risks.cat.operational":      "Operational",
        "risks.cat.cyber":            "Cyber",
        "risks.cat.compliance":       "Compliance",
        "risks.cat.financial":        "Financial",
        "risks.cat.strategic":        "Strategic",
        "risks.cat.reputational":     "Reputational",
        "risks.treat.avoid":          "Avoid",
        "risks.treat.transfer":       "Transfer",
        "risks.treat.mitigate":       "Mitigate",
        "risks.treat.accept":         "Accept",
        "risks.status.open":          "Open",
        "risks.status.under_treatment": "Under Treatment",
        "risks.status.accepted":      "Accepted",
        "risks.status.closed":        "Closed",
        # ── Vendor Risk ──────────────────────────────────────────
        "vendors.header":             "Vendor Risk",
        "vendors.intro":              "Assess and monitor your third-party suppliers against a 10-question security baseline.",
        "vendors.kpi.total":          "Total vendors",
        "vendors.kpi.high_risk":      "Critical / High risk",
        "vendors.kpi.due":            "Due for reassessment",
        "vendors.kpi.active":         "Active",
        "vendors.filter.tier":        "Risk tier",
        "vendors.filter.category":    "Category",
        "vendors.filter.status":      "Status",
        "vendors.new_button":         "+ Add Vendor",
        "vendors.new_form_title":     "Add a new vendor",
        "vendors.field.name":         "Vendor name",
        "vendors.field.category":     "Category",
        "vendors.field.contact_email":"Contact email",
        "vendors.field.contract_url": "Contract URL",
        "vendors.field.status":       "Status",
        "vendors.create_button":      "Create vendor",
        "vendors.created_ok":         "Vendor added.",
        "vendors.updated_ok":         "Vendor updated.",
        "vendors.assess_button":      "Assess",
        "vendors.assess_form_title":  "Vendor security questionnaire",
        "vendors.assess_intro":       "Answer each question, optionally add notes, then submit to compute the risk score.",
        "vendors.assess_submit":      "Submit assessment",
        "vendors.assess_ok":          "Assessment saved. Risk score and tier updated.",
        "vendors.ai_summary":         "AI summary",
        "vendors.never_assessed":     "Not yet assessed",
        "vendors.last_assessed":      "Last assessed {date}",
        "vendors.score":              "Score",
        "vendors.tier":               "Tier",
        "vendors.no_vendors":         "No vendors registered. Click '+ Add Vendor' to start.",
        "vendors.answer.yes":         "Yes",
        "vendors.answer.no":          "No",
        "vendors.answer.partial":     "Partial",
        "vendors.answer.unknown":     "Unknown",
        "vendors.notes_label":        "Notes",
        "vendors.cat.cloud_infra":    "Cloud Infrastructure",
        "vendors.cat.saas":           "SaaS",
        "vendors.cat.payment":        "Payment",
        "vendors.cat.data_processor": "Data Processor",
        "vendors.cat.professional_services": "Professional Services",
        "vendors.cat.other":          "Other",
        "vendors.tier.low":           "Low",
        "vendors.tier.medium":        "Medium",
        "vendors.tier.high":          "High",
        "vendors.tier.critical":      "Critical",
        "vendors.status.active":      "Active",
        "vendors.status.under_review":"Under Review",
        "vendors.status.terminated":  "Terminated",
        # ── Policies ─────────────────────────────────────────────
        "policies.header":            "Policies",
        "policies.intro":             "Publish internal policies, assign them to people and collect acknowledgments.",
        "policies.tab_library":       "📚 Library",
        "policies.tab_acks":          "✅ My Acknowledgments",
        "policies.kpi.total":         "Total policies",
        "policies.kpi.active":        "Active",
        "policies.kpi.pending":       "Pending acknowledgments",
        "policies.new_button":        "+ Create Policy",
        "policies.new_form_title":    "Create a new policy",
        "policies.field.title":       "Title",
        "policies.field.version":     "Version",
        "policies.field.summary":     "Summary",
        "policies.field.content":     "Content (markdown)",
        "policies.field.effective":   "Effective date (YYYY-MM-DD)",
        "policies.field.review":      "Review date (YYYY-MM-DD)",
        "policies.field.owner":       "Owner",
        "policies.field.status":      "Status",
        "policies.field.linked_controls": "Linked controls (comma-separated)",
        "policies.create_button":     "Create policy",
        "policies.created_ok":        "Policy created.",
        "policies.assign_to":         "Assign to users (comma-separated user IDs, e.g. alice@demo, bob@demo)",
        "policies.assign_button":     "Assign",
        "policies.assign_ok":         "Assigned to {n} user(s); {s} already had this policy.",
        "policies.no_policies":       "No policies created yet. Click '+ Create Policy' to start.",
        "policies.demo_user_label":   "Demo user",
        "policies.demo_user_help":    "Type a user ID to see their pending acknowledgments.",
        "policies.no_pending":        "No pending acknowledgments for this user.",
        "policies.accept_button":     "✅ Accept",
        "policies.signature_note":    "Signature note (optional)",
        "policies.acknowledged_ok":   "Policy acknowledged. Thanks.",
        "policies.acknowledged_section": "Already acknowledged",
        "policies.policy_version":    "Version {v}",
        "policies.policy_owner":      "Owner: {o}",
        "policies.policy_effective":  "Effective: {d}",
        "policies.status.draft":      "Draft",
        "policies.status.active":     "Active",
        "policies.status.superseded": "Superseded",
        "policies.status.retired":    "Retired",
        # ── Incidents ────────────────────────────────────────────
        "incidents.header":           "Incidents",
        "incidents.intro":            "Track security incidents from report to resolution — with regulatory deadline awareness.",
        "incidents.kpi.open":         "Open incidents",
        "incidents.kpi.critical":     "Critical open",
        "incidents.kpi.breach_pending":"Breach notifications pending",
        "incidents.kpi.mttr":         "MTTR (days)",
        "incidents.filter.severity":  "Severity",
        "incidents.filter.status":    "Status",
        "incidents.filter.category":  "Category",
        "incidents.new_button":       "+ Report Incident",
        "incidents.new_form_title":   "Report a new incident",
        "incidents.field.title":      "Title",
        "incidents.field.description":"Description",
        "incidents.field.severity":   "Severity",
        "incidents.field.status":     "Status",
        "incidents.field.category":   "Category",
        "incidents.field.reported_by":"Reported by",
        "incidents.field.impact":     "Impact assessment",
        "incidents.field.root_cause": "Root cause",
        "incidents.field.remediation":"Remediation",
        "incidents.field.linked_controls": "Linked controls (comma-separated)",
        "incidents.field.linked_findings": "Linked finding IDs (comma-separated)",
        "incidents.field.breach_required":"Regulatory breach notification required",
        "incidents.field.breach_notified":"Breach notified at (ISO timestamp)",
        "incidents.create_button":    "Report incident",
        "incidents.created_ok":       "Incident reported.",
        "incidents.update_button":    "Save changes",
        "incidents.updated_ok":       "Incident updated.",
        "incidents.no_incidents":     "No incidents reported. Click '+ Report Incident' to log one.",
        "incidents.breach_banner":    "⚠ Regulatory breach notification required",
        "incidents.deadline_in":      "Deadline: {when}",
        "incidents.deadline_overdue": "OVERDUE — was due {when}",
        "incidents.deadline_notified":"Notified at {when}",
        "incidents.reported_on":      "Reported {date}",
        "incidents.resolved_on":      "Resolved {date}",
        "incidents.edit_section":     "Edit incident",
        "incidents.severity.low":     "Low",
        "incidents.severity.medium":  "Medium",
        "incidents.severity.high":    "High",
        "incidents.severity.critical":"Critical",
        "incidents.status.open":      "Open",
        "incidents.status.investigating":"Investigating",
        "incidents.status.contained": "Contained",
        "incidents.status.resolved":  "Resolved",
        "incidents.status.closed":    "Closed",
        "incidents.cat.security_breach": "Security Breach",
        "incidents.cat.data_loss":    "Data Loss",
        "incidents.cat.system_outage":"System Outage",
        "incidents.cat.policy_violation":"Policy Violation",
        "incidents.cat.third_party":  "Third Party",
        "incidents.cat.other":        "Other",
    },
    "it": {
        "sidebar.navigation":         "Navigazione",
        "sidebar.engine_online":      "Motore GRACE: Online",
        "sidebar.engine_degraded":    "Motore GRACE: Degradato",
        "sidebar.engine_offline":     "Motore GRACE: Offline",
        "sidebar.api_label":          "API: {api}",
        "sidebar.reset_section":      "Reset prototipo",
        "sidebar.reset_help":         "Cancella tutti i documenti caricati/generati, le run di assessment, i finding e le traduzioni. Il catalogo dei framework resta intatto.",
        "sidebar.reset_confirm":      "Sì, cancella tutto",
        "sidebar.reset_done":         "Dati prototipo cancellati.",
        "sidebar.reset_failed":       "Reset fallito: {detail}",
        "topbar.language":            "Lingua",
        "topbar.theme.light":         "Chiaro",
        "topbar.theme.dark":          "Scuro",
        "topbar.tagline":             "Governance · Risk · Assurance · Compliance Engine",
        "nav.ask_grace":              "🤖 Chiedi a GRACE",
        "nav.gap_analysis":           "📊 Analisi dei Gap",
        "nav.doc_gen":                "📝 Generazione Documenti",
        "nav.dashboard":              "🛡 Dashboard Governance",
        "nav.registry":               "🔍 Registro Findings",
        "nav.library":                "📚 Libreria Framework",
        "nav.risks":                  "🎲 Gestione Rischi",
        "nav.vendors":                "🤝 Rischio Fornitori",
        "nav.policies":               "📜 Policy",
        "nav.incidents":              "🚨 Incidenti",
        # ── Ask GRACE (chat) ──────────────────────────────────────
        "ask.header":                 "🤖 Chiedi a GRACE",
        "ask.intro":                  "IA conversazionale per il GRC — esplora, spiega, mappa. Non crea finding né run.",
        "ask.new_chat":               "+ Nuova chat",
        "ask.delete_chat":            "Elimina chat",
        "ask.delete_confirm":         "Conferma eliminazione",
        "ask.rename_chat":            "Rinomina",
        "ask.save":                   "Salva",
        "ask.cancel":                 "Annulla",
        "ask.history_title":          "Conversazioni",
        "ask.no_history":             "Nessuna conversazione — iniziane una qui sotto.",
        "ask.placeholder":            "Chiedi a GRACE qualsiasi cosa — spiega un controllo, mappa due documenti, riassumi i tuoi finding…",
        "ask.send_button":            "Invia",
        "ask.attached_files_label":   "File allegati (opzionale)",
        "ask.paste_label":            "Incolla testo (opzionale)",
        "ask.context_framework_label":"Contesto framework (opzionale)",
        "ask.no_framework":           "(nessuno)",
        "ask.empty_state_title":      "Inizia una conversazione",
        "ask.empty_state_body":       "Fai una domanda, allega evidenze, o incolla del testo per il cross-mapping. Per un assessment strutturato che genera finding, usa **Analisi dei Gap**.",
        "ask.empty_state_cta":        "+ Inizia una chat",
        "ask.thinking":               "GRACE sta pensando…",
        "ask.you":                    "Tu",
        "ask.grace":                  "GRACE",
        "ask.add_context":            "Aggiungi Contesto",
        "ask.no_session_yet":         "Avvia una nuova chat dalla sidebar per iniziare.",
        "ask.untitled":               "Senza titolo",
        "ga.header":                  "📊 Analisi dei Gap",
        "ga.intro":                   "Esegui un assessment di conformità strutturato. I finding sono persistiti e popolano la Governance Dashboard.",
        # ── Gap Analysis wizard ───────────────────────────────────
        "ga.wizard_step1":            "Step 1 — Carica le evidenze",
        "ga.wizard_step2":            "Step 2 — Scegli il framework",
        "ga.wizard_step3":            "Step 3 — Scope opzionale",
        "ga.wizard_step4":            "Step 4 — Esegui analisi",
        "ga.run_button":              "▶ Esegui analisi",
        "ga.running":                 "Analisi in corso — può richiedere 30-60s…",
        "ga.results_title":           "Risultati assessment",
        "ga.coverage_score":          "Punteggio di copertura",
        "ga.open_in_registry":        "Apri nel Registro Finding",
        "ga.gen_report":              "📄 Genera Report di Assessment",
        "ga.no_docs_yet":             "Carica almeno un documento per abilitare l'analisi.",
        "ga.no_fw_yet":               "Seleziona un framework per abilitare l'analisi.",
        "ga.results_placeholder_title": "I risultati appariranno qui",
        "ga.results_placeholder_body":  "Quando clicchi Esegui, GRACE:\n- Unisce le tue evidenze e le analizza rispetto a ogni controllo\n- Calcola la copertura complessiva e elenca i gap con severità\n- Persiste i finding così appaiono nel Registro e nella Dashboard\n- Ti permette di esportare un report PDF",
        "ga.paste_label":             "Incolla evidenze (opzionale)",
        "ga.scope_label":             "Limita a controlli specifici",
        "ga.report_filename":         "GRACE_Analisi_Gap",
        "ga.report_failed":           "Esportazione report fallita: {detail}",
        "ga.intro_legacy":            "Analizza, chiedi o aggiungi contesto — un unico workspace in linguaggio naturale sui tuoi contenuti GRC.",
        "ga.input":                   "Input",
        "ga.ws.query_label":          "Chiedi a GRACE",
        "ga.ws.query_placeholder":    "Chiedi a GRACE di analizzare un documento, spiegare un finding, riassumere i risultati o confrontare framework…",
        "ga.ws.query_examples":       "Prova: \"Analizza questo rispetto a ISO 27001\" · \"Mostra i finding critici aperti\" · \"Spiega il controllo A.5.1\"",
        "ga.ws.add_context":          "Aggiungi contesto (opzionale)",
        "ga.ws.paste_label":          "Incolla il testo di una policy",
        "ga.ws.upload_label":         "Allega documenti (PDF, DOCX, TXT) — multipli ammessi",
        "ga.ws.active_context":       "Contesto attivo",
        "ga.ws.ctx_paste":            "Testo incollato ({n} caratteri)",
        "ga.ws.ctx_files":            "{n} file allegati",
        "ga.ws.ctx_framework":        "Framework: {fw}",
        "ga.ws.no_framework":         "Nessun framework selezionato",
        "ga.ws.submit":               "Chiedi a GRACE",
        "ga.ws.uploading":            "Carico i documenti…",
        "ga.ws.thinking":             "Sto pensando…",
        "ga.ws.no_input":             "Scrivi una domanda per iniziare, oppure allega un documento e scegli un framework per lanciare un'analisi.",
        "ga.ws.intent_analysis":      "Analisi",
        "ga.ws.intent_explanation":   "Spiegazione",
        "ga.ws.intent_findings_qa":   "Q&A Finding",
        "ga.ws.intent_qa":            "Conversazione",
        "ga.ws.intent_error":         "Errore",
        "ga.ws.cites":                "Riferimenti",
        "ga.select_framework":        "Framework",
        "ga.coming_soon_info":        "Questo framework sarà disponibile nella Fase 3 del rollout GRACE.",
        "ga.doc_source":              "Origine documento",
        "ga.opt_paste":               "Incolla testo",
        "ga.opt_upload":              "Carica file",
        "ga.opt_example":             "Usa policy d'esempio",
        "ga.doc_title":               "Titolo documento",
        "ga.doc_content":             "Contenuto documento",
        "ga.paste_placeholder":       "Incolla qui la tua policy, procedura o standard…",
        "ga.upload_label":            "Carica PDF, DOCX o TXT",
        "ga.choose_example":          "Scegli documento d'esempio",
        "ga.doc_preview":             "Anteprima documento",
        "ga.run_button":              "Esegui Analisi",
        "ga.copilot_response":        "Assessment",
        "ga.provide_content":         "Fornisci il contenuto del documento.",
        "ga.registering":             "Registrazione del documento…",
        "ga.analyzing":               "Claude sta analizzando il documento rispetto al framework…",
        "ga.registration_failed":     "Registrazione documento fallita: {detail}",
        "ga.assessment_failed":       "Assessment fallito: {detail}",
        "ga.remediation":             "Rimedio",
        "ga.evidence_required":       "Evidenze richieste per piena conformità",
        "dg.header":                  "Generazione Documenti",
        "dg.intro":                   "Genera documenti di conformità audit-ready ed esportali in tre formati.",
        "dg.configure":               "Configura",
        "dg.doc_type":                "Tipo di documento",
        "dg.framework":               "Framework",
        "dg.organization":            "Nome organizzazione",
        "dg.processor":               "Processor / Fornitore",
        "dg.purpose":                 "Finalità del trattamento",
        "dg.policy_scope":            "Ambito della policy",
        "dg.isms_scope":              "Ambito ISMS",
        "dg.generate_button":         "✍️  Genera",
        "dg.generated":               "Documento Generato",
        "dg.spinner":                 "Claude sta generando il tuo {kind}…",
        "dg.success":                 "Documento generato e salvato.",
        "dg.download_md":             "⬇️  Markdown",
        "dg.download_pdf":            "📕  PDF",
        "dg.download_docx":           "📘  Word (.docx)",
        "dg.placeholder":             "Configura il documento e clicca Genera.",
        "dg.type_policy":             "Information Security Policy",
        "dg.type_dpa":                "Data Processing Agreement (GDPR Art.28)",
        "dg.type_soa":                "Statement of Applicability (SoA)",
        "db.header":                  "Dashboard Governance",
        "db.intro":                   "Vista live della postura di conformità tra framework — simula la dashboard XSOAR.",
        "db.no_data":                 "Nessun dato. Esegui prima una gap analysis per popolare la dashboard.",
        "db.kpi.open_findings":       "Findings Aperti",
        "db.kpi.documents":           "Documenti",
        "db.kpi.assessments":         "Assessment",
        "db.kpi.avg_coverage":        "Copertura Media",
        "db.kpi.critical_open":       "Critici Aperti",
        "db.kpi.open":                "Apri nel Registro",
        "db.kpi.view":                "Vedi",
        "db.status_distribution":     "Stato di Conformità",
        "db.coverage_framework":      "Copertura per Framework",
        "db.severity_breakdown":      "Distribuzione Severità",
        "db.recent_docs":             "Ultimi Documenti Analizzati",
        "db.no_findings":             "Nessun finding al momento.",
        "db.no_framework_data":       "Nessun dato per framework al momento.",
        "db.no_severity_data":        "Nessun dato di severità al momento.",
        "db.no_assessments":          "Nessun assessment completato al momento.",
        "db.no_document":             "(nessun documento)",
        "db.findings_avg":            "{count} findings · media {score}%",
        "reg.header":                 "Registro Findings",
        "reg.intro":                  "Tutti i findings mai generati — simula la coda incident XSOAR.",
        "reg.framework":              "Framework",
        "reg.verdict":                "Verdetto",
        "reg.operational_status":     "Stato Operativo",
        "reg.no_findings":            "Nessun finding al momento. Esegui prima un'Analisi dei Gap.",
        "reg.findings_count":         "**{n} finding** in **{d} documento/i**",
        "reg.document":               "**Documento:** {title}",
        "reg.unknown_doc":            "(documento sconosciuto)",
        "reg.doc_summary":            "{n} finding · {framework} · {date}",
        "reg.lang_tag":               "Generato in",
        "reg.finding":                "Finding",
        "reg.remediation":            "Rimedio",
        "reg.update_op_status":       "Aggiorna stato operativo",
        "reg.update_button":          "Aggiorna",
        "reg.status_updated":         "Stato aggiornato.",
        "reg.xframework_title":       "🔗 Impatto Multi-Framework",
        "reg.xframework_show":        "🔗 Mostra impatto multi-framework",
        "reg.xframework_hide":        "🔗 Nascondi impatto multi-framework",
        "reg.xframework_empty":       "Nessun controllo equivalente trovato negli altri framework attivi.",
        "reg.xframework_loading":     "Mappatura controlli tra framework…",
        "reg.xframework_failed":      "Impossibile caricare le mappature multi-framework.",
        "reg.xframework_confidence":  "Confidenza",
        "reg.xframework_badge":       "🔗 +{n}",
        "xfw.high":                   "Alta",
        "xfw.medium":                 "Media",
        "xfw.low":                    "Bassa",
        "lib.header":                 "Libreria Framework",
        "lib.intro":                  "25 framework internazionali — i framework P0 sono attivi in questo prototipo.",
        "lib.coming_phase3":          "🚧  In arrivo in Fase 3",
        "lib.active":                 "Attivo",
        "lib.category":               "Categoria",
        "lib.priority":               "Priorità",
        "lib.controls":               "Controlli",
        "lib.controls_loaded":        "{n} controlli caricati nel prototipo",
        "lib.more_controls":          "+ altri {n} controlli…",
        "lib.explain_ctrl":           "Spiega un controllo",
        "lib.explain_button":         "Spiega con Claude",
        "lib.explain_spinner":        "Recupero la spiegazione in linguaggio naturale…",
        "lib.cannot_reach":           "Impossibile raggiungere l'API GRACE",
        "lib.framework_entry":        "**{name}** — {controls} controlli · {tag}",
        "verdict.compliant":          "Conforme",
        "verdict.partial":            "Parziale",
        "verdict.non_compliant":      "Non Conforme",
        "verdict.no_evidence":        "Senza Evidenza",
        "verdict.not_applicable":     "Non Applicabile",
        "verdict_emoji.compliant":    "Conforme",
        "verdict_emoji.partial":      "Parziale",
        "verdict_emoji.non_compliant":"Non Conforme",
        "verdict_emoji.no_evidence":  "Senza Evidenza",
        "severity.critical":          "CRITICA",
        "severity.high":              "ALTA",
        "severity.medium":            "MEDIA",
        "severity.low":               "BASSA",
        "opstatus.new":               "Nuovo",
        "opstatus.acknowledged":      "Preso in Carico",
        "opstatus.in_progress":       "In Lavorazione",
        "opstatus.resolved":          "Risolto",
        "opstatus.accepted_risk":     "Rischio Accettato",
        "opstatus.closed":            "Chiuso",
        "opstatus.dismissed":         "Scartato",
        "all":                        "Tutti",
        # ── Risk Management ──────────────────────────────────────
        "risks.header":               "Gestione Rischi",
        "risks.intro":                "Mantieni il registro dei rischi aziendali — probabilità × impatto, piani di trattamento, owner.",
        "risks.kpi.total":            "Rischi totali",
        "risks.kpi.critical":         "Critici (score ≥ 15)",
        "risks.kpi.avg_residual":     "Score residuo medio",
        "risks.kpi.open":             "Aperti",
        "risks.filter.status":        "Stato",
        "risks.filter.category":      "Categoria",
        "risks.filter.owner":         "Owner",
        "risks.heatmap_title":        "Heatmap 5 × 5 dei rischi (probabilità × impatto)",
        "risks.heatmap_xaxis":        "Impatto →",
        "risks.heatmap_yaxis":        "Probabilità →",
        "risks.new_button":           "+ Nuovo rischio",
        "risks.new_form_title":       "Crea un nuovo rischio",
        "risks.edit_button":          "Modifica",
        "risks.cancel_button":        "Annulla",
        "risks.save_button":          "Salva modifiche",
        "risks.delete_button":        "Elimina",
        "risks.delete_confirm":       "Rischio eliminato.",
        "risks.no_risks":             "Nessun rischio registrato. Clicca '+ Nuovo rischio' per aggiungerne uno.",
        "risks.field.title":          "Titolo",
        "risks.field.description":    "Descrizione",
        "risks.field.category":       "Categoria",
        "risks.field.likelihood":     "Probabilità (1–5)",
        "risks.field.impact":         "Impatto (1–5)",
        "risks.field.residual":       "Score residuo (0–25)",
        "risks.field.treatment":      "Piano di trattamento",
        "risks.field.treatment_notes":"Note al trattamento",
        "risks.field.owner":          "Owner",
        "risks.field.status":         "Stato",
        "risks.field.linked_controls":"Controlli collegati (separati da virgola, es. ISO27001:2022:A.5.1, GDPR:Art.32)",
        "risks.create_button":        "Crea rischio",
        "risks.created_ok":           "Rischio creato.",
        "risks.updated_ok":           "Rischio aggiornato.",
        "risks.score_inherent":       "Inerente",
        "risks.score_residual":       "Residuo",
        "risks.cat.operational":      "Operativo",
        "risks.cat.cyber":            "Cyber",
        "risks.cat.compliance":       "Compliance",
        "risks.cat.financial":        "Finanziario",
        "risks.cat.strategic":        "Strategico",
        "risks.cat.reputational":     "Reputazionale",
        "risks.treat.avoid":          "Evitare",
        "risks.treat.transfer":       "Trasferire",
        "risks.treat.mitigate":       "Mitigare",
        "risks.treat.accept":         "Accettare",
        "risks.status.open":          "Aperto",
        "risks.status.under_treatment": "In Trattamento",
        "risks.status.accepted":      "Accettato",
        "risks.status.closed":        "Chiuso",
        # ── Vendor Risk ──────────────────────────────────────────
        "vendors.header":             "Rischio Fornitori",
        "vendors.intro":              "Valuta e monitora i tuoi fornitori esterni rispetto a una baseline di sicurezza di 10 domande.",
        "vendors.kpi.total":          "Fornitori totali",
        "vendors.kpi.high_risk":      "Rischio critico / alto",
        "vendors.kpi.due":            "Da rivalutare",
        "vendors.kpi.active":         "Attivi",
        "vendors.filter.tier":        "Livello rischio",
        "vendors.filter.category":    "Categoria",
        "vendors.filter.status":      "Stato",
        "vendors.new_button":         "+ Aggiungi fornitore",
        "vendors.new_form_title":     "Aggiungi un nuovo fornitore",
        "vendors.field.name":         "Nome fornitore",
        "vendors.field.category":     "Categoria",
        "vendors.field.contact_email":"Email di contatto",
        "vendors.field.contract_url": "URL contratto",
        "vendors.field.status":       "Stato",
        "vendors.create_button":      "Crea fornitore",
        "vendors.created_ok":         "Fornitore aggiunto.",
        "vendors.updated_ok":         "Fornitore aggiornato.",
        "vendors.assess_button":      "Valuta",
        "vendors.assess_form_title":  "Questionario di sicurezza fornitore",
        "vendors.assess_intro":       "Rispondi a ciascuna domanda, eventualmente aggiungi delle note, poi invia per calcolare lo score di rischio.",
        "vendors.assess_submit":      "Invia valutazione",
        "vendors.assess_ok":          "Valutazione salvata. Score e tier aggiornati.",
        "vendors.ai_summary":         "Sintesi AI",
        "vendors.never_assessed":     "Non ancora valutato",
        "vendors.last_assessed":      "Ultima valutazione: {date}",
        "vendors.score":              "Score",
        "vendors.tier":               "Tier",
        "vendors.no_vendors":         "Nessun fornitore registrato. Clicca '+ Aggiungi fornitore' per iniziare.",
        "vendors.answer.yes":         "Sì",
        "vendors.answer.no":          "No",
        "vendors.answer.partial":     "Parziale",
        "vendors.answer.unknown":     "Sconosciuto",
        "vendors.notes_label":        "Note",
        "vendors.cat.cloud_infra":    "Infrastruttura Cloud",
        "vendors.cat.saas":           "SaaS",
        "vendors.cat.payment":        "Pagamenti",
        "vendors.cat.data_processor": "Responsabile del Trattamento",
        "vendors.cat.professional_services": "Servizi Professionali",
        "vendors.cat.other":          "Altro",
        "vendors.tier.low":           "Basso",
        "vendors.tier.medium":        "Medio",
        "vendors.tier.high":          "Alto",
        "vendors.tier.critical":      "Critico",
        "vendors.status.active":      "Attivo",
        "vendors.status.under_review":"In Revisione",
        "vendors.status.terminated":  "Terminato",
        # ── Policies ─────────────────────────────────────────────
        "policies.header":            "Policy",
        "policies.intro":             "Pubblica policy interne, assegnale alle persone e raccogli le conferme di presa visione.",
        "policies.tab_library":       "📚 Libreria",
        "policies.tab_acks":          "✅ Le mie conferme",
        "policies.kpi.total":         "Policy totali",
        "policies.kpi.active":        "Attive",
        "policies.kpi.pending":       "Conferme in attesa",
        "policies.new_button":        "+ Crea policy",
        "policies.new_form_title":    "Crea una nuova policy",
        "policies.field.title":       "Titolo",
        "policies.field.version":     "Versione",
        "policies.field.summary":     "Sintesi",
        "policies.field.content":     "Contenuto (markdown)",
        "policies.field.effective":   "Data di entrata in vigore (YYYY-MM-DD)",
        "policies.field.review":      "Data revisione (YYYY-MM-DD)",
        "policies.field.owner":       "Owner",
        "policies.field.status":      "Stato",
        "policies.field.linked_controls": "Controlli collegati (separati da virgola)",
        "policies.create_button":     "Crea policy",
        "policies.created_ok":        "Policy creata.",
        "policies.assign_to":         "Assegna agli utenti (ID separati da virgola, es. alice@demo, bob@demo)",
        "policies.assign_button":     "Assegna",
        "policies.assign_ok":         "Assegnata a {n} utente/i; {s} già la avevano.",
        "policies.no_policies":       "Nessuna policy creata. Clicca '+ Crea policy' per iniziare.",
        "policies.demo_user_label":   "Utente demo",
        "policies.demo_user_help":    "Inserisci un ID utente per vedere le sue conferme in attesa.",
        "policies.no_pending":        "Nessuna conferma in attesa per questo utente.",
        "policies.accept_button":     "✅ Accetto",
        "policies.signature_note":    "Nota di firma (opzionale)",
        "policies.acknowledged_ok":   "Policy confermata. Grazie.",
        "policies.acknowledged_section": "Già confermate",
        "policies.policy_version":    "Versione {v}",
        "policies.policy_owner":      "Owner: {o}",
        "policies.policy_effective":  "In vigore dal: {d}",
        "policies.status.draft":      "Bozza",
        "policies.status.active":     "Attiva",
        "policies.status.superseded": "Sostituita",
        "policies.status.retired":    "Ritirata",
        # ── Incidents ────────────────────────────────────────────
        "incidents.header":           "Incidenti",
        "incidents.intro":            "Traccia gli incidenti di sicurezza dalla segnalazione alla risoluzione — con consapevolezza dei termini regolatori.",
        "incidents.kpi.open":         "Incidenti aperti",
        "incidents.kpi.critical":     "Critici aperti",
        "incidents.kpi.breach_pending":"Notifiche da inviare",
        "incidents.kpi.mttr":         "MTTR (giorni)",
        "incidents.filter.severity":  "Severità",
        "incidents.filter.status":    "Stato",
        "incidents.filter.category":  "Categoria",
        "incidents.new_button":       "+ Segnala incidente",
        "incidents.new_form_title":   "Segnala un nuovo incidente",
        "incidents.field.title":      "Titolo",
        "incidents.field.description":"Descrizione",
        "incidents.field.severity":   "Severità",
        "incidents.field.status":     "Stato",
        "incidents.field.category":   "Categoria",
        "incidents.field.reported_by":"Segnalato da",
        "incidents.field.impact":     "Valutazione d'impatto",
        "incidents.field.root_cause": "Causa principale",
        "incidents.field.remediation":"Rimedio",
        "incidents.field.linked_controls": "Controlli collegati (separati da virgola)",
        "incidents.field.linked_findings": "ID finding collegati (separati da virgola)",
        "incidents.field.breach_required":"Notifica di violazione richiesta",
        "incidents.field.breach_notified":"Notificato il (timestamp ISO)",
        "incidents.create_button":    "Segnala incidente",
        "incidents.created_ok":       "Incidente segnalato.",
        "incidents.update_button":    "Salva modifiche",
        "incidents.updated_ok":       "Incidente aggiornato.",
        "incidents.no_incidents":     "Nessun incidente segnalato. Clicca '+ Segnala incidente' per registrarne uno.",
        "incidents.breach_banner":    "⚠ Notifica regolatoria richiesta",
        "incidents.deadline_in":      "Scadenza: {when}",
        "incidents.deadline_overdue": "IN RITARDO — scadeva il {when}",
        "incidents.deadline_notified":"Notificato il {when}",
        "incidents.reported_on":      "Segnalato il {date}",
        "incidents.resolved_on":      "Risolto il {date}",
        "incidents.edit_section":     "Modifica incidente",
        "incidents.severity.low":     "Bassa",
        "incidents.severity.medium":  "Media",
        "incidents.severity.high":    "Alta",
        "incidents.severity.critical":"Critica",
        "incidents.status.open":      "Aperto",
        "incidents.status.investigating":"In indagine",
        "incidents.status.contained": "Contenuto",
        "incidents.status.resolved":  "Risolto",
        "incidents.status.closed":    "Chiuso",
        "incidents.cat.security_breach": "Violazione di Sicurezza",
        "incidents.cat.data_loss":    "Perdita di Dati",
        "incidents.cat.system_outage":"Disservizio Sistema",
        "incidents.cat.policy_violation":"Violazione di Policy",
        "incidents.cat.third_party":  "Terze Parti",
        "incidents.cat.other":        "Altro",
    },
}


def get_lang() -> str:
    return st.session_state.get("language", DEFAULT_LANGUAGE)


def get_theme() -> str:
    return st.session_state.get("theme", DEFAULT_THEME)


def t(key: str, **kwargs) -> str:
    lang = get_lang()
    s = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    return s.format(**kwargs) if kwargs else s


# ─── Theme / CSS ─────────────────────────────────────────────────────

THEMES = {
    "light": {
        # Off-white with a cool blueish undertone — replaces the previous
        # beige to land closer to enterprise-SaaS conventions while
        # staying coherent with the navy/teal brand.
        "bg":            "#F5F7FA",
        "surface":       "#FFFFFF",
        "surface_alt":   "#EEF1F6",   # mid layer (sidebar, sub-panels)
        "surface_elev":  "#FFFFFF",   # dropdowns/modals (stronger shadow)
        "text":          "#0F1F3D",
        "text_dim":      "#5B6B85",
        "primary":       "#163265",
        "accent":        "#0F8FA6",   # teal, slightly deeper for AA on white
        "accent_soft":   "#DCEFF3",
        "border":        "#E2E7EE",
        "border_soft":   "rgba(15,31,61,0.06)",
        "sidebar_bg":    "#FFFFFF",
        "shadow":        "0 1px 2px rgba(15,31,61,0.04), 0 4px 16px rgba(15,31,61,0.05)",
        "shadow_lg":     "0 4px 20px rgba(15,31,61,0.06), 0 16px 40px rgba(15,31,61,0.04)",
        "shadow_elev":   "0 4px 20px rgba(15,31,61,0.08)",
        "card_hover_bg": "#FAFBFD",
        "logo_text":     "#163265",
        "danger":        "#DC2626",
        "warn":          "#EA580C",
        "ok":            "#10B981",
    },
    "dark": {
        "bg":            "#0A1929",
        "surface":       "#152E47",
        "surface_alt":   "#1A3650",
        "surface_elev":  "#1F3F5C",
        "text":          "#E6F0F5",
        "text_dim":      "#8FA5BD",
        "primary":       "#4EC6D9",
        "accent":        "#4EC6D9",
        "accent_soft":   "#1E3E5C",
        "border":        "#1E3E5C",
        "border_soft":   "rgba(255,255,255,0.08)",
        "sidebar_bg":    "#0A1929",
        "shadow":        "0 1px 3px rgba(0,0,0,0.4), 0 4px 16px rgba(0,0,0,0.25)",
        "shadow_lg":     "0 4px 16px rgba(0,0,0,0.5), 0 16px 40px rgba(0,0,0,0.35)",
        "shadow_elev":   "0 4px 20px rgba(0,0,0,0.45)",
        "card_hover_bg": "#1A3650",
        "logo_text":     "#E6F0F5",
        "danger":        "#F87171",
        "warn":          "#FB923C",
        "ok":            "#34D399",
    },
}


def inject_css():
    th = THEMES[get_theme()]
    is_dark = get_theme() == "dark"
    # Atmospheric backdrop intensity differs per theme
    bg_overlay = (
        "radial-gradient(800px circle at 18% -10%, rgba(78,198,217,0.10) 0%, transparent 55%),"
        "radial-gradient(900px circle at 90% 110%, rgba(244,114,182,0.06) 0%, transparent 55%)"
        if is_dark else
        "radial-gradient(800px circle at 18% -10%, rgba(42,122,138,0.06) 0%, transparent 55%),"
        "radial-gradient(900px circle at 90% 110%, rgba(22,50,101,0.04) 0%, transparent 55%)"
    )
    grid_color = "rgba(78,198,217,0.04)" if is_dark else "rgba(22,50,101,0.04)"
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root {{
  --bg:           {th['bg']};
  --surface:      {th['surface']};
  --surface-alt:  {th['surface_alt']};
  --surface-elev: {th['surface_elev']};
  --text:         {th['text']};
  --text-dim:     {th['text_dim']};
  --primary:      {th['primary']};
  --accent:       {th['accent']};
  --accent-soft:  {th['accent_soft']};
  --border:       {th['border']};
  --border-soft:  {th['border_soft']};
  --sidebar-bg:   {th['sidebar_bg']};
  --shadow:       {th['shadow']};
  --shadow-lg:    {th['shadow_lg']};
  --shadow-elev:  {th['shadow_elev']};
  --card-hover-bg: {th['card_hover_bg']};
  --logo-text:    {th['logo_text']};
  --c-danger:     {th['danger']};
  --c-warn:       {th['warn']};
  --c-ok:         {th['ok']};
  --font-display: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-body:    'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono:    'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
}}

/* ── Compact language dropdown with inline SVG flag icons ── */
/* Both language and theme controls live in a flex container forced to
   the same baseline height (38 px) so their visual rectangles align. */
.grace-lang-wrap, .grace-theme-wrap {{
  display: flex; align-items: center;
  height: 38px;
}}
/* Streamlit wraps each widget in a container with vertical padding;
   strip it inside our wraps so the rectangles align on the same y. */
.grace-lang-wrap [data-testid="stSelectbox"],
.grace-theme-wrap [data-testid="stButton"] {{
  margin: 0 !important;
  width: 100% !important;
}}
.grace-lang-wrap [data-baseweb="select"] {{
  min-height: 38px !important;
  height: 38px !important;
}}
.grace-lang-wrap [data-baseweb="select"] > div {{
  min-height: 38px !important;
  height: 38px !important;
  padding-left: 32px !important;
  padding-right: 30px !important;
  border-radius: 10px !important;
  background-color: var(--surface) !important;
  border: 1px solid var(--border) !important;
  background-repeat: no-repeat !important;
  background-position: 8px center !important;
  background-size: 18px 12px !important;
  font-family: var(--font-display) !important;
  font-weight: 700 !important;
  font-size: 0.82rem !important;
  letter-spacing: 0.8px !important;
  display: flex !important;
  align-items: center !important;
  box-shadow: var(--shadow);
}}
.grace-lang-wrap.lang-selected-en [data-baseweb="select"] > div {{
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'><rect width='60' height='40' fill='%23B22234'/><rect y='3.1' width='60' height='3.1' fill='%23fff'/><rect y='9.3' width='60' height='3.1' fill='%23fff'/><rect y='15.5' width='60' height='3.1' fill='%23fff'/><rect y='21.7' width='60' height='3.1' fill='%23fff'/><rect y='27.9' width='60' height='3.1' fill='%23fff'/><rect y='34.1' width='60' height='3.1' fill='%23fff'/><rect width='24' height='21.5' fill='%233C3B6E'/></svg>") !important;
}}
.grace-lang-wrap.lang-selected-it [data-baseweb="select"] > div {{
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 3 2'><rect width='1' height='2' x='0' fill='%23009246'/><rect width='1' height='2' x='1' fill='%23fff'/><rect width='1' height='2' x='2' fill='%23CE2B37'/></svg>") !important;
}}
/* Open-state dropdown items: paint flags ONLY on the language popover.
   BaseWeb renders selectbox popovers as <body>-level portals, so the
   trigger's .grace-lang-wrap class doesn't propagate inside. We scope
   instead via :has() — popovers whose option list has exactly two
   options (the EN/IT picker is the only 2-option selectbox in the app)
   get flags. The selectors don't require direct-child relationships
   so they survive any internal wrapper BaseWeb may render. */
[data-baseweb="popover"]:has([role="option"]:nth-child(2):last-child) [role="option"] {{
  background-repeat: no-repeat !important;
  background-position: 14px center !important;
  background-size: 22px 14px !important;
  padding-left: 46px !important;
  font-family: var(--font-display) !important;
  font-weight: 600 !important;
  letter-spacing: 0.6px !important;
}}
[data-baseweb="popover"]:has([role="option"]:nth-child(2):last-child) [role="option"]:nth-child(1) {{
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'><rect width='60' height='40' fill='%23B22234'/><rect y='3.1' width='60' height='3.1' fill='%23fff'/><rect y='9.3' width='60' height='3.1' fill='%23fff'/><rect y='15.5' width='60' height='3.1' fill='%23fff'/><rect y='21.7' width='60' height='3.1' fill='%23fff'/><rect y='27.9' width='60' height='3.1' fill='%23fff'/><rect y='34.1' width='60' height='3.1' fill='%23fff'/><rect width='24' height='21.5' fill='%233C3B6E'/></svg>") !important;
}}
[data-baseweb="popover"]:has([role="option"]:nth-child(2):last-child) [role="option"]:nth-child(2) {{
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 3 2'><rect width='1' height='2' x='0' fill='%23009246'/><rect width='1' height='2' x='1' fill='%23fff'/><rect width='1' height='2' x='2' fill='%23CE2B37'/></svg>") !important;
}}
/* Fallback for browsers without :has() — only ~3% of users. Targets
   any popover with 2 options. Harmless because no other 2-option
   selectbox exists in the app. */
@supports not (selector(:has(*))) {{
  [data-baseweb="popover"] [role="option"]:nth-child(1):nth-last-child(2) {{
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'><rect width='60' height='40' fill='%23B22234'/><rect width='24' height='21.5' fill='%233C3B6E'/></svg>") !important;
    background-repeat: no-repeat !important;
    background-position: 14px center !important;
    background-size: 22px 14px !important;
    padding-left: 46px !important;
  }}
  [data-baseweb="popover"] [role="option"]:nth-child(2):last-child {{
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 3 2'><rect width='1' height='2' x='0' fill='%23009246'/><rect width='1' height='2' x='1' fill='%23fff'/><rect width='1' height='2' x='2' fill='%23CE2B37'/></svg>") !important;
    background-repeat: no-repeat !important;
    background-position: 14px center !important;
    background-size: 22px 14px !important;
    padding-left: 46px !important;
  }}
}}

.grace-theme-wrap .stButton button {{
  min-height: 38px !important;
  height: 38px !important;
  width: 44px !important;
  padding: 0 !important;
  border-radius: 10px !important;
  font-size: 1.1rem !important;
  line-height: 1 !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  box-shadow: var(--shadow);
}}
.grace-theme-wrap .stButton button:hover {{
  border-color: var(--accent) !important;
  transform: translateY(-1px);
}}
.grace-theme-wrap .stButton button p {{
  margin: 0 !important; font-size: 1.05rem !important;
}}

/* ── Update buttons in the Finding Registry: black on white ──
   The previous .finding-update wrapper didn't actually wrap anything
   (st.markdown HTML is a sibling of subsequent widgets, not a parent),
   so the selectors never matched. Switching to a structural target:
   every non-primary stButton that lives inside an expander gets the
   black-on-white treatment. The theme-toggle button keeps its own
   look via its specific .grace-theme-wrap override later. */
[data-testid="stExpander"] [data-testid="stButton"] button[kind="secondary"],
[data-testid="stExpander"] [data-testid="stButton"] button:not([kind="primary"]) {{
  background: #FFFFFF !important;
  color: #000000 !important;
  border: 1px solid var(--border) !important;
  font-weight: 700 !important;
  letter-spacing: 0.3px;
}}
[data-testid="stExpander"] [data-testid="stButton"] button:not([kind="primary"]) *,
[data-testid="stExpander"] [data-testid="stButton"] button:not([kind="primary"]) p,
[data-testid="stExpander"] [data-testid="stButton"] button:not([kind="primary"]) div {{
  color: #000000 !important;
}}
[data-testid="stExpander"] [data-testid="stButton"] button:not([kind="primary"]):hover {{
  background: var(--accent) !important;
  color: #FFFFFF !important;
  border-color: var(--accent) !important;
}}
[data-testid="stExpander"] [data-testid="stButton"] button:not([kind="primary"]):hover *,
[data-testid="stExpander"] [data-testid="stButton"] button:not([kind="primary"]):hover p,
[data-testid="stExpander"] [data-testid="stButton"] button:not([kind="primary"]):hover div {{
  color: #FFFFFF !important;
}}

/* ── Sidebar brand panel (circular GRACE symbol) ── */
.grace-side-brand {{
  background: linear-gradient(140deg, #4EC6D9 0%, #2A7A8A 100%);
  border-radius: 16px;
  padding: 22px 14px 18px;
  text-align: center;
  margin-bottom: 14px;
  box-shadow: 0 8px 24px rgba(22,50,101,0.22), inset 0 1px 0 rgba(255,255,255,0.10);
  position: relative; overflow: hidden;
}}
.grace-side-brand::before {{
  content: ""; position: absolute; inset: 0;
  background: radial-gradient(circle at 50% 30%, rgba(255,255,255,0.18) 0%, transparent 60%);
  pointer-events: none;
}}
.grace-side-brand img {{
  height: 96px; width: auto; display: block; margin: 0 auto;
  filter: drop-shadow(0 2px 6px rgba(0,0,0,0.20));
  position: relative; z-index: 1;
}}

/* ── Streamlit app chrome ── */
.stApp {{
  background: var(--bg);
  background-image: {bg_overlay};
  background-attachment: fixed;
  color: var(--text);
}}
[data-testid="stHeader"] {{ display: none; }}
[data-testid="stSidebar"] {{
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
}}
[data-testid="stSidebar"] * {{ color: var(--text) !important; }}
.block-container {{
  padding-top: 0.5rem !important;
  max-width: 1500px;
  position: relative;
  z-index: 1;
}}

/* Faint grid backdrop on the main app */
.stApp::before {{
  content: "";
  position: fixed; inset: 0;
  background-image:
    linear-gradient({grid_color} 1px, transparent 1px),
    linear-gradient(90deg, {grid_color} 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(circle at 50% 30%, rgba(0,0,0,0.65) 0%, transparent 70%);
  -webkit-mask-image: radial-gradient(circle at 50% 30%, rgba(0,0,0,0.65) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}}

/* ── Typography ── */
html, body, .stApp, [data-testid="stMarkdownContainer"],
.stMarkdown p, .stMarkdown li {{
  font-family: var(--font-body); color: var(--text);
}}
h1, h2, h3, h4 {{
  font-family: var(--font-display);
  color: var(--text); letter-spacing: -0.015em;
}}
h1 {{ font-weight: 700; }}
h2 {{ font-weight: 600; }}
h3 {{ font-weight: 600; }}
code, pre, .stCode {{ font-family: var(--font-mono) !important; }}

/* ── Top bar: full-width header dominated by the GRACE logo image
   (the image itself carries the wordmark + tagline, no duplicate text). ── */
.grace-topbar {{
  display: flex; align-items: stretch; justify-content: flex-start;
  background:
    linear-gradient(160deg, var(--surface) 0%, var(--surface-alt) 100%);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 12px 18px;
  margin: 14px 0 28px 0;
  box-shadow: var(--shadow);
  position: relative; overflow: hidden;
}}
.grace-topbar::before {{
  content: ""; position: absolute; inset: -1px;
  background: linear-gradient(120deg, transparent 0%, rgba(78,198,217,0.30) 40%, transparent 80%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  padding: 1px; border-radius: 18px; pointer-events: none;
}}
.grace-topbar .brand {{
  display: flex; align-items: center; justify-content: center;
  position: relative; z-index: 1;
  width: 100%; height: 100%;
}}
.grace-topbar .brand-logo {{
  /* Fill the topbar horizontally. Aspect ratio is preserved, so the
     topbar height grows proportionally with the page width.
     max-height keeps it from getting silly on very wide screens. */
  width: 100%;
  height: auto;
  max-height: 360px;
  object-fit: contain;
  filter: drop-shadow(0 3px 8px rgba(22,50,101,0.25));
  display: block;
}}

/* ── Status pill ── */
.status-pill {{
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--accent-soft); color: var(--primary);
  padding: 6px 12px; border-radius: 999px;
  font-size: 0.78rem; font-weight: 600; letter-spacing: 0.3px;
  border: 1px solid var(--border);
  font-family: var(--font-display);
}}
.status-pill.online::before {{
  content: ""; width: 8px; height: 8px; border-radius: 50%; background: #22C55E;
  box-shadow: 0 0 8px #22C55E;
  animation: grace-pulse 2s ease-in-out infinite;
}}
.status-pill.degraded {{ color: #B45309; }}
.status-pill.degraded::before {{
  content: ""; width: 8px; height: 8px; border-radius: 50%; background: #F59E0B;
  box-shadow: 0 0 8px #F59E0B;
  animation: grace-pulse 2s ease-in-out infinite;
}}
.status-pill.offline {{ color: #991B1B; }}
.status-pill.offline::before {{
  content: ""; width: 8px; height: 8px; border-radius: 50%; background: #DC2626;
  box-shadow: 0 0 8px #DC2626;
}}
@keyframes grace-pulse {{
  0%, 100% {{ box-shadow: 0 0 0 0 rgba(34,197,94,0.55); }}
  50%      {{ box-shadow: 0 0 0 6px rgba(34,197,94,0); }}
}}

/* ── Badges ── */
.badge {{
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: 999px;
  font-size: 11.5px; font-weight: 600;
  border: 1px solid transparent;
  font-family: var(--font-display); letter-spacing: 0.3px;
}}
.badge-red    {{ background:#FEE2E2; color:#991B1B; border-color:#FCA5A5; }}
.badge-orange {{ background:#FFEDD5; color:#9A3412; border-color:#FED7AA; }}
.badge-yellow {{ background:#FEF9C3; color:#854D0E; border-color:#FDE68A; }}
.badge-green  {{ background:#D1FAE5; color:#065F46; border-color:#86EFAC; }}
.badge-gray   {{ background:#F3F4F6; color:#374151; border-color:#D1D5DB; }}
.badge-teal   {{ background:#CCFBF1; color:#115E59; border-color:#5EEAD4; }}
.badge-blue   {{ background:#DBEAFE; color:#1E40AF; border-color:#93C5FD; }}

/* ── Cross-framework impact (small pill matching .badge sizing) ── */
.xframework-badge {{
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 999px;
  font-size: 11.5px; font-weight: 600;
  font-family: var(--font-display); letter-spacing: 0.3px;
  background: #EEF2FF; color: #3730A3; border: 1px solid #C7D2FE;
}}
.xfw-conf {{
  display: inline-block; padding: 2px 8px; border-radius: 999px;
  font-size: 10.5px; font-weight: 600; letter-spacing: 0.3px;
  font-family: var(--font-display); border: 1px solid transparent;
}}
.xfw-conf.high   {{ background:#D1FAE5; color:#065F46; border-color:#86EFAC; }}
.xfw-conf.medium {{ background:#FEF9C3; color:#854D0E; border-color:#FDE68A; }}
.xfw-conf.low    {{ background:#F3F4F6; color:#374151; border-color:#D1D5DB; }}
.xfw-row {{
  padding: 10px 12px; margin: 6px 0;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px;
}}
.xfw-row .xfw-head {{
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  font-size: 0.85rem;
}}
.xfw-row .xfw-fw {{
  font-family: var(--font-mono); font-size: 0.78rem;
  color: var(--text-dim); background: var(--surface-alt);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 1px 6px;
}}
.xfw-row .xfw-ctrl {{
  font-family: var(--font-mono); font-weight: 700; color: var(--primary);
}}
.xfw-row .xfw-title {{ color: var(--text); }}
.xfw-row .xfw-rat {{
  margin-top: 6px; font-size: 0.82rem; color: var(--text-dim);
  line-height: 1.45;
}}

/* ── Finding card ── */
.finding-card {{
  background: linear-gradient(180deg, var(--surface) 0%, var(--surface-alt) 100%);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 20px;
  margin-bottom: 14px;
  border-left: 4px solid var(--accent);
  box-shadow: var(--shadow);
  transition: transform 0.18s cubic-bezier(.2,.6,.2,1), box-shadow 0.18s ease;
  position: relative; overflow: hidden;
}}
.finding-card::after {{
  content: ""; position: absolute; right: -40px; top: -40px;
  width: 110px; height: 110px; border-radius: 50%;
  background: radial-gradient(circle, rgba(78,198,217,0.10) 0%, transparent 70%);
  pointer-events: none;
}}
.finding-card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-lg); }}
.finding-card.critical {{ border-left-color: #DC2626; }}
.finding-card.high     {{ border-left-color: #EA580C; }}
.finding-card.medium   {{ border-left-color: #EAB308; }}
.finding-card.low      {{ border-left-color: #6B7280; }}
.finding-card .ctrl-id {{
  color: var(--primary); font-weight: 700;
  font-family: var(--font-mono); font-size: 0.9rem;
}}
.finding-card .ctrl-title {{ color: var(--text); font-weight: 500; }}
.finding-card .finding-body {{
  color: var(--text-dim); font-size: 0.88rem; margin: 10px 0;
  line-height: 1.55;
}}
.finding-card .rem {{
  color: var(--text); font-size: 0.84rem;
  padding-top: 10px; border-top: 1px solid var(--border);
}}
.finding-card .reg-ref {{ color: var(--text-dim); font-size: 0.78rem; font-family: var(--font-mono); }}

/* ── Ask GRACE: chat bubbles & history ── */
.chat-bubble {{
  padding: 12px 14px;
  border-radius: 14px;
  max-width: 80%;
  margin: 8px 0;
  font-size: 0.92rem;
  line-height: 1.55;
  box-shadow: var(--shadow);
}}
.chat-bubble.user {{
  background: color-mix(in srgb, var(--accent) 18%, var(--surface));
  border: 1px solid color-mix(in srgb, var(--accent) 35%, var(--border));
  color: var(--text);
  margin-left: auto;
  margin-right: 0;
  border-bottom-right-radius: 4px;
}}
.chat-bubble.assistant {{
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
  margin-right: auto;
  margin-left: 0;
  border-bottom-left-radius: 4px;
}}
.chat-bubble .chat-role {{
  font-family: var(--font-display);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--text-dim);
  margin-bottom: 6px;
  font-weight: 700;
}}
.chat-bubble.user .chat-role {{ color: var(--accent); text-align: right; }}
.chat-bubble.assistant .chat-role {{ color: var(--primary); }}
.chat-bubble .chat-body {{ color: var(--text); }}
.chat-citations {{
  display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
  padding-top: 8px; border-top: 1px dashed var(--border);
}}
.chat-citation {{
  display: inline-block;
  background: color-mix(in srgb, var(--text-dim) 12%, transparent);
  color: var(--text-dim);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 9px;
  font-size: 0.72rem;
  font-family: var(--font-mono);
}}
.chat-history-item {{
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid transparent;
  margin-bottom: 4px;
  cursor: pointer;
  transition: background 0.12s ease;
}}
.chat-history-item:hover {{
  background: color-mix(in srgb, var(--text-dim) 8%, transparent);
}}
.chat-history-item.active {{
  background: color-mix(in srgb, var(--accent) 14%, transparent);
  border-left: 3px solid var(--accent);
}}
.chat-empty-state {{
  text-align: center;
  padding: 36px 24px;
  background: var(--surface-alt);
  border: 1px dashed var(--border);
  border-radius: 14px;
  color: var(--text-dim);
}}
.chat-empty-state h3 {{
  color: var(--primary);
  font-family: var(--font-display);
  margin: 0 0 8px 0;
}}

/* ── Gap Analysis wizard ── */
.wizard-step {{
  display: flex; align-items: center; gap: 8px;
  font-family: var(--font-display);
  font-size: 0.78rem; font-weight: 700;
  color: var(--text-dim);
  letter-spacing: 1px; text-transform: uppercase;
  margin: 16px 0 6px 0;
}}
.wizard-step .step-num {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 18%, var(--surface));
  color: var(--accent);
  border: 1px solid color-mix(in srgb, var(--accent) 40%, var(--border));
  font-size: 0.72rem;
}}
.wizard-placeholder {{
  text-align: left;
  padding: 24px 22px;
  background: var(--surface-alt);
  border: 1px dashed var(--border);
  border-radius: 14px;
  color: var(--text-dim);
}}
.wizard-placeholder h3 {{
  color: var(--primary);
  font-family: var(--font-display);
  margin: 0 0 8px 0; font-size: 1.05rem;
}}

/* ── KPI cards (hub-grid style) ── */
.kpi-card {{
  background: linear-gradient(180deg, var(--surface) 0%, var(--surface-alt) 100%);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px 18px;
  text-align: center;
  box-shadow: var(--shadow);
  transition: transform 0.18s cubic-bezier(.2,.6,.2,1), box-shadow 0.18s ease;
  position: relative; overflow: hidden;
}}
.kpi-card::before {{
  content: ""; position: absolute; inset: 0;
  background: radial-gradient(circle at 50% 0%, rgba(78,198,217,0.10) 0%, transparent 60%);
  pointer-events: none;
}}
.kpi-card:hover {{ transform: translateY(-3px); box-shadow: var(--shadow-lg); }}
.kpi-card .kpi-value {{
  font-family: var(--font-display);
  font-size: 2.4rem; font-weight: 700; color: var(--primary); line-height: 1;
}}
.kpi-card .kpi-label {{
  font-family: var(--font-display);
  font-size: 0.74rem; color: var(--text-dim); margin-top: 8px;
  text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600;
}}
.kpi-card .kpi-icon {{ font-size: 1.5rem; opacity: 0.65; margin-bottom: 4px; }}

/* ── Score bar ── */
.score-bar {{
  height: 10px; border-radius: 10px;
  background: var(--accent-soft); overflow: hidden;
  border: 1px solid var(--border);
}}
.score-fill {{
  height: 100%; border-radius: 10px;
  transition: width 0.4s cubic-bezier(.2,.6,.2,1);
  background: linear-gradient(90deg, currentColor 0%, color-mix(in srgb, currentColor 70%, white) 100%);
}}

/* ── Hero panel ── */
.page-hero {{
  background:
    linear-gradient(135deg, var(--surface) 0%, var(--surface-alt) 100%);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px 26px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  position: relative; overflow: hidden;
}}
.page-hero::after {{
  content: ""; position: absolute;
  top: -60px; right: -60px;
  width: 200px; height: 200px; border-radius: 50%;
  background: radial-gradient(circle, rgba(78,198,217,0.14) 0%, transparent 70%);
  pointer-events: none;
}}
.page-hero h1 {{
  margin: 0 0 6px 0; font-size: 1.75rem; color: var(--primary);
  font-family: var(--font-display); font-weight: 700;
  letter-spacing: -0.5px;
}}
.page-hero p {{ margin: 0; color: var(--text-dim); font-size: 0.94rem; }}

/* ── Section subtitle ── */
.section-sub {{
  font-family: var(--font-display);
  font-size: 0.85rem; font-weight: 700; color: var(--accent);
  margin: 18px 0 10px 0; letter-spacing: 1.4px; text-transform: uppercase;
}}

/* ── Streamlit widget tweaks ── */
.stButton button, .stDownloadButton button {{
  border-radius: 10px; font-weight: 600;
  font-family: var(--font-body);
  transition: all 0.18s cubic-bezier(.2,.6,.2,1);
}}
.stButton button[kind="primary"],
.stDownloadButton button[kind="primary"] {{
  background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%) !important;
  color: #FFFFFF !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(22,50,101,0.25);
}}
.stButton button[kind="primary"] *,
.stButton button[kind="primary"] p,
.stDownloadButton button[kind="primary"] *,
.stDownloadButton button[kind="primary"] p {{
  color: #FFFFFF !important;
}}
.stButton button[kind="primary"]:hover,
.stDownloadButton button[kind="primary"]:hover {{
  transform: translateY(-2px);
  box-shadow: 0 6px 22px rgba(78,198,217,0.35);
  filter: brightness(1.06);
}}
[data-testid="stExpander"] {{
  background: var(--surface);
  border-radius: 12px;
  border: 1px solid var(--border) !important;
  box-shadow: var(--shadow);
  transition: box-shadow 0.18s ease;
}}
[data-testid="stExpander"]:hover {{ box-shadow: var(--shadow-lg); }}
[data-testid="stExpander"] summary {{ padding: 10px 14px; font-weight: 500; }}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {{
  border-radius: 10px !important;
  border: 1px solid var(--border) !important;
  font-family: var(--font-body) !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-soft) !important;
}}
[data-testid="stSelectbox"] > div {{ border-radius: 10px !important; }}

/* ── Recent doc row ── */
.recent-row {{
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 10px;
  background: var(--surface); border: 1px solid var(--border);
  margin-bottom: 8px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.recent-row:hover {{ transform: translateX(2px); box-shadow: var(--shadow); }}
.recent-row .doc-name {{ font-weight: 600; color: var(--text); }}
.recent-row .meta {{
  color: var(--text-dim); font-size: 0.78rem;
  margin-left: auto; font-family: var(--font-mono);
}}
.recent-row .fw-tag {{
  background: var(--accent-soft); color: var(--primary);
  padding: 3px 9px; border-radius: 6px;
  font-size: 0.72rem; font-weight: 700;
  font-family: var(--font-display); letter-spacing: 0.5px;
}}

/* ════════════════════════════════════════════════════════════════
   ENTERPRISE-SaaS REFRESH — sidebar nav, topbar crumb, status,
   KPI typography, hover lifts, surface elevation, all-caps labels
   ════════════════════════════════════════════════════════════════ */

/* ── Sidebar brand: symbol + CSS wordmark + tagline (all readable) ── */
.grace-side-brand-compact {{
  display: flex; flex-direction: column; align-items: center;
  gap: 8px;
  padding: 22px 14px;
  margin-bottom: 14px;
  text-align: center;
  /* Brand card is intentionally LIGHT on both themes — the GRACE logo
     is navy + teal on a cream background by design, so its strokes
     need a light backdrop to read crisply. On the dark-mode sidebar
     this also makes the panel pop forward as a distinct surface. */
  background: linear-gradient(160deg, #FFFFFF 0%, #E8F1F8 100%);
  border: 1px solid #4EC6D9;
  border-radius: 14px;
  box-shadow:
    0 0 0 1px rgba(78,198,217,0.20),
    0 8px 22px rgba(0,0,0,0.30),
    inset 0 1px 0 rgba(255,255,255,0.50);
}}
.grace-side-brand-compact .brand-symbol {{
  width: 96px; height: 96px;
  object-fit: contain;
  filter: drop-shadow(0 2px 6px rgba(15,31,61,0.18));
  display: block;
}}
.grace-side-brand-compact .brand-symbol-fallback {{
  font-size: 4.4rem; line-height: 1;
}}
.grace-side-brand-compact .brand-name {{
  font-family: var(--font-display);
  font-size: 1.72rem; font-weight: 800;
  /* Brand card is always light, so the wordmark stays dark navy on
     BOTH themes. !important is needed because the global sidebar
     rule '[data-testid=stSidebar] * {{ color: var(--text) !important }}'
     would otherwise paint it light in dark mode. */
  color: #163265 !important;
  letter-spacing: 4px;
  margin-top: 4px;
  line-height: 1;
}}
.grace-side-brand-compact .brand-tagline {{
  font-family: var(--font-display);
  font-size: 0.74rem; font-weight: 600;
  letter-spacing: 0.5px;
  color: #5B6B85 !important;
  line-height: 1.3;
  margin-top: 2px;
  padding: 0 4px;
}}

/* ── Sidebar nav items ──
   Streamlit emits HTML markdown as a sibling of subsequent widgets
   (not as a parent), so wrapping divs around st.button() doesn't
   actually nest. We target the buttons directly via [data-testid="stSidebar"]
   instead — that selector matches reliably on both themes.
   Icons are positioned visually next to each button via a small SVG
   row rendered above the button; the active state is signalled by
   wrapping markdown that uses CSS `+` selectors to colour the
   following Streamlit button. */
[data-testid="stSidebar"] .nav-list {{ margin: 6px 0; }}
[data-testid="stSidebar"] .nav-icon {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px;
  color: var(--text-dim);
  vertical-align: middle;
  margin-right: 4px;
}}
[data-testid="stSidebar"] .nav-icon.active {{ color: var(--accent); }}
[data-testid="stSidebar"] .nav-icon svg {{ width: 18px; height: 18px; }}
[data-testid="stSidebar"] .nav-row {{
  display: flex; align-items: center; gap: 8px;
  padding: 2px 8px 2px 12px;
  margin: 4px 0 -8px;
  border-radius: 10px 10px 0 0;
  transition: background 0.18s ease;
}}
[data-testid="stSidebar"] .nav-row.active {{
  background: var(--accent-soft);
  box-shadow: inset 3px 0 0 var(--accent);
}}
[data-testid="stSidebar"] .nav-row .nav-label-hint {{
  font-family: var(--font-display);
  font-size: 0.62rem; letter-spacing: 1.1px;
  text-transform: uppercase;
  color: var(--text-dim);
  font-weight: 700;
}}
[data-testid="stSidebar"] .nav-row.active .nav-label-hint {{ color: var(--accent); }}

/* Generic sidebar button restyle — used by the nav buttons AND the
   reset confirm button. Black text on white surface for guaranteed
   readability on both themes. */
[data-testid="stSidebar"] [data-testid="stButton"] button {{
  background: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  font-family: var(--font-body) !important;
  font-weight: 600 !important;
  font-size: 0.92rem !important;
  text-align: left !important;
  padding: 9px 14px !important;
  width: 100% !important;
  box-shadow: none !important;
  letter-spacing: 0.2px;
}}
[data-testid="stSidebar"] [data-testid="stButton"] button *,
[data-testid="stSidebar"] [data-testid="stButton"] button p {{
  color: var(--text) !important;
}}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {{
  background: var(--accent-soft) !important;
  border-color: var(--accent) !important;
  transform: translateX(2px);
}}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover *,
[data-testid="stSidebar"] [data-testid="stButton"] button:hover p {{
  color: var(--accent) !important;
}}
/* Primary-kind sidebar buttons (reset confirm) keep the accent fill */
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {{
  background: var(--accent) !important;
  color: #FFFFFF !important;
  border-color: var(--accent) !important;
  text-align: center !important;
}}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] *,
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] p {{
  color: #FFFFFF !important;
}}

/* ── System status component (sidebar) ── */
.system-status {{
  display: flex; align-items: center; gap: 10px;
  margin: 14px 0 10px;
  padding: 10px 12px;
  background: var(--surface-alt);
  border: 1px solid var(--border-soft);
  border-radius: 10px;
}}
.system-status .status-dot {{
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
  position: relative;
}}
.system-status.status-ok       .status-dot {{ background: var(--c-ok);      box-shadow: 0 0 0 0 rgba(16,185,129,0.5); animation: stat-pulse 2s ease-in-out infinite; }}
.system-status.status-degraded .status-dot {{ background: var(--c-warn);    box-shadow: 0 0 0 0 rgba(234,88,12,0.5);  animation: stat-pulse 2s ease-in-out infinite; }}
.system-status.status-down     .status-dot {{ background: var(--c-danger); }}
@keyframes stat-pulse {{
  0%, 100% {{ box-shadow: 0 0 0 0 currentColor; opacity: 1; }}
  50%      {{ box-shadow: 0 0 0 6px transparent; opacity: 0.7; }}
}}
.system-status .status-body {{ display: flex; flex-direction: column; line-height: 1.2; min-width: 0; }}
.system-status .status-title {{
  font-size: 0.78rem; font-weight: 700; color: var(--text);
  font-family: var(--font-display);
}}
.system-status .status-meta {{
  font-size: 0.66rem; color: var(--text-dim);
  font-family: var(--font-mono);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-top: 2px;
}}

/* ── Topbar breadcrumb (replaces the hero logo on operative pages) ── */
.grace-crumb {{
  display: flex; align-items: center; gap: 10px;
  padding: 14px 4px 6px;
  font-family: var(--font-display);
}}
.grace-crumb .crumb-home {{
  font-weight: 700; color: var(--text-dim); font-size: 0.85rem;
  letter-spacing: 0.5px;
}}
.grace-crumb .crumb-sep {{ color: var(--text-dim); opacity: 0.5; }}
.grace-crumb .crumb-current {{
  font-weight: 700; color: var(--text); font-size: 1rem;
  letter-spacing: 0.3px;
}}

/* ── Typography hierarchy (premium) ── */
.page-hero h1 {{
  font-size: 2.05rem !important; font-weight: 700 !important;
  letter-spacing: -0.6px !important;
}}
.section-sub {{
  font-family: var(--font-display);
  font-size: 0.72rem !important; font-weight: 700 !important;
  letter-spacing: 1.6px !important;
  text-transform: uppercase;
  color: var(--text-dim) !important;
  margin-top: 22px !important;
}}
/* Form labels: small-caps, dim, professional */
.stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label,
.stMultiSelect label, .stNumberInput label, .stDateInput label {{
  font-family: var(--font-display) !important;
  font-size: 0.7rem !important; font-weight: 700 !important;
  letter-spacing: 1.2px !important;
  text-transform: uppercase;
  color: var(--text-dim) !important;
}}

/* ── KPI cards: bigger numbers, trend chip ── */
.kpi-card {{
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: 16px;
  padding: 22px 20px;
  box-shadow: var(--shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  text-align: left;
}}
.kpi-card:hover {{ transform: translateY(-3px); box-shadow: var(--shadow-lg); }}
.kpi-card .kpi-label {{
  font-family: var(--font-display);
  font-size: 0.66rem; font-weight: 700; letter-spacing: 1.4px;
  text-transform: uppercase; color: var(--text-dim);
  margin-bottom: 10px;
}}
.kpi-card .kpi-value {{
  font-family: var(--font-display);
  font-size: 2.6rem; font-weight: 800; line-height: 1;
  color: var(--text);
  font-variant-numeric: tabular-nums;
  letter-spacing: -1px;
}}
.kpi-card .kpi-row {{ display: flex; align-items: baseline; gap: 10px; margin-top: 4px; }}
.kpi-card .kpi-trend {{
  display: inline-flex; align-items: center; gap: 3px;
  font-family: var(--font-display);
  font-size: 0.74rem; font-weight: 700;
  padding: 2px 7px; border-radius: 6px;
}}
.kpi-card .kpi-trend.neutral {{ color: var(--text-dim); background: var(--surface-alt); }}
.kpi-card .kpi-trend.up      {{ color: var(--c-ok);     background: color-mix(in srgb, var(--c-ok) 12%, transparent); }}
.kpi-card .kpi-trend.down    {{ color: var(--c-danger); background: color-mix(in srgb, var(--c-danger) 12%, transparent); }}
/* Primary KPI tile — bigger value, accent-tinted background */
.kpi-card.kpi-primary {{
  background: linear-gradient(180deg, var(--surface) 0%, color-mix(in srgb, var(--accent) 8%, var(--surface)) 100%);
  border: 1px solid color-mix(in srgb, var(--accent) 25%, var(--border));
}}
.kpi-card.kpi-primary .kpi-value {{ font-size: 3.4rem; color: var(--accent); }}
.kpi-card.kpi-primary .kpi-label {{ color: var(--accent); }}

/* ── Buttons: micro-lift and smoother transitions ── */
.stButton button, .stDownloadButton button {{
  transition: transform 0.18s cubic-bezier(.2,.6,.2,1),
              box-shadow 0.18s ease,
              background 0.18s ease !important;
}}

/* Secondary buttons in the MAIN area (not sidebar) need explicit
   black-on-white styling in dark mode — Streamlit's default in dark
   theme was making the 'Open in Registry' KPI buttons render with
   light text on a light background (illegible). Sidebar buttons are
   already styled separately and override this. */
[data-testid="stAppViewContainer"] .stButton button:not([kind="primary"]),
[data-testid="stAppViewContainer"] .stDownloadButton button:not([kind="primary"]) {{
  background: #FFFFFF !important;
  color: #000000 !important;
  border: 1px solid var(--border) !important;
  font-weight: 600 !important;
}}
[data-testid="stAppViewContainer"] .stButton button:not([kind="primary"]) *,
[data-testid="stAppViewContainer"] .stButton button:not([kind="primary"]) p,
[data-testid="stAppViewContainer"] .stDownloadButton button:not([kind="primary"]) *,
[data-testid="stAppViewContainer"] .stDownloadButton button:not([kind="primary"]) p {{
  color: #000000 !important;
}}
[data-testid="stAppViewContainer"] .stButton button:not([kind="primary"]):hover,
[data-testid="stAppViewContainer"] .stDownloadButton button:not([kind="primary"]):hover {{
  background: var(--accent-soft) !important;
  border-color: var(--accent) !important;
}}
/* Re-restore the theme-toggle button (icon-only, brand-aligned) so the
   global rule above doesn't flatten it. */
.grace-theme-wrap .stButton button {{
  background: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}
.grace-theme-wrap .stButton button * {{ color: var(--text) !important; }}

/* ── Inputs: focus glow ── */
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stSelectbox"] > div:focus-within {{
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 22%, transparent) !important;
}}

/* ── Dividers: alpha gradient instead of harsh line ── */
hr {{
  border: none !important;
  height: 1px !important;
  background: linear-gradient(90deg, transparent 0%, var(--border-soft) 20%, var(--border-soft) 80%, transparent 100%) !important;
  margin: 16px 0 !important;
}}

/* ════════════════════════════════════════════════════════════════
   Phase 2: SVG icon badges, donut, severity stacked bar,
            KPI head/link/clickable styling
   ════════════════════════════════════════════════════════════════ */

/* Inline icon inside .badge */
.badge {{ gap: 5px; }}
.badge .badge-icon {{
  display: inline-flex; align-items: center; line-height: 0;
}}

/* KPI card glyph row + click affordance */
.kpi-card .kpi-head {{
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 10px;
  color: var(--text-dim);
}}
.kpi-card.kpi-primary .kpi-head {{ color: var(--accent); }}
.kpi-card .kpi-glyph {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  border-radius: 7px;
  background: var(--surface-alt);
  color: var(--text-dim);
}}
.kpi-card.kpi-primary .kpi-glyph {{
  background: color-mix(in srgb, var(--accent) 18%, transparent);
  color: var(--accent);
}}
.kpi-card .kpi-link {{
  display: inline-flex; align-items: center; gap: 4px;
  font-family: var(--font-display);
  font-size: 0.66rem; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-dim);
  margin-top: 14px;
  opacity: 0;
  transition: opacity 0.2s ease;
}}
.kpi-card:hover .kpi-link {{ opacity: 1; color: var(--accent); }}
.kpi-card.kpi-clickable {{ cursor: pointer; }}

/* ── Donut chart ── */
.donut-grid {{
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}}
.donut-wrap {{
  display: flex; align-items: center; gap: 14px;
  margin-bottom: 14px;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}}
.donut-wrap:hover {{ transform: translateY(-1px); box-shadow: var(--shadow); }}
.donut-wrap .donut-svg {{
  width: 72px; height: 72px;
  flex-shrink: 0;
}}
.donut-wrap .donut-meta {{ display: flex; flex-direction: column; line-height: 1.25; min-width: 0; }}
.donut-wrap .donut-label {{
  font-family: var(--font-display);
  font-size: 0.92rem; font-weight: 700;
  color: var(--text);
}}
.donut-wrap .donut-sub {{
  font-size: 0.76rem; color: var(--text-dim);
  margin-top: 2px;
}}

/* ── Severity stacked bar + legend ── */
.sev-bar {{
  display: flex; width: 100%; height: 24px;
  border-radius: 8px; overflow: hidden;
  background: var(--surface-alt);
  border: 1px solid var(--border-soft);
}}
.sev-seg {{ height: 100%; transition: opacity 0.2s ease; }}
.sev-seg:hover {{ opacity: 0.8; }}
.sev-legend {{
  display: flex; flex-wrap: wrap; gap: 18px;
  margin-top: 12px;
}}
.sev-leg {{
  display: inline-flex; align-items: center; gap: 6px;
  font-family: var(--font-display);
  font-size: 0.76rem;
}}
.sev-dot {{
  width: 10px; height: 10px; border-radius: 50%;
}}
.sev-leg-label {{
  color: var(--text-dim);
  font-weight: 600; letter-spacing: 0.4px;
  text-transform: uppercase; font-size: 0.7rem;
}}
.sev-leg-count {{
  color: var(--text);
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}}

/* ── Phase 1 — Risk / Vendor / Policy / Incident module styles ── */

/* Generic record card — drop-in for findings-style cards in non-findings
   pages. Keeps the navy/teal/amber palette and the same left-border
   severity colouring. */
.record-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--text-dim);
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 12px;
  box-shadow: var(--shadow);
  transition: transform .15s ease, box-shadow .15s ease;
}}
.record-card:hover {{ transform: translateY(-1px); box-shadow: var(--shadow-lg); }}
.record-card.critical {{ border-left-color: #DC2626; }}
.record-card.high     {{ border-left-color: #EA580C; }}
.record-card.medium   {{ border-left-color: #EAB308; }}
.record-card.low      {{ border-left-color: #6B7280; }}
.record-card.green    {{ border-left-color: #10B981; }}
.record-card .rc-head {{
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px; flex-wrap: wrap;
}}
.record-card .rc-title {{
  font-weight: 700;
  color: var(--text);
  font-size: 0.98rem;
}}
.record-card .rc-meta {{
  color: var(--text-dim);
  font-size: 0.82rem;
  margin-top: 4px;
}}
.record-card .rc-body {{
  color: var(--text);
  margin-top: 8px;
  font-size: 0.9rem;
  line-height: 1.45;
}}
.record-card .rc-foot {{
  margin-top: 10px;
  display: flex; flex-wrap: wrap; gap: 6px;
  color: var(--text-dim);
  font-size: 0.8rem;
}}

/* ── Risk heatmap (5×5) ── */
.risk-heatmap {{
  display: grid;
  grid-template-columns: 36px repeat(5, 1fr);
  gap: 4px;
  margin: 8px 0 14px 0;
}}
.risk-heatmap .hm-cell {{
  position: relative;
  aspect-ratio: 1.4 / 1;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 0.9rem;
  color: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(15, 23, 42, 0.08);
}}
.risk-heatmap .hm-cell .hm-count {{
  position: absolute; top: 3px; right: 5px;
  font-size: 0.62rem; font-weight: 700;
  background: rgba(15, 23, 42, 0.18); color: #fff;
  padding: 1px 5px; border-radius: 8px;
}}
.risk-heatmap .hm-axis {{
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 700;
  color: var(--text-dim);
  text-transform: uppercase;
}}
.risk-heatmap-legend {{
  display: flex; gap: 8px; flex-wrap: wrap;
  font-size: 0.72rem; color: var(--text-dim);
  margin-top: 4px;
}}
.risk-heatmap-legend .leg-chip {{
  display: inline-flex; align-items: center; gap: 4px;
}}
.risk-heatmap-legend .leg-sq {{
  width: 10px; height: 10px; border-radius: 3px; display: inline-block;
}}

/* ── Score chips (risk inherent / residual) ── */
.score-chip {{
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 0.74rem;
  letter-spacing: 0.3px;
  background: var(--surface-alt);
  color: var(--text);
  border: 1px solid var(--border);
}}
.score-chip.crit  {{ background: #FEE2E2; color: #991B1B; border-color: #FCA5A5; }}
.score-chip.hi    {{ background: #FFEDD5; color: #9A3412; border-color: #FED7AA; }}
.score-chip.mid   {{ background: #FEF9C3; color: #854D0E; border-color: #FDE68A; }}
.score-chip.lo    {{ background: #D1FAE5; color: #065F46; border-color: #86EFAC; }}

/* ── Breach banner (incidents) ── */
.breach-banner {{
  margin: 8px 0;
  padding: 8px 12px;
  border-radius: 8px;
  background: #FEF2F2;
  border: 1px solid #FCA5A5;
  color: #7F1D1D;
  font-weight: 600;
  font-size: 0.84rem;
}}
.breach-banner.overdue {{ background: #DC2626; color: #FEF2F2; border-color: #991B1B; }}
.breach-banner.notified {{ background: #ECFDF5; border-color: #86EFAC; color: #065F46; }}
</style>
""", unsafe_allow_html=True)


# ─── Helper functions ────────────────────────────────────────────────

# ── Inline SVG icon system ───────────────────────────────────────────
# Lucide-style outline icons (single-stroke, currentColor). Centralised
# in one helper so we can swap emojis out everywhere without touching
# the call sites individually. icon('name', size=16) returns an inline
# <svg> string ready to embed in markdown blocks.
_ICON_PATHS = {
    # Verdict states (status badges)
    "compliant":     "<polyline points='4 12 9 17 20 6'/>",
    "partial":       "<path d='M12 2L2 21h20z'/><line x1='12' y1='10' x2='12' y2='15'/><circle cx='12' cy='18.5' r='0.6' fill='currentColor'/>",
    "non_compliant": "<circle cx='12' cy='12' r='9'/><line x1='8' y1='8' x2='16' y2='16'/><line x1='16' y1='8' x2='8' y2='16'/>",
    "no_evidence":   "<circle cx='12' cy='12' r='9'/><path d='M9 9.5a3 3 0 1 1 4.5 2.5c-.9.5-1.5 1-1.5 2'/><line x1='12' y1='17' x2='12' y2='17.5'/>",
    "not_applicable": "<circle cx='12' cy='12' r='9'/><line x1='5' y1='12' x2='19' y2='12'/>",
    # Severity (used as small dots)
    "dot":           "<circle cx='12' cy='12' r='5' fill='currentColor'/>",
    # Page-section markers
    "input":         "<rect x='3' y='5' width='18' height='14' rx='2'/><line x1='7' y1='10' x2='17' y2='10'/><line x1='7' y1='14' x2='14' y2='14'/>",
    "assessment":    "<path d='M9 11l3 3 8-8'/><path d='M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11'/>",
    "doc":           "<path d='M5 3h9l5 5v13H5z'/><polyline points='14 3 14 9 19 9'/><line x1='8' y1='13' x2='16' y2='13'/><line x1='8' y1='17' x2='14' y2='17'/>",
    "upload":        "<path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><polyline points='17 8 12 3 7 8'/><line x1='12' y1='3' x2='12' y2='15'/>",
    "example":       "<path d='M9 11h6'/><path d='M9 15h4'/><rect x='4' y='4' width='16' height='16' rx='2'/>",
    "play":          "<polygon points='6 4 20 12 6 20 6 4' fill='currentColor' stroke='none'/>",
    "stat_open":     "<circle cx='12' cy='12' r='9'/><polyline points='12 6 12 12 16 14'/>",
    "stat_doc":      "<path d='M5 3h9l5 5v13H5z'/><polyline points='14 3 14 9 19 9'/>",
    "stat_assess":   "<rect x='3' y='4' width='18' height='16' rx='2'/><polyline points='7 12 11 16 17 9'/>",
    "stat_coverage": "<path d='M3 12a9 9 0 1 0 9-9'/><polyline points='12 3 12 12 19 8'/>",
    "stat_critical": "<path d='M12 2L2 21h20z'/><line x1='12' y1='10' x2='12' y2='14'/><circle cx='12' cy='17.5' r='0.8' fill='currentColor'/>",
    "reset":         "<polyline points='4 8 4 4 8 4'/><path d='M4 12a8 8 0 1 0 2.3-5.7'/>",
    "explain":       "<circle cx='12' cy='12' r='9'/><path d='M9.5 9a2.5 2.5 0 1 1 4 2c-.9.6-1.5 1.2-1.5 2.2'/><line x1='12' y1='17' x2='12' y2='17.5'/>",
    "filter":        "<polygon points='3 4 21 4 14 13 14 19 10 21 10 13 3 4'/>",
    "external":      "<path d='M5 5h6'/><path d='M19 13v6H5V5h6'/><polyline points='14 4 20 4 20 10'/><line x1='10' y1='14' x2='20' y2='4'/>",
}

def icon(name: str, size: int = 16, color: str = "currentColor") -> str:
    """Return an inline <svg> for the given icon name."""
    path = _ICON_PATHS.get(name, _ICON_PATHS["dot"])
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' "
        f"stroke='{color}' stroke-width='1.8' stroke-linecap='round' "
        f"stroke-linejoin='round' style='vertical-align:middle;display:inline-block'>"
        f"{path}</svg>"
    )


def status_badge(status: str) -> str:
    styles = {"compliant":"green","partial":"yellow","non_compliant":"red","no_evidence":"gray","not_applicable":"gray"}
    style = styles.get(status, "gray")
    label = t(f"verdict.{status}") if status in styles else status.replace("_"," ").title()
    return (
        f'<span class="badge badge-{style}">'
        f'<span class="badge-icon">{icon(status, size=12)}</span>'
        f'{label}</span>'
    )

def severity_badge(severity: str) -> str:
    styles = {"critical":"red","high":"orange","medium":"yellow","low":"gray"}
    style = styles.get(severity, "gray")
    label = t(f"severity.{severity}") if severity in styles else severity.upper()
    return (
        f'<span class="badge badge-{style}">'
        f'<span class="badge-icon">{icon("dot", size=10)}</span>'
        f'{label}</span>'
    )

def opstatus_label(op_status: str) -> str:
    return t(f"opstatus.{op_status}") if op_status else ""

def score_bar(score: int, color: str = None) -> str:
    if color is None:
        color = THEMES[get_theme()]["accent"]
    return f'<div class="score-bar"><div class="score-fill" style="width:{score}%;background:{color}"></div></div>'


# ── Visualisation: coverage donut ─────────────────────────────────────
def coverage_donut(score: int, label: str, count: int) -> str:
    """SVG donut showing % coverage. Inline so the dashboard doesn't
    need plotly/altair just for a single ring per framework."""
    s = max(0, min(100, int(score)))
    color = "#10B981" if s >= 80 else "#EA580C" if s >= 40 else "#DC2626"
    radius, stroke = 32, 7
    circ = 2 * 3.14159 * radius
    filled = circ * s / 100
    return f"""
<div class='donut-wrap'>
  <svg viewBox='0 0 80 80' class='donut-svg'>
    <circle cx='40' cy='40' r='{radius}' fill='none'
            stroke='var(--surface-alt)' stroke-width='{stroke}'/>
    <circle cx='40' cy='40' r='{radius}' fill='none'
            stroke='{color}' stroke-width='{stroke}'
            stroke-dasharray='{filled} {circ}'
            stroke-linecap='round'
            transform='rotate(-90 40 40)'/>
    <text x='40' y='44' text-anchor='middle'
          fill='var(--text)' font-family='Space Grotesk' font-weight='700'
          font-size='16'>{s}%</text>
  </svg>
  <div class='donut-meta'>
    <div class='donut-label'>{label}</div>
    <div class='donut-sub'>{count} finding{'s' if count != 1 else ''}</div>
  </div>
</div>
"""


# ── Visualisation: severity stacked bar ───────────────────────────────
def severity_stacked_bar(by_sev: dict) -> str:
    """Single horizontal stacked bar (critical → high → medium → low)
    with each segment proportional to its count. Replaces the old
    grid of four separate KPI cards for severity."""
    order = [("critical", "#DC2626"), ("high", "#EA580C"),
             ("medium", "#EAB308"), ("low", "#6B7280")]
    total = sum(by_sev.get(k, 0) for k, _ in order) or 1
    segs = []
    legend = []
    for k, color in order:
        n = by_sev.get(k, 0)
        pct = (n / total) * 100
        if n > 0:
            segs.append(
                f"<div class='sev-seg' style='width:{pct:.2f}%;background:{color}' "
                f"title='{n} {k}'></div>"
            )
        legend.append(
            f"<div class='sev-leg'>"
            f"<span class='sev-dot' style='background:{color}'></span>"
            f"<span class='sev-leg-label'>{t(f'severity.{k}')}</span>"
            f"<span class='sev-leg-count'>{n}</span>"
            f"</div>"
        )
    return (
        f"<div class='sev-bar'>{''.join(segs)}</div>"
        f"<div class='sev-legend'>{''.join(legend)}</div>"
    )


def api_get(path: str):
    try:
        r = requests.get(f"{API}{path}", timeout=10)
        return r.json() if r.ok else None
    except Exception:
        return None

def api_post(path: str, data: dict):
    try:
        r = requests.post(f"{API}{path}", json=data, timeout=600)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}


# ─── Init session state ──────────────────────────────────────────────

if "language" not in st.session_state:
    st.session_state["language"] = DEFAULT_LANGUAGE
if "theme" not in st.session_state:
    st.session_state["theme"] = DEFAULT_THEME


# Inject CSS for current theme
inject_css()


# ─── Top bar (logo + language + theme) ───────────────────────────────

# Language dropdown was replaced by two flag-buttons (see top_lang block);
# LANG_OPTIONS is no longer referenced. Keep the keys list for any future
# integration that might need to enumerate the available locales.
LANG_KEYS = ("en", "it")

# Build the top-bar as a single HTML block on the left + Streamlit widgets on the right
top_left, top_mid, top_lang, top_theme = st.columns([7, 1.8, 1.3, 0.55])

with top_left:
    # The huge hero logo is gone from operative pages — it lives only
    # in the sidebar brand block now (saved a lot of vertical real
    # estate). What stays here is a slim breadcrumb-style row that
    # tells the user where they are.
    _crumb_labels = {
        "ask_grace":    t("nav.ask_grace"),
        "gap_analysis": t("nav.gap_analysis"),
        "doc_gen":      t("nav.doc_gen"),
        "dashboard":    t("nav.dashboard"),
        "registry":     t("nav.registry"),
        "library":      t("nav.library"),
        "risks":        t("nav.risks"),
        "vendors":      t("nav.vendors"),
        "policies":     t("nav.policies"),
        "incidents":    t("nav.incidents"),
    }
    _crumb_current = _crumb_labels.get(
        st.session_state.get("current_page", "ask_grace"),
        ""
    )
    st.markdown(
        f"""
<div class="grace-crumb">
  <span class="crumb-home">GRACE</span>
  <span class="crumb-sep">/</span>
  <span class="crumb-current">{_crumb_current}</span>
</div>
""",
        unsafe_allow_html=True,
    )

with top_mid:
    st.markdown("")  # spacer

with top_lang:
    # Single dropdown with inline-SVG flag icons. Two important details:
    #
    # 1. The selectbox label is HARDCODED ('Language') — not localised
    #    via t() — because Streamlit derives widget identity from
    #    (type, label, position). Localising the label means the
    #    identity changes the moment the user toggles the language,
    #    which used to make Streamlit drop the widget's state and
    #    require a second click to commit. label_visibility='collapsed'
    #    keeps it invisible anyway.
    #
    # 2. We attach an empty on_change callback so Streamlit treats the
    #    selection as a explicit state mutation and reruns with the
    #    fresh value on the very first click.
    current_lang = st.session_state.get("language", "en")
    wrap_cls = f"grace-lang-wrap lang-selected-{current_lang}"
    st.markdown(f'<div class="{wrap_cls}">', unsafe_allow_html=True)

    def _on_lang_change():
        pass  # presence of the callback is enough to force a clean commit

    st.selectbox(
        "Language",  # constant label — see comment above
        options=["en", "it"],
        format_func=lambda k: "EN" if k == "en" else "IT",
        key="language",
        label_visibility="collapsed",
        on_change=_on_lang_change,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with top_theme:
    is_dark = get_theme() == "dark"
    theme_label = "🌙" if not is_dark else "☀️"
    st.markdown('<div class="grace-theme-wrap">', unsafe_allow_html=True)
    if st.button(theme_label, help=t(f"topbar.theme.{'light' if is_dark else 'dark'}"),
                 key="theme_toggle"):
        st.session_state["theme"] = "light" if is_dark else "dark"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ─── Sidebar ─────────────────────────────────────────────────────────

PAGE_KEYS = ["ask_grace", "gap_analysis", "doc_gen", "dashboard", "registry", "library",
             "risks", "vendors", "policies", "incidents"]
# Inline SVG icons (lucide-style outline) used by the sidebar nav and
# elsewhere. Kept tiny so they ship inside the stylesheet without
# external HTTP. Single-stroke, no fills, currentColor — they inherit
# the active/inactive accent automatically.
def _nav_icon_svg(name: str) -> str:
    paths = {
        "ask_grace":    "<path d='M4 5h16v11H8l-4 4z'/><circle cx='9' cy='10' r='0.9'/><circle cx='12' cy='10' r='0.9'/><circle cx='15' cy='10' r='0.9'/>",
        "gap_analysis": "<circle cx='10' cy='10' r='6'/><line x1='14.5' y1='14.5' x2='19' y2='19'/>",
        "doc_gen":      "<path d='M5 3h9l5 5v13H5z'/><path d='M14 3v5h5'/><line x1='8' y1='13' x2='16' y2='13'/><line x1='8' y1='16' x2='14' y2='16'/>",
        "dashboard":    "<line x1='4' y1='19' x2='4' y2='11'/><line x1='10' y1='19' x2='10' y2='5'/><line x1='16' y1='19' x2='16' y2='14'/><line x1='3' y1='19' x2='21' y2='19'/>",
        "registry":     "<line x1='6' y1='6' x2='20' y2='6'/><line x1='6' y1='12' x2='20' y2='12'/><line x1='6' y1='18' x2='20' y2='18'/><circle cx='3' cy='6' r='1.2'/><circle cx='3' cy='12' r='1.2'/><circle cx='3' cy='18' r='1.2'/>",
        "library":      "<path d='M4 5a2 2 0 0 1 2-2h6v18H6a2 2 0 0 1-2-2z'/><path d='M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6z'/>",
        "risks":        "<polygon points='12 3 22 20 2 20'/><line x1='12' y1='10' x2='12' y2='15'/><circle cx='12' cy='18' r='0.7'/>",
        "vendors":      "<path d='M16 3v2'/><path d='M8 3v2'/><rect x='3' y='6' width='18' height='15' rx='2'/><line x1='3' y1='11' x2='21' y2='11'/>",
        "policies":     "<path d='M6 3h9l4 4v14H6z'/><line x1='9' y1='10' x2='15' y2='10'/><line x1='9' y1='14' x2='15' y2='14'/><line x1='9' y1='18' x2='13' y2='18'/>",
        "incidents":    "<path d='M12 2 L22 22 H2 Z'/><line x1='12' y1='9' x2='12' y2='14'/><circle cx='12' cy='17' r='0.7'/>",
        "reset":        "<polyline points='4 8 4 4 8 4'/><path d='M4 12a8 8 0 1 0 2.3-5.7'/>",
    }
    return paths.get(name, "")


with st.sidebar:
    # Small brand mark + wordmark — the huge hero logo is gone from the
    # topbar; this is now the only place the GRACE identity lives in
    # operative pages.
    # Sidebar brand: big circular symbol + CSS-rendered wordmark.
    # The full LOGO_B64 image is too narrow inside the sidebar (~244 px),
    # which shrunk the embedded tagline below readability. Using the
    # circular symbol at a comfortable size + rendering 'GRACE' and the
    # full tagline as live text keeps both elements crisp at any zoom.
    _sym_html = (
        f'<img class="brand-symbol" src="data:image/png;base64,{SYMBOL_B64}" alt="GRACE"/>'
        if SYMBOL_B64 else
        '<div class="brand-symbol-fallback">🛡</div>'
    )
    st.markdown(
        f'''
<div class="grace-side-brand-compact">
  {_sym_html}
  <div class="brand-name">GRACE</div>
  <div class="brand-tagline">Governance, Risk, Assurance &amp; Compliance Engine</div>
</div>
        ''',
        unsafe_allow_html=True,
    )

    # Streamlit-managed selection mirror (survives the topbar reruns)
    current = st.session_state.get("current_page", PAGE_KEYS[0])
    if current not in PAGE_KEYS:
        current = PAGE_KEYS[0]

    st.markdown('<div class="nav-list">', unsafe_allow_html=True)
    # Streamlit's button(type=…) is the cleanest way to mark active
    # state — 'primary' for the current page, 'secondary' for the rest.
    # The previous icon-on-top-of-button approach didn't actually nest
    # (markdown is a sibling of widgets, not a parent), so the icons
    # were orphan SVGs floating next to buttons whose own style had
    # taken over. Phase 2 will add real icons via a custom component;
    # for now: clean, readable text nav.
    for _k in PAGE_KEYS:
        is_active = (_k == current)
        if st.button(
            t(f"nav.{_k}"),
            key=f"nav_btn_{_k}",
            type=("primary" if is_active else "secondary"),
            use_container_width=True,
        ):
            st.session_state["current_page"] = _k
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    page = current  # downstream pages still read `page`

    # ── System status (elegant component) ─────────────────────────
    try:
        _hr = requests.get(f"{API}/health", timeout=2)
        if _hr.status_code == 200:
            _hstate = _hr.json().get("status", "ok")
        else:
            _hstate = "down"
    except Exception:
        _hstate = "down"
    _status_text = {
        "ok":       t("sidebar.engine_online"),
        "degraded": t("sidebar.engine_degraded"),
        "down":     t("sidebar.engine_offline"),
    }[_hstate]
    st.markdown(
        f'''
<div class="system-status status-{_hstate}">
  <span class="status-dot"></span>
  <div class="status-body">
    <div class="status-title">{_status_text}</div>
    <div class="status-meta">{API}</div>
  </div>
</div>
        ''',
        unsafe_allow_html=True,
    )

    # ── Prototype reset (with explicit confirmation) ──────────────
    st.markdown("---")
    # Expander labels can't host HTML, so we keep a single text label
    # for the disclosure and let the inline icon live next to the
    # primary confirm button below.
    with st.expander(t("sidebar.reset_section"), expanded=False):
        st.caption(t("sidebar.reset_help"))
        if st.button(t("sidebar.reset_confirm"), key="reset_btn",
                     type="primary", use_container_width=True):
            try:
                resp = requests.post(f"{API}/api/v1/admin/reset", timeout=15)
                if resp.ok:
                    # Drop frontend-side caches too, so the UI doesn't
                    # show stale findings/frameworks from before the wipe.
                    st.cache_data.clear()
                    for k in list(st.session_state.keys()):
                        if k.startswith(("ctrls_", "fw_data_")):
                            st.session_state.pop(k, None)
                    st.success(t("sidebar.reset_done"))
                    st.rerun()
                else:
                    st.error(t("sidebar.reset_failed", detail=resp.text[:200]))
            except Exception as e:
                st.error(t("sidebar.reset_failed", detail=str(e)))

# Set the default avatar state for the active page (page-level handlers
# may override via avatar.set_state(...) after specific events).
if "avatar_state" not in st.session_state:
    st.session_state["avatar_state"] = state_for_page(page).value


# ─── Helpers: page hero ──────────────────────────────────────────────

def page_hero(title: str, subtitle: str):
    st.markdown(
        f"""
<div class="page-hero">
  <h1>{title}</h1>
  <p>{subtitle}</p>
</div>
""",
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# PAGE: GAP ANALYSIS
# ════════════════════════════════════════════════════════════════

# ── Avatar message resolution ─────────────────────────────────────
# The bubble next to the avatar shows: (1) an explicit message set by a
# page handler (st.session_state['avatar_message']) — flashes once, then
# reverts to (2) the contextual default from compose_message().

def _resolve_avatar_message() -> str:
    explicit = st.session_state.pop("avatar_message", None)
    if explicit:
        return explicit
    from avatar import compose_message as _cm
    return _cm(page, get_avatar_state(), get_lang())


# ── Layout: [avatar column | main content] ─────────────────────────
# The avatar lives in the left column but is rendered LAST, at the
# bottom of this file. That ordering matters: state changes triggered
# by page handlers — set_avatar_state(…) and avatar_message in
# session_state — must show up in the SAME rerun, which means we have
# to defer the avatar render until after the page body has executed.
_avatar_col, _main_col = st.columns([1.5, 6])

with _main_col:
    # ════════════════════════════════════════════════════════════════
    # PAGE: ASK GRACE (conversational chat with persistent history)
    # ════════════════════════════════════════════════════════════════
    if page == "ask_grace":
        page_hero(t("ask.header"), t("ask.intro"))

        # ── Cached message fetcher (cheap re-render guard) ────────
        @st.cache_data(ttl=10, show_spinner=False)
        def _fetch_chat_messages(sid: str, cache_buster: int = 0):
            data = api_get(f"/api/v1/chat/sessions/{sid}/messages")
            if not isinstance(data, dict):
                return []
            return data.get("messages", [])

        def _bust_message_cache():
            # Bump the buster integer to force the cache_data layer to miss
            # without nuking the wider cache (other sessions stay warm).
            st.session_state["ask_msg_cache_buster"] = (
                st.session_state.get("ask_msg_cache_buster", 0) + 1
            )

        if "ask_msg_cache_buster" not in st.session_state:
            st.session_state["ask_msg_cache_buster"] = 0

        # ── Layout: history sidebar (1) | active chat (3) ─────────
        side_col, chat_col = st.columns([1, 3])

        # ── LEFT: history sidebar ─────────────────────────────────
        with side_col:
            st.markdown(
                f'<div class="section-sub">{t("ask.history_title")}</div>',
                unsafe_allow_html=True,
            )
            if st.button(t("ask.new_chat"), type="primary",
                         use_container_width=True, key="ask_new_chat_btn"):
                r = api_post("/api/v1/chat/sessions", {"title": None})
                if isinstance(r, dict) and r.get("session_id"):
                    st.session_state["ask_session_id"] = r["session_id"]
                    _bust_message_cache()
                    st.rerun()

            sessions_data = api_get("/api/v1/chat/sessions")
            sessions = (sessions_data or {}).get("sessions", [])
            active_sid = st.session_state.get("ask_session_id")

            if not sessions:
                st.caption(t("ask.no_history"))
            else:
                for s in sessions:
                    sid = s["session_id"]
                    label = s.get("title") or t("ask.untitled")
                    if len(label) > 38:
                        label = label[:35] + "…"
                    is_active = (sid == active_sid)
                    btn_label = ("● " if is_active else "") + label
                    if st.button(
                        btn_label,
                        key=f"ask_sess_btn_{sid}",
                        type=("primary" if is_active else "secondary"),
                        use_container_width=True,
                        help=s.get("updated_at", "")[:19].replace("T", " "),
                    ):
                        st.session_state["ask_session_id"] = sid
                        _bust_message_cache()
                        st.rerun()

            # Rename / delete affordances apply ONLY to the active session
            if active_sid:
                st.markdown("---")
                renaming_key = f"ask_rename_open_{active_sid}"
                if st.session_state.get(renaming_key):
                    new_title = st.text_input(
                        t("ask.rename_chat"),
                        value=(next((s.get("title") or "" for s in sessions
                                     if s["session_id"] == active_sid), "")),
                        key=f"ask_rename_input_{active_sid}",
                    )
                    # Streamlit allows columns nested only 1 level deep.
                    # The rename form is already inside the left history
                    # column, so we stack Save/Cancel vertically instead
                    # of side-by-side.
                    if st.button(t("ask.save"),
                                 key=f"ask_rename_save_{active_sid}",
                                 use_container_width=True,
                                 type="primary"):
                        requests.patch(
                            f"{API}/api/v1/chat/sessions/{active_sid}",
                            json={"title": (new_title or "").strip() or None},
                            timeout=10,
                        )
                        st.session_state[renaming_key] = False
                        st.rerun()
                    if st.button(t("ask.cancel"),
                                 key=f"ask_rename_cancel_{active_sid}",
                                 use_container_width=True):
                        st.session_state[renaming_key] = False
                        st.rerun()
                else:
                    if st.button(f"✏ {t('ask.rename_chat')}",
                                 key=f"ask_rename_btn_{active_sid}",
                                 use_container_width=True):
                        st.session_state[renaming_key] = True
                        st.rerun()

                # Two-click delete confirm
                confirm_key = f"ask_delete_confirm_{active_sid}"
                if st.session_state.get(confirm_key):
                    if st.button(f"⚠ {t('ask.delete_confirm')}",
                                 type="primary",
                                 key=f"ask_delete_confirm_btn_{active_sid}",
                                 use_container_width=True):
                        requests.delete(
                            f"{API}/api/v1/chat/sessions/{active_sid}",
                            timeout=10,
                        )
                        st.session_state.pop("ask_session_id", None)
                        st.session_state[confirm_key] = False
                        _bust_message_cache()
                        st.rerun()
                else:
                    if st.button(f"🗑 {t('ask.delete_chat')}",
                                 key=f"ask_delete_btn_{active_sid}",
                                 use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun()

        # ── RIGHT: active conversation ────────────────────────────
        with chat_col:
            active_sid = st.session_state.get("ask_session_id")

            # No session yet → empty state with CTA
            if not active_sid:
                st.markdown(
                    f"""
<div class="chat-empty-state">
  <h3>{t("ask.empty_state_title")}</h3>
  <p>{t("ask.empty_state_body")}</p>
</div>
""",
                    unsafe_allow_html=True,
                )
                if st.button(t("ask.empty_state_cta"), type="primary",
                             key="ask_empty_cta"):
                    r = api_post("/api/v1/chat/sessions", {"title": None})
                    if isinstance(r, dict) and r.get("session_id"):
                        st.session_state["ask_session_id"] = r["session_id"]
                        _bust_message_cache()
                        st.rerun()

            else:
                # Render existing messages as bubbles
                messages = _fetch_chat_messages(
                    active_sid,
                    st.session_state["ask_msg_cache_buster"],
                )
                if not messages:
                    st.caption(t("ask.no_session_yet"))
                for m in messages:
                    role = m.get("role", "assistant")
                    if role == "system":
                        continue
                    role_label = t("ask.you") if role == "user" else t("ask.grace")
                    body_md = m.get("content", "")
                    # Escape minimally — Streamlit markdown handles formatting
                    cites = m.get("citations") or []
                    cites_html = ""
                    if cites and role == "assistant":
                        chip_spans = []
                        for c in cites[:6]:
                            icon = ("📄" if c.get("type") == "document"
                                    else "🔗" if c.get("type") == "control"
                                    else "🏷")
                            chip_spans.append(
                                f"<span class='chat-citation'>{icon} "
                                f"{c.get('label', c.get('id', ''))}</span>"
                            )
                        cites_html = (
                            "<div class='chat-citations'>"
                            + "".join(chip_spans)
                            + "</div>"
                        )
                    st.markdown(
                        f"""
<div class="chat-bubble {role}">
  <div class="chat-role">{role_label}</div>
  <div class="chat-body">{body_md}</div>
  {cites_html}
</div>
""",
                        unsafe_allow_html=True,
                    )

                # ── Sticky input zone ─────────────────────────────
                st.markdown("---")
                with st.expander(t("ask.add_context"), expanded=False):
                    pasted_context = st.text_area(
                        t("ask.paste_label"),
                        key=f"ask_paste_{active_sid}",
                        height=120,
                    )
                    uploaded_files = st.file_uploader(
                        t("ask.attached_files_label"),
                        type=["pdf", "docx", "txt", "csv", "xlsx"],
                        accept_multiple_files=True,
                        key=f"ask_files_{active_sid}",
                    )

                # Framework context (optional)
                fw_data = api_get("/api/v1/frameworks")
                fw_options = {t("ask.no_framework"): None}
                if fw_data:
                    for fw in fw_data.get("frameworks", []):
                        if not fw.get("coming_soon"):
                            fw_options[fw["name"]] = fw["id"]
                selected_fw_name = st.selectbox(
                    t("ask.context_framework_label"),
                    list(fw_options.keys()),
                    key=f"ask_fw_{active_sid}",
                )
                selected_fw_id = fw_options.get(selected_fw_name)

                query_text = st.chat_input(t("ask.placeholder"),
                                           key=f"ask_input_{active_sid}")

                if query_text:
                    # Materialise any attached evidence as documents
                    document_ids: list = []
                    if (pasted_context or "").strip() or uploaded_files:
                        with st.spinner(t("ask.thinking")):
                            if (pasted_context or "").strip():
                                r = api_post("/api/v1/documents/text", {
                                    "title":   "Pasted context",
                                    "content": pasted_context,
                                })
                                if isinstance(r, dict) and r.get("document_id"):
                                    document_ids.append(r["document_id"])
                            for upl in (uploaded_files or []):
                                files = {"file": (upl.name, upl.getvalue(), upl.type)}
                                rr = requests.post(
                                    f"{API}/api/v1/documents/upload",
                                    files=files, data={"owner": "demo"},
                                    timeout=60,
                                )
                                if rr.ok:
                                    j = rr.json()
                                    if j.get("document_id"):
                                        document_ids.append(j["document_id"])

                    set_avatar_state(AvatarState.ANALYZING)
                    with st.spinner(t("ask.thinking")):
                        api_post(
                            f"/api/v1/chat/sessions/{active_sid}/messages",
                            {
                                "query":         query_text.strip(),
                                "document_ids":  document_ids,
                                "framework_id":  selected_fw_id,
                                "language":      get_lang(),
                            },
                        )
                    set_avatar_state(AvatarState.SUCCESS)
                    _bust_message_cache()
                    st.rerun()

        # Avatar state machine — chat is always "ready" once a session is open
        _terminal_ask = (AvatarState.SUCCESS, AvatarState.ERROR, AvatarState.WARNING)
        if get_avatar_state() not in _terminal_ask:
            set_avatar_state(
                AvatarState.READY if st.session_state.get("ask_session_id")
                else AvatarState.GUIDANCE
            )

    # ════════════════════════════════════════════════════════════════
    # PAGE: GAP ANALYSIS WIZARD (structured assessment, persisted)
    # ════════════════════════════════════════════════════════════════
    elif page == "gap_analysis":
        page_hero(t("ga.header"), t("ga.intro"))

        wiz_col, res_col = st.columns([2, 3])

        # ── LEFT: wizard ──────────────────────────────────────────
        with wiz_col:
            # Step 1: upload + paste
            st.markdown(
                f"<div class='wizard-step'><span class='step-num'>1</span>"
                f"{t('ga.wizard_step1')}</div>",
                unsafe_allow_html=True,
            )
            uploaded_files = st.file_uploader(
                t("ga.wizard_step1"),
                type=["pdf", "docx", "txt", "xlsx", "csv"],
                accept_multiple_files=True,
                key="ga_files",
                label_visibility="collapsed",
            )
            pasted_text = st.text_area(
                t("ga.paste_label"),
                key="ga_paste",
                height=120,
                placeholder=t("ga.paste_label"),
                label_visibility="collapsed",
            )

            # Step 2: framework
            st.markdown(
                f"<div class='wizard-step'><span class='step-num'>2</span>"
                f"{t('ga.wizard_step2')}</div>",
                unsafe_allow_html=True,
            )
            fw_data = api_get("/api/v1/frameworks")
            fw_options: dict = {}
            if fw_data:
                for fw in fw_data.get("frameworks", []):
                    if not fw.get("coming_soon"):
                        fw_options[fw["name"]] = fw["id"]
            if not fw_options:
                st.warning(t("lib.cannot_reach"))
                fw_options = {"(none)": None}
            selected_fw_name = st.selectbox(
                t("ga.wizard_step2"),
                list(fw_options.keys()),
                key="ga_framework",
                label_visibility="collapsed",
            )
            selected_fw_id = fw_options.get(selected_fw_name)

            # Step 3: optional scope
            st.markdown(
                f"<div class='wizard-step'><span class='step-num'>3</span>"
                f"{t('ga.wizard_step3')}</div>",
                unsafe_allow_html=True,
            )
            with st.expander(t("ga.scope_label"), expanded=False):
                controls_scope: list = []
                if selected_fw_id:
                    ctrl_data = api_get(
                        f"/api/v1/frameworks/{selected_fw_id}/controls"
                    )
                    if isinstance(ctrl_data, dict):
                        all_ctrls = ctrl_data.get("controls", [])
                        ctrl_labels = [
                            f"{c.get('control_id', c.get('id', '?'))} · "
                            f"{c.get('control_title', c.get('title', ''))[:60]}"
                            for c in all_ctrls
                        ]
                        ctrl_ids_by_label = {
                            lbl: (c.get("control_id") or c.get("id"))
                            for lbl, c in zip(ctrl_labels, all_ctrls)
                        }
                        picked = st.multiselect(
                            t("ga.scope_label"),
                            ctrl_labels,
                            key="ga_scope",
                            label_visibility="collapsed",
                        )
                        controls_scope = [
                            ctrl_ids_by_label[p] for p in picked
                            if ctrl_ids_by_label.get(p)
                        ]
                else:
                    st.caption(t("ga.no_fw_yet"))

            # Step 4: run
            st.markdown(
                f"<div class='wizard-step'><span class='step-num'>4</span>"
                f"{t('ga.wizard_step4')}</div>",
                unsafe_allow_html=True,
            )

            has_docs = bool(uploaded_files) or bool((pasted_text or "").strip())
            if not has_docs:
                st.caption(t("ga.no_docs_yet"))
            elif not selected_fw_id:
                st.caption(t("ga.no_fw_yet"))

            run_clicked = st.button(
                t("ga.run_button"),
                type="primary",
                use_container_width=True,
                disabled=not (has_docs and selected_fw_id),
                key="ga_run_btn",
            )

        # ── RIGHT: results panel ──────────────────────────────────
        with res_col:
            st.markdown(
                f"<div class='section-sub'>{t('ga.results_title')}</div>",
                unsafe_allow_html=True,
            )
            res_container = st.container()

            # Pull most recent result (per session) for sticky render
            last_run_id = st.session_state.get("ga_last_run_id")
            last_result_key = (
                f"gap_result_{last_run_id}" if last_run_id else None
            )

            if run_clicked:
                with res_container:
                    set_avatar_state(AvatarState.ANALYZING)
                    document_ids: list = []
                    with st.spinner(t("ga.running")):
                        if (pasted_text or "").strip():
                            r = api_post("/api/v1/documents/text", {
                                "title":   "Pasted evidence",
                                "content": pasted_text,
                            })
                            if isinstance(r, dict) and r.get("document_id"):
                                document_ids.append(r["document_id"])
                        for upl in (uploaded_files or []):
                            files = {"file": (upl.name, upl.getvalue(), upl.type)}
                            rr = requests.post(
                                f"{API}/api/v1/documents/upload",
                                files=files, data={"owner": "demo"},
                                timeout=60,
                            )
                            if rr.ok:
                                j = rr.json()
                                if j.get("document_id"):
                                    document_ids.append(j["document_id"])

                        if not document_ids:
                            st.error(t("ga.no_docs_yet"))
                            set_avatar_state(AvatarState.ERROR)
                            st.stop()

                        resp = api_post("/api/v1/assessments/run-sync", {
                            "document_ids":   document_ids,
                            "framework":      selected_fw_id,
                            "controls_scope": controls_scope or None,
                            "language":       get_lang(),
                        })

                    if not isinstance(resp, dict) or "error" in resp:
                        set_avatar_state(AvatarState.ERROR)
                        err = resp.get("error", "unknown") if isinstance(resp, dict) else "unknown"
                        st.error(t("ga.assessment_failed", detail=str(err)))
                        st.stop()

                    rid = resp.get("run_id")
                    st.session_state["ga_last_run_id"] = rid
                    st.session_state[f"gap_result_{rid}"] = resp
                    last_run_id = rid
                    last_result_key = f"gap_result_{rid}"

                    # Avatar mood
                    score = (resp.get("result") or {}).get("overall_coverage_score", 0)
                    if score >= 80:
                        set_avatar_state(AvatarState.SUCCESS)
                    elif score < 40:
                        set_avatar_state(AvatarState.WARNING)
                    else:
                        set_avatar_state(AvatarState.ATTENTIVE)

            # Render persisted result if any
            stored = (st.session_state.get(last_result_key)
                      if last_result_key else None)
            with res_container:
                if not stored:
                    st.markdown(
                        f"""
<div class="wizard-placeholder">
  <h3>{t("ga.results_placeholder_title")}</h3>
  <div>{t("ga.results_placeholder_body").replace(chr(10), '<br/>')}</div>
</div>
""",
                        unsafe_allow_html=True,
                    )
                else:
                    result = stored.get("result", {}) or {}
                    overall_score  = result.get("overall_coverage_score", 0)
                    overall_status = result.get("overall_status", "partial")
                    color = ("#16A34A" if overall_score >= 80
                             else "#EA580C" if overall_score >= 40 else "#DC2626")
                    fw_label = selected_fw_name or ""
                    st.markdown(f"""
<div class="page-hero" style="margin-top:0">
  <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:8px">
    <div>
      <div style="font-weight:700;color:var(--primary);font-size:1.05rem">{fw_label}</div>
      <div style="color:var(--text-dim);font-size:0.85rem">{stored.get('document_title','')}</div>
    </div>
    <div style="text-align:right">
      <div style="font-family:var(--font-display);font-size:0.7rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:1.2px">{t('ga.coverage_score')}</div>
      <div style="font-size:2.2rem;font-weight:700;color:{color};line-height:1">{overall_score}%</div>
      {status_badge(overall_status)}
    </div>
  </div>
  {score_bar(overall_score, color)}
  <div style="margin-top:10px;color:var(--text);font-size:0.9rem;line-height:1.5">
    {result.get('executive_summary','Assessment completed.')}
  </div>
</div>
""", unsafe_allow_html=True)

                    for ctrl in result.get("controls", []):
                        sev = ctrl.get("severity", "medium")
                        st.markdown(f"""
<div class="finding-card {sev}">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
    <div>
      <span class="ctrl-id">{ctrl.get('control_id','')}</span>
      <span class="ctrl-title"> · {ctrl.get('control_title','')}</span>
    </div>
    <div style="display:flex;gap:6px">
      {status_badge(ctrl.get('status','no_evidence'))}
      {severity_badge(sev)}
    </div>
  </div>
  <div class="finding-body">{ctrl.get('finding','')}</div>
  <div class="rem">
    <strong>{t('ga.remediation')}:</strong> {ctrl.get('remediation','')}
    <div class="reg-ref" style="margin-top:4px">{ctrl.get('regulatory_reference','')}</div>
  </div>
</div>""", unsafe_allow_html=True)

                    with st.expander(t("ga.evidence_required")):
                        for ctrl in result.get("controls", []):
                            if ctrl.get("evidence_required"):
                                st.markdown(
                                    f"**{ctrl.get('control_id')} — "
                                    f"{ctrl.get('control_title')}**"
                                )
                                for ev in ctrl.get("evidence_required", []):
                                    st.markdown(f"  - {ev}")

                    # Action row — stacked because we're already inside
                    # the right-hand column of the wizard layout (Streamlit
                    # only allows 1 level of column nesting).
                    if st.button(t("ga.open_in_registry"),
                                 use_container_width=True,
                                 key="ga_open_registry"):
                        st.session_state["current_page"] = "registry"
                        st.rerun()
                    if st.button(t("ga.gen_report"),
                                 type="primary",
                                 use_container_width=True,
                                 key="ga_export_pdf"):
                        md_lines = [
                            f"# {t('ga.results_title')}",
                            "",
                            f"**Framework:** {fw_label}",
                            f"**Document(s):** {stored.get('document_title','')}",
                            f"**Coverage:** {overall_score}% · {overall_status}",
                            "",
                            f"## Executive summary",
                            "",
                            result.get("executive_summary", ""),
                            "",
                            "## Findings",
                            "",
                        ]
                        for ctrl in result.get("controls", []):
                            md_lines += [
                                f"### {ctrl.get('control_id','')} — {ctrl.get('control_title','')}",
                                f"- Status: **{ctrl.get('status','')}**  · Severity: **{ctrl.get('severity','')}**",
                                f"- Finding: {ctrl.get('finding','')}",
                                f"- Remediation: {ctrl.get('remediation','')}",
                                "",
                            ]
                        try:
                            exp = requests.post(
                                f"{API}/api/v1/generate/export",
                                json={
                                    "content":  "\n".join(md_lines),
                                    "format":   "pdf",
                                    "filename": t("ga.report_filename"),
                                },
                                timeout=120,
                            )
                            if exp.ok:
                                st.download_button(
                                    t("dg.download_pdf"),
                                    data=exp.content,
                                    file_name=f"{t('ga.report_filename')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    key="ga_dl_pdf",
                                )
                            else:
                                st.error(t("ga.report_failed",
                                           detail=exp.text[:200]))
                        except Exception as e:
                            st.error(t("ga.report_failed", detail=str(e)))

        # Avatar state machine — disabled-Run = GUIDANCE, otherwise READY
        _terminal_ga = (AvatarState.SUCCESS, AvatarState.ERROR, AvatarState.WARNING)
        if get_avatar_state() not in _terminal_ga:
            ready_ga = bool((uploaded_files or
                             (pasted_text or "").strip())
                            and selected_fw_id)
            set_avatar_state(
                AvatarState.READY if ready_ga else AvatarState.GUIDANCE
            )


    # ════════════════════════════════════════════════════════════════
    # PAGE: DOCUMENT GENERATION
    # ════════════════════════════════════════════════════════════════

    elif page == "doc_gen":
        page_hero(t("dg.header"), t("dg.intro"))

        col1, col2 = st.columns([1, 1.5])

        with col1:
            st.markdown(f'<div class="section-sub">{t("dg.configure")}</div>', unsafe_allow_html=True)
            fw_data = api_get("/api/v1/frameworks")
            fw_options = {}
            if fw_data:
                for fw in fw_data.get("frameworks", []):
                    if not fw.get("coming_soon"):
                        fw_options[fw["name"]] = fw["id"]

            doc_types = {"policy": t("dg.type_policy"), "dpa": t("dg.type_dpa"), "soa": t("dg.type_soa")}

            doc_type = st.selectbox(t("dg.doc_type"), list(doc_types.keys()),
                                    format_func=lambda k: doc_types[k])
            doc_type_name = doc_types[doc_type]
            fw_name       = st.selectbox(t("dg.framework"), list(fw_options.keys()))
            fw_id         = fw_options[fw_name]
            organization  = st.text_input(t("dg.organization"), "Brightstar Ltd")

            context = {"organization": organization, "doc_type": doc_type}
            if doc_type == "dpa":
                context["controller"] = organization
                context["processor"]  = st.text_input(t("dg.processor"), "CloudVendor Srl")
                context["purpose"]    = st.text_input(t("dg.purpose"), "HR management system")
            elif doc_type == "policy":
                context["scope"] = st.text_input(t("dg.policy_scope"), "All employees and contractors")
            elif doc_type == "soa":
                context["scope"] = st.text_input(t("dg.isms_scope"), "All IT systems and data processing")

            gen_clicked = st.button(t("dg.generate_button"), type="primary", use_container_width=True)

        # Avatar state machine for Doc Gen: READY when fw_id + doc_type
        # + at least one context field are set; GUIDANCE otherwise.
        _terminal_dg = (AvatarState.SUCCESS, AvatarState.ERROR)
        if get_avatar_state() not in _terminal_dg:
            _ctx_filled = any((v or "").strip() for v in context.values())
            set_avatar_state(
                AvatarState.READY if (fw_id and doc_type and _ctx_filled) else AvatarState.GUIDANCE
            )

        with col2:
            st.markdown(f'<div class="section-sub">{t("dg.generated")}</div>', unsafe_allow_html=True)
            if gen_clicked:
                set_avatar_state(AvatarState.THINKING)
                _lang_dg = get_lang()
                with st.spinner(t("dg.spinner", kind=doc_type_name)):
                    resp = api_post("/api/v1/generate", {
                        "framework_id": fw_id, "doc_type": doc_type,
                        "context": context, "language": _lang_dg,
                    })

                if "error" in resp:
                    set_avatar_state(AvatarState.ERROR)
                    st.session_state["avatar_message"] = (
                        "The generator hit an issue. Try again or simplify the context."
                        if _lang_dg == "en" else
                        "Il generatore ha riscontrato un problema. Riprova o semplifica il contesto."
                    )
                    st.error(resp["error"])
                else:
                    set_avatar_state(AvatarState.SUCCESS)
                    st.session_state["avatar_message"] = (
                        f"Your {doc_type_name} draft is ready. Read it end-to-end and adapt it to your organisation before publishing."
                        if _lang_dg == "en" else
                        f"Il draft del {doc_type_name} è pronto. Rileggilo per intero e adattalo alla tua organizzazione prima di pubblicarlo."
                    )
                    content = resp.get("content","")
                    st.success(t("dg.success"))
                    st.markdown(content)

                    file_base = f"GRACE_{doc_type}_{fw_id}"

                    pdf_bytes = None
                    docx_bytes = None
                    try:
                        pdf_r = requests.post(f"{API}/api/v1/generate/export",
                            json={"content": content, "format": "pdf", "filename": file_base},
                            timeout=60)
                        if pdf_r.ok:
                            pdf_bytes = pdf_r.content
                    except Exception:
                        pass
                    try:
                        docx_r = requests.post(f"{API}/api/v1/generate/export",
                            json={"content": content, "format": "docx", "filename": file_base},
                            timeout=60)
                        if docx_r.ok:
                            docx_bytes = docx_r.content
                    except Exception:
                        pass

                    dl1, dl2, dl3 = st.columns(3)
                    dl1.download_button(t("dg.download_md"),
                        data=content, file_name=f"{file_base}.md", mime="text/markdown",
                        use_container_width=True)
                    if pdf_bytes:
                        dl2.download_button(t("dg.download_pdf"),
                            data=pdf_bytes, file_name=f"{file_base}.pdf",
                            mime="application/pdf", use_container_width=True)
                    else:
                        dl2.button(t("dg.download_pdf"), disabled=True, use_container_width=True)
                    if docx_bytes:
                        dl3.download_button(t("dg.download_docx"),
                            data=docx_bytes, file_name=f"{file_base}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True)
                    else:
                        dl3.button(t("dg.download_docx"), disabled=True, use_container_width=True)
            else:
                st.info(t("dg.placeholder"))


    # ════════════════════════════════════════════════════════════════
    # PAGE: GOVERNANCE DASHBOARD
    # ════════════════════════════════════════════════════════════════

    elif page == "dashboard":
        page_hero(t("db.header"), t("db.intro"))

        kpi = api_get("/api/v1/kpi/summary")
        if not kpi:
            st.warning(t("db.no_data"))
            st.stop()

        # Bento-style KPIs: primary metric (Open Findings) wider, with
        # SVG glyph on the left and click-through to the Registry. The
        # smaller four sit beside it. Trend chip is neutral for now
        # (period snapshots not stored yet — UI ready for it).
        cols = st.columns([2, 1, 1, 1, 1])
        metrics = [
            ("open_findings",  t("db.kpi.open_findings"),  kpi.get("total_open_findings", 0), True,  "stat_open",     None),
            ("documents",      t("db.kpi.documents"),      kpi.get("documents_registered", 0), False, "stat_doc",      None),
            ("assessments",    t("db.kpi.assessments"),    kpi.get("assessment_runs", 0),      False, "stat_assess",   None),
            ("avg_coverage",   t("db.kpi.avg_coverage"),   f"{kpi.get('avg_coverage_score', 0):.0f}%", False, "stat_coverage", None),
            ("critical_open",  t("db.kpi.critical_open"),  kpi.get("by_severity", {}).get("critical", 0), False, "stat_critical", "critical"),
        ]
        for i, (kpi_key, label, value, primary, ico, sev_filter) in enumerate(metrics):
            primary_cls = " kpi-primary" if primary else ""
            cols[i].markdown(f"""
    <div class="kpi-card kpi-clickable{primary_cls}" data-kpi="{kpi_key}">
      <div class="kpi-head">
        <span class="kpi-glyph">{icon(ico, size=18)}</span>
        <span class="kpi-label">{label}</span>
      </div>
      <div class="kpi-row">
        <div class="kpi-value">{value}</div>
        <span class="kpi-trend neutral">— %</span>
      </div>
      <div class="kpi-link">{t("db.kpi.view")} {icon("external", size=12)}</div>
    </div>""", unsafe_allow_html=True)
            # Tiny "Open" button under each card — Streamlit-native, fires
            # the navigation + filter pre-fill.
            if cols[i].button(t("db.kpi.open"), key=f"kpi_open_{kpi_key}",
                              use_container_width=True):
                # Pre-fill the Registry filters based on which KPI was clicked
                if kpi_key == "critical_open":
                    st.session_state["registry_filter_severity"] = "critical"
                # All KPIs route to Registry by default — landing there gives
                # the user a clear next action.
                st.session_state["current_page"] = "registry"
                st.rerun()

        st.markdown("&nbsp;", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1.4])

        with col1:
            st.markdown(f'<div class="section-sub">{t("db.status_distribution")}</div>', unsafe_allow_html=True)
            by_status = kpi.get("by_status",{})
            if by_status:
                for status, count in by_status.items():
                    if status in ("compliant","partial","non_compliant","no_evidence","not_applicable"):
                        st.markdown(
                            f"<div class='recent-row'>"
                            f"<span class='doc-name'>{status_badge(status)}</span>"
                            f"<span class='meta'>{count}</span></div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"<div class='recent-row'><span class='doc-name'>{status}</span>"
                            f"<span class='meta'>{count}</span></div>",
                            unsafe_allow_html=True,
                        )
            else:
                st.info(t("db.no_findings"))

        with col2:
            st.markdown(f'<div class="section-sub">{t("db.coverage_framework")}</div>', unsafe_allow_html=True)
            by_fw = kpi.get("by_framework",{})
            if by_fw:
                # CSS grid (instead of st.columns) so we don't hit
                # Streamlit's 'columns only one level deep' limit —
                # the dashboard is already nested inside _main_col and
                # an outer st.columns([1, 1.4]), which puts us at the
                # edge of the allowed nesting.
                _donut_html = "".join(
                    coverage_donut(
                        data.get("avg_score", 0) or 0,
                        fw,
                        data.get("count", 0),
                    )
                    for fw, data in by_fw.items()
                )
                st.markdown(
                    f'<div class="donut-grid">{_donut_html}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info(t("db.no_framework_data"))

        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.markdown(f'<div class="section-sub">{t("db.severity_breakdown")}</div>', unsafe_allow_html=True)
        by_sev = kpi.get("by_severity",{})
        if by_sev:
            st.markdown(severity_stacked_bar(by_sev), unsafe_allow_html=True)
        else:
            st.info(t("db.no_severity_data"))

        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.markdown(f'<div class="section-sub">{t("db.recent_docs")}</div>', unsafe_allow_html=True)
        runs = api_get("/api/v1/assessments")
        completed_runs = [r for r in (runs or {}).get("runs", []) if r.get("status") == "completed"][:10]
        if completed_runs:
            for r in completed_runs:
                ts = r.get("started_at","")
                ts_short = ts[:19].replace("T", " ") if ts else ""
                doc = r.get("document_title") or t("db.no_document")
                fw = r.get("framework","")
                st.markdown(
                    f"<div class='recent-row'>"
                    f"<span style='color:#16A34A'>✅</span>"
                    f"<span class='doc-name'>{doc}</span>"
                    f"<span class='fw-tag'>{fw}</span>"
                    f"<span class='meta'>{ts_short} UTC</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info(t("db.no_assessments"))


    # ════════════════════════════════════════════════════════════════
    # PAGE: FINDING REGISTRY
    # ════════════════════════════════════════════════════════════════

    elif page == "registry":
        page_hero(t("reg.header"), t("reg.intro"))

        OP_STATUSES = ["new","acknowledged","in_progress","resolved","accepted_risk","closed","dismissed"]
        VERDICTS = ["non_compliant","partial","compliant","no_evidence","not_applicable"]
        # All 10 active frameworks — kept in lock-step with
        # backend.modules.grc_engine.list_supported_frameworks(). Adding
        # a new framework here without activating it in the engine would
        # surface a filter for which the API has no data.
        FRAMEWORKS = [
            "ISO27001:2022","GDPR","SOC2","NIS2","NISTCSF2.0",
            "PCI-DSS4.0.1","HIPAA","DORA","ISO42001","EUAIACT",
        ]
        ALL = "__ALL__"

        # Pre-fill from dashboard KPI click-through, if any.
        _preset_severity = st.session_state.pop("registry_filter_severity", None)
        _preset_verdict  = st.session_state.pop("registry_filter_verdict", None)
        _preset_op       = st.session_state.pop("registry_filter_op", None)

        col1, col2, col3 = st.columns(3)
        fw_filter = col1.selectbox(
            t("reg.framework"), [ALL] + FRAMEWORKS,
            format_func=lambda v: t("all") if v == ALL else v,
            key="reg_fw_filter",
        )
        verdict_filter = col2.selectbox(
            t("reg.verdict"), [ALL] + VERDICTS,
            format_func=lambda v: t("all") if v == ALL else t(f"verdict.{v}"),
            index=(VERDICTS.index(_preset_verdict) + 1) if _preset_verdict in VERDICTS else 0,
            key="reg_verdict_filter",
        )
        op_status_filter = col3.selectbox(
            t("reg.operational_status"), [ALL] + OP_STATUSES,
            format_func=lambda v: t("all") if v == ALL else t(f"opstatus.{v}"),
            index=(OP_STATUSES.index(_preset_op) + 1) if _preset_op in OP_STATUSES else 0,
            key="reg_op_filter",
        )

        query = f"/api/v1/findings?limit=100&language={get_lang()}"
        if fw_filter != ALL:
            query += f"&framework={fw_filter}"
        if verdict_filter != ALL:
            query += f"&status={verdict_filter}"
        if op_status_filter != ALL:
            query += f"&operational_status={op_status_filter}"

        findings = api_get(query)

        if not findings or not findings.get("findings"):
            st.info(t("reg.no_findings"))
        else:
            items = findings["findings"]

            # Group by document
            from collections import OrderedDict
            groups = OrderedDict()
            for f in items:
                key = f.get("document_title") or t("reg.unknown_doc")
                groups.setdefault(key, []).append(f)

            st.markdown(t("reg.findings_count", n=len(items), d=len(groups)))

            LANG_FLAG = {"en": "🇬🇧 EN", "it": "🇮🇹 IT"}

            for doc_title, doc_findings in groups.items():
                # Document-level meta: latest framework, latest created_at, count
                latest = max(doc_findings, key=lambda x: x.get("created_at",""))
                doc_framework = latest.get("framework","")
                doc_date = (latest.get("created_at","") or "")[:10]
                summary = t("reg.doc_summary", n=len(doc_findings), framework=doc_framework, date=doc_date)
                # Worst severity for the document (drives chip)
                sev_rank = {"critical":4,"high":3,"medium":2,"low":1}
                worst_sev = max((f.get("severity","medium") for f in doc_findings),
                                key=lambda s: sev_rank.get(s, 0))

                with st.expander(f"📄  {doc_title}  ·  {summary}  ·  {t(f'severity.{worst_sev}')}"):
                    for f in doc_findings:
                        severity = f.get("severity","medium")
                        # cross_framework_count comes from the cache only
                        # (cheap COUNT), so the badge stays 0 until the
                        # user expands the impact panel — that's where
                        # the on-demand Claude call happens.
                        xfw_n = int(f.get("cross_framework_count") or 0)
                        xfw_badge_html = (
                            f"<span class='xframework-badge'>"
                            f"{t('reg.xframework_badge', n=xfw_n)}</span>"
                            if xfw_n > 0 else ""
                        )
                        # The backend lazily translates the user-facing fields
                        # to the requested UI language and caches the result,
                        # so no "Generated in IT" chip is needed any more.
                        st.markdown(
                            f"<div class='finding-card {severity}'>"
                            f"<div style='display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap'>"
                            f"<div><span class='ctrl-id'>{f.get('control_id','')}</span>"
                            f"<span class='ctrl-title'> · {f.get('control_title','')}</span></div>"
                            f"<div style='display:flex;gap:6px;align-items:center;flex-wrap:wrap'>"
                            f"{status_badge(f.get('compliance_status','no_evidence'))}"
                            f"{severity_badge(severity)}"
                            f"{xfw_badge_html}"
                            f"</div></div>"
                            f"<div class='finding-body'>{f.get('description','')}</div>"
                            f"<div class='rem'><strong>{t('reg.remediation')}:</strong> {f.get('recommended_action','')}"
                            f"<div class='reg-ref' style='margin-top:4px'>{f.get('regulatory_reference','')}</div>"
                            f"</div></div>",
                            unsafe_allow_html=True,
                        )

                        # ── Cross-framework impact (lazy, cached) ──
                        # Streamlit doesn't allow nested expanders, so we
                        # mimic the collapse/expand behaviour with a
                        # session_state toggle button. The heavy Claude
                        # call only fires once: subsequent reruns (theme
                        # toggle, status update) read from the cache.
                        _xfw_cache_key   = f"xfw_{f['finding_id']}"
                        _xfw_toggle_key  = f"xfw_open_{f['finding_id']}"
                        _xfw_btn_key     = f"xfw_btn_{f['finding_id']}"
                        is_open = st.session_state.get(_xfw_toggle_key, False)
                        if st.button(
                            t("reg.xframework_hide" if is_open else "reg.xframework_show"),
                            key=_xfw_btn_key,
                            use_container_width=False,
                        ):
                            st.session_state[_xfw_toggle_key] = not is_open
                            st.rerun()
                        if st.session_state.get(_xfw_toggle_key, False):
                            if _xfw_cache_key not in st.session_state:
                                with st.spinner(t("reg.xframework_loading")):
                                    st.session_state[_xfw_cache_key] = api_get(
                                        f"/api/v1/findings/{f['finding_id']}"
                                        f"/cross-framework-impact"
                                    )
                            xfw_resp = st.session_state.get(_xfw_cache_key)
                            if xfw_resp is None:
                                st.warning(t("reg.xframework_failed"))
                            else:
                                xfw_list = xfw_resp.get("mappings", []) or []
                                if not xfw_list:
                                    st.info(t("reg.xframework_empty"))
                                else:
                                    for m in xfw_list:
                                        conf = (m.get("confidence") or "low").lower()
                                        if conf not in ("high", "medium", "low"):
                                            conf = "low"
                                        st.markdown(
                                            f"<div class='xfw-row'>"
                                            f"<div class='xfw-head'>"
                                            f"<span class='xfw-fw'>{m.get('target_framework','')}</span>"
                                            f"<span class='xfw-ctrl'>{m.get('target_control_id','')}</span>"
                                            f"<span class='xfw-title'>· {m.get('target_control_title','')}</span>"
                                            f"<span class='xfw-conf {conf}'>"
                                            f"{t('reg.xframework_confidence')}: {t(f'xfw.{conf}')}"
                                            f"</span>"
                                            f"</div>"
                                            f"<div class='xfw-rat'>{m.get('rationale','')}</div>"
                                            f"</div>",
                                            unsafe_allow_html=True,
                                        )

                        op_st = f.get('operational_status','')
                        st.markdown('<div class="finding-update">', unsafe_allow_html=True)
                        upd_cols = st.columns([3, 1])
                        new_status = upd_cols[0].selectbox(
                            f"{t('reg.update_op_status')} — {f.get('control_id','')}",
                            OP_STATUSES,
                            index=OP_STATUSES.index(op_st) if op_st in OP_STATUSES else 0,
                            format_func=lambda v: t(f"opstatus.{v}"),
                            key=f"status_{f['finding_id']}",
                            label_visibility="collapsed",
                        )
                        clicked_update = upd_cols[1].button(
                            t("reg.update_button"),
                            key=f"upd_{f['finding_id']}",
                            use_container_width=True,
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                        if clicked_update:
                            resp = requests.patch(
                                f"{API}/api/v1/findings/{f['finding_id']}/status",
                                json={"operational_status": new_status}
                            )
                            if resp.ok:
                                st.success(t("reg.status_updated"))
                                st.rerun()


    # ════════════════════════════════════════════════════════════════
    # PAGE: FRAMEWORK LIBRARY
    # ════════════════════════════════════════════════════════════════

    elif page == "library":
        page_hero(t("lib.header"), t("lib.intro"))

        # Frameworks list + per-framework controls are cached for 5
        # minutes. Without this, each rerun (a click, a theme switch,
        # an expander toggle) re-fired 1 + N API calls — which made
        # the page feel half-rendered until 3-4 retries warmed it up.
        @st.cache_data(ttl=300, show_spinner=False)
        def _cached_frameworks_list():
            return api_get("/api/v1/frameworks")

        @st.cache_data(ttl=300, show_spinner=False)
        def _cached_framework_controls(framework_id: str):
            return api_get(f"/api/v1/frameworks/{framework_id}/controls")

        fw_data = _cached_frameworks_list()
        if not fw_data:
            st.warning(t("lib.cannot_reach"))
            if st.button("↻ Retry", key="lib_retry"):
                _cached_frameworks_list.clear()
                st.rerun()
        else:
            for fw in fw_data.get("frameworks", []):
                coming_soon = fw.get("coming_soon", False)
                status_tag = t("lib.coming_phase3") if coming_soon else t("lib.active")
                with st.expander(t("lib.framework_entry", name=fw['name'],
                                    controls=fw['controls'], tag=status_tag)):
                    col1, col2 = st.columns([2, 1])
                    col1.markdown(
                        f"**{t('lib.category')}:** {fw['category']}  \n"
                        f"**{t('lib.priority')}:** {fw['priority']}"
                    )
                    col2.markdown(f"**{t('lib.controls')}:** {fw['controls']}")

                    if not coming_soon:
                        ctrl_data = _cached_framework_controls(fw['id'])
                        if ctrl_data:
                            controls = ctrl_data.get("controls", [])
                            st.markdown(t("lib.controls_loaded", n=len(controls)))
                            for ctrl in controls[:5]:
                                st.markdown(f"- **{ctrl['control_id']}** · {ctrl['title']}")
                            if len(controls) > 5:
                                st.caption(t("lib.more_controls", n=len(controls) - 5))

                            st.markdown("---")
                            ctrl_ids = [c["control_id"] for c in controls]
                            selected_ctrl = st.selectbox(
                                t("lib.explain_ctrl"), ctrl_ids,
                                key=f"ctrl_{fw['id']}",
                            )
                            if st.button(t("lib.explain_button"), key=f"exp_{fw['id']}"):
                                with st.spinner(t("lib.explain_spinner")):
                                    # The default api_get times out at 10 s,
                                    # which used to be too short for the
                                    # streaming Sonnet call and the UI just
                                    # stopped silently. Use a dedicated call
                                    # with a 60 s timeout and URL-encode the
                                    # framework_id so colons (e.g. ISO27001:
                                    # 2022) are preserved cleanly.
                                    import urllib.parse as _up
                                    _fw_enc = _up.quote(fw['id'], safe='')
                                    _ctrl_enc = _up.quote(selected_ctrl, safe='')
                                    try:
                                        _r = requests.get(
                                            f"{API}/api/v1/frameworks/{_fw_enc}/controls/"
                                            f"{_ctrl_enc}/explain",
                                            params={"language": get_lang()},
                                            timeout=60,
                                        )
                                        if _r.ok:
                                            _result = _r.json()
                                            _expl = _result.get("explanation", "")
                                            if _expl:
                                                st.markdown(_expl)
                                            else:
                                                st.warning("Empty explanation returned.")
                                        else:
                                            st.error(f"API error {_r.status_code}: {_r.text[:200]}")
                                    except Exception as _e:
                                        st.error(f"Request failed: {_e}")


    # ════════════════════════════════════════════════════════════════
    # PAGE: RISK MANAGEMENT (Phase 1)
    # ════════════════════════════════════════════════════════════════

    elif page == "risks":
        page_hero(t("risks.header"), t("risks.intro"))

        RISK_CATEGORIES = ["operational", "cyber", "compliance", "financial",
                            "strategic", "reputational"]
        RISK_TREATMENTS = ["avoid", "transfer", "mitigate", "accept"]
        RISK_STATUSES = ["open", "under_treatment", "accepted", "closed"]
        ALL = "__ALL__"

        # ── Filter row ──────────────────────────────────────────
        fcol1, fcol2, fcol3 = st.columns(3)
        f_status = fcol1.selectbox(
            t("risks.filter.status"), [ALL] + RISK_STATUSES,
            format_func=lambda v: t("all") if v == ALL else t(f"risks.status.{v}"),
            key="risks_filter_status",
        )
        f_category = fcol2.selectbox(
            t("risks.filter.category"), [ALL] + RISK_CATEGORIES,
            format_func=lambda v: t("all") if v == ALL else t(f"risks.cat.{v}"),
            key="risks_filter_category",
        )
        f_owner = fcol3.text_input(t("risks.filter.owner"), value="",
                                    key="risks_filter_owner")

        query = "/api/v1/risks?"
        if f_status != ALL:
            query += f"status={f_status}&"
        if f_category != ALL:
            query += f"category={f_category}&"
        if f_owner.strip():
            query += f"owner={f_owner.strip()}&"
        resp = api_get(query.rstrip("&?")) or {"risks": []}
        risks = resp.get("risks", []) or []

        # ── KPI strip ───────────────────────────────────────────
        kc1, kc2, kc3, kc4 = st.columns(4)
        total = len(risks)
        critical = sum(1 for r in risks if (r.get("residual_score") or 0) >= 15)
        open_n = sum(1 for r in risks if r.get("status") == "open")
        avg_res = round(
            sum((r.get("residual_score") or 0) for r in risks) / total, 1
        ) if total else 0
        kc1.metric(t("risks.kpi.total"), total)
        kc2.metric(t("risks.kpi.critical"), critical)
        kc3.metric(t("risks.kpi.avg_residual"), avg_res)
        kc4.metric(t("risks.kpi.open"), open_n)

        # ── 5×5 Heatmap ─────────────────────────────────────────
        def _heatmap_color(score: int) -> str:
            # Green (low) → amber (mid) → red (high). Returns hex.
            palette = [
                "#D1FAE5",  # 1-3   very low
                "#A7F3D0",  # 4-6   low
                "#FEF3C7",  # 7-9   medium-low
                "#FDE68A",  # 10-12 medium
                "#FCA5A5",  # 13-15 medium-high
                "#F87171",  # 16-19 high
                "#DC2626",  # 20-25 critical
            ]
            if score <= 3: return palette[0]
            if score <= 6: return palette[1]
            if score <= 9: return palette[2]
            if score <= 12: return palette[3]
            if score <= 15: return palette[4]
            if score <= 19: return palette[5]
            return palette[6]

        # Build grid: rows are likelihood 5..1 (top to bottom), cols are
        # impact 1..5. Counts and max-score per cell drive the colour.
        cells = {(L, I): [] for L in range(1, 6) for I in range(1, 6)}
        for r in risks:
            L = int(r.get("likelihood") or 0)
            I = int(r.get("impact") or 0)
            if 1 <= L <= 5 and 1 <= I <= 5:
                cells[(L, I)].append(r)

        st.markdown(f"#### {t('risks.heatmap_title')}")
        # Grid: top header row (axis label + I1..I5), then 5 rows
        # likelihood 5..1, each starting with the likelihood label.
        html_parts = ['<div class="risk-heatmap">']
        # Top-left empty + impact column headers
        html_parts.append('<div class="hm-axis"></div>')
        for I in range(1, 6):
            html_parts.append(f'<div class="hm-axis">I={I}</div>')
        # Rows: likelihood 5 down to 1
        for L in range(5, 0, -1):
            html_parts.append(f'<div class="hm-axis">L={L}</div>')
            for I in range(1, 6):
                cell_risks = cells.get((L, I), [])
                score = L * I
                color = _heatmap_color(score)
                count = len(cell_risks)
                count_html = f'<span class="hm-count">{count}</span>' if count else ''
                html_parts.append(
                    f'<div class="hm-cell" style="background:{color}" '
                    f'title="L={L} × I={I} = {score} · {count} risk(s)">'
                    f'{score}{count_html}</div>'
                )
        html_parts.append('</div>')
        st.markdown("\n".join(html_parts), unsafe_allow_html=True)
        st.caption(
            f"{t('risks.heatmap_yaxis')} · {t('risks.heatmap_xaxis')}"
        )

        st.markdown("---")

        # ── New Risk form ───────────────────────────────────────
        show_new_key = "risks_show_new"
        if st.button(t("risks.new_button"), key="risks_new_btn"):
            st.session_state[show_new_key] = not st.session_state.get(show_new_key, False)

        if st.session_state.get(show_new_key, False):
            with st.form("risks_new_form", clear_on_submit=True):
                st.markdown(f"**{t('risks.new_form_title')}**")
                nc1, nc2 = st.columns(2)
                title = nc1.text_input(t("risks.field.title"))
                owner = nc2.text_input(t("risks.field.owner"))
                description = st.text_area(t("risks.field.description"))
                nc3, nc4, nc5 = st.columns(3)
                category = nc3.selectbox(
                    t("risks.field.category"), RISK_CATEGORIES,
                    format_func=lambda v: t(f"risks.cat.{v}"),
                )
                treatment = nc4.selectbox(
                    t("risks.field.treatment"), RISK_TREATMENTS,
                    format_func=lambda v: t(f"risks.treat.{v}"),
                )
                status = nc5.selectbox(
                    t("risks.field.status"), RISK_STATUSES,
                    format_func=lambda v: t(f"risks.status.{v}"),
                )
                nc6, nc7, nc8 = st.columns(3)
                likelihood = nc6.slider(t("risks.field.likelihood"), 1, 5, 3)
                impact = nc7.slider(t("risks.field.impact"), 1, 5, 3)
                residual = nc8.slider(t("risks.field.residual"), 0, 25,
                                       likelihood * impact)
                treatment_notes = st.text_area(t("risks.field.treatment_notes"))
                linked_str = st.text_input(t("risks.field.linked_controls"))
                submitted = st.form_submit_button(t("risks.create_button"))
                if submitted:
                    if not title.strip():
                        st.error(t("risks.field.title"))
                    else:
                        linked = [s.strip() for s in linked_str.split(",") if s.strip()]
                        payload = {
                            "title": title.strip(),
                            "description": description,
                            "category": category,
                            "likelihood": int(likelihood),
                            "impact": int(impact),
                            "residual_score": int(residual),
                            "treatment_plan": treatment,
                            "treatment_notes": treatment_notes,
                            "owner": owner,
                            "status": status,
                            "linked_controls": linked,
                        }
                        out = api_post("/api/v1/risks", payload)
                        if out and not out.get("error"):
                            st.success(t("risks.created_ok"))
                            st.session_state[show_new_key] = False
                            st.rerun()
                        else:
                            st.error(out.get("error", "Failed to create risk"))

        # ── Risk cards ──────────────────────────────────────────
        if not risks:
            st.info(t("risks.no_risks"))
        else:
            for r in risks:
                rid = r["risk_id"]
                residual = int(r.get("residual_score") or 0)
                inherent = int(r.get("inherent_score") or 0)
                sev_band = ("critical" if residual >= 20 else
                            "high" if residual >= 15 else
                            "medium" if residual >= 8 else "low")
                chip_class = ("crit" if residual >= 15 else
                              "hi" if residual >= 8 else
                              "mid" if residual >= 4 else "lo")
                status_v = r.get("status", "open")
                cat_v = r.get("category", "operational")
                treat_v = r.get("treatment_plan", "mitigate")
                owner_v = r.get("owner") or "—"
                linked_v = r.get("linked_controls") or []
                linked_html = ""
                if linked_v:
                    chips = "".join(
                        f"<span class='score-chip'>{c}</span> " for c in linked_v
                    )
                    linked_html = f"<div class='rc-foot'>{chips}</div>"

                st.markdown(
                    f"<div class='record-card {sev_band}'>"
                    f"<div class='rc-head'>"
                    f"<div class='rc-title'>{r.get('title','')}</div>"
                    f"<div style='display:flex;gap:6px;align-items:center;flex-wrap:wrap'>"
                    f"<span class='score-chip {chip_class}'>{t('risks.score_residual')}: {residual}</span>"
                    f"<span class='score-chip'>{t('risks.score_inherent')}: {inherent}</span>"
                    f"<span class='badge badge-gray'>{t(f'risks.cat.{cat_v}')}</span>"
                    f"<span class='badge badge-yellow'>{t(f'risks.treat.{treat_v}')}</span>"
                    f"<span class='badge badge-green'>{t(f'risks.status.{status_v}')}</span>"
                    f"</div></div>"
                    f"<div class='rc-meta'>👤 {owner_v} · L={r.get('likelihood','?')} × I={r.get('impact','?')}</div>"
                    f"<div class='rc-body'>{r.get('description','') or ''}</div>"
                    f"{linked_html}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                edit_key = f"risks_edit_{rid}"
                btn_cols = st.columns([1, 1, 6])
                if btn_cols[0].button(t("risks.edit_button"), key=f"risk_edit_btn_{rid}"):
                    st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                if btn_cols[1].button(t("risks.delete_button"), key=f"risk_del_btn_{rid}"):
                    try:
                        dr = requests.delete(f"{API}/api/v1/risks/{rid}", timeout=10)
                        if dr.ok:
                            st.success(t("risks.delete_confirm"))
                            st.rerun()
                    except Exception as _e:
                        st.error(str(_e))

                if st.session_state.get(edit_key, False):
                    with st.form(f"risk_edit_form_{rid}", clear_on_submit=False):
                        ec1, ec2 = st.columns(2)
                        e_title = ec1.text_input(t("risks.field.title"), value=r.get("title", ""))
                        e_owner = ec2.text_input(t("risks.field.owner"), value=r.get("owner", "") or "")
                        e_desc = st.text_area(t("risks.field.description"), value=r.get("description", "") or "")
                        ec3, ec4, ec5 = st.columns(3)
                        e_cat = ec3.selectbox(
                            t("risks.field.category"), RISK_CATEGORIES,
                            index=RISK_CATEGORIES.index(cat_v) if cat_v in RISK_CATEGORIES else 0,
                            format_func=lambda v: t(f"risks.cat.{v}"),
                            key=f"e_cat_{rid}",
                        )
                        e_treat = ec4.selectbox(
                            t("risks.field.treatment"), RISK_TREATMENTS,
                            index=RISK_TREATMENTS.index(treat_v) if treat_v in RISK_TREATMENTS else 2,
                            format_func=lambda v: t(f"risks.treat.{v}"),
                            key=f"e_treat_{rid}",
                        )
                        e_status = ec5.selectbox(
                            t("risks.field.status"), RISK_STATUSES,
                            index=RISK_STATUSES.index(status_v) if status_v in RISK_STATUSES else 0,
                            format_func=lambda v: t(f"risks.status.{v}"),
                            key=f"e_status_{rid}",
                        )
                        ec6, ec7, ec8 = st.columns(3)
                        e_like = ec6.slider(t("risks.field.likelihood"), 1, 5,
                                             int(r.get("likelihood") or 3),
                                             key=f"e_like_{rid}")
                        e_imp = ec7.slider(t("risks.field.impact"), 1, 5,
                                            int(r.get("impact") or 3),
                                            key=f"e_imp_{rid}")
                        e_res = ec8.slider(t("risks.field.residual"), 0, 25,
                                            int(r.get("residual_score") or 0),
                                            key=f"e_res_{rid}")
                        e_treat_notes = st.text_area(
                            t("risks.field.treatment_notes"),
                            value=r.get("treatment_notes", "") or "",
                            key=f"e_tnotes_{rid}",
                        )
                        e_linked = st.text_input(
                            t("risks.field.linked_controls"),
                            value=", ".join(r.get("linked_controls") or []),
                            key=f"e_linked_{rid}",
                        )
                        save_col, cancel_col = st.columns(2)
                        save_clicked = save_col.form_submit_button(t("risks.save_button"))
                        cancel_clicked = cancel_col.form_submit_button(t("risks.cancel_button"))
                        if cancel_clicked:
                            st.session_state[edit_key] = False
                            st.rerun()
                        if save_clicked:
                            linked = [s.strip() for s in e_linked.split(",") if s.strip()]
                            payload = {
                                "title": e_title.strip(),
                                "description": e_desc,
                                "category": e_cat,
                                "likelihood": int(e_like),
                                "impact": int(e_imp),
                                "residual_score": int(e_res),
                                "treatment_plan": e_treat,
                                "treatment_notes": e_treat_notes,
                                "owner": e_owner,
                                "status": e_status,
                                "linked_controls": linked,
                            }
                            try:
                                pr = requests.patch(
                                    f"{API}/api/v1/risks/{rid}",
                                    json=payload, timeout=10
                                )
                                if pr.ok:
                                    st.success(t("risks.updated_ok"))
                                    st.session_state[edit_key] = False
                                    st.rerun()
                                else:
                                    st.error(f"{pr.status_code}: {pr.text[:200]}")
                            except Exception as _e:
                                st.error(str(_e))


    # ════════════════════════════════════════════════════════════════
    # PAGE: VENDOR RISK (Phase 1)
    # ════════════════════════════════════════════════════════════════

    elif page == "vendors":
        page_hero(t("vendors.header"), t("vendors.intro"))

        VENDOR_CATEGORIES = ["cloud_infra", "saas", "payment", "data_processor",
                              "professional_services", "other"]
        VENDOR_STATUSES = ["active", "under_review", "terminated"]
        VENDOR_TIERS = ["low", "medium", "high", "critical"]
        ALL = "__ALL__"

        # ── Filter row ──────────────────────────────────────────
        vfc1, vfc2, vfc3 = st.columns(3)
        f_tier = vfc1.selectbox(
            t("vendors.filter.tier"), [ALL] + VENDOR_TIERS,
            format_func=lambda v: t("all") if v == ALL else t(f"vendors.tier.{v}"),
            key="vendors_filter_tier",
        )
        f_vcat = vfc2.selectbox(
            t("vendors.filter.category"), [ALL] + VENDOR_CATEGORIES,
            format_func=lambda v: t("all") if v == ALL else t(f"vendors.cat.{v}"),
            key="vendors_filter_category",
        )
        f_vstatus = vfc3.selectbox(
            t("vendors.filter.status"), [ALL] + VENDOR_STATUSES,
            format_func=lambda v: t("all") if v == ALL else t(f"vendors.status.{v}"),
            key="vendors_filter_status",
        )

        vquery = "/api/v1/vendors?"
        if f_tier != ALL:
            vquery += f"risk_tier={f_tier}&"
        if f_vcat != ALL:
            vquery += f"category={f_vcat}&"
        if f_vstatus != ALL:
            vquery += f"status={f_vstatus}&"
        vresp = api_get(vquery.rstrip("&?")) or {"vendors": []}
        vendors = vresp.get("vendors", []) or []

        # ── KPIs ────────────────────────────────────────────────
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td
        def _parse_iso(s):
            try:
                return _dt.fromisoformat((s or "").replace("Z", "+00:00"))
            except Exception:
                return None
        now_dt = _dt.now(_tz.utc)
        total_v = len(vendors)
        high_v = sum(1 for v in vendors if v.get("risk_tier") in ("high", "critical"))
        active_v = sum(1 for v in vendors if v.get("status") == "active")
        due_v = 0
        for v in vendors:
            la = _parse_iso(v.get("last_assessed_at"))
            if la is None:
                due_v += 1
            elif (now_dt - la) > _td(days=365):
                due_v += 1

        kpc1, kpc2, kpc3, kpc4 = st.columns(4)
        kpc1.metric(t("vendors.kpi.total"), total_v)
        kpc2.metric(t("vendors.kpi.high_risk"), high_v)
        kpc3.metric(t("vendors.kpi.due"), due_v)
        kpc4.metric(t("vendors.kpi.active"), active_v)

        st.markdown("---")

        # ── New Vendor form ─────────────────────────────────────
        nv_key = "vendors_show_new"
        if st.button(t("vendors.new_button"), key="vendors_new_btn"):
            st.session_state[nv_key] = not st.session_state.get(nv_key, False)

        if st.session_state.get(nv_key, False):
            with st.form("vendors_new_form", clear_on_submit=True):
                st.markdown(f"**{t('vendors.new_form_title')}**")
                vc1, vc2 = st.columns(2)
                v_name = vc1.text_input(t("vendors.field.name"))
                v_cat = vc2.selectbox(
                    t("vendors.field.category"), VENDOR_CATEGORIES,
                    format_func=lambda v: t(f"vendors.cat.{v}"),
                )
                vc3, vc4 = st.columns(2)
                v_email = vc3.text_input(t("vendors.field.contact_email"))
                v_url = vc4.text_input(t("vendors.field.contract_url"))
                v_status = st.selectbox(
                    t("vendors.field.status"), VENDOR_STATUSES,
                    format_func=lambda v: t(f"vendors.status.{v}"),
                )
                submitted = st.form_submit_button(t("vendors.create_button"))
                if submitted:
                    if not v_name.strip():
                        st.error(t("vendors.field.name"))
                    else:
                        out = api_post("/api/v1/vendors", {
                            "name": v_name.strip(),
                            "category": v_cat,
                            "contact_email": v_email,
                            "contract_url": v_url,
                            "status": v_status,
                        })
                        if out and not out.get("error"):
                            st.success(t("vendors.created_ok"))
                            st.session_state[nv_key] = False
                            st.rerun()
                        else:
                            st.error(out.get("error", "Failed to create vendor"))

        # ── Vendor cards ────────────────────────────────────────
        if not vendors:
            st.info(t("vendors.no_vendors"))
        else:
            tier_to_band = {"critical": "critical", "high": "high",
                            "medium": "medium", "low": "low"}
            tier_to_badge = {"critical": "badge-red", "high": "badge-orange",
                             "medium": "badge-yellow", "low": "badge-green"}
            for v in vendors:
                vid = v["vendor_id"]
                tier_v = v.get("risk_tier") or "medium"
                band = tier_to_band.get(tier_v, "medium")
                badge_class = tier_to_badge.get(tier_v, "badge-gray")
                score = v.get("risk_score")
                score_txt = "—" if score is None else str(score)
                la_str = v.get("last_assessed_at")
                if la_str:
                    la_display = t("vendors.last_assessed", date=la_str[:10])
                else:
                    la_display = t("vendors.never_assessed")
                ai_summary_v = (v.get("ai_summary") or "").strip()
                v_cat_key = v.get("category", "other")
                v_status_key = v.get("status", "active")
                v_cat_label = t(f"vendors.cat.{v_cat_key}")
                v_status_label = t(f"vendors.status.{v_status_key}")
                v_tier_label = t(f"vendors.tier.{tier_v}")
                v_email_html = v.get("contact_email") or "—"

                st.markdown(
                    f"<div class='record-card {band}'>"
                    f"<div class='rc-head'>"
                    f"<div class='rc-title'>{v.get('name','')}</div>"
                    f"<div style='display:flex;gap:6px;align-items:center;flex-wrap:wrap'>"
                    f"<span class='score-chip'>{t('vendors.score')}: {score_txt}</span>"
                    f"<span class='badge {badge_class}'>{t('vendors.tier')}: {v_tier_label}</span>"
                    f"<span class='badge badge-gray'>{v_cat_label}</span>"
                    f"<span class='badge badge-yellow'>{v_status_label}</span>"
                    f"</div></div>"
                    f"<div class='rc-meta'>✉ {v_email_html} · 📅 {la_display}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                if ai_summary_v:
                    with st.expander(t("vendors.ai_summary")):
                        st.markdown(ai_summary_v)

                # Assess toggle
                assess_key = f"vendors_assess_{vid}"
                if st.button(t("vendors.assess_button"), key=f"vendors_assess_btn_{vid}"):
                    st.session_state[assess_key] = not st.session_state.get(assess_key, False)

                if st.session_state.get(assess_key, False):
                    # Either use existing answers if any, else default template
                    existing_answers = v.get("questionnaire") or []
                    if not existing_answers:
                        tpl = api_get("/api/v1/vendors/questionnaire-template") or {"questions": []}
                        existing_answers = tpl.get("questions", [])
                    with st.form(f"vendors_assess_form_{vid}", clear_on_submit=False):
                        st.markdown(f"**{t('vendors.assess_form_title')}**")
                        st.caption(t("vendors.assess_intro"))
                        new_answers = []
                        for idx, q in enumerate(existing_answers):
                            qid = q.get("question_id", f"Q{idx+1}")
                            st.markdown(
                                f"**[{qid}]** {q.get('question','')} · "
                                f"_weight: {q.get('weight','?')}_"
                            )
                            cA, cN = st.columns([1, 3])
                            cur_ans = (q.get("answer") or "unknown").lower()
                            ans_opts = ["yes", "no", "partial", "unknown"]
                            cur_idx = ans_opts.index(cur_ans) if cur_ans in ans_opts else 3
                            ans = cA.selectbox(
                                "Answer", ans_opts,
                                index=cur_idx,
                                format_func=lambda v: t(f"vendors.answer.{v}"),
                                key=f"v_a_{vid}_{idx}",
                                label_visibility="collapsed",
                            )
                            note = cN.text_input(
                                t("vendors.notes_label"),
                                value=q.get("notes", "") or "",
                                key=f"v_n_{vid}_{idx}",
                                label_visibility="collapsed",
                                placeholder=t("vendors.notes_label"),
                            )
                            new_answers.append({
                                "question_id": qid,
                                "question": q.get("question", ""),
                                "answer": ans,
                                "weight": int(q.get("weight", 0) or 0),
                                "notes": note,
                            })
                        submit_assess = st.form_submit_button(t("vendors.assess_submit"))
                        if submit_assess:
                            try:
                                rresp = requests.post(
                                    f"{API}/api/v1/vendors/{vid}/assess",
                                    json={"answers": new_answers},
                                    timeout=90,
                                )
                                if rresp.ok:
                                    st.success(t("vendors.assess_ok"))
                                    st.session_state[assess_key] = False
                                    st.rerun()
                                else:
                                    st.error(f"{rresp.status_code}: {rresp.text[:200]}")
                            except Exception as _e:
                                st.error(str(_e))


    # ════════════════════════════════════════════════════════════════
    # PAGE: POLICIES (Phase 1)
    # ════════════════════════════════════════════════════════════════

    elif page == "policies":
        page_hero(t("policies.header"), t("policies.intro"))

        POLICY_STATUSES = ["draft", "active", "superseded", "retired"]
        tab_lib, tab_ack = st.tabs([t("policies.tab_library"), t("policies.tab_acks")])

        # ── LIBRARY TAB ─────────────────────────────────────────
        with tab_lib:
            policies_resp = api_get("/api/v1/policies") or {"policies": []}
            policies = policies_resp.get("policies", []) or []
            pending_resp = api_get("/api/v1/policy-assignments?status=pending") or {"assignments": []}
            pending_count = len(pending_resp.get("assignments", []) or [])
            active_count = sum(1 for p in policies if p.get("status") == "active")

            kp1, kp2, kp3 = st.columns(3)
            kp1.metric(t("policies.kpi.total"), len(policies))
            kp2.metric(t("policies.kpi.active"), active_count)
            kp3.metric(t("policies.kpi.pending"), pending_count)

            np_key = "policies_show_new"
            if st.button(t("policies.new_button"), key="policies_new_btn"):
                st.session_state[np_key] = not st.session_state.get(np_key, False)

            if st.session_state.get(np_key, False):
                with st.form("policies_new_form", clear_on_submit=True):
                    st.markdown(f"**{t('policies.new_form_title')}**")
                    pc1, pc2 = st.columns([3, 1])
                    p_title = pc1.text_input(t("policies.field.title"))
                    p_version = pc2.text_input(t("policies.field.version"), value="1.0")
                    p_summary = st.text_area(t("policies.field.summary"))
                    p_content = st.text_area(t("policies.field.content"), height=180)
                    pc3, pc4, pc5 = st.columns(3)
                    p_eff = pc3.text_input(t("policies.field.effective"))
                    p_rev = pc4.text_input(t("policies.field.review"))
                    p_owner = pc5.text_input(t("policies.field.owner"))
                    p_status = st.selectbox(
                        t("policies.field.status"), POLICY_STATUSES,
                        index=1,
                        format_func=lambda v: t(f"policies.status.{v}"),
                    )
                    p_linked = st.text_input(t("policies.field.linked_controls"))
                    submit_p = st.form_submit_button(t("policies.create_button"))
                    if submit_p:
                        if not p_title.strip():
                            st.error(t("policies.field.title"))
                        else:
                            linked = [s.strip() for s in p_linked.split(",") if s.strip()]
                            out = api_post("/api/v1/policies", {
                                "title": p_title.strip(),
                                "version": p_version or "1.0",
                                "summary": p_summary,
                                "content": p_content,
                                "effective_date": p_eff,
                                "review_date": p_rev,
                                "owner": p_owner,
                                "status": p_status,
                                "linked_controls": linked,
                            })
                            if out and not out.get("error"):
                                st.success(t("policies.created_ok"))
                                st.session_state[np_key] = False
                                st.rerun()
                            else:
                                st.error(out.get("error", "Failed to create policy"))

            if not policies:
                st.info(t("policies.no_policies"))
            else:
                for p in policies:
                    pid = p["policy_id"]
                    p_status = p.get("status", "active")
                    badge_map = {"active": "badge-green", "draft": "badge-yellow",
                                  "superseded": "badge-gray", "retired": "badge-gray"}
                    p_badge = badge_map.get(p_status, "badge-gray")
                    st.markdown(
                        f"<div class='record-card green'>"
                        f"<div class='rc-head'>"
                        f"<div class='rc-title'>{p.get('title','')}</div>"
                        f"<div style='display:flex;gap:6px;align-items:center;flex-wrap:wrap'>"
                        f"<span class='badge badge-gray'>{t('policies.policy_version', v=p.get('version','1.0'))}</span>"
                        f"<span class='badge {p_badge}'>{t(f'policies.status.{p_status}')}</span>"
                        f"</div></div>"
                        f"<div class='rc-meta'>"
                        f"{t('policies.policy_owner', o=p.get('owner','—') or '—')} · "
                        f"{t('policies.policy_effective', d=p.get('effective_date','—') or '—')}"
                        f"</div>"
                        f"<div class='rc-body'>{p.get('summary','') or ''}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    with st.expander(f"📄 {p.get('title','')} — {t('policies.policy_version', v=p.get('version','1.0'))}"):
                        if p.get("content"):
                            st.markdown(p["content"])
                        st.markdown("---")
                        assign_input = st.text_input(
                            t("policies.assign_to"),
                            key=f"pol_assign_in_{pid}",
                            placeholder="alice@demo, bob@demo",
                        )
                        if st.button(t("policies.assign_button"), key=f"pol_assign_btn_{pid}"):
                            uids = [s.strip() for s in (assign_input or "").split(",") if s.strip()]
                            if uids:
                                out = api_post(f"/api/v1/policies/{pid}/assign",
                                                {"user_ids": uids})
                                if out and not out.get("error"):
                                    st.success(t("policies.assign_ok",
                                                  n=out.get("assigned", 0),
                                                  s=out.get("skipped", 0)))
                                    st.rerun()
                                else:
                                    st.error(out.get("error", "Failed to assign"))

        # ── MY ACKNOWLEDGMENTS TAB ──────────────────────────────
        with tab_ack:
            demo_user = st.text_input(
                t("policies.demo_user_label"),
                value=st.session_state.get("policies_demo_user", "alice@demo"),
                help=t("policies.demo_user_help"),
                key="policies_demo_user_input",
            )
            st.session_state["policies_demo_user"] = demo_user

            user_resp = api_get(f"/api/v1/policy-assignments?user_id={demo_user}") or {"assignments": []}
            all_assignments = user_resp.get("assignments", []) or []
            pending = [a for a in all_assignments if a.get("status") == "pending"]
            acked = [a for a in all_assignments if a.get("status") == "acknowledged"]

            if not pending:
                st.info(t("policies.no_pending"))
            else:
                for a in pending:
                    aid = a["assignment_id"]
                    ptitle = a.get("policy_title") or "(deleted policy)"
                    pversion = a.get("policy_version", "1.0")
                    psummary = a.get("policy_summary", "") or ""
                    pcontent = a.get("policy_content", "") or ""
                    preview = pcontent[:400] + ("…" if len(pcontent) > 400 else "")

                    st.markdown(
                        f"<div class='record-card medium'>"
                        f"<div class='rc-head'>"
                        f"<div class='rc-title'>{ptitle}</div>"
                        f"<span class='badge badge-yellow'>"
                        f"{t('policies.policy_version', v=pversion)}</span>"
                        f"</div>"
                        f"<div class='rc-meta'>{psummary}</div>"
                        f"<div class='rc-body'><pre style='white-space:pre-wrap;font-family:inherit;font-size:0.85rem'>{preview}</pre></div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    with st.form(f"ack_form_{aid}", clear_on_submit=True):
                        sig = st.text_input(t("policies.signature_note"),
                                              key=f"ack_sig_{aid}")
                        submit_ack = st.form_submit_button(t("policies.accept_button"))
                        if submit_ack:
                            try:
                                rr = requests.post(
                                    f"{API}/api/v1/policy-assignments/{aid}/acknowledge",
                                    json={"signature_note": sig}, timeout=10,
                                )
                                if rr.ok:
                                    st.success(t("policies.acknowledged_ok"))
                                    st.rerun()
                                else:
                                    st.error(f"{rr.status_code}: {rr.text[:200]}")
                            except Exception as _e:
                                st.error(str(_e))

            if acked:
                with st.expander(t("policies.acknowledged_section")):
                    for a in acked:
                        st.markdown(
                            f"- ✅ **{a.get('policy_title') or '(deleted)'}** · "
                            f"{t('policies.policy_version', v=a.get('policy_version','1.0'))} · "
                            f"_acknowledged {((a.get('acknowledged_at') or '')[:10])}_"
                            + (f" — _{a.get('signature_note')}_" if a.get('signature_note') else "")
                        )


    # ════════════════════════════════════════════════════════════════
    # PAGE: INCIDENTS (Phase 1)
    # ════════════════════════════════════════════════════════════════

    elif page == "incidents":
        page_hero(t("incidents.header"), t("incidents.intro"))

        INC_SEVERITIES = ["low", "medium", "high", "critical"]
        INC_STATUSES = ["open", "investigating", "contained", "resolved", "closed"]
        INC_CATEGORIES = ["security_breach", "data_loss", "system_outage",
                            "policy_violation", "third_party", "other"]
        ALL = "__ALL__"

        # ── Filter row ──────────────────────────────────────────
        ifc1, ifc2, ifc3 = st.columns(3)
        f_sev = ifc1.selectbox(
            t("incidents.filter.severity"), [ALL] + INC_SEVERITIES,
            format_func=lambda v: t("all") if v == ALL else t(f"incidents.severity.{v}"),
            key="incidents_filter_sev",
        )
        f_istatus = ifc2.selectbox(
            t("incidents.filter.status"), [ALL] + INC_STATUSES,
            format_func=lambda v: t("all") if v == ALL else t(f"incidents.status.{v}"),
            key="incidents_filter_status",
        )
        f_icat = ifc3.selectbox(
            t("incidents.filter.category"), [ALL] + INC_CATEGORIES,
            format_func=lambda v: t("all") if v == ALL else t(f"incidents.cat.{v}"),
            key="incidents_filter_cat",
        )

        iquery = "/api/v1/incidents?"
        if f_sev != ALL:
            iquery += f"severity={f_sev}&"
        if f_istatus != ALL:
            iquery += f"status={f_istatus}&"
        if f_icat != ALL:
            iquery += f"category={f_icat}&"
        iresp = api_get(iquery.rstrip("&?")) or {"incidents": []}
        incidents = iresp.get("incidents", []) or []

        # ── KPIs ────────────────────────────────────────────────
        from datetime import datetime as _dt2, timezone as _tz2
        def _iso(s):
            try:
                return _dt2.fromisoformat((s or "").replace("Z", "+00:00"))
            except Exception:
                return None
        now2 = _dt2.now(_tz2.utc)
        open_inc = [i for i in incidents if i.get("status") not in ("closed", "resolved")]
        crit_open = sum(1 for i in open_inc if i.get("severity") == "critical")
        breach_pending = sum(
            1 for i in incidents
            if i.get("breach_notification_required") and not i.get("breach_notified_at")
        )
        # MTTR over closed incidents
        deltas = []
        for i in incidents:
            if i.get("status") in ("closed", "resolved") and i.get("reported_at") and i.get("resolved_at"):
                r = _iso(i["reported_at"])
                d = _iso(i["resolved_at"])
                if r and d:
                    deltas.append((d - r).total_seconds() / 86400.0)
        mttr = round(sum(deltas) / len(deltas), 1) if deltas else 0.0

        ic1, ic2, ic3, ic4 = st.columns(4)
        ic1.metric(t("incidents.kpi.open"), len(open_inc))
        ic2.metric(t("incidents.kpi.critical"), crit_open)
        ic3.metric(t("incidents.kpi.breach_pending"), breach_pending)
        ic4.metric(t("incidents.kpi.mttr"), mttr)

        st.markdown("---")

        # ── New Incident form ───────────────────────────────────
        ni_key = "incidents_show_new"
        if st.button(t("incidents.new_button"), key="incidents_new_btn"):
            st.session_state[ni_key] = not st.session_state.get(ni_key, False)

        if st.session_state.get(ni_key, False):
            with st.form("incidents_new_form", clear_on_submit=True):
                st.markdown(f"**{t('incidents.new_form_title')}**")
                i_title = st.text_input(t("incidents.field.title"))
                i_desc = st.text_area(t("incidents.field.description"))
                inc1, inc2, inc3 = st.columns(3)
                i_sev = inc1.selectbox(
                    t("incidents.field.severity"), INC_SEVERITIES,
                    index=1,
                    format_func=lambda v: t(f"incidents.severity.{v}"),
                )
                i_status = inc2.selectbox(
                    t("incidents.field.status"), INC_STATUSES,
                    format_func=lambda v: t(f"incidents.status.{v}"),
                )
                i_cat = inc3.selectbox(
                    t("incidents.field.category"), INC_CATEGORIES,
                    format_func=lambda v: t(f"incidents.cat.{v}"),
                )
                inc4, inc5 = st.columns(2)
                i_by = inc4.text_input(t("incidents.field.reported_by"))
                i_breach = inc5.checkbox(t("incidents.field.breach_required"),
                                          value=False)
                i_impact = st.text_area(t("incidents.field.impact"))
                submit_i = st.form_submit_button(t("incidents.create_button"))
                if submit_i:
                    if not i_title.strip():
                        st.error(t("incidents.field.title"))
                    else:
                        out = api_post("/api/v1/incidents", {
                            "title": i_title.strip(),
                            "description": i_desc,
                            "severity": i_sev,
                            "status": i_status,
                            "category": i_cat,
                            "reported_by": i_by,
                            "breach_notification_required": bool(i_breach),
                            "impact_assessment": i_impact,
                        })
                        if out and not out.get("error"):
                            st.success(t("incidents.created_ok"))
                            st.session_state[ni_key] = False
                            st.rerun()
                        else:
                            st.error(out.get("error", "Failed to create incident"))

        # ── Incident cards ──────────────────────────────────────
        if not incidents:
            st.info(t("incidents.no_incidents"))
        else:
            for i in incidents:
                iid = i["incident_id"]
                sev_v = i.get("severity", "medium")
                status_v = i.get("status", "open")
                cat_v = i.get("category", "other")
                reported_at = i.get("reported_at") or ""

                # Severity badge styling reuses our existing severity_badge helper
                sev_badge = severity_badge(sev_v)

                # Status badge — yellow for in-flight, green for resolved/closed
                status_color_map = {
                    "open": "badge-red",
                    "investigating": "badge-orange",
                    "contained": "badge-yellow",
                    "resolved": "badge-green",
                    "closed": "badge-gray",
                }
                status_badge_cls = status_color_map.get(status_v, "badge-gray")

                # Breach deadline banner
                breach_html = ""
                if i.get("breach_notification_required"):
                    deadline = i.get("regulatory_deadline")
                    notified = i.get("breach_notified_at")
                    if notified:
                        breach_html = (
                            f"<div class='breach-banner notified'>✅ "
                            f"{t('incidents.deadline_notified', when=notified[:16].replace('T',' '))}"
                            f"</div>"
                        )
                    elif deadline:
                        dl = _iso(deadline)
                        is_overdue = dl is not None and now2 > dl
                        when_display = deadline[:16].replace("T", " ")
                        if is_overdue:
                            breach_html = (
                                f"<div class='breach-banner overdue'>"
                                f"{t('incidents.breach_banner')} — "
                                f"{t('incidents.deadline_overdue', when=when_display)}"
                                f"</div>"
                            )
                        else:
                            breach_html = (
                                f"<div class='breach-banner'>"
                                f"{t('incidents.breach_banner')} — "
                                f"{t('incidents.deadline_in', when=when_display)}"
                                f"</div>"
                            )
                    else:
                        breach_html = (
                            f"<div class='breach-banner'>"
                            f"{t('incidents.breach_banner')}</div>"
                        )

                reported_line = t("incidents.reported_on",
                                   date=(reported_at[:10] if reported_at else "—"))
                if i.get("resolved_at"):
                    reported_line += " · " + t("incidents.resolved_on",
                                                date=i["resolved_at"][:10])
                owner_line = "👤 " + (i.get("reported_by") or "—")

                st.markdown(
                    f"<div class='record-card {sev_v}'>"
                    f"<div class='rc-head'>"
                    f"<div class='rc-title'>{i.get('title','')}</div>"
                    f"<div style='display:flex;gap:6px;align-items:center;flex-wrap:wrap'>"
                    f"{sev_badge}"
                    f"<span class='badge {status_badge_cls}'>{t(f'incidents.status.{status_v}')}</span>"
                    f"<span class='badge badge-gray'>{t(f'incidents.cat.{cat_v}')}</span>"
                    f"</div></div>"
                    f"<div class='rc-meta'>{reported_line} · {owner_line}</div>"
                    f"<div class='rc-body'>{i.get('description','') or ''}</div>"
                    f"{breach_html}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                edit_key = f"incident_edit_{iid}"
                if st.button(t("incidents.edit_section"), key=f"inc_edit_btn_{iid}"):
                    st.session_state[edit_key] = not st.session_state.get(edit_key, False)

                if st.session_state.get(edit_key, False):
                    with st.form(f"incident_edit_form_{iid}", clear_on_submit=False):
                        ei_title = st.text_input(t("incidents.field.title"),
                                                  value=i.get("title", ""))
                        ei_desc = st.text_area(t("incidents.field.description"),
                                                value=i.get("description", "") or "")
                        eic1, eic2, eic3 = st.columns(3)
                        ei_sev = eic1.selectbox(
                            t("incidents.field.severity"), INC_SEVERITIES,
                            index=INC_SEVERITIES.index(sev_v) if sev_v in INC_SEVERITIES else 1,
                            format_func=lambda v: t(f"incidents.severity.{v}"),
                            key=f"ei_sev_{iid}",
                        )
                        ei_status = eic2.selectbox(
                            t("incidents.field.status"), INC_STATUSES,
                            index=INC_STATUSES.index(status_v) if status_v in INC_STATUSES else 0,
                            format_func=lambda v: t(f"incidents.status.{v}"),
                            key=f"ei_status_{iid}",
                        )
                        ei_cat = eic3.selectbox(
                            t("incidents.field.category"), INC_CATEGORIES,
                            index=INC_CATEGORIES.index(cat_v) if cat_v in INC_CATEGORIES else 5,
                            format_func=lambda v: t(f"incidents.cat.{v}"),
                            key=f"ei_cat_{iid}",
                        )
                        eic4, eic5 = st.columns(2)
                        ei_by = eic4.text_input(t("incidents.field.reported_by"),
                                                 value=i.get("reported_by", "") or "",
                                                 key=f"ei_by_{iid}")
                        ei_breach = eic5.checkbox(
                            t("incidents.field.breach_required"),
                            value=bool(i.get("breach_notification_required")),
                            key=f"ei_breach_{iid}",
                        )
                        ei_breach_notified = st.text_input(
                            t("incidents.field.breach_notified"),
                            value=i.get("breach_notified_at") or "",
                            key=f"ei_notif_{iid}",
                        )
                        ei_impact = st.text_area(t("incidents.field.impact"),
                                                  value=i.get("impact_assessment", "") or "",
                                                  key=f"ei_imp_{iid}")
                        ei_root = st.text_area(t("incidents.field.root_cause"),
                                                value=i.get("root_cause", "") or "",
                                                key=f"ei_root_{iid}")
                        ei_rem = st.text_area(t("incidents.field.remediation"),
                                               value=i.get("remediation", "") or "",
                                               key=f"ei_rem_{iid}")
                        ei_lc = st.text_input(
                            t("incidents.field.linked_controls"),
                            value=", ".join(i.get("linked_controls") or []),
                            key=f"ei_lc_{iid}",
                        )
                        ei_lf = st.text_input(
                            t("incidents.field.linked_findings"),
                            value=", ".join(i.get("linked_findings") or []),
                            key=f"ei_lf_{iid}",
                        )
                        save_i = st.form_submit_button(t("incidents.update_button"))
                        if save_i:
                            payload = {
                                "title": ei_title.strip(),
                                "description": ei_desc,
                                "severity": ei_sev,
                                "status": ei_status,
                                "category": ei_cat,
                                "reported_by": ei_by,
                                "breach_notification_required": bool(ei_breach),
                                "breach_notified_at": ei_breach_notified or None,
                                "impact_assessment": ei_impact,
                                "root_cause": ei_root,
                                "remediation": ei_rem,
                                "linked_controls": [s.strip() for s in ei_lc.split(",") if s.strip()],
                                "linked_findings": [s.strip() for s in ei_lf.split(",") if s.strip()],
                            }
                            try:
                                pr = requests.patch(
                                    f"{API}/api/v1/incidents/{iid}",
                                    json=payload, timeout=10
                                )
                                if pr.ok:
                                    st.success(t("incidents.updated_ok"))
                                    st.session_state[edit_key] = False
                                    st.rerun()
                                else:
                                    st.error(f"{pr.status_code}: {pr.text[:200]}")
                            except Exception as _e:
                                st.error(str(_e))


# ── Render the avatar (last, so it reflects state changes from page handlers) ──
with _avatar_col:
    # Drop the avatar frame ~40px below the enlarged topbar baseline.
    st.markdown('<div style="height:40px"></div>', unsafe_allow_html=True)
    components.html(
        render_avatar(
            get_avatar_state(),
            message=_resolve_avatar_message(),
            page=page,
            lang=get_lang(),
        ),
        height=AVATAR_FRAME_HEIGHT,
        scrolling=False,
    )
