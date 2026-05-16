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
    # Hair / outline
    "hair_base":     "#0E2541",
    "hair_shadow":   "#0A1929",
    "hair_hilite":   "#1A3B6C",
    "outline":       "#0A1929",
    # Skin
    "skin":          "#F2DAC2",
    "skin_shadow":   "#E5C5A8",
    "blush":         "#F0BFB0",
    # Eyes
    "eye_white":     "#FBFCFD",
    "iris":          "#2A7A8A",
    "iris_dark":     "#0F2349",
    "iris_hilite":   "#FFFFFF",
    "brow":          "#1A2C50",
    # Mouth
    "lip":           "#A86A6A",
    # Outfit
    "blouse":        "#FAFBFC",
    "blouse_shadow": "#E2E6EB",
    "jacket":        "#163265",
    "jacket_shadow": "#0E2348",
    "jacket_collar": "#1F3F73",
    "accent_pin":    "#4EC6D9",
    "pin_core":      "#163265",
    # Halo / glow
    "halo":          "#4EC6D9",
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
    `.grace-avatar.state-<name>` selectors on the root SVG."""
    return f"""
<style>
.grace-avatar-frame {{
  display: flex; flex-direction: column; align-items: center;
  padding: 14px 6px 12px;
  background: linear-gradient(160deg, rgba(46,123,138,0.18) 0%, rgba(22,50,101,0.28) 100%);
  border: 1px solid rgba(78,198,217,0.25);
  border-radius: 16px;
  position: relative; overflow: hidden;
  margin-bottom: 14px;
  box-shadow: 0 6px 22px rgba(10,25,41,0.25), inset 0 1px 0 rgba(255,255,255,0.04);
}}
.grace-avatar-frame::before {{
  content: ""; position: absolute; inset: 0;
  background: radial-gradient(circle at 50% 25%, rgba(78,198,217,0.22) 0%, transparent 55%);
  pointer-events: none;
}}
.grace-avatar-name {{
  font-size: 0.74rem; letter-spacing: 1.4px; font-weight: 700;
  color: #DCEFF3; text-transform: uppercase; margin-top: 8px;
  font-family: "Space Grotesk", -apple-system, sans-serif;
}}
.grace-avatar-role {{
  font-size: 0.62rem; color: #94BAC2;
  text-transform: uppercase; letter-spacing: 1px; margin-top: 2px;
}}
.grace-avatar-status {{
  display: inline-flex; align-items: center; gap: 5px;
  margin-top: 6px;
  padding: 2px 8px; border-radius: 999px;
  font-size: 0.62rem; font-weight: 600; letter-spacing: 0.5px;
  background: rgba(78,198,217,0.14); color: #4EC6D9;
  text-transform: uppercase;
  border: 1px solid rgba(78,198,217,0.3);
}}
.grace-avatar-status::before {{
  content: ""; width: 6px; height: 6px; border-radius: 50%;
  background: #4EC6D9;
  animation: grace-pulse 2s ease-in-out infinite;
}}

@keyframes grace-pulse {{
  0%, 100% {{ box-shadow: 0 0 0 0 rgba(78,198,217,0.55); }}
  50%      {{ box-shadow: 0 0 0 5px rgba(78,198,217,0); }}
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
.grace-avatar.state-speaking .mouth-group {{
  transform-box: fill-box; transform-origin: center;
  animation: grace-speak 0.45s ease-in-out infinite;
}}
</style>
"""


# ─── [RENDERER] ───────────────────────────────────────────────────────

def _svg(state: AvatarState) -> str:
    """Return the layered SVG markup. All visual primitives live here."""
    t = TOKENS
    state_class = f"state-{state.value}"
    return f"""
<svg class="grace-avatar {state_class}" viewBox="0 0 200 240"
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
                  show_status_pill: bool = True) -> str:
    """
    Return the complete HTML (CSS + SVG + frame) for the GRACE avatar.

    Call once per page. If `state` is None the current session state is
    used. The frame around the SVG includes the analyst name, role and
    a live status pill — feel free to suppress with show_status_pill=False.
    """
    s = state if state is not None else get_state()
    status_label = s.value.capitalize()
    pill = (
        f'<div class="grace-avatar-status">{status_label}</div>'
        if show_status_pill else ""
    )
    return (
        _css()
        + '<div class="grace-avatar-frame">'
        + _svg(s)
        + '<div class="grace-avatar-name">GRACE</div>'
        + '<div class="grace-avatar-role">GRC Virtual Analyst</div>'
        + pill
        + '</div>'
    )
