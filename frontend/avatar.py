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
    """Supported behavioural states. The string value is also the CSS class."""
    IDLE      = "idle"
    ATTENTIVE = "attentive"
    THINKING  = "thinking"
    ANALYZING = "analyzing"
    SUCCESS   = "success"
    WARNING   = "warning"
    ERROR     = "error"
    SPEAKING  = "speaking"


# UI event → default avatar state mapping. The page renderer can override
# the resolved state at any point (e.g. after an API call returns success).
PAGE_DEFAULT_STATE = {
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
    ("gap_analysis", AvatarState.IDLE,      "en"): "Pick a framework, drop in your policy — I'll map every control and surface the gaps.",
    ("gap_analysis", AvatarState.ATTENTIVE, "en"): "Ready when you are. Choose a framework and paste or upload the document.",
    ("gap_analysis", AvatarState.ANALYZING, "en"): "Reading your policy now and matching it to the control catalog… give me a moment.",
    ("gap_analysis", AvatarState.SUCCESS,   "en"): "Strong coverage. Let's review what's working and where to harden further.",
    ("gap_analysis", AvatarState.WARNING,   "en"): "Several gaps detected — let's walk through them together, severity-first.",
    ("gap_analysis", AvatarState.ERROR,     "en"): "I couldn't complete the assessment. Check the document and try again.",

    ("doc_gen",      AvatarState.IDLE,      "en"): "Tell me the framework and the document type — I'll draft it audit-ready.",
    ("doc_gen",      AvatarState.ATTENTIVE, "en"): "Add a few words of context (scope, sector, tools) to make the draft more accurate.",
    ("doc_gen",      AvatarState.THINKING,  "en"): "Drafting your document — selecting clauses, citing references…",
    ("doc_gen",      AvatarState.SUCCESS,   "en"): "Draft ready. Read it end-to-end and adapt to your organisation before publishing.",
    ("doc_gen",      AvatarState.ERROR,     "en"): "The generator hit an issue. Try again or simplify the context.",

    ("dashboard",    AvatarState.IDLE,      "en"): "Here's the live picture of your compliance posture. Click any framework for the detail.",
    ("registry",     AvatarState.IDLE,      "en"): "Findings grouped by source document. Update the operational status as you triage.",
    ("library",      AvatarState.IDLE,      "en"): "Pick a framework to explore its controls. Ask me to explain any of them in plain language.",

    # ─── Italiano ───────────────────────────────────────────────
    ("gap_analysis", AvatarState.IDLE,      "it"): "Scegli un framework e carica la tua policy — mappo ogni controllo e ti mostro i gap.",
    ("gap_analysis", AvatarState.ATTENTIVE, "it"): "Sono pronta. Scegli framework e incolla o carica il documento.",
    ("gap_analysis", AvatarState.ANALYZING, "it"): "Sto leggendo la policy e confrontandola con il catalogo dei controlli… un attimo.",
    ("gap_analysis", AvatarState.SUCCESS,   "it"): "Copertura solida. Vediamo cosa funziona e dove rafforzare.",
    ("gap_analysis", AvatarState.WARNING,   "it"): "Ho trovato diversi gap — li affrontiamo per severità, partendo dai critici.",
    ("gap_analysis", AvatarState.ERROR,     "it"): "Non sono riuscita a completare l'analisi. Controlla il documento e riprova.",

    ("doc_gen",      AvatarState.IDLE,      "it"): "Dimmi framework e tipo di documento — lo redigo audit-ready.",
    ("doc_gen",      AvatarState.ATTENTIVE, "it"): "Aggiungi qualche riga di contesto (scope, settore, tool) per rendere il draft più accurato.",
    ("doc_gen",      AvatarState.THINKING,  "it"): "Sto redigendo — seleziono le clausole, cito i riferimenti…",
    ("doc_gen",      AvatarState.SUCCESS,   "it"): "Draft pronto. Rileggilo per intero e adattalo alla tua organizzazione prima della pubblicazione.",
    ("doc_gen",      AvatarState.ERROR,     "it"): "Il generatore ha riscontrato un problema. Riprova o semplifica il contesto.",

    ("dashboard",    AvatarState.IDLE,      "it"): "Ecco la fotografia live della tua compliance. Clicca un framework per il dettaglio.",
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
  padding: 16px 12px 14px;
  /* Deep, fully opaque navy gradient — sits BELOW the page bg tone
     so the avatar reads as foreground content, not blended chrome. */
  background:
    radial-gradient(ellipse 60% 35% at 50% 12%, rgba(92,227,248,0.22) 0%, transparent 70%),
    linear-gradient(180deg, var(--av-ink-3) 0%, var(--av-ink-1) 100%);
  border: 1px solid var(--av-line);
  border-radius: 18px;
  position: relative;
  margin-bottom: 14px;
  /* Crisp layered depth — no fuzzy halos. */
  box-shadow:
    0 0 0 1px rgba(92,227,248,0.18),
    0 10px 28px rgba(0,0,0,0.55),
    0 2px 6px rgba(0,0,0,0.45),
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

/* Typography — premium-enterprise hierarchy */
.grace-avatar-name {{
  font-size: 0.88rem; letter-spacing: 2px; font-weight: 800;
  color: var(--av-text-1); text-transform: uppercase;
  margin-top: 12px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.6);
  font-family: "Space Grotesk", -apple-system, sans-serif;
  line-height: 1.1;
}}
.grace-avatar-role {{
  font-size: 0.62rem; color: var(--av-text-2); font-weight: 600;
  text-transform: uppercase; letter-spacing: 1.5px;
  margin-top: 4px; line-height: 1.3;
  font-family: "Space Grotesk", -apple-system, sans-serif;
}}

/* Status badge — a real accent point, not a faded label */
.grace-avatar-status {{
  display: inline-flex; align-items: center; gap: 7px;
  margin-top: 10px;
  padding: 3px 10px 3px 9px;
  border-radius: 999px;
  font-size: 0.62rem; font-weight: 700; letter-spacing: 1px;
  background: linear-gradient(180deg, rgba(92,227,248,0.22) 0%, rgba(92,227,248,0.10) 100%);
  color: var(--av-accent);
  text-transform: uppercase;
  border: 1px solid rgba(92,227,248,0.55);
  box-shadow:
    0 0 0 1px rgba(92,227,248,0.10),
    0 2px 6px rgba(0,0,0,0.35);
  font-family: "Space Grotesk", -apple-system, sans-serif;
}}
.grace-avatar-status::before {{
  content: ""; width: 7px; height: 7px; border-radius: 50%;
  background: var(--av-accent);
  box-shadow: 0 0 6px var(--av-accent);
  animation: grace-pulse 2.6s ease-in-out infinite;
}}
@keyframes grace-pulse {{
  0%, 100% {{ transform: scale(1);   opacity: 1;   }}
  50%      {{ transform: scale(1.25); opacity: 0.7; }}
}}

/* Description block (the bubble below the badge) — better hierarchy,
   tighter contrast, more breathing room. */
.grace-avatar-bubble {{
  margin: 12px 4px 0;
  padding: 12px 14px;
  background: linear-gradient(180deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
  border: 1px solid rgba(92,227,248,0.22);
  border-radius: 12px;
  color: #E2F0F7;
  font-size: 0.74rem; line-height: 1.55;
  letter-spacing: 0.1px;
  text-align: left;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
  position: relative;
}}
.grace-avatar-bubble::before {{
  content: "";
  position: absolute; top: -7px; left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 12px; height: 12px;
  background: linear-gradient(135deg, rgba(92,227,248,0.30) 0%, rgba(255,255,255,0.06) 60%);
  border-left: 1px solid rgba(92,227,248,0.40);
  border-top: 1px solid rgba(92,227,248,0.40);
  border-radius: 2px;
}}

/* ── Avatar SVG ── */
.grace-avatar {{ width: 168px; height: auto; display: block; }}

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
    status_label = s.value.capitalize()
    pill = (
        f'<div class="grace-avatar-status">{status_label}</div>'
        if show_status_pill else ""
    )
    return (
        '<!DOCTYPE html><html><head>'
        '<style>'
        'html,body{margin:0;padding:0;background:transparent;}'
        '*{box-sizing:border-box;}'
        '</style>'
        + _css()
        + '</head><body>'
        + '<div class="grace-avatar-frame">'
        + _svg(s, speaking=speaking)
        + '<div class="grace-avatar-name">GRACE</div>'
        + '<div class="grace-avatar-role">GRC Virtual Analyst</div>'
        + pill
        + bubble
        + '</div>'
        + '</body></html>'
    )


# Recommended iframe height for st.components.v1.html callers.
# Bumped to fit the contextual speech bubble below the bust.
AVATAR_FRAME_HEIGHT = 480
