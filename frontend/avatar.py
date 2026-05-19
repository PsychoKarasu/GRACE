"""
GRACE Virtual Analyst — Avatar Subsystem
========================================

A modular SVG-based virtual analyst that lives in the GRACE UI.
Original anime-inspired character (NOT a copy of any existing IP),
designed for a Governance, Risk, Assurance & Compliance Engine.

Public API
----------
    AvatarState              enum of supported behavioural states
    render_avatar(state, …)  returns a string with the full SVG + CSS
    state_for_page(page)     maps a Streamlit page name to a default state
    set_state(new_state)     stores the next state in st.session_state

The module is structured as a single file but conceptually split into:

    [TOKENS]    palette + design tokens derived from GRACE brand
    [STATE]     AvatarState + state machine + UI event mapping
    [STYLES]    CSS keyframes + per-state activation rules
    [RENDERER]  SVG markup builder (layered groups)

Streamlit limitations: we cannot push events to a running SVG from
the Python side without a custom component. The state machine is
therefore resolved on every rerun — `render_avatar(state)` re-injects
the SVG with the appropriate state class, and CSS animations take
over from there. This is enough for the polished, restrained motion
the design brief calls for.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

import streamlit as st


# ─── [TOKENS] ─────────────────────────────────────────────────────────
# Palette derived from the GRACE logo (navy + teal + neutrals).

TOKENS = {
    # Hair / outline — richer cobalt with stronger hilite/shadow split.
    # The previous tones sat in the same range as the page background
    # and read as flat; widened the dynamic range so the strands look
    # glossy and read clearly off the deep-navy frame.
    "hair_base":     "#2A5AB8",
    "hair_shadow":   "#1A3B7A",
    "hair_hilite":   "#4880D8",
    "outline":       "#08152A",
    # Skin — warmer, more saturated peach; the previous beige read
    # as washed-out under the frame's glow overlay (now removed).
    "skin":          "#FFD0A8",
    "skin_shadow":   "#EAA67E",
    "blush":         "#F88774",
    # Eyes — vivid aqua iris with a deep teal mid-tone for depth.
    "eye_white":     "#FFFFFF",
    "iris":          "#28D2EA",
    "iris_dark":     "#0F4A6E",
    "iris_hilite":   "#FFFFFF",
    "brow":          "#1A2B52",
    # Mouth — saturated coral red, no muted brown-pink.
    "lip":           "#DA4A3F",
    # Outfit — richer cobalt with high-contrast highlights, crisp white
    # blouse, ice-cyan accent pin that stands out from the jacket.
    "blouse":        "#FFFFFF",
    "blouse_shadow": "#D2DCE6",
    "jacket":        "#2D63B5",
    "jacket_shadow": "#163A78",
    "jacket_collar": "#4078CE",
    "accent_pin":    "#5CE3F8",
    "pin_core":      "#163A78",
    # Halo — bright ice cyan, used only behind the bust (not as overlay).
    "halo":          "#5CE3F8",
}


# ─── [STATE] ──────────────────────────────────────────────────────────

class AvatarState(str, Enum):
    """Behavioural states. The string value is also the CSS class.

    Priority for the resolver (higher wins when multiple signals fire
    in the same script run):

        ERROR > ANALYZING (loading) > THINKING > SUCCESS > WARNING >
        READY > GUIDANCE > ATTENTIVE > SPEAKING > IDLE
    """
    IDLE      = "idle"
    ATTENTIVE = "attentive"
    GUIDANCE  = "guidance"        # Required input still missing
    READY     = "ready"           # All inputs present, action enabled
    THINKING  = "thinking"        # Loading — document generation
    ANALYZING = "analyzing"       # Loading — gap analysis ("loading-analysis")
    SUCCESS   = "success"         # Action completed successfully
    WARNING   = "warning"         # Soft warning (e.g. partial coverage)
    ERROR     = "error"           # Action failed
    SPEAKING  = "speaking"        # Generic talking state


# Numeric priority — higher value preempts lower.
STATE_PRIORITY = {
    AvatarState.ERROR:     100,
    AvatarState.ANALYZING:  90,
    AvatarState.THINKING:   90,
    AvatarState.SUCCESS:    80,
    AvatarState.WARNING:    70,
    AvatarState.READY:      60,
    AvatarState.GUIDANCE:   50,
    AvatarState.ATTENTIVE:  40,
    AvatarState.SPEAKING:   30,
    AvatarState.IDLE:        0,
}


def resolve_state(*candidates: AvatarState) -> AvatarState:
    """Return the highest-priority state out of the provided candidates.
    None entries are ignored; falls back to IDLE if nothing is passed."""
    valid = [c for c in candidates if isinstance(c, AvatarState)]
    if not valid:
        return AvatarState.IDLE
    return max(valid, key=lambda s: STATE_PRIORITY.get(s, 0))


# UI event → default avatar state mapping. The page renderer can override
# the resolved state at any point (e.g. after an API call returns success).
PAGE_DEFAULT_STATE = {
    "ask_grace":    AvatarState.ATTENTIVE,
    "gap_analysis": AvatarState.ATTENTIVE,
    "doc_gen":      AvatarState.ATTENTIVE,
    "dashboard":    AvatarState.IDLE,
    "registry":     AvatarState.IDLE,
    "library":      AvatarState.IDLE,
}

# Contextual lines spoken by the avatar — keyed by (page, state, lang).
# `compose_message()` resolves the right one, with progressive fallback:
# (page, state, lang) → (page, IDLE, lang) → ("*", state, lang) → "".
MESSAGES = {
    # ─── English ────────────────────────────────────────────────
    # Gap Analysis
    ("gap_analysis", AvatarState.IDLE,      "en"): "Ask me to analyse a document, explain a finding, or query results in plain language. Attach files or paste text to add context.",
    ("gap_analysis", AvatarState.GUIDANCE,  "en"): "Type a question, or attach a document and pick a framework to run an analysis.",
    ("gap_analysis", AvatarState.ATTENTIVE, "en"): "Ready when you are. Describe what you need or add context — I'll route it.",
    ("gap_analysis", AvatarState.READY,     "en"): "All set. Click Ask GRACE to dispatch.",
    ("gap_analysis", AvatarState.ANALYZING, "en"): "Working on it — reading your context and routing to the right pipeline…",
    ("gap_analysis", AvatarState.SUCCESS,   "en"): "Done. Check the response panel on the right. Open Finding Registry for the full triage.",
    ("gap_analysis", AvatarState.WARNING,   "en"): "Several gaps detected — let's walk through them together, severity-first.",
    ("gap_analysis", AvatarState.ERROR,     "en"): "Couldn't complete the request. Check the input, the framework, or the service status.",

    # Document Generation
    ("doc_gen",      AvatarState.IDLE,      "en"): "Tell me the framework and document type — I'll draft it audit-ready.",
    ("doc_gen",      AvatarState.GUIDANCE,  "en"): "Choose a framework and a document type, then add a sentence of context.",
    ("doc_gen",      AvatarState.ATTENTIVE, "en"): "Add a few words of context (scope, sector, tools) to make the draft more accurate.",
    ("doc_gen",      AvatarState.READY,     "en"): "Inputs look good. Click Generate when you're ready.",
    ("doc_gen",      AvatarState.THINKING,  "en"): "Drafting your document — selecting clauses, citing references…",
    ("doc_gen",      AvatarState.SUCCESS,   "en"): "Draft is ready in the right panel. Read it end-to-end and tailor it to your organisation before publishing.",
    ("doc_gen",      AvatarState.ERROR,     "en"): "The generator hit an issue. Try again or simplify the context.",

    # Ask GRACE (chat)
    ("ask_grace",    AvatarState.IDLE,      "en"): "Open a chat to ask me anything — explain a control, map two documents, summarise findings. Conversations are saved.",
    ("ask_grace",    AvatarState.GUIDANCE,  "en"): "Click + New chat to start, then ask a question or attach evidence.",
    ("ask_grace",    AvatarState.ATTENTIVE, "en"): "I'm listening. Type your question below — I'll keep the thread.",
    ("ask_grace",    AvatarState.READY,     "en"): "Ready when you are.",
    ("ask_grace",    AvatarState.ANALYZING, "en"): "Thinking through it now…",
    ("ask_grace",    AvatarState.SUCCESS,   "en"): "Done — see the reply above. Ask a follow-up or open Gap Analysis for a structured run.",
    ("ask_grace",    AvatarState.ERROR,     "en"): "Couldn't reach the model. Check the backend status and retry.",

    # Other pages
    ("dashboard",    AvatarState.IDLE,      "en"): "Here's the live picture of your compliance posture. Click any KPI for the filtered registry view.",
    ("registry",     AvatarState.IDLE,      "en"): "Findings grouped by source document. Update the operational status as you triage.",
    ("library",      AvatarState.IDLE,      "en"): "Pick a framework to explore its controls. Ask me to explain any of them in plain language.",

    # ─── Italiano ───────────────────────────────────────────────
    ("gap_analysis", AvatarState.IDLE,      "it"): "Chiedimi di analizzare un documento, spiegare un finding o interrogare risultati in linguaggio naturale. Allega file o incolla testo per aggiungere contesto.",
    ("gap_analysis", AvatarState.GUIDANCE,  "it"): "Scrivi una domanda, oppure allega un documento e scegli un framework per lanciare un'analisi.",
    ("gap_analysis", AvatarState.ATTENTIVE, "it"): "Sono pronta. Descrivi cosa ti serve o aggiungi contesto — instrado io.",
    ("gap_analysis", AvatarState.READY,     "it"): "Tutto pronto. Clicca Chiedi a GRACE per inviare.",
    ("gap_analysis", AvatarState.ANALYZING, "it"): "Sto lavorando — leggo il tuo contesto e instrado verso la pipeline giusta…",
    ("gap_analysis", AvatarState.SUCCESS,   "it"): "Fatto. Guarda il pannello di risposta a destra. Apri il Registro Findings per il triage completo.",
    ("gap_analysis", AvatarState.WARNING,   "it"): "Ho trovato diversi gap — li affrontiamo per severità, partendo dai critici.",
    ("gap_analysis", AvatarState.ERROR,     "it"): "Non sono riuscita a completare la richiesta. Controlla l'input, il framework o lo stato del servizio.",

    ("doc_gen",      AvatarState.IDLE,      "it"): "Dimmi framework e tipo di documento — lo redigo audit-ready.",
    ("doc_gen",      AvatarState.GUIDANCE,  "it"): "Scegli un framework e un tipo di documento, poi aggiungi una frase di contesto.",
    ("doc_gen",      AvatarState.ATTENTIVE, "it"): "Aggiungi qualche riga di contesto (scope, settore, tool) per rendere il draft più accurato.",
    ("doc_gen",      AvatarState.READY,     "it"): "Input ok. Clicca Genera quando vuoi.",
    ("doc_gen",      AvatarState.THINKING,  "it"): "Sto redigendo — seleziono le clausole, cito i riferimenti…",
    ("doc_gen",      AvatarState.SUCCESS,   "it"): "Il draft è pronto nel pannello a destra. Rileggilo per intero e adattalo alla tua organizzazione prima di pubblicare.",
    ("doc_gen",      AvatarState.ERROR,     "it"): "Il generatore ha riscontrato un problema. Riprova o semplifica il contesto.",

    ("ask_grace",    AvatarState.IDLE,      "it"): "Apri una chat per chiedermi qualunque cosa — spiegare un controllo, mappare due documenti, riassumere i finding. Le conversazioni si salvano.",
    ("ask_grace",    AvatarState.GUIDANCE,  "it"): "Clicca + Nuova chat per iniziare, poi fai una domanda o allega evidenze.",
    ("ask_grace",    AvatarState.ATTENTIVE, "it"): "Ti ascolto. Scrivi la domanda qui sotto — mantengo il thread.",
    ("ask_grace",    AvatarState.READY,     "it"): "Pronta quando vuoi.",
    ("ask_grace",    AvatarState.ANALYZING, "it"): "Sto pensando…",
    ("ask_grace",    AvatarState.SUCCESS,   "it"): "Fatto — leggi la risposta sopra. Fai una follow-up o apri Analisi dei Gap per un run strutturato.",
    ("ask_grace",    AvatarState.ERROR,     "it"): "Non sono riuscita a raggiungere il modello. Controlla lo stato del backend e riprova.",

    ("dashboard",    AvatarState.IDLE,      "it"): "Ecco la fotografia live della tua compliance. Clicca un KPI per la vista filtrata.",
    ("registry",     AvatarState.IDLE,      "it"): "Finding raggruppati per documento sorgente. Aggiorna lo stato operativo durante il triage.",
    ("library",      AvatarState.IDLE,      "it"): "Scegli un framework per esplorarne i controlli. Posso spiegartene uno qualsiasi a parole semplici.",
}


def compose_message(page: Optional[str], state: AvatarState, lang: str = "en") -> str:
    """Resolve the right line for the current (page, state, lang).

    Falls back to (page, IDLE) then to an empty string if nothing matches —
    callers can also override with an explicit `message=` to render_avatar.
    """
    lang = lang if lang in ("en", "it") else "en"
    candidates = [
        (page, state, lang),
        (page, AvatarState.IDLE, lang),
    ]
    for c in candidates:
        if c in MESSAGES:
            return MESSAGES[c]
    return ""


def state_for_page(page_key: str) -> AvatarState:
    return PAGE_DEFAULT_STATE.get(page_key, AvatarState.IDLE)


def get_state() -> AvatarState:
    s = st.session_state.get("avatar_state")
    if isinstance(s, AvatarState):
        return s
    if isinstance(s, str):
        try:
            return AvatarState(s)
        except ValueError:
            pass
    return AvatarState.IDLE


def set_state(new_state: AvatarState) -> None:
    """Store the next avatar state. Read on the next rerun."""
    st.session_state["avatar_state"] = (
        new_state.value if isinstance(new_state, AvatarState) else str(new_state)
    )


# ─── [STYLES] ─────────────────────────────────────────────────────────

def _css() -> str:
    """CSS injected with the SVG. Animations are state-gated via
    `.grace-avatar.state-<name>` selectors on the root SVG.

    Design notes (premium-enterprise look):
    - Frame uses a DEEP navy that sits darker than the page bg, so the
      character pops instead of merging into the surrounding dark-mode
      navy. No teal in the base gradient.
    - No full-card overlay: the previous radial-gradient with 0.42 alpha
      teal veiled the colours. The accent glow is now LOCALISED to the
      top quarter of the frame.
    - Border is a single hairline accent + a precise outer ring shadow.
    - Typography hierarchy: name (largest, white, tight tracking) →
      role (smaller, ice-blue, secondary) → badge (vivid accent pill).
    - Card depth via layered, non-fuzzy shadows.
    """
    return f"""
<style>
:root {{
  --av-ink-1: #08172E;
  --av-ink-2: #0E2548;
  --av-ink-3: #122D5C;
  --av-line: #4EC6D9;
  --av-line-soft: rgba(78,198,217,0.35);
  --av-text-1: #F2FAFF;
  --av-text-2: #BFD8E8;
  --av-accent: #5CE3F8;
  --av-accent-soft: rgba(92,227,248,0.18);
}}
.grace-avatar-frame {{
  display: flex; flex-direction: column; align-items: center;
  padding: 24px 18px 21px;
  /* Deep, fully opaque navy gradient — sits BELOW the page bg tone
     so the avatar reads as foreground content, not blended chrome. */
  background:
    radial-gradient(ellipse 60% 35% at 50% 12%, rgba(92,227,248,0.22) 0%, transparent 70%),
    linear-gradient(180deg, var(--av-ink-3) 0%, var(--av-ink-1) 100%);
  border: 1px solid var(--av-line);
  border-radius: 22px;
  position: relative;
  margin-bottom: 14px;
  box-shadow:
    0 0 0 1px rgba(92,227,248,0.18),
    0 14px 38px rgba(0,0,0,0.55),
    0 3px 9px rgba(0,0,0,0.45),
    inset 0 1px 0 rgba(255,255,255,0.08);
  overflow: hidden;
  isolation: isolate;
}}
/* Subtle, very slow shimmer along the border — adds 'alive' without
   gaming-glow. The animation runs once every 7 s; opacity stays low. */
.grace-avatar-frame::before {{
  content: ""; position: absolute; inset: 0;
  border-radius: 18px;
  padding: 1px;
  background: linear-gradient(
    115deg,
    transparent 30%,
    rgba(92,227,248,0.55) 50%,
    transparent 70%
  );
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  pointer-events: none;
  opacity: 0.55;
  background-size: 200% 200%;
  animation: grace-shimmer 7s ease-in-out infinite;
}}
@keyframes grace-shimmer {{
  0%   {{ background-position: 0% 50%; }}
  100% {{ background-position: 200% 50%; }}
}}

/* Typography — premium-enterprise hierarchy (1.5× scale) */
.grace-avatar-name {{
  font-size: 1.32rem; letter-spacing: 3px; font-weight: 800;
  color: var(--av-text-1); text-transform: uppercase;
  margin-top: 18px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.6);
  font-family: "Space Grotesk", -apple-system, sans-serif;
  line-height: 1.1;
}}
.grace-avatar-role {{
  font-size: 0.93rem; color: var(--av-text-2); font-weight: 600;
  text-transform: uppercase; letter-spacing: 2.2px;
  margin-top: 6px; line-height: 1.3;
  font-family: "Space Grotesk", -apple-system, sans-serif;
}}

/* Status badge — a real accent point, scaled 1.5× */
.grace-avatar-status {{
  display: inline-flex; align-items: center; gap: 10px;
  margin-top: 15px;
  padding: 5px 15px 5px 14px;
  border-radius: 999px;
  font-size: 0.93rem; font-weight: 700; letter-spacing: 1.5px;
  background: linear-gradient(180deg, rgba(92,227,248,0.22) 0%, rgba(92,227,248,0.10) 100%);
  color: var(--av-accent);
  text-transform: uppercase;
  border: 1px solid rgba(92,227,248,0.55);
  box-shadow:
    0 0 0 1px rgba(92,227,248,0.10),
    0 3px 9px rgba(0,0,0,0.35);
  font-family: "Space Grotesk", -apple-system, sans-serif;
}}
.grace-avatar-status::before {{
  content: ""; width: 10px; height: 10px; border-radius: 50%;
  background: var(--av-accent);
  box-shadow: 0 0 9px var(--av-accent);
  animation: grace-pulse 2.6s ease-in-out infinite;
}}
@keyframes grace-pulse {{
  0%, 100% {{ transform: scale(1);   opacity: 1;   }}
  50%      {{ transform: scale(1.25); opacity: 0.7; }}
}}

/* Description block (the bubble below the badge) — 1.5× scaled. */
.grace-avatar-bubble {{
  margin: 18px 4px 0;
  padding: 18px 20px;
  background: linear-gradient(180deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
  border: 1px solid rgba(92,227,248,0.22);
  border-radius: 14px;
  color: #E2F0F7;
  font-size: 1.05rem; line-height: 1.55;
  letter-spacing: 0.15px;
  text-align: left;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
  position: relative;
}}
.grace-avatar-bubble::before {{
  content: "";
  position: absolute; top: -10px; left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 18px; height: 18px;
  background: linear-gradient(135deg, rgba(92,227,248,0.30) 0%, rgba(255,255,255,0.06) 60%);
  border-left: 1px solid rgba(92,227,248,0.40);
  border-top: 1px solid rgba(92,227,248,0.40);
  border-radius: 3px;
}}

/* ── Avatar SVG ── */
.grace-avatar {{ width: 252px; height: auto; display: block; }}

/* ── Always-on micro-animations ── */
@keyframes grace-blink {{
  0%, 92%, 100% {{ transform: scaleY(1); }}
  95%           {{ transform: scaleY(0.08); }}
}}
.grace-avatar .eye-l, .grace-avatar .eye-r {{
  transform-box: fill-box; transform-origin: center;
  animation: grace-blink 5.4s ease-in-out infinite;
}}
.grace-avatar .eye-r {{ animation-delay: 0.05s; }}

@keyframes grace-breathe {{
  0%, 100% {{ transform: translateY(0); }}
  50%      {{ transform: translateY(1px); }}
}}
.grace-avatar .torso {{
  transform-box: fill-box; transform-origin: center;
  animation: grace-breathe 4.6s ease-in-out infinite;
}}

@keyframes grace-hair-sway-l {{
  0%, 100% {{ transform: rotate(0deg); }}
  50%      {{ transform: rotate(-1deg); }}
}}
@keyframes grace-hair-sway-r {{
  0%, 100% {{ transform: rotate(0deg); }}
  50%      {{ transform: rotate(1deg); }}
}}
.grace-avatar .hair-side-l {{
  transform-box: fill-box; transform-origin: top center;
  animation: grace-hair-sway-l 7s ease-in-out infinite;
}}
.grace-avatar .hair-side-r {{
  transform-box: fill-box; transform-origin: top center;
  animation: grace-hair-sway-r 7s ease-in-out infinite;
}}

@keyframes grace-halo {{
  0%, 100% {{ opacity: 0.45; }}
  50%      {{ opacity: 0.75; }}
}}
.grace-avatar .halo {{ animation: grace-halo 5s ease-in-out infinite; }}

/* ── State-specific ── */

/* THINKING — slight head tilt + pupils glance up */
.grace-avatar.state-thinking .head {{ transform: rotate(-3deg); transform-origin: 100px 130px; }}
.grace-avatar.state-thinking .pupil,
.grace-avatar.state-thinking .pupil-inner,
.grace-avatar.state-thinking .highlight {{
  transform: translateY(-1.5px);
  transition: transform 0.6s ease;
}}

/* ANALYZING — pupils scan left-right */
@keyframes grace-scan {{
  0%, 100% {{ transform: translateX(-1.5px); }}
  50%      {{ transform: translateX(1.5px); }}
}}
.grace-avatar.state-analyzing .pupil,
.grace-avatar.state-analyzing .pupil-inner,
.grace-avatar.state-analyzing .highlight {{
  animation: grace-scan 2.2s ease-in-out infinite;
}}

/* ATTENTIVE — brows raised slightly, eyes a touch wider */
.grace-avatar.state-attentive .brow-l,
.grace-avatar.state-attentive .brow-r {{ transform: translateY(-1px); }}
.grace-avatar.state-attentive .eye-l,
.grace-avatar.state-attentive .eye-r {{ transform: scaleY(1.05); }}

/* SUCCESS — gentle smile + closed-eye soft arch */
.grace-avatar.state-success .mouth {{ d: path("M 92 117 Q 100 123 108 117"); }}
.grace-avatar.state-success .eye-l,
.grace-avatar.state-success .eye-r {{ transform: scaleY(0.5); }}

/* WARNING — brows raised + mouth slightly parted */
.grace-avatar.state-warning .brow-l {{ transform: translate(0, -1.5px) rotate(-3deg); }}
.grace-avatar.state-warning .brow-r {{ transform: translate(0, -1.5px) rotate(3deg); }}
.grace-avatar.state-warning .mouth {{ d: path("M 95 119 Q 100 122 105 119"); }}

/* ERROR — brows down, mouth flat */
.grace-avatar.state-error .brow-l {{ transform: rotate(8deg); transform-origin: right center; }}
.grace-avatar.state-error .brow-r {{ transform: rotate(-8deg); transform-origin: left center; }}
.grace-avatar.state-error .mouth {{ d: path("M 94 120 L 106 120"); }}
.grace-avatar.state-error .halo {{ opacity: 0.2 !important; }}

/* READY — eyes brighter+wider, soft halo intensification, brows up */
.grace-avatar.state-ready .brow-l,
.grace-avatar.state-ready .brow-r {{ transform: translateY(-1.4px); }}
.grace-avatar.state-ready .eye-l,
.grace-avatar.state-ready .eye-r {{ transform: scaleY(1.08); }}
.grace-avatar.state-ready .halo {{
  filter: brightness(1.18) saturate(1.1);
}}

/* GUIDANCE — gentle head tilt + slow brow-up, soft repeated halo pulse */
.grace-avatar.state-guidance .head {{
  transform: rotate(-2deg);
  transform-origin: 100px 130px;
}}
.grace-avatar.state-guidance .brow-l,
.grace-avatar.state-guidance .brow-r {{ transform: translateY(-0.6px); }}
@keyframes grace-guidance-pulse {{
  0%, 100% {{ opacity: 0.45; transform: scale(1); }}
  50%      {{ opacity: 0.75; transform: scale(1.04); }}
}}
.grace-avatar.state-guidance .halo {{
  animation: grace-guidance-pulse 3s ease-in-out infinite;
  transform-box: fill-box; transform-origin: center;
}}

/* ── LOADING-ANALYSIS specifics: scanning line sweep ──
   Reads as 'GRACE is reading/processing the document'. A thin teal
   line moves vertically across the bust, suggesting OCR/scanning.
   The pupils' horizontal scan animation (state-analyzing rule above)
   reinforces the same metaphor. */
@keyframes grace-scan-line {{
  0%   {{ transform: translateY(-20px); opacity: 0; }}
  15%  {{ opacity: 0.9; }}
  85%  {{ opacity: 0.9; }}
  100% {{ transform: translateY(190px); opacity: 0; }}
}}
.grace-avatar .scan-overlay {{ opacity: 0; }}
.grace-avatar.state-analyzing .scan-overlay,
.grace-avatar.state-thinking  .scan-overlay {{
  opacity: 1;
}}
.grace-avatar.state-analyzing .scan-line,
.grace-avatar.state-thinking  .scan-line {{
  animation: grace-scan-line 1.7s linear infinite;
  transform-box: fill-box; transform-origin: center;
}}
/* Faster border shimmer during loading — reinforces 'working' */
.grace-avatar-frame.is-loading::before {{
  animation-duration: 1.8s !important;
  opacity: 0.85;
}}

/* ── SUCCESS-ANALYSIS: single completion burst around the halo ──
   A teal ring expands outward from the bust center exactly once,
   then fades. Plus the halo briefly brightens. State-success on the
   frame container drives a soft green-tinged glow border. */
@keyframes grace-success-burst {{
  0%   {{ r: 50; opacity: 0.0; }}
  20%  {{ opacity: 0.55; }}
  100% {{ r: 92; opacity: 0.0; }}
}}
.grace-avatar .success-burst {{ opacity: 0; }}
.grace-avatar.state-success .success-burst {{
  animation: grace-success-burst 1.1s ease-out 1 forwards;
}}
.grace-avatar.state-success .halo {{ filter: brightness(1.25); }}
.grace-avatar-frame.is-success {{
  border-color: #34D399 !important;
  box-shadow:
    0 0 0 1px rgba(52,211,153,0.25),
    0 12px 32px rgba(0,0,0,0.55),
    0 4px 12px rgba(52,211,153,0.18),
    inset 0 1px 0 rgba(255,255,255,0.10) !important;
}}
.grace-avatar-frame.is-error {{
  border-color: #F87171 !important;
}}


/* SPEAKING — mouth opens & closes */
@keyframes grace-speak {{
  0%, 100% {{ transform: scaleY(1); }}
  25%      {{ transform: scaleY(1.6) translateY(0.5px); }}
  50%      {{ transform: scaleY(0.7); }}
  75%      {{ transform: scaleY(1.4) translateY(0.5px); }}
}}
.grace-avatar.state-speaking .mouth-group,
.grace-avatar.is-speaking .mouth-group {{
  transform-box: fill-box; transform-origin: center;
  animation: grace-speak 0.45s ease-in-out infinite;
}}

/* Bubble fade-in keyframe (the bubble styling itself lives in the
   premium block above with the rest of the layout typography). */
@keyframes grace-bubble-in {{
  0%   {{ opacity: 0; transform: translateY(-4px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
.grace-avatar-bubble {{ animation: grace-bubble-in 0.45s ease-out; }}

/* Very subtle micro-float on the whole avatar SVG — adds 'alive'
   without ever drifting far enough to feel like an animation loop. */
@keyframes grace-float {{
  0%, 100% {{ transform: translateY(0); }}
  50%      {{ transform: translateY(-2px); }}
}}
.grace-avatar {{
  animation: grace-float 6.2s ease-in-out infinite;
  filter: drop-shadow(0 6px 12px rgba(0,0,0,0.35));
}}
</style>
"""


# ─── [RENDERER] ───────────────────────────────────────────────────────

def _svg(state: AvatarState, speaking: bool = False) -> str:
    """Return the layered SVG markup. All visual primitives live here."""
    t = TOKENS
    state_class = f"state-{state.value}"
    speak_class = " is-speaking" if speaking else ""
    return f"""
<svg class="grace-avatar {state_class}{speak_class}" viewBox="0 0 200 240"
     xmlns="http://www.w3.org/2000/svg" aria-label="GRACE Virtual Analyst">
  <defs>
    <radialGradient id="ga-halo" cx="50%" cy="40%" r="65%">
      <stop offset="0%"   stop-color="{t['halo']}" stop-opacity="0.55"/>
      <stop offset="60%"  stop-color="{t['halo']}" stop-opacity="0.10"/>
      <stop offset="100%" stop-color="{t['halo']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="ga-hair" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="{t['hair_hilite']}"/>
      <stop offset="55%" stop-color="{t['hair_base']}"/>
      <stop offset="100%" stop-color="{t['hair_shadow']}"/>
    </linearGradient>
    <linearGradient id="ga-jacket" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{t['jacket']}"/>
      <stop offset="100%" stop-color="{t['jacket_shadow']}"/>
    </linearGradient>
    <linearGradient id="ga-face" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{t['skin']}"/>
      <stop offset="100%" stop-color="{t['skin_shadow']}"/>
    </linearGradient>
    <radialGradient id="ga-iris" cx="50%" cy="40%" r="60%">
      <stop offset="0%"   stop-color="{t['iris']}"/>
      <stop offset="80%"  stop-color="{t['iris_dark']}"/>
    </radialGradient>
  </defs>

  <!-- Halo glow behind the bust -->
  <ellipse class="halo" cx="100" cy="115" rx="100" ry="100" fill="url(#ga-halo)"/>

  <!-- Hair back -->
  <path class="hair-back" d="
    M 52 95
    Q 46 38 100 30
    Q 154 38 148 95
    L 152 175
    Q 152 184 144 184
    L 130 178
    L 70 178
    L 56 184
    Q 48 184 48 175 Z"
    fill="url(#ga-hair)"/>

  <!-- Torso group -->
  <g class="torso">
    <!-- Jacket body -->
    <path d="
      M 30 240
      Q 30 178 60 168
      L 78 162
      L 100 178
      L 122 162
      L 140 168
      Q 170 178 170 240 Z"
      fill="url(#ga-jacket)" stroke="{t['outline']}" stroke-width="0.6"/>
    <!-- Blouse V -->
    <path d="M 84 162 L 100 200 L 116 162 Z" fill="{t['blouse']}"/>
    <!-- Blouse shadow seam -->
    <path d="M 84 162 L 100 200 L 116 162" stroke="{t['blouse_shadow']}" stroke-width="0.5" fill="none"/>
    <!-- Collar fold -->
    <path d="M 78 162 L 84 162 L 100 175 Z" fill="{t['jacket_collar']}"/>
    <path d="M 122 162 L 116 162 L 100 175 Z" fill="{t['jacket_collar']}"/>
    <!-- Tie / scarf accent (teal) -->
    <rect x="97" y="163" width="6" height="24" fill="{t['accent_pin']}" rx="1"/>
    <!-- Pin / brooch -->
    <circle cx="100" cy="184" r="3" fill="{t['pin_core']}" stroke="{t['accent_pin']}" stroke-width="0.8"/>
  </g>

  <!-- Neck -->
  <path class="neck" d="M 90 135 Q 90 148 86 156 L 114 156 Q 110 148 110 135 Z"
        fill="url(#ga-face)"/>
  <path d="M 90 152 Q 100 156 110 152" stroke="{t['skin_shadow']}" stroke-width="0.4" fill="none" opacity="0.7"/>

  <!-- Head -->
  <g class="head">
    <!-- Face -->
    <ellipse class="face" cx="100" cy="92" rx="42" ry="50" fill="url(#ga-face)"/>
    <!-- Cheek blush (very subtle) -->
    <ellipse cx="74" cy="108" rx="6" ry="2.5" fill="{t['blush']}" opacity="0.45"/>
    <ellipse cx="126" cy="108" rx="6" ry="2.5" fill="{t['blush']}" opacity="0.45"/>
    <!-- Ear hints -->
    <path d="M 58 95 Q 56 102 60 108 L 62 100 Z" fill="{t['skin_shadow']}" opacity="0.7"/>
    <path d="M 142 95 Q 144 102 140 108 L 138 100 Z" fill="{t['skin_shadow']}" opacity="0.7"/>

    <!-- Nose -->
    <path class="nose" d="M 100 103 L 98 113 L 102 113 Z"
          fill="{t['skin_shadow']}" opacity="0.55"/>

    <!-- Mouth -->
    <g class="mouth-group">
      <path class="mouth" d="M 95 119 Q 100 122 105 119"
            stroke="{t['lip']}" stroke-width="1.6" fill="none" stroke-linecap="round"/>
    </g>

    <!-- Eyebrows -->
    <g class="brows">
      <path class="brow-l" d="M 69 80 Q 78 76 88 80"
            stroke="{t['brow']}" stroke-width="2.2" fill="none" stroke-linecap="round"/>
      <path class="brow-r" d="M 112 80 Q 122 76 131 80"
            stroke="{t['brow']}" stroke-width="2.2" fill="none" stroke-linecap="round"/>
    </g>

    <!-- Eyes -->
    <g class="eyes">
      <g class="eye-l">
        <ellipse class="eye-white" cx="80" cy="94" rx="9.5" ry="7.5" fill="{t['eye_white']}"/>
        <circle  class="pupil"        cx="80" cy="94" r="5.5" fill="url(#ga-iris)"/>
        <circle  class="pupil-inner"  cx="80" cy="94" r="2.6" fill="{t['iris_dark']}"/>
        <circle  class="highlight"    cx="82" cy="92" r="1.6" fill="{t['iris_hilite']}"/>
        <ellipse class="eye-lash"     cx="80" cy="87.5" rx="9" ry="1.2" fill="{t['brow']}"/>
      </g>
      <g class="eye-r">
        <ellipse class="eye-white" cx="120" cy="94" rx="9.5" ry="7.5" fill="{t['eye_white']}"/>
        <circle  class="pupil"        cx="120" cy="94" r="5.5" fill="url(#ga-iris)"/>
        <circle  class="pupil-inner"  cx="120" cy="94" r="2.6" fill="{t['iris_dark']}"/>
        <circle  class="highlight"    cx="122" cy="92" r="1.6" fill="{t['iris_hilite']}"/>
        <ellipse class="eye-lash"     cx="120" cy="87.5" rx="9" ry="1.2" fill="{t['brow']}"/>
      </g>
    </g>
  </g>

  <!-- Hair front: bangs + side strands -->
  <g class="hair-front">
    <!-- Side strands (long, sway gently) -->
    <path class="hair-side-l" d="M 56 70 Q 50 110 56 142 L 66 138 Q 64 100 64 75 Z"
          fill="url(#ga-hair)"/>
    <path class="hair-side-r" d="M 144 70 Q 150 110 144 142 L 134 138 Q 136 100 136 75 Z"
          fill="url(#ga-hair)"/>
    <!-- Bangs (covering forehead, soft asymmetric parting) -->
    <path class="bangs" d="
      M 58 62
      Q 70 35 102 33
      Q 134 35 142 62
      L 138 80
      Q 130 70 122 76
      Q 114 82 108 72
      Q 102 64 96 72
      Q 90 80 80 75
      Q 70 70 62 80 Z"
      fill="url(#ga-hair)"/>
  </g>

  <!-- Always-present overlays for loading + success states.
       Hidden by default; CSS unhides them per state. -->
  <defs>
    <linearGradient id="ga-scan" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{t['halo']}" stop-opacity="0"/>
      <stop offset="50%"  stop-color="{t['halo']}" stop-opacity="1"/>
      <stop offset="100%" stop-color="{t['halo']}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <g class="scan-overlay">
    <rect class="scan-line" x="32" y="40" width="136" height="2"
          fill="url(#ga-scan)" rx="1"/>
  </g>
  <circle class="success-burst"
          cx="100" cy="115" r="50"
          fill="none" stroke="#34D399" stroke-width="2"/>
</svg>
"""


def render_avatar(state: Optional[AvatarState] = None,
                  show_status_pill: bool = True,
                  message: Optional[str] = None,
                  page: Optional[str] = None,
                  lang: str = "en") -> str:
    """
    Return a self-contained HTML document with the GRACE avatar.

    Designed to be injected via `st.components.v1.html(..., height=...)`,
    which sandboxes the content in an iframe and bypasses Streamlit's
    HTML sanitizer.

    If `message` is provided, the avatar speaks it via a bubble below
    the bust and plays the speaking-mouth animation regardless of state.
    If `message` is None and `page` is provided, a contextual default is
    composed from the (page, state, lang) lookup.
    """
    s = state if state is not None else get_state()
    resolved_message = message
    if resolved_message is None and page is not None:
        resolved_message = compose_message(page, s, lang)
    # The mouth only animates during genuinely transient "working" states
    # (analyzing the policy, drafting a document). On idle / success /
    # warning / error the smile stays still — no jittery tremor.
    speaking = s in (AvatarState.ANALYZING, AvatarState.THINKING, AvatarState.SPEAKING)

    bubble = (
        f'<div class="grace-avatar-bubble">{resolved_message}</div>'
        if resolved_message else ""
    )
    status_label = s.value.replace("_", " ").capitalize()
    pill = (
        f'<div class="grace-avatar-status">{status_label}</div>'
        if show_status_pill else ""
    )
    # Map behavioural state → frame container class (drives the soft
    # tinted border/halo around the whole card during loading, success
    # and error — used together with the inner SVG state class).
    frame_modifier = ""
    if s in (AvatarState.ANALYZING, AvatarState.THINKING):
        frame_modifier = " is-loading"
    elif s == AvatarState.SUCCESS:
        frame_modifier = " is-success"
    elif s == AvatarState.ERROR:
        frame_modifier = " is-error"
    return (
        '<!DOCTYPE html><html><head>'
        '<style>'
        'html,body{margin:0;padding:0;background:transparent;}'
        '*{box-sizing:border-box;}'
        '</style>'
        + _css()
        + '</head><body>'
        + f'<div class="grace-avatar-frame{frame_modifier}">'
        + _svg(s, speaking=speaking)
        + '<div class="grace-avatar-name">GRACE</div>'
        + '<div class="grace-avatar-role">GRC Virtual Analyst</div>'
        + pill
        + bubble
        + '</div>'
        + '</body></html>'
    )


# Recommended iframe height for st.components.v1.html callers.
# Scaled to 1.5× with the rest of the widget — the avatar SVG is now
# 252 px wide, the bubble has 1.05 rem text, and the frame needs the
# extra height to fit them without scroll.
AVATAR_FRAME_HEIGHT = 720
