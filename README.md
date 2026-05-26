# PPM & Workday Financial Gap Agent

**Live Demo:** [ppm-workday-financial-gap-agent.streamlit.app](https://ppm-workday-financial-gap-agent.streamlit.app)

An AI agent that cross-references Oracle Project Portfolio Management (PPM) resource commitments against Workday Financial approved budgets, detects financial gaps, and either resolves them autonomously or surfaces them for human approval depending on a configurable threshold.

Built as a proof of concept to demonstrate agentic AI applied to a real enterprise finance problem: budget misalignments between Oracle PPM and Workday Financial that typically go undetected until quarter-end reconciliation.

---

## The Problem

In most enterprises that run Oracle PPM alongside Workday Financial, two teams manage the same financial reality in two different systems:

- **Project managers** commit resources and costs in Oracle PPM
- **Finance teams** manage approved budgets and actuals in Workday Financial

When scope changes, roles are added, or schedules extend, Oracle PPM gets updated but Workday often does not. The gap accumulates silently until quarter-end reconciliation, by which point it is expensive and disruptive to fix.

---

## What the Agent Does

1. Reads the Oracle PPM resource plan (committed headcount, hours, rates, costs)
2. Reads the Workday Financial budget (approved budget, period actuals)
3. Cross-references both systems using Claude AI to identify every financial gap
4. Scores each gap by severity based on dollar amount vs a configurable threshold
5. In **Human-in-the-Loop (HITL)** mode: surfaces each gap with Approve and Escalate buttons
6. In **Human Over the Loop (HOTL)** mode: auto-resolves gaps below the threshold, flags gaps above it

In this prototype the analysis is triggered on demand. In a production environment this would run automatically at period close or on any budget change event in either system.

---

## Demo Scenarios

The app uses three simulated projects to demonstrate different gap types:

| Project | Gap Type | Amount | Severity |
|---|---|---|---|
| Meridian ERP Rollout | 6-week schedule extension not submitted to Workday | $79,200 | 🔴 Critical Gap |
| Hillman Consultancy | Deployment Engineer added to PPM after Workday budget approved | $52,800 | 🟡 Watch Item |
| Apex Cloud Migration | None | $0 | 🟢 Aligned |

All dollar amounts are derived from real rate calculations, not hardcoded. Every number is traceable back to hours and role rates.

---

## Autonomy Modes

| Mode | How it works |
|---|---|
| **HITL (Human-in-the-Loop)** | Agent pauses at each gap. PMO sees Approve and Escalate buttons. No action taken without explicit human decision. |
| **HOTL (Human Over the Loop)** | Agent auto-resolves gaps below the threshold. Gaps above the threshold are flagged for human review. PMO sets objectives and monitors outcomes. |

The autonomy threshold is configurable (default $60,000). Enterprise teams raise it over time as they build trust in the agent, moving naturally from supervised to autonomous operation.

---

## Tech Stack

| Component | Technology |
|---|---|
| AI Agent | Anthropic Claude API (claude-sonnet-4-6) |
| Frontend | Streamlit |
| IDE | Cursor |
| Version Control | GitHub |
| Deployment | Streamlit Cloud |
| Language | Python |

---

## Key Design Decisions

**Severity based on financial exposure, not issue type.** A gap above the auto-approve threshold is Critical regardless of what caused it. A gap below the threshold is a Watch Item. This makes severity consistent, defensible, and scalable to any number of projects.

**One gap per root cause.** The Hillman Deployment Engineer issue is reported as a single $52,800 gap, not two separate gaps ($96,000 headcount + $52,800 overrun). Reporting both would result in double the budget amendment if both were approved.

**All calculations derived, nothing hardcoded.** Every dollar amount in the app is the result of a calculation: headcount x hours x rate. The 6-week Meridian extension cost ($79,200) is derived from the crew size (2 Developers + 1 BA), weekly hours (40), and role rates ($120/hr and $90/hr).

---

## Running Locally

**Requirements:**
```
streamlit>=1.32.0
anthropic
```

**Install:**
```bash
pip install -r requirements.txt
```

**Run:**
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) and enter your Anthropic API key in the sidebar.

**To use Streamlit Secrets instead of manual key entry**, add to `.streamlit/secrets.toml`:
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-..."
```
Then uncomment the `st.secrets` line and comment out the `st.text_input` line in `app.py`.

---

## Author

**Sanjay Kumar Kannojia**
Senior Principal Product Manager | AI Agent Platform PM

26 years enterprise PPM domain experience at Oracle America. Designed and shipped two production AI agents (Resource Optimization and Project Forecasting) embedded inside Oracle Fusion PPM. Currently completing Johns Hopkins Agentic AI certificate program.

[LinkedIn](https://www.linkedin.com/in/skannojia/)