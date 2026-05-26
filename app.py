"""
Project Financial Intelligence Agent — Streamlit App
Cross-references Oracle PPM resource plans against Workday Financial budgets
and surfaces financial alignment gaps with configurable autonomy modes.

Author  : Sanjay Kumar Kannojia
Powered : Anthropic Claude API + Streamlit
"""

import streamlit as st
import anthropic
import json

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Project Financial Intelligence Agent",
    page_icon="⚡",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

  .main-header {
    background: linear-gradient(135deg, #1E1B4B, #1D4ED8);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .main-header h1 {
    color: white !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  .main-header p {
    color: rgba(255,255,255,0.7) !important;
    font-size: 12px !important;
    margin: 4px 0 0 0 !important;
    font-family: 'DM Mono', monospace !important;
  }

  .status-hitl {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 8px;
    padding: 10px 16px;
    color: #1D4ED8;
    font-weight: 500;
    font-size: 13px;
    margin-bottom: 16px;
  }
  .status-hotl {
    background: #F5F3FF;
    border: 1px solid #DDD6FE;
    border-radius: 8px;
    padding: 10px 16px;
    color: #6D28D9;
    font-weight: 500;
    font-size: 13px;
    margin-bottom: 16px;
  }

  .panel-header {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px 10px 0 0;
    padding: 10px 14px;
    font-weight: 600;
    font-size: 13px;
    color: #0F172A;
  }

  .gap-card-high {
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
  }
  .gap-card-medium {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
  }
  .gap-card-low {
    background: #F0FDFA;
    border: 1px solid #99F6E4;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
  }

  .gap-title { font-size: 14px; font-weight: 700; color: #0F172A; }
  .gap-sub   { font-size: 11px; color: #64748B; margin-top: 3px; }
  .gap-amount-high   { font-size: 22px; font-weight: 700; color: #B91C1C; font-family: 'DM Mono', monospace; }
  .gap-amount-medium { font-size: 22px; font-weight: 700; color: #B45309; font-family: 'DM Mono', monospace; }
  .gap-amount-low    { font-size: 22px; font-weight: 700; color: #0F766E; font-family: 'DM Mono', monospace; }
  .gap-rec   { font-size: 12px; color: #475569; line-height: 1.6; margin-top: 8px; }

  .badge-high   { background: #FEF2F2; color: #B91C1C; border: 1px solid #FECACA; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 700; }
  .badge-medium { background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 700; }
  .badge-low    { background: #F0FDFA; color: #0F766E; border: 1px solid #99F6E4; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 700; }

  .resolved-pill { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }
  .flagged-pill  { background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }

  .footer-note {
    background: #F5F3FF;
    border: 1px solid #DDD6FE;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    color: #6D28D9;
    margin-top: 16px;
  }

  div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
  .stButton button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
  }
  .stTextInput input {
    font-family: 'DM Mono', monospace !important;
    font-size: 13px !important;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────
AUTO_APPROVE_THRESHOLD = 50_000
MODEL = "claude-sonnet-4-6"

# ─────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────
PPM_DATA = {
    "projects": [
        {
            "name": "Hillman Consultancy",
            "resources": [
                {"role": "Developer",           "count": 8, "hours": 10240, "cost": 1_228_800},
                {"role": "Product Manager",     "count": 1, "hours":  1280, "cost":   192_000},
                {"role": "QA Engineer",         "count": 2, "hours":  2560, "cost":   256_000},
                {"role": "Deployment Engineer", "count": 1, "hours":   640, "cost":    96_000},
            ],
            "total_cost": 1_772_800,
        },
        {
            "name": "Meridian ERP Rollout",
            "resources": [
                {"role": "Developer",        "count": 5, "hours": 6400, "cost": 768_000},
                {"role": "Business Analyst", "count": 2, "hours": 2560, "cost": 230_400},
            ],
            "total_cost": 998_400,
            "schedule_extension_weeks": 6,
            "extension_cost": 38_400,
        },
        {
            "name": "Apex Cloud Migration",
            "resources": [
                {"role": "Developer", "count": 6, "hours": 7680, "cost": 921_600},
                {"role": "Architect", "count": 1, "hours":  960, "cost": 192_000},
            ],
            "total_cost": 1_113_600,
        },
    ]
}

WORKDAY_DATA = {
    "budgets": [
        {
            "name": "Hillman Consultancy",
            "approved_budget": 1_720_000,
            "period_actuals":    986_400,
            "headcount_gap": "Deployment Engineer not in Workday headcount plan",
        },
        {
            "name": "Meridian ERP Rollout",
            "approved_budget":  998_400,
            "period_actuals":   512_000,
            "schedule_note": "6-week extension not reflected in Workday forecast",
        },
        {
            "name": "Apex Cloud Migration",
            "approved_budget": 1_113_600,
            "period_actuals":    634_200,
            "status": "aligned",
        },
    ]
}

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
if "gaps"         not in st.session_state: st.session_state.gaps         = None
if "mode"         not in st.session_state: st.session_state.mode         = "HITL"
if "actions"      not in st.session_state: st.session_state.actions      = {}
if "analysis_run" not in st.session_state: st.session_state.analysis_run = False

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <div style="font-size:32px;">⚡</div>
  <div>
    <h1>Project Financial Intelligence Agent</h1>
    <p>Oracle PPM × Workday Financial — Cross-System Gap Analysis · Powered by Claude AI</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SIDEBAR — CONFIG
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.divider()

    api_key = api_key = st.secrets.get("ANTHROPIC_API_KEY", "") or st.text_input(
    "Anthropic API Key",
    type="password",
    placeholder="sk-ant-api03-...",
)

    st.divider()
    st.markdown("### 🎚️ Autonomy Mode")
    mode_choice = st.radio(
        "Select how the agent operates",
        options=["Human-in-the-Loop (HITL)", "Human Over the Loop (HOTL)"],
        help="HITL: Agent pauses for your approval. HOTL: Agent acts autonomously within threshold."
    )
    st.session_state.mode = "HOTL" if "HOTL" in mode_choice else "HITL"

    st.divider()
    st.markdown("### 💰 Threshold")
    threshold = st.number_input(
        "Auto-approve threshold ($)",
        min_value=10_000,
        max_value=500_000,
        value=AUTO_APPROVE_THRESHOLD,
        step=10_000,
        help="Gaps below this amount are auto-resolved in HOTL mode"
    )

    st.divider()
    if st.session_state.mode == "HITL":
        st.info("🔵 **Human-in-the-Loop**\n\nAgent pauses at each gap and waits for your Approve or Escalate decision.")
    else:
        st.success("🟣 **Human Over the Loop**\n\nAgent acts autonomously on gaps below threshold. High-value gaps are flagged for your awareness.")

    st.divider()
    st.markdown(f"**Threshold:** ${threshold:,.0f}")
    st.markdown(f"**Model:** `{MODEL}`")

# ─────────────────────────────────────────────────────────────
# STATUS BAR
# ─────────────────────────────────────────────────────────────
if st.session_state.mode == "HITL":
    st.markdown("""<div class="status-hitl">🔵 Human-in-the-Loop mode — Agent will pause at each gap and await your decision</div>""", unsafe_allow_html=True)
else:
    st.markdown("""<div class="status-hotl">🟣 Human Over the Loop mode — Agent acts autonomously within threshold · High-value gaps flagged for awareness</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# DATA PANELS
# ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="panel-header">📋 Oracle PPM Resource Plan</div>', unsafe_allow_html=True)
    ppm_rows = []
    for proj in PPM_DATA["projects"]:
        for i, r in enumerate(proj["resources"]):
            flag = " ⚠️" if r["role"] == "Deployment Engineer" else ""
            ppm_rows.append({
                "Project"  : proj["name"] if i == 0 else "",
                "Role"     : f"{r['count']}× {r['role']}{flag}",
                "Hours"    : f"{r['hours']:,}",
                "PPM Cost" : f"${r['cost']:,.0f}",
            })
    st.dataframe(ppm_rows, use_container_width=True, hide_index=True)

with col2:
    st.markdown('<div class="panel-header">💰 Workday Financial Budget</div>', unsafe_allow_html=True)
    wd_rows = []
    for b in WORKDAY_DATA["budgets"]:
        note = ""
        if b.get("headcount_gap"):   note = "⚠️ " + b["headcount_gap"]
        elif b.get("schedule_note"): note = "⚠️ " + b["schedule_note"]
        elif b.get("status") == "aligned": note = "✅ Aligned"
        wd_rows.append({
            "Project"         : b["name"],
            "Approved Budget" : f"${b['approved_budget']:,.0f}",
            "Period Actuals"  : f"${b['period_actuals']:,.0f}",
            "Note"            : note,
        })
    st.dataframe(wd_rows, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────
# AGENT ANALYSIS
# ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("### 🤖 Agent Intelligence — Financial Alignment Analysis")

run_col, _ = st.columns([1, 3])
with run_col:
    run_clicked = st.button(
        "🤖 Run Agent Analysis",
        type="primary",
        use_container_width=True,
        disabled=not bool(api_key),
        help="Enter your Anthropic API key in the sidebar to enable"
    )

if not api_key:
    st.info("👈 Enter your Anthropic API key in the sidebar to run the live agent analysis.")

if run_clicked and api_key:
    with st.spinner("Claude AI is cross-referencing Oracle PPM commitments against Workday financial data..."):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            prompt = f"""You are a Project Financial Intelligence Agent for enterprise PPM and financial management.

Cross-reference the Oracle PPM resource plan against the Workday financial budgets.

Oracle PPM data:
{json.dumps(PPM_DATA, indent=2)}

Workday Financial data:
{json.dumps(WORKDAY_DATA, indent=2)}

Auto-approve threshold: ${threshold:,}

Return ONLY a valid JSON array with exactly 3 gap objects. Each must have:
- project: string
- gap_type: string (short title)
- gap_subtype: string (one sentence, mention ABOVE or BELOW ${threshold:,} threshold)
- severity: "HIGH" or "MEDIUM" or "LOW"
- amount: integer (positive dollar amount)
- recommendation: string (2-3 sentences, specific, enterprise PPM and Workday terminology)
- auto_resolvable: boolean (true if amount < {threshold})
- hotl_status: string ("Auto-resolved — Below threshold" if auto_resolvable else "Flagged — Above threshold")

Analyse: 1) Hillman cost overrun vs Workday budget 2) Hillman Deployment Engineer missing from Workday headcount 3) Meridian schedule extension cost impact."""

            message = client.messages.create(
                model=MODEL,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw  = message.content[0].text.strip()
            # robustly extract JSON array even if Claude adds explanation text
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON array found in agent response.")
            raw  = raw[start:end]
            gaps = json.loads(raw)
            st.session_state.gaps         = gaps
            st.session_state.actions      = {}
            st.session_state.analysis_run = True
            st.rerun()
        except Exception as e:
            st.error(f"Agent error: {e}")

# ─────────────────────────────────────────────────────────────
# GAP CARDS
# ─────────────────────────────────────────────────────────────
if st.session_state.gaps:
    gaps = st.session_state.gaps
    mode = st.session_state.mode

    # stats row
    critical = sum(1 for g in gaps if g["severity"] == "HIGH")
    watch    = sum(1 for g in gaps if g["severity"] == "MEDIUM")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Critical Gaps",  critical)
    m2.metric("Watch Items",    watch)
    m3.metric("Aligned",        1)
    m4.metric("Total Exposure", f"${sum(g['amount'] for g in gaps):,.0f}")

    st.divider()

    for i, gap in enumerate(gaps):
        sev        = gap["severity"].upper()
        card_class = f"gap-card-{sev.lower()}"
        amt_class  = f"gap-amount-{sev.lower()}"
        badge_cls  = f"badge-{sev.lower()}"
        auto       = gap.get("auto_resolvable", False)

        # card header
        st.markdown(f"""
        <div class="{card_class}">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;">
            <div>
              <div class="gap-title">{gap['project']} — {gap['gap_type']}</div>
              <div class="gap-sub">{gap['gap_subtype']}</div>
            </div>
            <div style="text-align:right;">
              <div class="{amt_class}">+${gap['amount']:,}</div>
              <span class="{badge_cls}">{sev}</span>
            </div>
          </div>
          <div class="gap-rec"><strong>Recommendation:</strong> {gap['recommendation']}</div>
        </div>
        """, unsafe_allow_html=True)

        # action row
        action_key = f"action_{i}"
        if action_key in st.session_state.actions:
            taken = st.session_state.actions[action_key]
            if taken == "approved":
                st.success(f"✓ Approved — action queued in Workday workflow")
            elif taken == "escalated":
                st.warning(f"↑ Escalated — sent to Finance / HR for review")
        else:
            if mode == "HITL":
                c1, c2, c3 = st.columns([1, 1, 4])
                with c1:
                    if st.button(f"✓ Approve", key=f"approve_{i}", use_container_width=True):
                        st.session_state.actions[action_key] = "approved"
                        st.rerun()
                with c2:
                    if st.button(f"↑ Escalate", key=f"escalate_{i}", use_container_width=True):
                        st.session_state.actions[action_key] = "escalated"
                        st.rerun()
            else:
                if auto:
                    st.markdown(f'<div class="resolved-pill">✓ Auto-resolved — Below threshold</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="flagged-pill">⚠ Flagged — Above threshold</div>', unsafe_allow_html=True)

        st.write("")

    # all resolved check
    if mode == "HITL" and len(st.session_state.actions) == len(gaps):
        st.success("✅ All gaps resolved — Agent ready for next analysis cycle")

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer-note">
  🔮 <strong>Configurable Autonomy:</strong> The ${threshold:,.0f} threshold determines which gaps
  the agent resolves automatically (Human Over the Loop) vs. which require human approval
  (Human-in-the-Loop). Enterprise teams raise this threshold as they build trust in the agent
  over time — the natural path from supervised to autonomous AI adoption.
</div>
""", unsafe_allow_html=True)
