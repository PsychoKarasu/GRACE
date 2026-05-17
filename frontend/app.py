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
        "nav.gap_analysis":           "Gap Analysis",
        "nav.doc_gen":                "Document Generation",
        "nav.dashboard":              "Governance Dashboard",
        "nav.registry":               "Finding Registry",
        "nav.library":                "Framework Library",
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
        "nav.gap_analysis":           "Analisi dei Gap",
        "nav.doc_gen":                "Generazione Documenti",
        "nav.dashboard":              "Dashboard Governance",
        "nav.registry":               "Registro Findings",
        "nav.library":                "Libreria Framework",
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
/* Open-state dropdown items: flag-by-position (1st option = EN, 2nd = IT). */
[data-baseweb="popover"] li {{
  background-repeat: no-repeat !important;
  background-position: 12px center !important;
  background-size: 18px 12px !important;
  padding-left: 38px !important;
  font-family: var(--font-display) !important;
  font-weight: 600 !important;
  letter-spacing: 0.6px !important;
}}
[data-baseweb="popover"] li:nth-child(1) {{
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'><rect width='60' height='40' fill='%23B22234'/><rect y='3.1' width='60' height='3.1' fill='%23fff'/><rect y='9.3' width='60' height='3.1' fill='%23fff'/><rect y='15.5' width='60' height='3.1' fill='%23fff'/><rect y='21.7' width='60' height='3.1' fill='%23fff'/><rect y='27.9' width='60' height='3.1' fill='%23fff'/><rect y='34.1' width='60' height='3.1' fill='%23fff'/><rect width='24' height='21.5' fill='%233C3B6E'/></svg>") !important;
}}
[data-baseweb="popover"] li:nth-child(2) {{
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 3 2'><rect width='1' height='2' x='0' fill='%23009246'/><rect width='1' height='2' x='1' fill='%23fff'/><rect width='1' height='2' x='2' fill='%23CE2B37'/></svg>") !important;
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
  padding: 18px 10px 20px;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--border-soft);
  text-align: center;
}}
.grace-side-brand-compact .brand-symbol {{
  width: 96px; height: 96px;
  object-fit: contain;
  filter: drop-shadow(0 3px 8px rgba(15,31,61,0.22));
  display: block;
}}
.grace-side-brand-compact .brand-symbol-fallback {{
  font-size: 4.4rem; line-height: 1;
}}
.grace-side-brand-compact .brand-name {{
  font-family: var(--font-display);
  font-size: 1.72rem; font-weight: 800;
  color: var(--logo-text);
  letter-spacing: 4px;
  margin-top: 4px;
  line-height: 1;
}}
.grace-side-brand-compact .brand-tagline {{
  font-family: var(--font-display);
  font-size: 0.74rem; font-weight: 600;
  letter-spacing: 0.5px;
  color: var(--text-dim);
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
        "gap_analysis": t("nav.gap_analysis"),
        "doc_gen":      t("nav.doc_gen"),
        "dashboard":    t("nav.dashboard"),
        "registry":     t("nav.registry"),
        "library":      t("nav.library"),
    }
    _crumb_current = _crumb_labels.get(
        st.session_state.get("current_page", "gap_analysis"),
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
    # Single dropdown with inline-SVG flag icons (Unicode flag emojis
    # don't render reliably on Windows). The wrapper carries a class
    # that signals the active language to CSS, which then paints the
    # correct flag onto the selectbox's closed-state value.
    current_lang = st.session_state.get("language", "en")
    wrap_cls = f"grace-lang-wrap lang-selected-{current_lang}"
    st.markdown(f'<div class="{wrap_cls}">', unsafe_allow_html=True)
    st.selectbox(
        t("topbar.language"),
        options=["en", "it"],
        format_func=lambda k: "EN" if k == "en" else "IT",
        key="language",
        label_visibility="collapsed",
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

PAGE_KEYS = ["gap_analysis", "doc_gen", "dashboard", "registry", "library"]
# Inline SVG icons (lucide-style outline) used by the sidebar nav and
# elsewhere. Kept tiny so they ship inside the stylesheet without
# external HTTP. Single-stroke, no fills, currentColor — they inherit
# the active/inactive accent automatically.
def _nav_icon_svg(name: str) -> str:
    paths = {
        "gap_analysis": "<circle cx='10' cy='10' r='6'/><line x1='14.5' y1='14.5' x2='19' y2='19'/>",
        "doc_gen":      "<path d='M5 3h9l5 5v13H5z'/><path d='M14 3v5h5'/><line x1='8' y1='13' x2='16' y2='13'/><line x1='8' y1='16' x2='14' y2='16'/>",
        "dashboard":    "<line x1='4' y1='19' x2='4' y2='11'/><line x1='10' y1='19' x2='10' y2='5'/><line x1='16' y1='19' x2='16' y2='14'/><line x1='3' y1='19' x2='21' y2='19'/>",
        "registry":     "<line x1='6' y1='6' x2='20' y2='6'/><line x1='6' y1='12' x2='20' y2='12'/><line x1='6' y1='18' x2='20' y2='18'/><circle cx='3' cy='6' r='1.2'/><circle cx='3' cy='12' r='1.2'/><circle cx='3' cy='18' r='1.2'/>",
        "library":      "<path d='M4 5a2 2 0 0 1 2-2h6v18H6a2 2 0 0 1-2-2z'/><path d='M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6z'/>",
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

                set_avatar_state(AvatarState.ANALYZING)
                with st.spinner(t("ga.analyzing")):
                    assessment = api_post("/api/v1/assessments/run-sync", {
                        "document_id": doc_id,
                        "framework": selected_fw_id,
                        "channel": "web_demo",
                        "language": get_lang(),
                    })

                if "error" in assessment:
                    set_avatar_state(AvatarState.ERROR)
                    st.session_state["avatar_message"] = (
                        "I couldn't complete the assessment. Check the document and try again."
                        if get_lang() == "en" else
                        "Non sono riuscita a completare l'analisi. Controlla il documento e riprova."
                    )
                    st.error(t("ga.assessment_failed", detail=assessment['error']))
                    st.stop()

                result = assessment.get("result", {})
                overall_score = result.get("overall_coverage_score", 0)
                overall_status = result.get("overall_status","partial")
                # Map result → avatar mood + a dynamic, score-aware line.
                _lang = get_lang()
                if overall_score >= 80:
                    set_avatar_state(AvatarState.SUCCESS)
                    st.session_state["avatar_message"] = (
                        f"Solid coverage at {overall_score}%. Let's review the strong points and the residual gaps."
                        if _lang == "en" else
                        f"Copertura solida al {overall_score}%. Vediamo i punti di forza e i gap residui."
                    )
                elif overall_score < 40:
                    set_avatar_state(AvatarState.WARNING)
                    st.session_state["avatar_message"] = (
                        f"Only {overall_score}% coverage — several gaps to address. Open the findings below, critical-first."
                        if _lang == "en" else
                        f"Solo {overall_score}% di copertura — diversi gap da affrontare. Apri i finding qui sotto, partendo dai critici."
                    )
                else:
                    set_avatar_state(AvatarState.ATTENTIVE)
                    st.session_state["avatar_message"] = (
                        f"Partial coverage at {overall_score}%. Plenty of room to harden — let's prioritise the medium/high severity items."
                        if _lang == "en" else
                        f"Copertura parziale al {overall_score}%. C'è margine — prioritizziamo i finding medi/alti."
                    )
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
        FRAMEWORKS = ["ISO27001:2022","GDPR","SOC2","NIS2"]
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
                        # The backend lazily translates the user-facing fields
                        # to the requested UI language and caches the result,
                        # so no "Generated in IT" chip is needed any more.
                        st.markdown(
                            f"<div class='finding-card {severity}'>"
                            f"<div style='display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap'>"
                            f"<div><span class='ctrl-id'>{f.get('control_id','')}</span>"
                            f"<span class='ctrl-title'> · {f.get('control_title','')}</span></div>"
                            f"<div style='display:flex;gap:6px'>"
                            f"{status_badge(f.get('compliance_status','no_evidence'))}"
                            f"{severity_badge(severity)}"
                            f"</div></div>"
                            f"<div class='finding-body'>{f.get('description','')}</div>"
                            f"<div class='rem'><strong>{t('reg.remediation')}:</strong> {f.get('recommended_action','')}"
                            f"<div class='reg-ref' style='margin-top:4px'>{f.get('regulatory_reference','')}</div>"
                            f"</div></div>",
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
