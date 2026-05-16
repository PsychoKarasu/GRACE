"""
GRACE Prototype — Streamlit Frontend
Professional GRC demo UI: Gap Analysis, Document Generation, Dashboard
"""
import os
import streamlit as st
import requests
import json
import time
from datetime import datetime

# ─── Config ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GRACE — GRC Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API = os.environ.get("GRACE_API_URL", "http://localhost:8000")
DEFAULT_LANGUAGE = os.environ.get("GRACE_DEFAULT_LANGUAGE", "en")

# ─── i18n ────────────────────────────────────────────────────────────

TRANSLATIONS = {
    "en": {
        # Sidebar
        "sidebar.copilot_brand":      "**Microsoft Copilot** *(simulated)*",
        "sidebar.language":           "Language",
        "sidebar.navigation":         "Navigation",
        "sidebar.engine_online":      "🟢 GRACE Engine: Online",
        "sidebar.engine_offline":     "🔴 GRACE Engine: Offline",
        "sidebar.api_label":          "API: {api}",
        # Page nav labels
        "nav.gap_analysis":           "🔍 Gap Analysis",
        "nav.doc_gen":                "📄 Document Generation",
        "nav.dashboard":              "📊 Governance Dashboard",
        "nav.registry":               "🗂️ Finding Registry",
        "nav.library":                "📚 Framework Library",
        # Gap Analysis
        "ga.header":                  "Gap Analysis",
        "ga.intro":                   "*Simulate a Copilot interaction: upload a document and receive a structured compliance assessment.*",
        "ga.input":                   "📋 Input",
        "ga.select_framework":        "Select framework",
        "ga.coming_soon_info":        "This framework will be available in Phase 3 of the GRACE rollout.",
        "ga.doc_source":              "Document source",
        "ga.opt_paste":               "Paste text",
        "ga.opt_upload":              "Upload file",
        "ga.opt_example":             "Use example policy",
        "ga.doc_title":               "Document title",
        "ga.doc_content":             "Paste document content",
        "ga.paste_placeholder":       "Paste your policy, procedure or standard here...",
        "ga.upload_label":            "Upload PDF or DOCX",
        "ga.choose_example":          "Choose example document",
        "ga.doc_preview":             "Document preview",
        "ga.run_button":              "🚀 Run Gap Analysis",
        "ga.copilot_response":        "📡 GRACE · Copilot Response",
        "ga.provide_content":         "Please provide document content.",
        "ga.registering":             "Registering document...",
        "ga.analyzing":               "🤖 Claude is analyzing your document against the framework...",
        "ga.registration_failed":     "Document registration failed: {detail}",
        "ga.assessment_failed":       "Assessment failed: {detail}",
        "ga.remediation":             "Remediation",
        "ga.evidence_required":       "📋 Evidence required for full compliance",
        # Document Generation
        "dg.header":                  "Document Generation",
        "dg.intro":                   "*Generate audit-ready compliance documents using Claude AI.*",
        "dg.configure":               "Configure",
        "dg.doc_type":                "Document type",
        "dg.framework":               "Framework",
        "dg.organization":            "Organization name",
        "dg.processor":               "Processor / Vendor name",
        "dg.purpose":                 "Processing purpose",
        "dg.policy_scope":            "Policy scope",
        "dg.isms_scope":              "ISMS scope",
        "dg.generate_button":         "✍️ Generate Document",
        "dg.generated":               "Generated Document",
        "dg.spinner":                 "Claude is generating your {kind}...",
        "dg.success":                 "✅ Document generated and saved",
        "dg.download":                "⬇️ Download as Markdown",
        "dg.placeholder":             "Configure the document and click Generate.",
        "dg.type_policy":             "Information Security Policy",
        "dg.type_dpa":                "Data Processing Agreement (GDPR Art.28)",
        "dg.type_soa":                "Statement of Applicability (SoA)",
        # Dashboard
        "db.header":                  "Governance Dashboard",
        "db.intro":                   "*Live view of compliance posture — simulates the XSOAR dashboard.*",
        "db.no_data":                 "No data yet. Run some gap analyses first.",
        "db.kpi.open_findings":       "Open Findings",
        "db.kpi.documents":           "Documents",
        "db.kpi.assessments":         "Assessments Run",
        "db.kpi.avg_coverage":        "Avg Coverage",
        "db.kpi.critical_open":       "Critical Open",
        "db.status_distribution":     "Compliance Status Distribution",
        "db.coverage_framework":      "Coverage by Framework",
        "db.severity_breakdown":      "Severity Breakdown",
        "db.recent_docs":             "📄 Recent Documents Analyzed",
        "db.no_findings":             "No findings yet.",
        "db.no_framework_data":       "No framework data yet.",
        "db.no_severity_data":        "No severity data yet.",
        "db.no_assessments":          "No assessments yet.",
        "db.no_document":             "(no document)",
        "db.findings_avg":            "{count} findings · avg {score}%",
        # Registry
        "reg.header":                 "Finding Registry",
        "reg.intro":                  "*All findings — simulates the XSOAR incident queue.*",
        "reg.framework":              "Framework",
        "reg.verdict":                "Verdict",
        "reg.operational_status":     "Operational Status",
        "reg.no_findings":            "No findings yet. Run a Gap Analysis first.",
        "reg.findings_count":         "**{n} finding(s)**",
        "reg.document":               "📄 **Document:** {title}",
        "reg.unknown_doc":            "(unknown document)",
        "reg.finding":                "Finding",
        "reg.remediation":            "Remediation",
        "reg.update_op_status":       "Update operational status",
        "reg.update_button":          "Update",
        "reg.status_updated":         "Status updated",
        # Library
        "lib.header":                 "Framework Library",
        "lib.intro":                  "*25 international frameworks — P0 frameworks active in this prototype.*",
        "lib.coming_phase3":          "🚧 Coming Phase 3",
        "lib.active":                 "✅ Active",
        "lib.category":               "Category",
        "lib.priority":               "Priority",
        "lib.controls":               "Controls",
        "lib.controls_loaded":        "*{n} controls loaded in prototype*",
        "lib.more_controls":          "+ {n} more controls...",
        "lib.explain_ctrl":           "Explain a control",
        "lib.explain_button":         "🤖 Explain with Claude",
        "lib.explain_spinner":        "Getting plain-language explanation...",
        "lib.cannot_reach":           "Cannot reach GRACE API",
        "lib.framework_entry":        "**{name}** — {controls} controls · {tag}",
        # Verdict labels (compliance status)
        "verdict.compliant":          "Compliant",
        "verdict.partial":            "Partial",
        "verdict.non_compliant":      "Non-Compliant",
        "verdict.no_evidence":        "No Evidence",
        "verdict.not_applicable":     "Not Applicable",
        # Verdict labels with emoji (dashboard distribution)
        "verdict_emoji.compliant":    "✅ Compliant",
        "verdict_emoji.partial":      "⚠️ Partial",
        "verdict_emoji.non_compliant":"❌ Non-Compliant",
        "verdict_emoji.no_evidence":  "❓ No Evidence",
        # Severity
        "severity.critical":          "CRITICAL",
        "severity.high":              "HIGH",
        "severity.medium":            "MEDIUM",
        "severity.low":               "LOW",
        # Operational status
        "opstatus.new":               "New",
        "opstatus.acknowledged":      "Acknowledged",
        "opstatus.in_progress":       "In Progress",
        "opstatus.resolved":          "Resolved",
        "opstatus.accepted_risk":     "Accepted Risk",
        "opstatus.closed":            "Closed",
        "opstatus.dismissed":         "Dismissed",
        # Common
        "all":                        "All",
    },
    "it": {
        "sidebar.copilot_brand":      "**Microsoft Copilot** *(simulato)*",
        "sidebar.language":           "Lingua",
        "sidebar.navigation":         "Navigazione",
        "sidebar.engine_online":      "🟢 Motore GRACE: Online",
        "sidebar.engine_offline":     "🔴 Motore GRACE: Offline",
        "sidebar.api_label":          "API: {api}",
        "nav.gap_analysis":           "🔍 Analisi dei Gap",
        "nav.doc_gen":                "📄 Generazione Documenti",
        "nav.dashboard":              "📊 Dashboard Governance",
        "nav.registry":               "🗂️ Registro Findings",
        "nav.library":                "📚 Libreria Framework",
        "ga.header":                  "Analisi dei Gap",
        "ga.intro":                   "*Simula un'interazione Copilot: carica un documento e ricevi un assessment di conformità strutturato.*",
        "ga.input":                   "📋 Input",
        "ga.select_framework":        "Seleziona framework",
        "ga.coming_soon_info":        "Questo framework sarà disponibile in Fase 3 del rollout GRACE.",
        "ga.doc_source":              "Origine documento",
        "ga.opt_paste":               "Incolla testo",
        "ga.opt_upload":              "Carica file",
        "ga.opt_example":             "Usa policy d'esempio",
        "ga.doc_title":               "Titolo documento",
        "ga.doc_content":             "Incolla il contenuto del documento",
        "ga.paste_placeholder":       "Incolla qui la tua policy, procedura o standard...",
        "ga.upload_label":            "Carica PDF o DOCX",
        "ga.choose_example":          "Scegli documento d'esempio",
        "ga.doc_preview":             "Anteprima documento",
        "ga.run_button":              "🚀 Esegui Analisi dei Gap",
        "ga.copilot_response":        "📡 GRACE · Risposta Copilot",
        "ga.provide_content":         "Fornisci il contenuto del documento.",
        "ga.registering":             "Registrazione del documento...",
        "ga.analyzing":               "🤖 Claude sta analizzando il documento rispetto al framework...",
        "ga.registration_failed":     "Registrazione documento fallita: {detail}",
        "ga.assessment_failed":       "Assessment fallito: {detail}",
        "ga.remediation":             "Rimedio",
        "ga.evidence_required":       "📋 Evidenze richieste per piena conformità",
        "dg.header":                  "Generazione Documenti",
        "dg.intro":                   "*Genera documenti di conformità audit-ready usando Claude AI.*",
        "dg.configure":               "Configura",
        "dg.doc_type":                "Tipo di documento",
        "dg.framework":               "Framework",
        "dg.organization":            "Nome organizzazione",
        "dg.processor":               "Nome processor / fornitore",
        "dg.purpose":                 "Finalità del trattamento",
        "dg.policy_scope":            "Ambito della policy",
        "dg.isms_scope":              "Ambito ISMS",
        "dg.generate_button":         "✍️ Genera Documento",
        "dg.generated":               "Documento Generato",
        "dg.spinner":                 "Claude sta generando il tuo {kind}...",
        "dg.success":                 "✅ Documento generato e salvato",
        "dg.download":                "⬇️ Scarica in Markdown",
        "dg.placeholder":             "Configura il documento e clicca Genera.",
        "dg.type_policy":             "Information Security Policy",
        "dg.type_dpa":                "Data Processing Agreement (GDPR Art.28)",
        "dg.type_soa":                "Statement of Applicability (SoA)",
        "db.header":                  "Dashboard Governance",
        "db.intro":                   "*Vista live della postura di conformità — simula la dashboard XSOAR.*",
        "db.no_data":                 "Nessun dato. Esegui prima qualche analisi dei gap.",
        "db.kpi.open_findings":       "Findings Aperti",
        "db.kpi.documents":           "Documenti",
        "db.kpi.assessments":         "Assessment Eseguiti",
        "db.kpi.avg_coverage":        "Copertura Media",
        "db.kpi.critical_open":       "Critici Aperti",
        "db.status_distribution":    "Distribuzione Stato di Conformità",
        "db.coverage_framework":      "Copertura per Framework",
        "db.severity_breakdown":      "Distribuzione Severità",
        "db.recent_docs":             "📄 Ultimi Documenti Analizzati",
        "db.no_findings":             "Nessun finding al momento.",
        "db.no_framework_data":       "Nessun dato per framework al momento.",
        "db.no_severity_data":        "Nessun dato di severità al momento.",
        "db.no_assessments":          "Nessun assessment al momento.",
        "db.no_document":             "(nessun documento)",
        "db.findings_avg":            "{count} findings · media {score}%",
        "reg.header":                 "Registro Findings",
        "reg.intro":                  "*Tutti i findings — simula la coda incident XSOAR.*",
        "reg.framework":              "Framework",
        "reg.verdict":                "Verdetto",
        "reg.operational_status":     "Stato Operativo",
        "reg.no_findings":            "Nessun finding al momento. Esegui prima un'Analisi dei Gap.",
        "reg.findings_count":         "**{n} finding**",
        "reg.document":               "📄 **Documento:** {title}",
        "reg.unknown_doc":            "(documento sconosciuto)",
        "reg.finding":                "Finding",
        "reg.remediation":            "Rimedio",
        "reg.update_op_status":       "Aggiorna stato operativo",
        "reg.update_button":          "Aggiorna",
        "reg.status_updated":         "Stato aggiornato",
        "lib.header":                 "Libreria Framework",
        "lib.intro":                  "*25 framework internazionali — i framework P0 sono attivi in questo prototipo.*",
        "lib.coming_phase3":          "🚧 In arrivo in Fase 3",
        "lib.active":                 "✅ Attivo",
        "lib.category":               "Categoria",
        "lib.priority":               "Priorità",
        "lib.controls":               "Controlli",
        "lib.controls_loaded":        "*{n} controlli caricati nel prototipo*",
        "lib.more_controls":          "+ altri {n} controlli...",
        "lib.explain_ctrl":           "Spiega un controllo",
        "lib.explain_button":         "🤖 Spiega con Claude",
        "lib.explain_spinner":        "Recupero la spiegazione in linguaggio naturale...",
        "lib.cannot_reach":           "Impossibile raggiungere l'API GRACE",
        "lib.framework_entry":        "**{name}** — {controls} controlli · {tag}",
        "verdict.compliant":          "Conforme",
        "verdict.partial":            "Parziale",
        "verdict.non_compliant":      "Non Conforme",
        "verdict.no_evidence":        "Senza Evidenza",
        "verdict.not_applicable":     "Non Applicabile",
        "verdict_emoji.compliant":    "✅ Conforme",
        "verdict_emoji.partial":      "⚠️ Parziale",
        "verdict_emoji.non_compliant":"❌ Non Conforme",
        "verdict_emoji.no_evidence":  "❓ Senza Evidenza",
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
    },
}


def get_lang() -> str:
    return st.session_state.get("language", DEFAULT_LANGUAGE)


def t(key: str, **kwargs) -> str:
    lang = get_lang()
    s = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    return s.format(**kwargs) if kwargs else s


# ─── Custom CSS ──────────────────────────────────────────────────────

st.markdown("""
<style>
/* Brightstar brand accent */
:root { --bs-blue: #002EE5; --bs-deep: #000F4F; }

/* Header strip */
.grace-header {
    background: linear-gradient(90deg, #000F4F 0%, #002EE5 100%);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.grace-header h1 { margin: 0; font-size: 1.5rem; font-weight: 700; }
.grace-header p  { margin: 0; font-size: 0.85rem; opacity: 0.8; }

/* Status badges */
.badge-red    { background:#FEE2E2; color:#991B1B; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-orange { background:#FFEDD5; color:#9A3412; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-yellow { background:#FEF9C3; color:#854D0E; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-amber  { background:#FEF3C7; color:#92400E; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-green  { background:#D1FAE5; color:#065F46; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-gray   { background:#F3F4F6; color:#374151; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-blue   { background:#DBEAFE; color:#1E40AF; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }

/* Finding card */
.finding-card {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
    border-left: 4px solid #002EE5;
}
.finding-card.critical { border-left-color: #DC2626; }
.finding-card.high     { border-left-color: #EA580C; }
.finding-card.medium   { border-left-color: #EAB308; }
.finding-card.low      { border-left-color: #6B7280; }

/* KPI card */
.kpi-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}
.kpi-value { font-size: 2rem; font-weight: 700; color: #000F4F; line-height: 1; }
.kpi-label { font-size: 0.8rem; color: #64748B; margin-top: 4px; }

/* Score bar */
.score-bar {
    height: 8px; border-radius: 4px;
    background: #E2E8F0; overflow: hidden;
}
.score-fill { height: 100%; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ─── Helper functions ────────────────────────────────────────────────

def status_badge(status: str) -> str:
    icons = {"compliant":"✅","partial":"⚠️","non_compliant":"❌","no_evidence":"❓","not_applicable":"➖"}
    styles = {"compliant":"green","partial":"amber","non_compliant":"red","no_evidence":"gray","not_applicable":"gray"}
    icon  = icons.get(status, "•")
    style = styles.get(status, "gray")
    label = t(f"verdict.{status}") if status in icons else status.replace("_"," ").title()
    return f'<span class="badge-{style}">{icon} {label}</span>'

def severity_badge(severity: str) -> str:
    styles = {"critical":"red","high":"orange","medium":"yellow","low":"gray"}
    style = styles.get(severity, "gray")
    label = t(f"severity.{severity}") if severity in styles else severity.upper()
    return f'<span class="badge-{style}">{label}</span>'

def opstatus_label(op_status: str) -> str:
    return t(f"opstatus.{op_status}") if op_status else ""

def score_bar(score: int, color: str = "#002EE5") -> str:
    return f"""<div class="score-bar">
        <div class="score-fill" style="width:{score}%;background:{color}"></div></div>"""

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


# ─── Header ──────────────────────────────────────────────────────────

st.markdown("""
<div class="grace-header">
    <div style="font-size:2rem">🛡️</div>
    <div>
        <h1>GRACE · Governance, Risk, Assurance & Compliance Engine</h1>
        <p>Prototype v1.0 · Powered by Claude AI · Brightstar Security Operations</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Sidebar Navigation ──────────────────────────────────────────────

LANG_LABELS = {"en": "🇬🇧 English", "it": "🇮🇹 Italiano"}

with st.sidebar:
    # Language selector — first so it persists nav selection across switches
    if "language" not in st.session_state:
        st.session_state["language"] = DEFAULT_LANGUAGE
    chosen_lang = st.selectbox(
        TRANSLATIONS[get_lang()]["sidebar.language"],
        options=list(LANG_LABELS.keys()),
        index=list(LANG_LABELS.keys()).index(get_lang()),
        format_func=lambda k: LANG_LABELS[k],
        key="language",
    )

    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Microsoft_logo.svg/320px-Microsoft_logo.svg.png", width=80)
    st.markdown(t("sidebar.copilot_brand"))
    st.markdown("---")

    PAGE_KEYS = ["gap_analysis", "doc_gen", "dashboard", "registry", "library"]
    page = st.radio(
        t("sidebar.navigation"),
        PAGE_KEYS,
        format_func=lambda k: t(f"nav.{k}"),
    )
    st.markdown("---")
    health = api_get("/health")
    if health:
        st.success(t("sidebar.engine_online"))
    else:
        st.error(t("sidebar.engine_offline"))
    st.caption(t("sidebar.api_label", api=API))


# ════════════════════════════════════════════════════════════════
# PAGE: GAP ANALYSIS
# ════════════════════════════════════════════════════════════════

if page == "gap_analysis":
    st.header(t("ga.header"))
    st.markdown(t("ga.intro"))

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader(t("ga.input"))

        # Framework selection
        fw_data = api_get("/api/v1/frameworks")
        fw_options = {}
        if fw_data:
            for fw in fw_data.get("frameworks", []):
                if not fw.get("coming_soon"):
                    fw_options[fw["name"]] = fw["id"]
                else:
                    fw_options[f"{fw['name']} *(coming soon)*"] = None

        selected_fw_name = st.selectbox(t("ga.select_framework"), list(fw_options.keys()))
        selected_fw_id   = fw_options.get(selected_fw_name)

        if not selected_fw_id:
            st.info(t("ga.coming_soon_info"))
            st.stop()

        # Document input method
        input_methods = {
            "paste":   t("ga.opt_paste"),
            "upload":  t("ga.opt_upload"),
            "example": t("ga.opt_example"),
        }
        input_method = st.radio(
            t("ga.doc_source"),
            list(input_methods.keys()),
            format_func=lambda k: input_methods[k],
        )

        document_text = ""
        document_title = ""
        uploaded = None

        if input_method == "paste":
            document_title = st.text_input(t("ga.doc_title"), value="Security Policy v1.0")
            document_text = st.text_area(t("ga.doc_content"), height=200,
                placeholder=t("ga.paste_placeholder"))

        elif input_method == "upload":
            uploaded = st.file_uploader(t("ga.upload_label"), type=["pdf","docx","txt"])
            if uploaded:
                document_title = uploaded.name

        elif input_method == "example":
            examples = {
                "Access Control Policy (partial)": (
                    "Access Control Policy v2.1\nOwner: IT Security\nVersion: 2.1\n\n"
                    "1. PURPOSE\nThis policy defines the access control requirements for all information systems.\n\n"
                    "2. SCOPE\nThis policy applies to all employees and contractors.\n\n"
                    "3. ACCESS CONTROL REQUIREMENTS\n"
                    "All users must authenticate with a username and password before accessing company systems. "
                    "Remote access requires VPN. Administrators have elevated access for system management. "
                    "New employees receive access based on their job role. "
                    "When employees leave, their accounts are disabled.\n\n"
                    "4. PASSWORD REQUIREMENTS\nPasswords must be at least 8 characters. "
                    "Passwords must be changed every 90 days.\n\n"
                    "5. RESPONSIBILITIES\nIT department is responsible for implementing access controls. "
                    "Managers approve access requests."
                ),
                "Privacy Policy (GDPR)": (
                    "Privacy Policy — Brightstar Ltd\nLast updated: January 2026\n\n"
                    "We collect personal information when you use our services. "
                    "This includes your name, email address, and usage data. "
                    "We use your information to provide our services and improve user experience. "
                    "We may share your data with third-party service providers who assist us. "
                    "You can request deletion of your data by contacting privacy@brightstar.com. "
                    "We retain data for 3 years after your last interaction. "
                    "We use cookies to improve our website. "
                    "For questions about your privacy, contact our Data Protection Officer at dpo@brightstar.com."
                ),
                "Incident Response Procedure": (
                    "Incident Response Procedure v1.0\n"
                    "1. DETECTION: Security incidents are detected via SIEM alerts and employee reports.\n"
                    "2. TRIAGE: The Security Operations team assesses the severity of each incident.\n"
                    "3. CONTAINMENT: Affected systems are isolated to prevent spread.\n"
                    "4. INVESTIGATION: Root cause analysis is performed.\n"
                    "5. RECOVERY: Systems are restored from clean backups.\n"
                    "6. LESSONS LEARNED: Post-incident review is conducted within 30 days.\n"
                    "Note: Critical incidents must be reported to senior management within 24 hours."
                )
            }
            choice = st.selectbox(t("ga.choose_example"), list(examples.keys()))
            document_title = choice
            document_text  = examples[choice]
            st.text_area(t("ga.doc_preview"), document_text, height=150, disabled=True)

        # Run button
        run_clicked = st.button(t("ga.run_button"), type="primary", use_container_width=True)

    with col2:
        st.subheader(t("ga.copilot_response"))
        result_container = st.container()

    if run_clicked:
        if not document_text and input_method != "upload":
            st.warning(t("ga.provide_content"))
            st.stop()

        with result_container:
            with st.spinner(t("ga.registering")):
                if input_method == "upload" and uploaded:
                    files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                    resp = requests.post(f"{API}/api/v1/documents/upload",
                                         files=files, data={"owner":"demo"})
                    doc_result = resp.json() if resp.ok else {}
                else:
                    doc_result = api_post("/api/v1/documents/text", {
                        "title": document_title,
                        "content": document_text
                    })

                if "document_id" not in doc_result:
                    st.error(t("ga.registration_failed", detail=str(doc_result)))
                    st.stop()
                doc_id = doc_result["document_id"]

            with st.spinner(t("ga.analyzing")):
                assessment = api_post("/api/v1/assessments/run-sync", {
                    "document_id": doc_id,
                    "framework": selected_fw_id,
                    "channel": "web_demo",
                    "language": get_lang(),
                })

            if "error" in assessment:
                st.error(t("ga.assessment_failed", detail=assessment['error']))
                st.stop()

            result = assessment.get("result", {})

            # ── Executive summary ──
            overall_score = result.get("overall_coverage_score", 0)
            overall_status = result.get("overall_status","partial")
            color = "#059669" if overall_score >= 80 else "#D97706" if overall_score >= 40 else "#DC2626"

            st.markdown(f"""
**{selected_fw_name}** · *{document_title}*

{score_bar(overall_score, color)}
<div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px">
<span style="font-size:1.5rem;font-weight:700;color:{color}">{overall_score}%</span>
{status_badge(overall_status)}
</div>

> {result.get('executive_summary','Assessment completed.')}
""", unsafe_allow_html=True)

            # ── Controls breakdown ──
            st.markdown("---")
            controls = result.get("controls", [])
            for ctrl in controls:
                severity = ctrl.get("severity","medium")
                st.markdown(f"""
<div class="finding-card {severity}">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
<strong>{ctrl.get('control_id','')} · {ctrl.get('control_title','')}</strong>
<div>{status_badge(ctrl.get('status','no_evidence'))} &nbsp; {severity_badge(severity)}</div>
</div>
<div style="font-size:0.85rem;color:#4B5563;margin-bottom:6px">{ctrl.get('finding','')}</div>
<div style="font-size:0.8rem">
<strong>{t('ga.remediation')}:</strong> {ctrl.get('remediation','')} &nbsp;|&nbsp;
<span style="color:#6B7280">{ctrl.get('regulatory_reference','')}</span>
</div>
</div>
""", unsafe_allow_html=True)

            # ── Evidence required ──
            with st.expander(t("ga.evidence_required")):
                for ctrl in controls:
                    if ctrl.get("evidence_required"):
                        st.markdown(f"**{ctrl.get('control_id')} — {ctrl.get('control_title')}**")
                        for ev in ctrl.get("evidence_required", []):
                            st.markdown(f"  - {ev}")


# ════════════════════════════════════════════════════════════════
# PAGE: DOCUMENT GENERATION
# ════════════════════════════════════════════════════════════════

elif page == "doc_gen":
    st.header(t("dg.header"))
    st.markdown(t("dg.intro"))

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.subheader(t("dg.configure"))
        fw_data = api_get("/api/v1/frameworks")
        fw_options = {}
        if fw_data:
            for fw in fw_data.get("frameworks", []):
                if not fw.get("coming_soon"):
                    fw_options[fw["name"]] = fw["id"]

        doc_types = {
            "policy": t("dg.type_policy"),
            "dpa":    t("dg.type_dpa"),
            "soa":    t("dg.type_soa"),
        }

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

    with col2:
        st.subheader(t("dg.generated"))
        if gen_clicked:
            with st.spinner(t("dg.spinner", kind=doc_type_name)):
                resp = api_post("/api/v1/generate", {
                    "framework_id": fw_id,
                    "doc_type": doc_type,
                    "context": context,
                    "language": get_lang(),
                })

            if "error" in resp:
                st.error(resp["error"])
            else:
                content = resp.get("content","")
                st.success(t("dg.success"))
                st.markdown(content)
                st.download_button(t("dg.download"),
                                    data=content,
                                    file_name=f"GRACE_{doc_type}_{fw_id}.md",
                                    mime="text/markdown")
        else:
            st.info(t("dg.placeholder"))


# ════════════════════════════════════════════════════════════════
# PAGE: GOVERNANCE DASHBOARD
# ════════════════════════════════════════════════════════════════

elif page == "dashboard":
    st.header(t("db.header"))
    st.markdown(t("db.intro"))

    kpi = api_get("/api/v1/kpi/summary")
    if not kpi:
        st.warning(t("db.no_data"))
        st.stop()

    # Top KPIs
    cols = st.columns(5)
    metrics = [
        (t("db.kpi.open_findings"), kpi.get("total_open_findings",0),        None),
        (t("db.kpi.documents"),      kpi.get("documents_registered",0),        None),
        (t("db.kpi.assessments"),    kpi.get("assessment_runs",0),             None),
        (t("db.kpi.avg_coverage"),  f"{kpi.get('avg_coverage_score',0):.0f}%", None),
        (t("db.kpi.critical_open"),  kpi.get("by_severity",{}).get("critical",0), "🔴"),
    ]
    for i, (label, value, icon) in enumerate(metrics):
        cols[i].markdown(f"""
<div class="kpi-card">
<div class="kpi-value">{icon or ''}{value}</div>
<div class="kpi-label">{label}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(t("db.status_distribution"))
        by_status = kpi.get("by_status",{})
        if by_status:
            for status, count in by_status.items():
                label = t(f"verdict_emoji.{status}") if status in ("compliant","partial","non_compliant","no_evidence") else status
                st.markdown(f"**{label}** — {count}")
        else:
            st.info(t("db.no_findings"))

    with col2:
        st.subheader(t("db.coverage_framework"))
        by_fw = kpi.get("by_framework",{})
        if by_fw:
            for fw, data in by_fw.items():
                score = data.get("avg_score",0) or 0
                color = "#059669" if score >= 80 else "#D97706" if score >= 40 else "#DC2626"
                st.markdown(f"**{fw}** — " + t("db.findings_avg", count=data.get('count',0), score=f"{score:.0f}"))
                st.markdown(score_bar(score, color), unsafe_allow_html=True)
                st.markdown("")
        else:
            st.info(t("db.no_framework_data"))

    st.markdown("---")
    st.subheader(t("db.severity_breakdown"))
    by_sev = kpi.get("by_severity",{})
    sev_order = ["critical","high","medium","low"]
    sev_colors = {"critical":"#DC2626","high":"#EA580C","medium":"#EAB308","low":"#6B7280"}
    if by_sev:
        cols = st.columns(len(sev_order))
        for i, sev in enumerate(sev_order):
            count = by_sev.get(sev,0)
            cols[i].markdown(f"""
<div class="kpi-card">
<div class="kpi-value" style="color:{sev_colors[sev]}">{count}</div>
<div class="kpi-label">{t(f"severity.{sev}")}</div>
</div>""", unsafe_allow_html=True)
    else:
        st.info(t("db.no_severity_data"))

    st.markdown("---")
    st.subheader(t("db.recent_docs"))
    runs = api_get("/api/v1/assessments")
    if runs and runs.get("runs"):
        recent = runs["runs"][:10]
        for r in recent:
            ts = r.get("started_at","")
            ts_short = ts[:19].replace("T", " ") if ts else ""
            doc = r.get("document_title") or t("db.no_document")
            fw = r.get("framework","")
            status = r.get("status","")
            status_emoji = {"completed":"✅","error":"❌","running":"⏳","pending":"⌛"}.get(status, "•")
            st.markdown(
                f"{status_emoji} **{doc}** · `{fw}` · "
                f"<span style='color:#6B7280;font-size:0.85rem'>{ts_short} UTC</span>",
                unsafe_allow_html=True
            )
    else:
        st.info(t("db.no_assessments"))


# ════════════════════════════════════════════════════════════════
# PAGE: FINDING REGISTRY
# ════════════════════════════════════════════════════════════════

elif page == "registry":
    st.header(t("reg.header"))
    st.markdown(t("reg.intro"))

    OP_STATUSES = ["new","acknowledged","in_progress","resolved","accepted_risk","closed","dismissed"]
    VERDICTS = ["non_compliant","partial","compliant","no_evidence","not_applicable"]
    FRAMEWORKS = ["ISO27001:2022","GDPR","SOC2","NIS2"]

    col1, col2, col3 = st.columns(3)
    fw_filter = col1.selectbox(
        t("reg.framework"), [t("all")] + FRAMEWORKS
    )
    verdict_filter = col2.selectbox(
        t("reg.verdict"),
        [t("all")] + VERDICTS,
        format_func=lambda v: v if v == t("all") else t(f"verdict.{v}")
    )
    op_status_filter = col3.selectbox(
        t("reg.operational_status"),
        [t("all")] + OP_STATUSES,
        format_func=lambda v: v if v == t("all") else t(f"opstatus.{v}")
    )

    query = "/api/v1/findings?limit=100"
    if fw_filter != t("all"):
        query += f"&framework={fw_filter}"
    if verdict_filter != t("all"):
        query += f"&status={verdict_filter}"
    if op_status_filter != t("all"):
        query += f"&operational_status={op_status_filter}"

    findings = api_get(query)

    if not findings or not findings.get("findings"):
        st.info(t("reg.no_findings"))
    else:
        items = findings["findings"]
        st.markdown(t("reg.findings_count", n=len(items)))
        for f in items:
            severity = f.get("severity","medium")
            doc_title = f.get("document_title") or t("reg.unknown_doc")
            with st.expander(
                f"[{f.get('framework','')}] {f.get('control_id','')} · "
                f"{f.get('control_title','')[:60]} — {t(f'severity.{severity}')}"
            ):
                st.markdown(t("reg.document", title=doc_title))
                cols = st.columns([2,1,1])
                cols[0].markdown(f"**{t('reg.finding')}:**  \n{f.get('description','')}")
                verdict = f.get('compliance_status','')
                cols[1].markdown(f"**{t('reg.verdict')}:**  \n{t(f'verdict.{verdict}') if verdict else ''}")
                op_st = f.get('operational_status','')
                cols[2].markdown(f"**{t('reg.operational_status')}:**  \n{opstatus_label(op_st)}")

                st.markdown(f"**{t('reg.remediation')}:** {f.get('recommended_action','')}")
                st.markdown(f"*{f.get('regulatory_reference','')}*")

                new_status = st.selectbox(
                    t("reg.update_op_status"),
                    OP_STATUSES,
                    format_func=lambda v: t(f"opstatus.{v}"),
                    key=f"status_{f['finding_id']}"
                )
                if st.button(t("reg.update_button"), key=f"upd_{f['finding_id']}"):
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
    st.header(t("lib.header"))
    st.markdown(t("lib.intro"))

    fw_data = api_get("/api/v1/frameworks")
    if not fw_data:
        st.error(t("lib.cannot_reach"))
        st.stop()

    for fw in fw_data.get("frameworks",[]):
        coming_soon = fw.get("coming_soon", False)
        status_tag = t("lib.coming_phase3") if coming_soon else t("lib.active")
        with st.expander(t("lib.framework_entry", name=fw['name'], controls=fw['controls'], tag=status_tag)):
            col1, col2 = st.columns([2,1])
            col1.markdown(f"**{t('lib.category')}:** {fw['category']}  \n**{t('lib.priority')}:** {fw['priority']}")
            col2.markdown(f"**{t('lib.controls')}:** {fw['controls']}")

            if not coming_soon:
                # Show controls
                ctrl_data = api_get(f"/api/v1/frameworks/{fw['id']}/controls")
                if ctrl_data:
                    controls = ctrl_data.get("controls",[])
                    st.markdown(t("lib.controls_loaded", n=len(controls)))
                    for ctrl in controls[:5]:
                        st.markdown(f"- **{ctrl['control_id']}** · {ctrl['title']}")
                    if len(controls) > 5:
                        st.caption(t("lib.more_controls", n=len(controls)-5))

                    # Explain a control
                    st.markdown("---")
                    ctrl_ids = [c["control_id"] for c in controls]
                    selected_ctrl = st.selectbox(t("lib.explain_ctrl"), ctrl_ids, key=f"ctrl_{fw['id']}")
                    if st.button(t("lib.explain_button"), key=f"exp_{fw['id']}"):
                        with st.spinner(t("lib.explain_spinner")):
                            result = api_get(f"/api/v1/frameworks/{fw['id']}/controls/{selected_ctrl}/explain?language={get_lang()}")
                            if result:
                                st.markdown(result.get("explanation",""))
