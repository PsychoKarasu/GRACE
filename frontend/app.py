"""
GRACE Prototype — Streamlit Frontend
Professional GRC demo UI: Gap Analysis, Document Generation, Dashboard
"""
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

API = "http://localhost:8000"

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
.finding-card.medium   { border-left-color: #D97706; }
.finding-card.low      { border-left-color: #059669; }

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
    label = status.replace("_"," ").title()
    return f'<span class="badge-{style}">{icon} {label}</span>'

def severity_badge(severity: str) -> str:
    styles = {"critical":"red","high":"amber","medium":"amber","low":"green"}
    style = styles.get(severity, "gray")
    return f'<span class="badge-{style}">{severity.upper()}</span>'

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
        r = requests.post(f"{API}{path}", json=data, timeout=120)
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

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Microsoft_logo.svg/320px-Microsoft_logo.svg.png", width=80)
    st.markdown("**Microsoft Copilot** *(simulated)*")
    st.markdown("---")
    page = st.radio("Navigation", [
        "🔍 Gap Analysis",
        "📄 Document Generation",
        "📊 Governance Dashboard",
        "🗂️ Finding Registry",
        "📚 Framework Library",
    ])
    st.markdown("---")
    health = api_get("/health")
    if health:
        st.success("🟢 GRACE Engine: Online")
    else:
        st.error("🔴 GRACE Engine: Offline")
    st.caption("API: localhost:8000")


# ════════════════════════════════════════════════════════════════
# PAGE: GAP ANALYSIS
# ════════════════════════════════════════════════════════════════

if page == "🔍 Gap Analysis":
    st.header("Gap Analysis")
    st.markdown("*Simulate a Copilot interaction: upload a document and receive a structured compliance assessment.*")

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("📋 Input")

        # Framework selection
        fw_data = api_get("/api/v1/frameworks")
        fw_options = {}
        if fw_data:
            for fw in fw_data.get("frameworks", []):
                if not fw.get("coming_soon"):
                    fw_options[fw["name"]] = fw["id"]
                else:
                    fw_options[f"{fw['name']} *(coming soon)*"] = None

        selected_fw_name = st.selectbox("Select framework", list(fw_options.keys()))
        selected_fw_id   = fw_options.get(selected_fw_name)

        if not selected_fw_id:
            st.info("This framework will be available in Phase 3 of the GRACE rollout.")
            st.stop()

        # Document input method
        input_method = st.radio("Document source", ["Paste text", "Upload file", "Use example policy"])

        document_text = ""
        document_title = ""

        if input_method == "Paste text":
            document_title = st.text_input("Document title", value="Security Policy v1.0")
            document_text = st.text_area("Paste document content", height=200,
                placeholder="Paste your policy, procedure or standard here...")

        elif input_method == "Upload file":
            uploaded = st.file_uploader("Upload PDF or DOCX", type=["pdf","docx","txt"])
            if uploaded:
                document_title = uploaded.name

        elif input_method == "Use example policy":
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
            choice = st.selectbox("Choose example document", list(examples.keys()))
            document_title = choice
            document_text  = examples[choice]
            st.text_area("Document preview", document_text, height=150, disabled=True)

        # Run button
        run_clicked = st.button("🚀 Run Gap Analysis", type="primary", use_container_width=True)

    with col2:
        st.subheader("📡 GRACE · Copilot Response")
        result_container = st.container()

    if run_clicked:
        if not document_text and input_method != "Upload file":
            st.warning("Please provide document content.")
            st.stop()

        with result_container:
            with st.spinner("Registering document..."):
                if input_method == "Upload file" and uploaded:
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
                    st.error(f"Document registration failed: {doc_result}")
                    st.stop()
                doc_id = doc_result["document_id"]

            with st.spinner("🤖 Claude is analyzing your document against the framework..."):
                assessment = api_post("/api/v1/assessments/run-sync", {
                    "document_id": doc_id,
                    "framework": selected_fw_id,
                    "channel": "web_demo"
                })

            if "error" in assessment:
                st.error(f"Assessment failed: {assessment['error']}")
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
<strong>Remediation:</strong> {ctrl.get('remediation','')} &nbsp;|&nbsp;
<span style="color:#6B7280">{ctrl.get('regulatory_reference','')}</span>
</div>
</div>
""", unsafe_allow_html=True)

            # ── Evidence required ──
            with st.expander("📋 Evidence required for full compliance"):
                for ctrl in controls:
                    if ctrl.get("evidence_required"):
                        st.markdown(f"**{ctrl.get('control_id')} — {ctrl.get('control_title')}**")
                        for ev in ctrl.get("evidence_required", []):
                            st.markdown(f"  - {ev}")


# ════════════════════════════════════════════════════════════════
# PAGE: DOCUMENT GENERATION
# ════════════════════════════════════════════════════════════════

elif page == "📄 Document Generation":
    st.header("Document Generation")
    st.markdown("*Generate audit-ready compliance documents using Claude AI.*")

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.subheader("Configure")
        fw_data = api_get("/api/v1/frameworks")
        fw_options = {}
        if fw_data:
            for fw in fw_data.get("frameworks", []):
                if not fw.get("coming_soon"):
                    fw_options[fw["name"]] = fw["id"]

        doc_types = {
            "Information Security Policy": "policy",
            "Data Processing Agreement (GDPR Art.28)": "dpa",
            "Statement of Applicability (SoA)": "soa",
        }

        doc_type_name = st.selectbox("Document type", list(doc_types.keys()))
        doc_type      = doc_types[doc_type_name]
        fw_name       = st.selectbox("Framework", list(fw_options.keys()))
        fw_id         = fw_options[fw_name]
        organization  = st.text_input("Organization name", "Brightstar Ltd")
        language      = st.selectbox("Language", ["en","it"])

        context = {"organization": organization, "doc_type": doc_type}
        if doc_type == "dpa":
            context["controller"] = organization
            context["processor"]  = st.text_input("Processor / Vendor name", "CloudVendor Srl")
            context["purpose"]    = st.text_input("Processing purpose", "HR management system")
        elif doc_type == "policy":
            context["scope"] = st.text_input("Policy scope", "All employees and contractors")
        elif doc_type == "soa":
            context["scope"] = st.text_input("ISMS scope", "All IT systems and data processing")

        gen_clicked = st.button("✍️ Generate Document", type="primary", use_container_width=True)

    with col2:
        st.subheader("Generated Document")
        if gen_clicked:
            with st.spinner(f"Claude is generating your {doc_type_name}..."):
                resp = api_post("/api/v1/generate", {
                    "framework_id": fw_id,
                    "doc_type": doc_type,
                    "context": context,
                    "language": language
                })

            if "error" in resp:
                st.error(resp["error"])
            else:
                content = resp.get("content","")
                st.success("✅ Document generated and saved")
                st.markdown(content)
                st.download_button("⬇️ Download as Markdown",
                                    data=content,
                                    file_name=f"GRACE_{doc_type}_{fw_id}.md",
                                    mime="text/markdown")
        else:
            st.info("Configure the document and click Generate.")


# ════════════════════════════════════════════════════════════════
# PAGE: GOVERNANCE DASHBOARD
# ════════════════════════════════════════════════════════════════

elif page == "📊 Governance Dashboard":
    st.header("Governance Dashboard")
    st.markdown("*Live view of compliance posture — simulates the XSOAR dashboard.*")

    kpi = api_get("/api/v1/kpi/summary")
    if not kpi:
        st.warning("No data yet. Run some gap analyses first.")
        st.stop()

    # Top KPIs
    cols = st.columns(5)
    metrics = [
        ("Open Findings",   kpi.get("total_open_findings",0),        None),
        ("Documents",        kpi.get("documents_registered",0),        None),
        ("Assessments Run",  kpi.get("assessment_runs",0),             None),
        ("Avg Coverage",    f"{kpi.get('avg_coverage_score',0):.0f}%", None),
        ("Critical Open",    kpi.get("by_severity",{}).get("critical",0), "🔴"),
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
        st.subheader("Compliance Status Distribution")
        by_status = kpi.get("by_status",{})
        if by_status:
            status_labels = {"compliant":"✅ Compliant","partial":"⚠️ Partial",
                             "non_compliant":"❌ Non-compliant","no_evidence":"❓ No evidence"}
            for status, count in by_status.items():
                label = status_labels.get(status, status)
                st.markdown(f"**{label}** — {count}")
        else:
            st.info("No findings yet.")

    with col2:
        st.subheader("Coverage by Framework")
        by_fw = kpi.get("by_framework",{})
        if by_fw:
            for fw, data in by_fw.items():
                score = data.get("avg_score",0) or 0
                color = "#059669" if score >= 80 else "#D97706" if score >= 40 else "#DC2626"
                st.markdown(f"**{fw}** — {data.get('count',0)} findings · avg {score:.0f}%")
                st.markdown(score_bar(score, color), unsafe_allow_html=True)
                st.markdown("")
        else:
            st.info("No framework data yet.")

    st.markdown("---")
    st.subheader("Severity Breakdown")
    by_sev = kpi.get("by_severity",{})
    sev_order = ["critical","high","medium","low"]
    sev_colors = {"critical":"#DC2626","high":"#EA580C","medium":"#D97706","low":"#059669"}
    if by_sev:
        cols = st.columns(len(sev_order))
        for i, sev in enumerate(sev_order):
            count = by_sev.get(sev,0)
            cols[i].markdown(f"""
<div class="kpi-card">
<div class="kpi-value" style="color:{sev_colors[sev]}">{count}</div>
<div class="kpi-label">{sev.upper()}</div>
</div>""", unsafe_allow_html=True)
    else:
        st.info("No severity data yet.")


# ════════════════════════════════════════════════════════════════
# PAGE: FINDING REGISTRY
# ════════════════════════════════════════════════════════════════

elif page == "🗂️ Finding Registry":
    st.header("Finding Registry")
    st.markdown("*All findings — simulates the XSOAR incident queue.*")

    col1, col2, col3 = st.columns(3)
    fw_filter  = col1.selectbox("Framework", ["All","ISO27001:2022","GDPR","SOC2"])
    sts_filter = col2.selectbox("Status", ["All","non_compliant","partial","compliant","no_evidence"])

    findings = api_get(
        f"/api/v1/findings?framework={fw_filter if fw_filter!='All' else ''}"
        f"&status={sts_filter if sts_filter!='All' else ''}&limit=50"
    )

    if not findings or not findings.get("findings"):
        st.info("No findings yet. Run a Gap Analysis first.")
    else:
        items = findings["findings"]
        st.markdown(f"**{len(items)} finding(s)**")
        for f in items:
            severity = f.get("severity","medium")
            with st.expander(
                f"[{f.get('framework','')}] {f.get('control_id','')} · "
                f"{f.get('control_title','')[:60]} — {severity.upper()}"
            ):
                cols = st.columns([2,1,1])
                cols[0].markdown(f"**Finding:**  \n{f.get('description','')}")
                cols[1].markdown(f"**Status:**  \n{f.get('compliance_status','')}")
                cols[2].markdown(f"**Operational:**  \n{f.get('operational_status','')}")

                st.markdown(f"**Remediation:** {f.get('recommended_action','')}")
                st.markdown(f"*{f.get('regulatory_reference','')}*")

                new_status = st.selectbox(
                    "Update operational status",
                    ["new","acknowledged","in_progress","resolved","accepted_risk"],
                    key=f"status_{f['finding_id']}"
                )
                if st.button("Update", key=f"upd_{f['finding_id']}"):
                    resp = requests.patch(
                        f"{API}/api/v1/findings/{f['finding_id']}/status",
                        json={"operational_status": new_status}
                    )
                    if resp.ok:
                        st.success("Status updated")
                        st.rerun()


# ════════════════════════════════════════════════════════════════
# PAGE: FRAMEWORK LIBRARY
# ════════════════════════════════════════════════════════════════

elif page == "📚 Framework Library":
    st.header("Framework Library")
    st.markdown("*25 international frameworks — P0 frameworks active in this prototype.*")

    fw_data = api_get("/api/v1/frameworks")
    if not fw_data:
        st.error("Cannot reach GRACE API")
        st.stop()

    for fw in fw_data.get("frameworks",[]):
        coming_soon = fw.get("coming_soon", False)
        status_tag = "🚧 Coming Phase 3" if coming_soon else "✅ Active"
        with st.expander(f"**{fw['name']}** — {fw['controls']} controls · {status_tag}"):
            col1, col2 = st.columns([2,1])
            col1.markdown(f"**Category:** {fw['category']}  \n**Priority:** {fw['priority']}")
            col2.markdown(f"**Controls:** {fw['controls']}")

            if not coming_soon:
                # Show controls
                ctrl_data = api_get(f"/api/v1/frameworks/{fw['id']}/controls")
                if ctrl_data:
                    controls = ctrl_data.get("controls",[])
                    st.markdown(f"*{len(controls)} controls loaded in prototype*")
                    for ctrl in controls[:5]:
                        st.markdown(f"- **{ctrl['control_id']}** · {ctrl['title']}")
                    if len(controls) > 5:
                        st.caption(f"+ {len(controls)-5} more controls...")

                    # Explain a control
                    st.markdown("---")
                    ctrl_ids = [c["control_id"] for c in controls]
                    selected_ctrl = st.selectbox("Explain a control", ctrl_ids, key=f"ctrl_{fw['id']}")
                    if st.button("🤖 Explain with Claude", key=f"exp_{fw['id']}"):
                        with st.spinner("Getting plain-language explanation..."):
                            result = api_get(f"/api/v1/frameworks/{fw['id']}/controls/{selected_ctrl}/explain")
                            if result:
                                st.markdown(result.get("explanation",""))
