"""
GRACE Prototype — Streamlit Frontend
Professional GRC demo UI: Gap Analysis, Document Generation, Dashboard
"""
import os
import base64
from pathlib import Path
import streamlit as st
import requests

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

ASSETS = Path(__file__).parent / "assets"


@st.cache_data
def load_logo_b64() -> str:
    p = ASSETS / "grace-logo.png"
    if p.exists():
        return base64.b64encode(p.read_bytes()).decode()
    return ""


LOGO_B64 = load_logo_b64()


# ─── i18n ────────────────────────────────────────────────────────────

TRANSLATIONS = {
    "en": {
        "sidebar.navigation":         "Navigation",
        "sidebar.engine_online":      "GRACE Engine: Online",
        "sidebar.engine_offline":     "GRACE Engine: Offline",
        "sidebar.api_label":          "API: {api}",
        "topbar.language":            "Language",
        "topbar.theme.light":         "Light",
        "topbar.theme.dark":          "Dark",
        "topbar.tagline":             "Governance · Risk · Assurance · Compliance Engine",
        "nav.gap_analysis":           "🔍  Gap Analysis",
        "nav.doc_gen":                "📄  Document Generation",
        "nav.dashboard":              "📊  Governance Dashboard",
        "nav.registry":               "🗂️  Finding Registry",
        "nav.library":                "📚  Framework Library",
        "ga.header":                  "Gap Analysis",
        "ga.intro":                   "Upload a document and receive a structured, framework-aligned compliance assessment in seconds.",
        "ga.input":                   "Input",
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
        "ga.run_button":              "🚀  Run Gap Analysis",
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
        "reg.findings_count":         "**{n} finding(s)**",
        "reg.document":               "**Document:** {title}",
        "reg.unknown_doc":            "(unknown document)",
        "reg.finding":                "Finding",
        "reg.remediation":            "Remediation",
        "reg.update_op_status":       "Update operational status",
        "reg.update_button":          "Update",
        "reg.status_updated":         "Status updated.",
        "lib.header":                 "Framework Library",
        "lib.intro":                  "25 international frameworks — P0 frameworks active in this prototype.",
        "lib.coming_phase3":          "🚧  Coming Phase 3",
        "lib.active":                 "✅  Active",
        "lib.category":               "Category",
        "lib.priority":               "Priority",
        "lib.controls":               "Controls",
        "lib.controls_loaded":        "{n} controls loaded in prototype",
        "lib.more_controls":          "+ {n} more controls…",
        "lib.explain_ctrl":           "Explain a control",
        "lib.explain_button":         "🤖  Explain with Claude",
        "lib.explain_spinner":        "Getting plain-language explanation…",
        "lib.cannot_reach":           "Cannot reach GRACE API",
        "lib.framework_entry":        "**{name}** — {controls} controls · {tag}",
        "verdict.compliant":          "Compliant",
        "verdict.partial":            "Partial",
        "verdict.non_compliant":      "Non-Compliant",
        "verdict.no_evidence":        "No Evidence",
        "verdict.not_applicable":     "Not Applicable",
        "verdict_emoji.compliant":    "✅ Compliant",
        "verdict_emoji.partial":      "⚠️ Partial",
        "verdict_emoji.non_compliant":"❌ Non-Compliant",
        "verdict_emoji.no_evidence":  "❓ No Evidence",
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
    },
    "it": {
        "sidebar.navigation":         "Navigazione",
        "sidebar.engine_online":      "Motore GRACE: Online",
        "sidebar.engine_offline":     "Motore GRACE: Offline",
        "sidebar.api_label":          "API: {api}",
        "topbar.language":            "Lingua",
        "topbar.theme.light":         "Chiaro",
        "topbar.theme.dark":          "Scuro",
        "topbar.tagline":             "Governance · Risk · Assurance · Compliance Engine",
        "nav.gap_analysis":           "🔍  Analisi dei Gap",
        "nav.doc_gen":                "📄  Generazione Documenti",
        "nav.dashboard":              "📊  Dashboard Governance",
        "nav.registry":               "🗂️  Registro Findings",
        "nav.library":                "📚  Libreria Framework",
        "ga.header":                  "Analisi dei Gap",
        "ga.intro":                   "Carica un documento e ottieni in pochi secondi un assessment di conformità strutturato e allineato al framework.",
        "ga.input":                   "Input",
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
        "ga.run_button":              "🚀  Esegui Analisi",
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
        "reg.findings_count":         "**{n} finding**",
        "reg.document":               "**Documento:** {title}",
        "reg.unknown_doc":            "(documento sconosciuto)",
        "reg.finding":                "Finding",
        "reg.remediation":            "Rimedio",
        "reg.update_op_status":       "Aggiorna stato operativo",
        "reg.update_button":          "Aggiorna",
        "reg.status_updated":         "Stato aggiornato.",
        "lib.header":                 "Libreria Framework",
        "lib.intro":                  "25 framework internazionali — i framework P0 sono attivi in questo prototipo.",
        "lib.coming_phase3":          "🚧  In arrivo in Fase 3",
        "lib.active":                 "✅  Attivo",
        "lib.category":               "Categoria",
        "lib.priority":               "Priorità",
        "lib.controls":               "Controlli",
        "lib.controls_loaded":        "{n} controlli caricati nel prototipo",
        "lib.more_controls":          "+ altri {n} controlli…",
        "lib.explain_ctrl":           "Spiega un controllo",
        "lib.explain_button":         "🤖  Spiega con Claude",
        "lib.explain_spinner":        "Recupero la spiegazione in linguaggio naturale…",
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


def get_theme() -> str:
    return st.session_state.get("theme", DEFAULT_THEME)


def t(key: str, **kwargs) -> str:
    lang = get_lang()
    s = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    return s.format(**kwargs) if kwargs else s


# ─── Theme / CSS ─────────────────────────────────────────────────────

THEMES = {
    "light": {
        "bg":          "#FAFAF7",
        "surface":     "#FFFFFF",
        "surface_alt": "#F4F1E8",
        "text":        "#163265",
        "text_dim":    "#5A6F8C",
        "primary":     "#163265",
        "accent":      "#2A7A8A",
        "accent_soft": "#D5EDF2",
        "border":      "#E5E7EB",
        "sidebar_bg":  "#F4F1E8",
        "shadow":      "0 1px 3px rgba(22,50,101,0.08), 0 4px 16px rgba(22,50,101,0.05)",
        "shadow_lg":   "0 4px 12px rgba(22,50,101,0.10), 0 16px 40px rgba(22,50,101,0.08)",
        "card_hover_bg": "#F8F9FB",
    },
    "dark": {
        "bg":          "#0A1929",
        "surface":     "#152E47",
        "surface_alt": "#1A3650",
        "text":        "#E6F0F5",
        "text_dim":    "#8FA5BD",
        "primary":     "#4EC6D9",
        "accent":      "#4EC6D9",
        "accent_soft": "#1E3E5C",
        "border":      "#1E3E5C",
        "sidebar_bg":  "#0A1929",
        "shadow":      "0 1px 3px rgba(0,0,0,0.3), 0 4px 16px rgba(0,0,0,0.2)",
        "shadow_lg":   "0 4px 12px rgba(0,0,0,0.4), 0 16px 40px rgba(0,0,0,0.3)",
        "card_hover_bg": "#1A3650",
    },
}


def inject_css():
    th = THEMES[get_theme()]
    st.markdown(f"""
<style>
:root {{
  --bg:          {th['bg']};
  --surface:     {th['surface']};
  --surface-alt: {th['surface_alt']};
  --text:        {th['text']};
  --text-dim:    {th['text_dim']};
  --primary:     {th['primary']};
  --accent:      {th['accent']};
  --accent-soft: {th['accent_soft']};
  --border:      {th['border']};
  --sidebar-bg:  {th['sidebar_bg']};
  --shadow:      {th['shadow']};
  --shadow-lg:   {th['shadow_lg']};
  --card-hover-bg: {th['card_hover_bg']};
}}

/* Streamlit app chrome */
.stApp {{ background: var(--bg); color: var(--text); }}
[data-testid="stHeader"] {{ display: none; }}
[data-testid="stSidebar"] {{ background: var(--sidebar-bg); border-right: 1px solid var(--border); }}
[data-testid="stSidebar"] * {{ color: var(--text) !important; }}
.block-container {{ padding-top: 0.5rem !important; max-width: 1400px; }}

/* Typography */
html, body, .stApp, [data-testid="stMarkdownContainer"], .stMarkdown p, .stMarkdown li {{
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
  color: var(--text);
}}
h1, h2, h3, h4 {{ color: var(--text); letter-spacing: -0.01em; }}
h1 {{ font-weight: 700; }}
h2 {{ font-weight: 650; }}
h3 {{ font-weight: 600; }}

/* Top bar */
.grace-topbar {{
  display: flex; align-items: center; justify-content: space-between;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px 18px;
  margin: 4px 0 18px 0;
  box-shadow: var(--shadow);
}}
.grace-topbar .brand {{
  display: flex; align-items: center; gap: 14px;
}}
.grace-topbar .brand-logo {{
  height: 44px; width: auto;
}}
.grace-topbar .brand-text {{
  display: flex; flex-direction: column; line-height: 1.15;
}}
.grace-topbar .brand-name {{
  font-size: 1.2rem; font-weight: 700; color: var(--primary);
  letter-spacing: 0.5px;
}}
.grace-topbar .brand-tagline {{
  font-size: 0.72rem; color: var(--text-dim); margin-top: 2px;
}}

/* Sidebar brand block */
.grace-side-brand {{
  background: linear-gradient(140deg, var(--primary) 0%, var(--accent) 100%);
  border-radius: 12px;
  padding: 18px 14px;
  color: white !important;
  text-align: center;
  margin-bottom: 10px;
}}
.grace-side-brand * {{ color: white !important; }}
.grace-side-brand img {{ height: 56px; margin-bottom: 6px; }}
.grace-side-brand .name {{ font-size: 1.05rem; font-weight: 700; letter-spacing: 1px; }}
.grace-side-brand .sub {{ font-size: 0.7rem; opacity: 0.85; margin-top: 2px; }}

/* Status pill */
.status-pill {{
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--accent-soft); color: var(--primary);
  padding: 6px 12px; border-radius: 999px;
  font-size: 0.8rem; font-weight: 600;
  border: 1px solid var(--border);
}}
.status-pill.online::before {{
  content: ""; width: 8px; height: 8px; border-radius: 50%; background: #16A34A;
  box-shadow: 0 0 8px #16A34A;
}}
.status-pill.offline::before {{
  content: ""; width: 8px; height: 8px; border-radius: 50%; background: #DC2626;
}}

/* Status badges (verdict/severity chips) */
.badge {{
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: 999px;
  font-size: 11.5px; font-weight: 600;
  border: 1px solid transparent;
}}
.badge-red    {{ background:#FEE2E2; color:#991B1B; border-color:#FCA5A5; }}
.badge-orange {{ background:#FFEDD5; color:#9A3412; border-color:#FED7AA; }}
.badge-yellow {{ background:#FEF9C3; color:#854D0E; border-color:#FDE68A; }}
.badge-green  {{ background:#D1FAE5; color:#065F46; border-color:#86EFAC; }}
.badge-gray   {{ background:#F3F4F6; color:#374151; border-color:#D1D5DB; }}
.badge-teal   {{ background:#CCFBF1; color:#115E59; border-color:#5EEAD4; }}
.badge-blue   {{ background:#DBEAFE; color:#1E40AF; border-color:#93C5FD; }}

/* Finding cards */
.finding-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 18px;
  margin-bottom: 12px;
  border-left: 4px solid var(--accent);
  box-shadow: var(--shadow);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.finding-card:hover {{ transform: translateY(-1px); box-shadow: var(--shadow-lg); }}
.finding-card.critical {{ border-left-color: #DC2626; }}
.finding-card.high     {{ border-left-color: #EA580C; }}
.finding-card.medium   {{ border-left-color: #EAB308; }}
.finding-card.low      {{ border-left-color: #6B7280; }}
.finding-card .ctrl-id {{
  color: var(--primary); font-weight: 700; font-size: 0.95rem;
}}
.finding-card .ctrl-title {{ color: var(--text); font-weight: 500; }}
.finding-card .finding-body {{
  color: var(--text-dim); font-size: 0.88rem; margin: 8px 0;
  line-height: 1.5;
}}
.finding-card .rem {{
  color: var(--text); font-size: 0.83rem;
  padding-top: 8px; border-top: 1px solid var(--border);
}}
.finding-card .reg-ref {{ color: var(--text-dim); font-size: 0.78rem; }}

/* KPI cards */
.kpi-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px 16px;
  text-align: center;
  box-shadow: var(--shadow);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.kpi-card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-lg); }}
.kpi-card .kpi-value {{
  font-size: 2.2rem; font-weight: 700; color: var(--primary); line-height: 1;
}}
.kpi-card .kpi-label {{
  font-size: 0.78rem; color: var(--text-dim); margin-top: 6px;
  text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;
}}
.kpi-card .kpi-icon {{
  font-size: 1.4rem; opacity: 0.6;
}}

/* Score bar */
.score-bar {{
  height: 10px; border-radius: 10px;
  background: var(--accent-soft); overflow: hidden;
  border: 1px solid var(--border);
}}
.score-fill {{ height: 100%; border-radius: 10px; transition: width 0.3s ease; }}

/* Hero panel for page header */
.page-hero {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px 22px;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
}}
.page-hero h1 {{
  margin: 0 0 4px 0; font-size: 1.6rem; color: var(--primary);
}}
.page-hero p {{ margin: 0; color: var(--text-dim); font-size: 0.92rem; }}

/* Section subtitle */
.section-sub {{
  font-size: 0.95rem; font-weight: 600; color: var(--primary);
  margin: 16px 0 8px 0; letter-spacing: 0.3px;
}}

/* Streamlit widget tweaks */
.stButton button, .stDownloadButton button {{
  border-radius: 10px; font-weight: 600;
  transition: all 0.15s ease;
}}
.stButton button[kind="primary"], .stDownloadButton button[kind="primary"] {{
  background: var(--primary); color: white; border: none;
}}
.stButton button[kind="primary"]:hover {{
  background: var(--accent); transform: translateY(-1px);
}}
[data-testid="stExpander"] {{
  background: var(--surface); border-radius: 12px;
  border: 1px solid var(--border) !important;
  box-shadow: var(--shadow);
}}
[data-testid="stExpander"] summary {{ padding: 6px 10px; }}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] {{
  border-radius: 10px !important;
}}

/* Recent doc row */
.recent-row {{
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; border-radius: 8px;
  background: var(--surface); border: 1px solid var(--border);
  margin-bottom: 6px;
}}
.recent-row .doc-name {{ font-weight: 600; color: var(--text); }}
.recent-row .meta {{ color: var(--text-dim); font-size: 0.82rem; margin-left: auto; }}
.recent-row .fw-tag {{
  background: var(--accent-soft); color: var(--primary);
  padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;
}}
</style>
""", unsafe_allow_html=True)


# ─── Helper functions ────────────────────────────────────────────────

def status_badge(status: str) -> str:
    icons = {"compliant":"✅","partial":"⚠️","non_compliant":"❌","no_evidence":"❓","not_applicable":"➖"}
    styles = {"compliant":"green","partial":"yellow","non_compliant":"red","no_evidence":"gray","not_applicable":"gray"}
    icon  = icons.get(status, "•")
    style = styles.get(status, "gray")
    label = t(f"verdict.{status}") if status in icons else status.replace("_"," ").title()
    return f'<span class="badge badge-{style}">{icon} {label}</span>'

def severity_badge(severity: str) -> str:
    styles = {"critical":"red","high":"orange","medium":"yellow","low":"gray"}
    style = styles.get(severity, "gray")
    label = t(f"severity.{severity}") if severity in styles else severity.upper()
    return f'<span class="badge badge-{style}">{label}</span>'

def opstatus_label(op_status: str) -> str:
    return t(f"opstatus.{op_status}") if op_status else ""

def score_bar(score: int, color: str = None) -> str:
    if color is None:
        color = THEMES[get_theme()]["accent"]
    return f'<div class="score-bar"><div class="score-fill" style="width:{score}%;background:{color}"></div></div>'

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

LANG_OPTIONS = {"en": "🇬🇧 EN", "it": "🇮🇹 IT"}

# Build the top-bar as a single HTML block on the left + Streamlit widgets on the right
top_left, top_mid, top_lang, top_theme = st.columns([5.5, 2, 1.4, 1.1])

with top_left:
    logo_html = (
        f'<img class="brand-logo" src="data:image/png;base64,{LOGO_B64}" alt="GRACE">'
        if LOGO_B64
        else '<div style="font-size:2rem">🛡️</div>'
    )
    st.markdown(
        f"""
<div class="grace-topbar" style="margin-right:6px">
  <div class="brand">
    {logo_html}
    <div class="brand-text">
      <span class="brand-name">GRACE</span>
      <span class="brand-tagline">{t('topbar.tagline')}</span>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

with top_mid:
    st.markdown("")  # spacer

with top_lang:
    st.selectbox(
        t("topbar.language"),
        options=list(LANG_OPTIONS.keys()),
        format_func=lambda k: LANG_OPTIONS[k],
        key="language",
        label_visibility="collapsed",
    )

with top_theme:
    is_dark = get_theme() == "dark"
    theme_label = "🌙" if not is_dark else "☀️"
    if st.button(theme_label, use_container_width=True, help=t(f"topbar.theme.{'light' if is_dark else 'dark'}")):
        st.session_state["theme"] = "light" if is_dark else "dark"
        st.rerun()


# ─── Sidebar ─────────────────────────────────────────────────────────

with st.sidebar:
    if LOGO_B64:
        st.markdown(
            f"""
<div class="grace-side-brand">
  <img src="data:image/png;base64,{LOGO_B64}" alt="GRACE">
  <div class="name">GRACE</div>
  <div class="sub">GRC Engine</div>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
<div class="grace-side-brand">
  <div style="font-size:2rem">🛡️</div>
  <div class="name">GRACE</div>
  <div class="sub">GRC Engine</div>
</div>
""",
            unsafe_allow_html=True,
        )

    PAGE_KEYS = ["gap_analysis", "doc_gen", "dashboard", "registry", "library"]
    page = st.radio(
        t("sidebar.navigation"),
        PAGE_KEYS,
        format_func=lambda k: t(f"nav.{k}"),
        label_visibility="collapsed",
    )

    st.markdown("---")
    health = api_get("/health")
    if health:
        st.markdown(
            f'<span class="status-pill online">{t("sidebar.engine_online")}</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<span class="status-pill offline">{t("sidebar.engine_offline")}</span>',
            unsafe_allow_html=True,
        )
    st.caption(t("sidebar.api_label", api=API))


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

if page == "gap_analysis":
    page_hero(t("ga.header"), t("ga.intro"))

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown(f'<div class="section-sub">{t("ga.input")}</div>', unsafe_allow_html=True)

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

        input_methods = {"paste": t("ga.opt_paste"), "upload": t("ga.opt_upload"), "example": t("ga.opt_example")}
        input_method = st.radio(t("ga.doc_source"), list(input_methods.keys()),
                                format_func=lambda k: input_methods[k], horizontal=True)

        document_text = ""
        document_title = ""
        uploaded = None

        if input_method == "paste":
            document_title = st.text_input(t("ga.doc_title"), value="Security Policy v1.0")
            document_text = st.text_area(t("ga.doc_content"), height=200, placeholder=t("ga.paste_placeholder"))
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

        run_clicked = st.button(t("ga.run_button"), type="primary", use_container_width=True)

    with col2:
        st.markdown(f'<div class="section-sub">{t("ga.copilot_response")}</div>', unsafe_allow_html=True)
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
                    doc_result = api_post("/api/v1/documents/text",
                                          {"title": document_title, "content": document_text})

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
            overall_score = result.get("overall_coverage_score", 0)
            overall_status = result.get("overall_status","partial")
            color = "#16A34A" if overall_score >= 80 else "#EA580C" if overall_score >= 40 else "#DC2626"

            st.markdown(f"""
<div class="page-hero" style="margin-top:0">
  <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:8px">
    <div>
      <div style="font-weight:700;color:var(--primary);font-size:1.05rem">{selected_fw_name}</div>
      <div style="color:var(--text-dim);font-size:0.85rem">{document_title}</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:2rem;font-weight:700;color:{color};line-height:1">{overall_score}%</div>
      {status_badge(overall_status)}
    </div>
  </div>
  {score_bar(overall_score, color)}
  <div style="margin-top:10px;color:var(--text);font-size:0.9rem;line-height:1.5">
    {result.get('executive_summary','Assessment completed.')}
  </div>
</div>
""", unsafe_allow_html=True)

            controls = result.get("controls", [])
            for ctrl in controls:
                severity = ctrl.get("severity","medium")
                st.markdown(f"""
<div class="finding-card {severity}">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
    <div>
      <span class="ctrl-id">{ctrl.get('control_id','')}</span>
      <span class="ctrl-title"> · {ctrl.get('control_title','')}</span>
    </div>
    <div style="display:flex;gap:6px">
      {status_badge(ctrl.get('status','no_evidence'))}
      {severity_badge(severity)}
    </div>
  </div>
  <div class="finding-body">{ctrl.get('finding','')}</div>
  <div class="rem">
    <strong>{t('ga.remediation')}:</strong> {ctrl.get('remediation','')}
    <div class="reg-ref" style="margin-top:4px">{ctrl.get('regulatory_reference','')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

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

    with col2:
        st.markdown(f'<div class="section-sub">{t("dg.generated")}</div>', unsafe_allow_html=True)
        if gen_clicked:
            with st.spinner(t("dg.spinner", kind=doc_type_name)):
                resp = api_post("/api/v1/generate", {
                    "framework_id": fw_id, "doc_type": doc_type,
                    "context": context, "language": get_lang(),
                })

            if "error" in resp:
                st.error(resp["error"])
            else:
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

    cols = st.columns(5)
    metrics = [
        (t("db.kpi.open_findings"),  kpi.get("total_open_findings",0),            "📋"),
        (t("db.kpi.documents"),       kpi.get("documents_registered",0),            "📄"),
        (t("db.kpi.assessments"),     kpi.get("assessment_runs",0),                 "🧪"),
        (t("db.kpi.avg_coverage"),   f"{kpi.get('avg_coverage_score',0):.0f}%",    "📈"),
        (t("db.kpi.critical_open"),   kpi.get("by_severity",{}).get("critical",0), "🔴"),
    ]
    for i, (label, value, icon) in enumerate(metrics):
        cols[i].markdown(f"""
<div class="kpi-card">
  <div class="kpi-icon">{icon}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-label">{label}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f'<div class="section-sub">{t("db.status_distribution")}</div>', unsafe_allow_html=True)
        by_status = kpi.get("by_status",{})
        if by_status:
            for status, count in by_status.items():
                label = t(f"verdict_emoji.{status}") if status in ("compliant","partial","non_compliant","no_evidence") else status
                st.markdown(f"<div class='recent-row'><span class='doc-name'>{label}</span><span class='meta'>{count}</span></div>",
                            unsafe_allow_html=True)
        else:
            st.info(t("db.no_findings"))

    with col2:
        st.markdown(f'<div class="section-sub">{t("db.coverage_framework")}</div>', unsafe_allow_html=True)
        by_fw = kpi.get("by_framework",{})
        if by_fw:
            for fw, data in by_fw.items():
                score = data.get("avg_score",0) or 0
                color = "#16A34A" if score >= 80 else "#EA580C" if score >= 40 else "#DC2626"
                st.markdown(
                    f"<div style='margin-bottom:10px'>"
                    f"<div style='display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:4px'>"
                    f"<span style='font-weight:600;color:var(--primary)'>{fw}</span>"
                    f"<span style='color:var(--text-dim)'>" + t("db.findings_avg", count=data.get('count',0), score=f"{score:.0f}") + "</span>"
                    f"</div>"
                    f"{score_bar(score, color)}"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info(t("db.no_framework_data"))

    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{t("db.severity_breakdown")}</div>', unsafe_allow_html=True)
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
    FRAMEWORKS = ["ISO27001:2022","GDPR","SOC2","NIS2"]
    ALL = "__ALL__"

    col1, col2, col3 = st.columns(3)
    fw_filter = col1.selectbox(
        t("reg.framework"), [ALL] + FRAMEWORKS,
        format_func=lambda v: t("all") if v == ALL else v,
    )
    verdict_filter = col2.selectbox(
        t("reg.verdict"), [ALL] + VERDICTS,
        format_func=lambda v: t("all") if v == ALL else t(f"verdict.{v}"),
    )
    op_status_filter = col3.selectbox(
        t("reg.operational_status"), [ALL] + OP_STATUSES,
        format_func=lambda v: t("all") if v == ALL else t(f"opstatus.{v}"),
    )

    query = "/api/v1/findings?limit=100"
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
                    t("reg.update_op_status"), OP_STATUSES,
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
    page_hero(t("lib.header"), t("lib.intro"))

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
                ctrl_data = api_get(f"/api/v1/frameworks/{fw['id']}/controls")
                if ctrl_data:
                    controls = ctrl_data.get("controls",[])
                    st.markdown(t("lib.controls_loaded", n=len(controls)))
                    for ctrl in controls[:5]:
                        st.markdown(f"- **{ctrl['control_id']}** · {ctrl['title']}")
                    if len(controls) > 5:
                        st.caption(t("lib.more_controls", n=len(controls)-5))

                    st.markdown("---")
                    ctrl_ids = [c["control_id"] for c in controls]
                    selected_ctrl = st.selectbox(t("lib.explain_ctrl"), ctrl_ids, key=f"ctrl_{fw['id']}")
                    if st.button(t("lib.explain_button"), key=f"exp_{fw['id']}"):
                        with st.spinner(t("lib.explain_spinner")):
                            result = api_get(f"/api/v1/frameworks/{fw['id']}/controls/{selected_ctrl}/explain?language={get_lang()}")
                            if result:
                                st.markdown(result.get("explanation",""))
