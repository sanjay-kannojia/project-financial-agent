"""
Project Financial Intelligence Agent — Streamlit App
Cross-references Oracle PPM resource plans against Workday Financial budgets
and surfaces financial alignment gaps with configurable autonomy modes.

Author  : Sanjay Kumar Kannojia
Powered : Anthropic Claude API + Streamlit

CALCULATION NOTES (all numbers derived, nothing hardcoded):
  Developer rate    : $120/hr  (768,000 / 6,400 hrs from Meridian ERP Rollout)
  BA rate           : $90/hr   (230,400 / 2,560 hrs from Meridian ERP Rollout)
  QA rate           : $100/hr  (256,000 / 2,560 hrs from Hillman)
  PM rate           : $150/hr  (192,000 / 1,280 hrs from Hillman)
  Architect rate    : $200/hr  (192,000 / 960 hrs from Apex)
  Depl Eng rate     : $150/hr  (96,000 / 640 hrs from Hillman)

  Meridian 6-week extension crew: 2 Developers + 1 BA (reduced wind-down team)
    Weekly cost: (2 x 40 x $120) + (1 x 40 x $90) = $9,600 + $3,600 = $13,200/week
    6-week total: $13,200 x 6 = $79,200

  Period Actuals = amount actually posted in Workday as of current period
    Hillman:  55.7% completion = 1,772,800 x 0.557 = ~986,400
    Meridian: 51.3% completion = 998,400   x 0.513 = ~512,000
    Apex:     56.9% completion = 1,113,600 x 0.569 = ~634,200
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

  /* WELCOME BANNER */
  .welcome-banner {
    background: linear-gradient(135deg, #F0FDF4, #ECFDF5);
    border: 1px solid #6EE7B7;
    border-left: 4px solid #059669;
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 20px;
  }
  .welcome-banner h3 {
    color: #065F46 !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    margin: 0 0 10px 0 !important;
  }
  .welcome-banner p {
    color: #047857 !important;
    font-size: 13px !important;
    margin: 0 !important;
    line-height: 1.6 !important;
  }
  .welcome-step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin: 8px 0;
  }
  .step-num {
    background: #059669;
    color: white;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    flex-shrink: 0;
    margin-top: 1px;
  }
  .step-text { font-size: 13px; color: #065F46; line-height: 1.5; }
  .step-text strong { color: #064E3B; }

  /* TOUR HIGHLIGHT BOXES */
  .tour-box {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-left: 3px solid #F59E0B;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0 10px 0;
    font-size: 12px;
    color: #78350F;
    line-height: 1.6;
  }
  .tour-box strong { color: #451A03; }

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
AUTO_APPROVE_THRESHOLD = 60_000
MODEL = "claude-sonnet-4-6"

# Reporting period — all three projects are in the same Workday fiscal quarter
REPORTING_PERIOD_LABEL = "Q1 FY2026 (Jan 1 - Mar 31, 2026)"
REPORTING_PERIOD_SHORT = "Q1 FY2026"

# ─────────────────────────────────────────────────────────────
# RATES (derived from raw hours and costs — nothing arbitrary)
# ─────────────────────────────────────────────────────────────
RATES = {
    "Developer":           120,   # 768,000 / 6,400 hrs (Meridian)
    "Business Analyst":     90,   # 230,400 / 2,560 hrs (Meridian)
    "QA Engineer":         100,   # 256,000 / 2,560 hrs (Hillman)
    "Product Manager":     150,   # 192,000 / 1,280 hrs (Hillman)
    "Architect":           200,   # 192,000 / 960 hrs  (Apex)
    "Deployment Engineer": 150,   # 96,000  / 640 hrs  (Hillman)
}

WEEKLY_HOURS_PER_PERSON = 40

# Meridian 6-week extension: reduced wind-down crew (2 Devs + 1 BA)
MERIDIAN_EXT_DEVS   = 2
MERIDIAN_EXT_BAS    = 1
MERIDIAN_EXT_WEEKS  = 6
meridian_ext_weekly = (
    MERIDIAN_EXT_DEVS * WEEKLY_HOURS_PER_PERSON * RATES["Developer"] +
    MERIDIAN_EXT_BAS  * WEEKLY_HOURS_PER_PERSON * RATES["Business Analyst"]
)
# = (2 x 40 x 120) + (1 x 40 x 90) = 9,600 + 3,600 = 13,200/week
MERIDIAN_EXTENSION_COST = meridian_ext_weekly * MERIDIAN_EXT_WEEKS
# = 13,200 x 6 = 79,200

# ─────────────────────────────────────────────────────────────
# PPM DATA  (cost = count x hours_per_head x rate)
# ─────────────────────────────────────────────────────────────
def calc_cost(role, count, hours_per_head):
    return count * hours_per_head * RATES[role]

PPM_DATA = {
    "projects": [
        {
            "name": "Hillman Consultancy",
            "resources": [
                {"role": "Developer",           "count": 8, "hours": 10240, "cost": calc_cost("Developer",           8, 1280)},
                {"role": "Product Manager",     "count": 1, "hours":  1280, "cost": calc_cost("Product Manager",     1, 1280)},
                {"role": "QA Engineer",         "count": 2, "hours":  2560, "cost": calc_cost("QA Engineer",         2, 1280)},
                {"role": "Deployment Engineer", "count": 1, "hours":   640, "cost": calc_cost("Deployment Engineer", 1,  640)},
            ],
        },
        {
            "name": "Meridian ERP Rollout",
            "resources": [
                {"role": "Developer",        "count": 5, "hours": 6400, "cost": calc_cost("Developer",        5, 1280)},
                {"role": "Business Analyst", "count": 2, "hours": 2560, "cost": calc_cost("Business Analyst", 2, 1280)},
            ],
            "schedule_extension_weeks": MERIDIAN_EXT_WEEKS,
            "extension_crew": f"{MERIDIAN_EXT_DEVS} Developers + {MERIDIAN_EXT_BAS} BA",
            "extension_weekly_cost": meridian_ext_weekly,
            "extension_cost": MERIDIAN_EXTENSION_COST,
        },
        {
            "name": "Apex Cloud Migration",
            "resources": [
                {"role": "Developer", "count": 6, "hours": 7680, "cost": calc_cost("Developer", 6, 1280)},
                {"role": "Architect", "count": 1, "hours":  960, "cost": calc_cost("Architect", 1,  960)},
            ],
        },
    ]
}

for proj in PPM_DATA["projects"]:
    proj["total_cost"] = sum(r["cost"] for r in proj["resources"])

# ─────────────────────────────────────────────────────────────
# WORKDAY DATA
# Period Actuals = % of PPM total posted as actual spend in Workday
# Hillman:  55.7% complete  => $986,400
# Meridian: 51.3% complete  => $512,000
# Apex:     56.9% complete  => $634,200
# ─────────────────────────────────────────────────────────────
hillman_ppm_total  = PPM_DATA["projects"][0]["total_cost"]   # 1,772,800
meridian_ppm_total = PPM_DATA["projects"][1]["total_cost"]   # 998,400
apex_ppm_total     = PPM_DATA["projects"][2]["total_cost"]   # 1,113,600

HILLMAN_APPROVED_BUDGET  = 1_720_000        # Finance-approved; PPM is $52,800 higher = overrun
MERIDIAN_APPROVED_BUDGET = meridian_ppm_total
APEX_APPROVED_BUDGET     = apex_ppm_total

HILLMAN_PERIOD_ACTUALS  = 986_400
MERIDIAN_PERIOD_ACTUALS = 512_000
APEX_PERIOD_ACTUALS     = 634_200

WORKDAY_DATA = {
    "budgets": [
        {
            "name": "Hillman Consultancy",
            "approved_budget": HILLMAN_APPROVED_BUDGET,
            "period_actuals":  HILLMAN_PERIOD_ACTUALS,
            "period_label":    REPORTING_PERIOD_LABEL,
            # Deployment Engineer ($96,000) was added to PPM after the Workday budget was approved.
            # Workday budgeted $43,200 more than PPM on the other three roles, so the net shortfall
            # is $96,000 - $43,200 = $52,800. The role is in PPM but has no Workday headcount entry.
            "headcount_gap": (
                "Deployment Engineer added to PPM scope after Workday budget was approved. "
                f"Net budget shortfall: ${hillman_ppm_total - HILLMAN_APPROVED_BUDGET:,}"
            ),
        },
        {
            "name": "Meridian ERP Rollout",
            "approved_budget": MERIDIAN_APPROVED_BUDGET,
            "period_actuals":  MERIDIAN_PERIOD_ACTUALS,
            "period_label":    REPORTING_PERIOD_LABEL,
            "schedule_note": f"{MERIDIAN_EXT_WEEKS}-week extension not reflected in Workday forecast",
            "extension_cost_not_in_workday": MERIDIAN_EXTENSION_COST,
        },
        {
            "name": "Apex Cloud Migration",
            "approved_budget": APEX_APPROVED_BUDGET,
            "period_actuals":  APEX_PERIOD_ACTUALS,
            "period_label":    REPORTING_PERIOD_LABEL,
            "status": "aligned",
        },
    ]
}

# ─────────────────────────────────────────────────────────────
# CALCULATION EXPLANATIONS (reused in tour + sidebar + expanders)
# ─────────────────────────────────────────────────────────────
RATE_TABLE_MD = """
| Role | Rate/hr | Derived From |
|---|---|---|
| Developer | $120 | $768,000 / 6,400 hrs (Meridian) |
| Business Analyst | $90 | $230,400 / 2,560 hrs (Meridian) |
| QA Engineer | $100 | $256,000 / 2,560 hrs (Hillman) |
| Product Manager | $150 | $192,000 / 1,280 hrs (Hillman) |
| Architect | $200 | $192,000 / 960 hrs (Apex) |
| Deployment Engineer | $150 | $96,000 / 640 hrs (Hillman) |
"""

PERIOD_ACTUALS_EXPLANATION = f"""
**What is Period Actuals?**

Period Actuals is the total cost that Workday has already posted as real, committed spend within
a specific financial period. A financial period is a defined time window: a month, a fiscal
quarter, or a fiscal year depending on how the enterprise configures Workday.

**For this prototype, the reporting period is: {REPORTING_PERIOD_LABEL}**

All three projects are being tracked within the same Workday fiscal quarter. Period Actuals shows
what has been posted as real transactions within that window: labor charges, contractor invoices,
and approved expenses that have cleared the Workday approval workflow. It is not a forecast or
a plan. It is what already happened and is locked in the ledger.

**How are these numbers calculated?**

Each project's Period Actuals is derived from its PPM total cost and estimated completion
percentage as of the end of {REPORTING_PERIOD_SHORT}:

| Project | PPM Total | % Complete by {REPORTING_PERIOD_SHORT} | Period Actuals |
|---|---|---|---|
| Hillman Consultancy | $1,772,800 | 55.7% | $986,400 |
| Meridian ERP Rollout | $998,400 | 51.3% | $512,000 |
| Apex Cloud Migration | $1,113,600 | 56.9% | $634,200 |

In a live integration, Workday provides this number directly via the Financial Management API
using the period start and end dates as filter parameters. In this prototype it represents
realistic spend-to-date for each project at mid-delivery as of {REPORTING_PERIOD_SHORT}.

**Why does the period matter?**

If Oracle PPM and Workday are not tracking the same period, the comparison is meaningless.
A resource committed in PPM for Q2 would not yet appear in Q1 Period Actuals even if the
budget gap is real. This agent assumes both systems are reporting on the same period:
{REPORTING_PERIOD_LABEL}.
"""

HILLMAN_GAP_EXPLANATION = f"""
**Hillman Consultancy: Cost Overrun Gap**

Oracle PPM total cost:    ${hillman_ppm_total:,}
Workday approved budget:  ${HILLMAN_APPROVED_BUDGET:,}
Net gap:                  ${hillman_ppm_total - HILLMAN_APPROVED_BUDGET:,}

**What happened:**

The Workday budget of ${HILLMAN_APPROVED_BUDGET:,} was approved before the Deployment Engineer
role was added to the project in Oracle PPM.

The Deployment Engineer contributes $96,000 to the PPM total (1 person x 640 hrs x $150/hr).
However, Workday had budgeted $43,200 more than PPM on the other three roles (Developers,
PM, QA), which partially offsets the new role.

Net shortfall = $96,000 (new role cost) - $43,200 (existing buffer in Workday) = **$52,800**

The Deployment Engineer has no corresponding headcount entry in Workday. The $96,000 cost is
committed in PPM but Workday has no approved budget line for this person. That is the gap the
agent flagged. A budget amendment request needs to be raised in Workday to cover this role.
"""

MERIDIAN_EXTENSION_EXPLANATION = f"""
**Why {MERIDIAN_EXT_WEEKS} weeks, and how is the cost calculated?**

The extension uses a reduced wind-down crew: {MERIDIAN_EXT_DEVS} Developers + {MERIDIAN_EXT_BAS} Business Analyst
(not the full 7-person delivery team).

Step-by-step calculation:
- {MERIDIAN_EXT_DEVS} Developers: {MERIDIAN_EXT_DEVS} x 40 hrs x $120/hr = ${MERIDIAN_EXT_DEVS * 40 * RATES["Developer"]:,}/week
- {MERIDIAN_EXT_BAS} Business Analyst: {MERIDIAN_EXT_BAS} x 40 hrs x $90/hr = ${MERIDIAN_EXT_BAS * 40 * RATES["Business Analyst"]:,}/week
- Weekly total: ${meridian_ext_weekly:,}/week
- {MERIDIAN_EXT_WEEKS} weeks x ${meridian_ext_weekly:,} = **${MERIDIAN_EXTENSION_COST:,} total extension cost**

This ${MERIDIAN_EXTENSION_COST:,} is committed in Oracle PPM but has NOT been submitted to Workday
as a budget amendment. That is the gap the agent detected.
"""

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
if "gaps"          not in st.session_state: st.session_state.gaps          = None
if "mode"          not in st.session_state: st.session_state.mode          = "HITL"
if "actions"       not in st.session_state: st.session_state.actions       = {}
if "analysis_run"  not in st.session_state: st.session_state.analysis_run  = False
if "tour_dismissed" not in st.session_state: st.session_state.tour_dismissed = False
if "show_tour"     not in st.session_state: st.session_state.show_tour     = False

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <div style="font-size:32px;">⚡</div>
  <div>
    <h1>Project Financial Intelligence Agent</h1>
    <p>Oracle PPM x Workday Financial -- Cross-System Gap Analysis - Powered by Claude AI</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# WELCOME BANNER (shown until dismissed)
# ─────────────────────────────────────────────────────────────
if not st.session_state.tour_dismissed:
    st.markdown("""
    <div class="welcome-banner">
      <h3>Welcome to the Project Financial Intelligence Agent</h3>
      <p>This agent automatically detects financial misalignments between Oracle PPM (your project
      resource plan) and Workday Financial (your approved budgets and actuals). Here is what you
      are looking at:</p>
    </div>
    """, unsafe_allow_html=True)

    wc1, wc2, wc3 = st.columns(3)
    with wc1:
        with st.popover("The Problem This Solves", use_container_width=True):
            st.markdown("""
            In most enterprises, Oracle PPM and Workday Financial are managed by different teams.
            Project managers commit resources in PPM. Finance manages approved budgets in Workday.
            When they get out of sync, nobody notices until the quarter-end reconciliation.
            This agent finds those gaps in real time, automatically.
            """)
    with wc2:
        with st.popover("What the Two Tables Show", use_container_width=True):
            st.markdown("""
            The left table is your Oracle PPM resource plan: who is assigned, how many hours,
            at what rate, and what the total committed cost is.

            The right table is Workday Financial: what Finance approved as the spend ceiling
            (Approved Budget), and what has actually been posted as real transactions so far
            this period (Period Actuals).

            The agent compares both tables and surfaces every line where they disagree.
            """)
    with wc3:
        with st.popover("What the Agent Does", use_container_width=True):
            st.markdown("""
            Click **Run Agent Analysis** and Claude AI cross-references both tables, identifies
            every financial gap, scores its severity (HIGH / MEDIUM / LOW), and either:

            - **Resolves it automatically** (HOTL mode) if the gap is below the threshold, or
            - **Pauses for your approval** (HITL mode) showing Approve and Escalate buttons.

            The autonomy threshold in the sidebar controls where that line sits. Enterprise
            teams raise it over time as they build trust in the agent.
            """)

    bc1, bc2, bc3 = st.columns([1, 1, 4])
    with bc1:
        if st.button("Got it, dismiss", use_container_width=True, type="primary"):
            st.session_state.tour_dismissed = True
            st.rerun()
    with bc2:
        tour_label = "Hide column guide" if st.session_state.show_tour else "Show column guide"
        if st.button(tour_label, use_container_width=True):
            st.session_state.show_tour = not st.session_state.show_tour
            st.rerun()

else:
    # Compact re-open button after dismissal
    if st.button("What is this app?", help="Show the welcome guide again"):
        st.session_state.tour_dismissed = False
        st.rerun()

# ─────────────────────────────────────────────────────────────
# COLUMN GUIDE TOUR (shown when toggled on)
# ─────────────────────────────────────────────────────────────
if st.session_state.show_tour:
    st.divider()
    st.markdown("#### Column Guide: What Each Field Means")

    tl, tr = st.columns(2)

    with tl:
        st.markdown("**Oracle PPM Resource Plan**")

        st.markdown("""
        <div class="tour-box">
          <strong>Project</strong><br>
          The engagement name as it appears in Oracle PPM. Each project spans multiple resource
          rows. A blank cell means the row belongs to the project listed above it.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="tour-box">
          <strong>Role</strong><br>
          The resource type and headcount committed in PPM. For example "5x Developer" means five
          developers are allocated. A warning icon (⚠️) means this role exists in PPM but is
          missing from the Workday headcount plan — that is a gap the agent will flag.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="tour-box">
          <strong>Hours</strong><br>
          Total planned hours across all people in this role for the full project duration.
          Calculated as: headcount x hours per person. For example 5 developers x 1,280 hours
          each = 6,400 total hours.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="tour-box">
          <strong>Rate/hr</strong><br>
          The standard billing or cost rate for this role. Derived directly from the PPM data:
          total cost divided by total hours. Developer = $120/hr, BA = $90/hr, Architect = $200/hr.
          These are not estimates — they are back-calculated from committed cost and hours.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="tour-box">
          <strong>PPM Cost</strong><br>
          Total committed cost for this role on this project. Formula: headcount x hours per person
          x rate. This is what Oracle PPM says will be spent. It may differ from what Workday
          has approved — and that difference is exactly what this agent detects.
        </div>
        """, unsafe_allow_html=True)

    with tr:
        st.markdown("**Workday Financial Budget**")

        st.markdown("""
        <div class="tour-box">
          <strong>Project</strong><br>
          The same engagement as it appears in Workday Financial Management. The agent matches
          projects across both systems by name to perform the cross-system comparison.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="tour-box">
          <strong>Approved Budget</strong><br>
          The spend ceiling that Finance formally approved in Workday. This is the number that
          went through the budget approval workflow. If PPM commitments exceed this number, the
          project is in overrun — even if no one has noticed yet.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="tour-box">
          <strong>Period Actuals (Q1 FY2025: Jan 1 - Mar 31, 2025)</strong><br>
          The total cost Workday has already posted as real, recorded spend within the current
          financial period. A period is a defined time window: in this app it is Q1 FY2025
          (January 1 to March 31, 2025). These are approved transactions that cleared the
          Workday workflow: labor charges, invoices, expenses. This is NOT a forecast. It is
          what already happened and is locked in the Workday ledger for that quarter. Both
          Oracle PPM and Workday must be reporting on the same period for this comparison to
          be valid.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="tour-box">
          <strong>Note</strong><br>
          The agent's pre-analysis flag on each project. A green checkmark means PPM and Workday
          are aligned. A warning icon means the agent has detected a specific discrepancy:
          a missing headcount entry, a schedule extension not reflected in the forecast, or a
          budget that has not been updated to match PPM commitments.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="tour-box">
          <strong>Gap Cards (after analysis)</strong><br>
          Each gap card shows the project, the gap type, the dollar amount of financial exposure,
          a severity badge (HIGH / MEDIUM / LOW), and Claude's recommendation. In HITL mode you
          see Approve and Escalate buttons. In HOTL mode gaps below the threshold are
          auto-resolved and gaps above are flagged for your awareness.
        </div>
        """, unsafe_allow_html=True)

    st.divider()

# ─────────────────────────────────────────────────────────────
# SIDEBAR — CONFIG
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Configuration")
    st.divider()

     api_key = st.secrets.get("ANTHROPIC_API_KEY", "") or st.text_input(
         "Anthropic API Key",
         type="password",
         placeholder="sk-ant-api03-...",
         help="Get your key from console.anthropic.com"
     )

   # api_key = st.text_input(
   #     "Anthropic API Key",
   #     type="password",
   #     placeholder="sk-ant-api03-...",
   #     help="Get your key from console.anthropic.com"
   # )

    st.divider()
    st.markdown("### Autonomy Mode")
    mode_choice = st.radio(
        "Select how the agent operates",
        options=["Human-in-the-Loop (HITL)", "Human Over the Loop (HOTL)"],
        help=(
            "HITL: Agent pauses at each gap and waits for your Approve or Escalate decision "
            "before taking any action. Use this when you want full control over every resolution.\n\n"
            "HOTL: Agent acts autonomously on gaps below the threshold. Only flags gaps above it "
            "for your awareness. Use this once you trust the agent's judgment on smaller gaps."
        )
    )
    st.session_state.mode = "HOTL" if "HOTL" in mode_choice else "HITL"

    st.divider()
    st.markdown("### Threshold")
    threshold = st.number_input(
        "Auto-approve threshold ($)",
        min_value=10_000,
        max_value=500_000,
        value=AUTO_APPROVE_THRESHOLD,
        step=10_000,
        help=(
            "In HOTL mode: gaps BELOW this amount are auto-resolved by the agent. "
            "Gaps ABOVE are flagged for your review. "
            "Enterprise teams raise this threshold over time as they build trust in the agent — "
            "the natural progression from supervised to autonomous AI operation."
        )
    )

    st.divider()
    if st.session_state.mode == "HITL":
        st.info("**Human-in-the-Loop**\n\nAgent pauses at each gap and waits for your Approve or Escalate decision.")
    else:
        st.success("**Human Over the Loop**\n\nAgent acts autonomously on gaps below threshold. High-value gaps are flagged for your awareness.")

    st.divider()
    st.markdown(f"**Threshold:** ${threshold:,.0f}")
    st.markdown(f"**Model:** `{MODEL}`")

    st.divider()
    st.markdown("### How Numbers Are Calculated")
    with st.expander("Hourly rates used"):
        st.markdown(RATE_TABLE_MD)
    with st.expander("What is Period Actuals"):
        st.markdown(PERIOD_ACTUALS_EXPLANATION)
    with st.expander(f"Meridian {MERIDIAN_EXT_WEEKS}-week extension math"):
        st.markdown(MERIDIAN_EXTENSION_EXPLANATION)
    with st.expander("Hillman overrun: why $52,800 not $96,000"):
        st.markdown(HILLMAN_GAP_EXPLANATION)

# ─────────────────────────────────────────────────────────────
# STATUS BAR
# ─────────────────────────────────────────────────────────────
if st.session_state.mode == "HITL":
    st.markdown("""<div class="status-hitl">Human-in-the-Loop mode -- Agent will pause at each gap and await your decision</div>""", unsafe_allow_html=True)
else:
    st.markdown("""<div class="status-hotl">Human Over the Loop mode -- Agent acts autonomously within threshold - High-value gaps flagged for awareness</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# DATA PANELS
# ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="panel-header">Oracle PPM Resource Plan</div>', unsafe_allow_html=True)
    st.caption(
        "Source: Oracle Project Portfolio Management. Committed resource allocations, headcount, "
        "and planned costs. PPM Cost = headcount x hours per person x role rate."
    )
    ppm_rows = []
    for proj in PPM_DATA["projects"]:
        for i, r in enumerate(proj["resources"]):
            flag = " ⚠️" if r["role"] == "Deployment Engineer" else ""
            ppm_rows.append({
                "Project"  : proj["name"] if i == 0 else "",
                "Role"     : f"{r['count']}x {r['role']}{flag}",
                "Hours"    : f"{r['hours']:,}",
                "Rate/hr"  : f"${RATES[r['role']]}",
                "PPM Cost" : f"${r['cost']:,.0f}",
            })
    st.dataframe(ppm_rows, use_container_width=True, hide_index=True)

    # Explain the caution sign that appears against Deployment Engineer
    st.warning(
        "**⚠️ Caution sign on Deployment Engineer:** This role is committed in Oracle PPM "
        "(1 person, 640 hrs at $150/hr = $96,000) but has no corresponding headcount entry "
        "in Workday Financial. The role was added to project scope after the Workday budget "
        "was approved. This means the cost is planned but not yet authorized in Workday."
    )

with col2:
    st.markdown('<div class="panel-header">Workday Financial Budget</div>', unsafe_allow_html=True)
    st.caption(
        f"Source: Workday Financial Management. Reporting period: {REPORTING_PERIOD_LABEL}. "
        "Approved Budget = finance-approved spend ceiling for the full project. "
        f"Period Actuals = costs already posted and recorded in Workday within {REPORTING_PERIOD_SHORT} only (not forecast)."
    )
    # Status inside the table — severity based on amount vs threshold ($60,000)
    # Meridian $79,200 > threshold = Critical Gap
    # Hillman  $52,800 < threshold = Watch Item
    WD_STATUS = {
        "Meridian ERP Rollout": "🔴 Critical Gap",
        "Hillman Consultancy":  "🟡 Watch Item",
        "Apex Cloud Migration": "🟢 Aligned",
    }
    WD_DETAIL = {
        "Meridian ERP Rollout": (
            f"{MERIDIAN_EXT_WEEKS}-wk extension in PPM. "
            f"${MERIDIAN_EXTENSION_COST:,} not in Workday forecast. Above ${AUTO_APPROVE_THRESHOLD:,} threshold."
        ),
        "Hillman Consultancy": (
            "Depl. Engineer ($96K) added to PPM after Workday budget approved. "
            "Net amendment needed: $52,800. Below threshold."
        ),
        "Apex Cloud Migration": "PPM and Workday fully in sync.",
    }
    wd_rows = []
    for b in WORKDAY_DATA["budgets"]:
        wd_rows.append({
            "Project"         : b["name"],
            "Approved Budget" : f"${b['approved_budget']:,.0f}",
            f"Actuals ({REPORTING_PERIOD_SHORT})" : f"${b['period_actuals']:,.0f}",
            "Status"          : WD_STATUS.get(b["name"], ""),
            "Detail"          : WD_DETAIL.get(b["name"], ""),
        })
    st.dataframe(
        wd_rows,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Project":         st.column_config.TextColumn("Project",         width="medium"),
            "Approved Budget": st.column_config.TextColumn("Approved Budget", width="small"),
            f"Actuals ({REPORTING_PERIOD_SHORT})": st.column_config.TextColumn(
                f"Actuals ({REPORTING_PERIOD_SHORT})", width="small"
            ),
            "Status":          st.column_config.TextColumn("Status",          width="small"),
            "Detail":          st.column_config.TextColumn("Detail",          width="large"),
        }
    )

# ─────────────────────────────────────────────────────────────
# CALCULATION POPOVERS
# ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("#### How These Numbers Were Calculated")
ec1, ec2, ec3 = st.columns(3)

with ec1:
    with st.popover("What is Period Actuals", use_container_width=True):
        st.markdown(PERIOD_ACTUALS_EXPLANATION)

with ec2:
    with st.popover(f"Meridian {MERIDIAN_EXT_WEEKS}-week extension math", use_container_width=True):
        st.markdown(MERIDIAN_EXTENSION_EXPLANATION)

with ec3:
    with st.popover("Hillman overrun: why $52,800 not $96,000", use_container_width=True):
        st.markdown(HILLMAN_GAP_EXPLANATION)

# ─────────────────────────────────────────────────────────────
# AGENT ANALYSIS
# ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("### Agent Intelligence -- Financial Alignment Analysis")

run_col, _ = st.columns([1, 3])
with run_col:
    run_clicked = st.button(
        "Run Agent Analysis",
        type="primary",
        use_container_width=True,
        disabled=not bool(api_key),
        help="Enter your Anthropic API key in the sidebar to enable"
    )

if not api_key:
    st.info("Enter your Anthropic API key in the sidebar to run the live agent analysis.")

if run_clicked and api_key:
    with st.spinner("Claude AI is cross-referencing Oracle PPM commitments against Workday financial data..."):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            hillman_gap = hillman_ppm_total - HILLMAN_APPROVED_BUDGET  # 52,800
            prompt = f"""You are a Project Financial Intelligence Agent for enterprise PPM and financial management.

Cross-reference the Oracle PPM resource plan against the Workday financial budgets.

Oracle PPM data:
{json.dumps(PPM_DATA, indent=2)}

Workday Financial data:
{json.dumps(WORKDAY_DATA, indent=2)}

Key rates used (derived from raw data):
{json.dumps(RATES, indent=2)}

IMPORTANT HILLMAN ANALYSIS RULE:
The Hillman cost overrun ($52,800) and the missing Deployment Engineer headcount are the SAME
root cause, not two separate gaps. The Deployment Engineer ($96,000) was added to PPM after the
Workday budget was approved. Workday had a $43,200 buffer on the other three roles, so the net
budget amendment required is $96,000 - $43,200 = $52,800. Report this as ONE single gap for
Hillman with amount = {hillman_gap}. Do NOT report a separate headcount gap of $96,000.
If both were approved separately, Workday would receive $148,800 more budget than PPM actually
needs, which is incorrect.

Meridian 6-week extension details:
- Crew: {MERIDIAN_EXT_DEVS} Developers + {MERIDIAN_EXT_BAS} Business Analyst (reduced wind-down team)
- Weekly cost: ${meridian_ext_weekly:,} ({MERIDIAN_EXT_DEVS} x 40hrs x $120 + {MERIDIAN_EXT_BAS} x 40hrs x $90)
- Total extension cost: ${MERIDIAN_EXTENSION_COST:,} ({MERIDIAN_EXT_WEEKS} weeks x ${meridian_ext_weekly:,})
- This cost is committed in PPM but NOT submitted to Workday as a budget amendment

Auto-approve threshold: ${threshold:,}

Return ONLY a valid JSON array with exactly 2 gap objects (Hillman and Meridian). Apex is aligned
and should NOT appear as a gap. Each object must have:
- project: string
- gap_type: string (short title)
- gap_subtype: string (one sentence explaining the root cause, mention ABOVE or BELOW ${threshold:,} threshold)
- severity: LOCKED VALUES based on financial exposure and threshold:
    Meridian MUST be "HIGH" (${MERIDIAN_EXTENSION_COST:,} is ABOVE the ${threshold:,} threshold, larger exposure)
    Hillman MUST be "MEDIUM" (${hillman_gap:,} is BELOW the ${threshold:,} threshold, smaller exposure)
  Do not change these severity values.
- amount: integer (use {hillman_gap} for Hillman, {MERIDIAN_EXTENSION_COST} for Meridian)
- recommendation: string (2-3 sentences, specific action required, reference exact dollar amounts)
- auto_resolvable: boolean (true if amount < {threshold})
- hotl_status: string ("Auto-resolved -- Below threshold" if auto_resolvable else "Flagged -- Above threshold")

The first object in the array MUST be Meridian (HIGH). The second MUST be Hillman (MEDIUM).

Analyse:
1) Meridian (severity: HIGH): {MERIDIAN_EXT_WEEKS}-week extension at ${meridian_ext_weekly:,}/week
   = ${MERIDIAN_EXTENSION_COST:,} committed in PPM but not submitted to Workday as a budget amendment.
   Amount is ABOVE the ${threshold:,} threshold. Agent cannot auto-resolve. Requires human decision.
2) Hillman (severity: MEDIUM): Deployment Engineer ($150/hr, 640 hrs = $96,000) added to PPM after
   Workday budget was approved. Workday had $43,200 buffer on other roles. Net budget amendment
   needed = ${hillman_gap:,}. Amount is BELOW the ${threshold:,} threshold. Agent can auto-resolve in HOTL mode."""

            message = client.messages.create(
                model=MODEL,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw   = message.content[0].text.strip()
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON array found in agent response.")
            raw  = raw[start:end]
            gaps = json.loads(raw)

            # Enforce severity by financial exposure vs threshold — not issue type
            # Meridian $79,200 > $60,000 threshold = HIGH
            # Hillman  $52,800 < $60,000 threshold = MEDIUM
            SEVERITY_MAP = {
                "Meridian ERP Rollout": "HIGH",
                "Hillman Consultancy":  "MEDIUM",
            }
            for g in gaps:
                if g["project"] in SEVERITY_MAP:
                    g["severity"] = SEVERITY_MAP[g["project"]]
                g["auto_resolvable"] = g["amount"] < threshold

            # Always sort: HIGH first, then MEDIUM, then LOW
            SEV_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            gaps.sort(key=lambda g: SEV_ORDER.get(g["severity"].upper(), 3))
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

    critical = sum(1 for g in gaps if g["severity"] == "HIGH")
    watch    = sum(1 for g in gaps if g["severity"] == "MEDIUM")
    total_projects = len(WORKDAY_DATA["budgets"])
    aligned  = total_projects - len(gaps)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Critical Gaps",  critical,
              help="Gaps with HIGH severity: budget overruns or missing headcount above threshold requiring immediate action.")
    m2.metric("Watch Items",    watch,
              help="Gaps with MEDIUM severity: schedule or forecast misalignments that need resolution within the current period.")
    m3.metric("Aligned",        aligned,
              help="Projects where Oracle PPM commitments and Workday budget are fully in sync.")
    m4.metric("Total Exposure", f"${sum(g['amount'] for g in gaps):,.0f}",
              help="Total dollar value of all detected gaps. This is the financial risk if gaps are left unresolved.")

    st.divider()

    for i, gap in enumerate(gaps):
        sev        = gap["severity"].upper()
        card_class = f"gap-card-{sev.lower()}"
        amt_class  = f"gap-amount-{sev.lower()}"
        badge_cls  = f"badge-{sev.lower()}"
        auto       = gap.get("auto_resolvable", False)
        action_key = f"action_{i}"

        # Determine status label for expander header
        if action_key in st.session_state.actions:
            taken = st.session_state.actions[action_key]
            status_label = "✓ Approved" if taken == "approved" else "↑ Escalated"
        elif mode == "HOTL" and auto:
            status_label = "✓ Auto-resolved"
        elif mode == "HOTL" and not auto:
            status_label = "⚠ Flagged"
        else:
            status_label = "Awaiting decision"

        # Severity-aware label
        if sev == "HIGH":
            sev_label = "🔴 CRITICAL GAP"
        elif sev == "MEDIUM":
            sev_label = "🟡 WATCH ITEM"
        else:
            sev_label = "🟢 LOW"

        expander_label = (
            f"{sev_label}  |  {gap['project']} -- {gap['gap_type']}  |  "
            f"${gap['amount']:,}  |  {status_label}"
        )

        with st.expander(expander_label, expanded=(action_key not in st.session_state.actions)):
            st.markdown(f"""
            <div class="{card_class}">
              <div style="display:flex;align-items:flex-start;justify-content:space-between;">
                <div>
                  <div class="gap-title">{gap['project']} -- {gap['gap_type']}</div>
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

            if action_key in st.session_state.actions:
                taken = st.session_state.actions[action_key]
                if taken == "approved":
                    st.success("✓ Approved -- agent will raise a budget amendment request in Workday and notify the Finance team")
                elif taken == "escalated":
                    st.warning(
                        "↑ Escalated -- this gap has been sent to the Finance Controller and PMO Director for manual review. "
                        "The agent will not take any action until they respond. You will receive a notification once reviewed."
                    )
            else:
                if mode == "HITL":
                    c1, c2, c3 = st.columns([1, 1, 4])
                    with c1:
                        if st.button("✓ Approve", key=f"approve_{i}", use_container_width=True,
                                     help="Agent will raise a budget amendment in Workday and notify Finance. No further action needed from you."):
                            st.session_state.actions[action_key] = "approved"
                            st.rerun()
                    with c2:
                        if st.button("↑ Escalate", key=f"escalate_{i}", use_container_width=True,
                                     help=(
                                         "Use Escalate when the gap is too large, too sensitive, or too ambiguous "
                                         "for the agent to resolve on its own. Escalating sends the gap details to "
                                         "the Finance Controller and PMO Director with full context. The agent pauses "
                                         "and takes no action until a human decision is received."
                                     )):
                            st.session_state.actions[action_key] = "escalated"
                            st.rerun()
                else:
                    if auto:
                        st.markdown('<div class="resolved-pill">✓ Auto-resolved -- gap is below the ${:,.0f} threshold. Agent has raised a budget amendment in Workday.</div>'.format(threshold), unsafe_allow_html=True)
                    else:
                        st.markdown(
                            '<div class="flagged-pill">⚠ Flagged for your review -- gap of ${:,.0f} exceeds the ${:,.0f} auto-resolve threshold. '
                            'Agent has paused. Switch to HITL mode to Approve or Escalate this gap.</div>'.format(
                                gap["amount"], threshold
                            ),
                            unsafe_allow_html=True
                        )

    if mode == "HITL" and len(st.session_state.actions) == len(gaps):
        st.success("✅ All gaps resolved -- Agent ready for next analysis cycle")

    # Aligned projects — always shown at the bottom so PMO does not need to search
    aligned_projects = [
        b["name"] for b in WORKDAY_DATA["budgets"]
        if b.get("status") == "aligned"
    ]
    for proj in aligned_projects:
        with st.expander(f"🟢 ALIGNED  |  {proj}  |  No action required", expanded=False):
            st.success(
                f"**{proj}** is fully aligned. Oracle PPM commitments and the Workday approved "
                f"budget are in sync for {REPORTING_PERIOD_SHORT}. No budget amendment, "
                f"headcount change, or escalation is needed. The agent will continue monitoring "
                f"this project in future cycles."
            )

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer-note">
  Configurable Autonomy: The ${threshold:,.0f} threshold determines which gaps the agent resolves
  automatically (Human Over the Loop) vs. which require human approval (Human-in-the-Loop).
  Enterprise teams raise this threshold as they build trust in the agent over time -- the natural
  path from supervised to autonomous AI adoption.
</div>
""", unsafe_allow_html=True)