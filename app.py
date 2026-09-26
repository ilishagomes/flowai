"""
FlowAI - AI Workflow Discovery & Adoption Assistant

A nontechnical employee describes a repetitive work task in plain English.
FlowAI analyzes it and produces:
  1. An AI Opportunity Map (what to automate, what stays human)
  2. An AI-assisted workflow diagram (who does each step)
  3. An implementation plan
  4. A before/after time-savings estimate
  5. An adoption plan (training, pilot, risks, success metrics)

Run locally:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...   # optional - app works offline without it
    streamlit run app.py
"""

import streamlit as st

from src.adoption_planner import generate_adoption_plan
from src.impact_estimator import estimate_impact
from src.workflow_analyzer import analyze_workflow

st.set_page_config(page_title="FlowAI - AI Workflow Discovery", page_icon="🧭", layout="wide")

EXAMPLE_WORKFLOW = (
    "Every Monday I take sales data from Excel, summarize the week's performance, "
    "identify unusual changes, and email my manager a report."
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "adoption" not in st.session_state:
    st.session_state.adoption = None
if "workflow_text" not in st.session_state:
    st.session_state.workflow_text = ""


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🧭 FlowAI")
st.caption("Find where AI fits in your workflow")

import os
if not os.environ.get("ANTHROPIC_API_KEY"):
    st.caption("⚠️ Offline demo mode — set ANTHROPIC_API_KEY for real AI analysis.")

# ---------------------------------------------------------------------------
# Step 1: Describe workflow
# ---------------------------------------------------------------------------
st.subheader("Describe your workflow")

col_input, col_button = st.columns([4, 1])
with col_input:
    workflow_text = st.text_area(
        "What do you do, step by step?",
        value=st.session_state.workflow_text,
        placeholder=EXAMPLE_WORKFLOW,
        height=100,
        label_visibility="collapsed",
    )
with col_button:
    st.write("")
    st.write("")
    use_example = st.button("Use example", use_container_width=True)

if use_example:
    workflow_text = EXAMPLE_WORKFLOW
    st.session_state.workflow_text = EXAMPLE_WORKFLOW
    st.rerun()

col_a, col_b, col_c = st.columns(3)
with col_a:
    runs_per_week = st.number_input("Times / week", min_value=1, max_value=50, value=1)
with col_b:
    current_minutes_override = st.number_input(
        "Current minutes / run (optional)", min_value=0, max_value=600, value=0,
        help="Leave at 0 to auto-estimate.",
    )
with col_c:
    hourly_rate = st.number_input("Hourly cost ($)", min_value=0, value=40)

analyze_clicked = st.button("🔍 Analyze", type="primary")

if analyze_clicked:
    if not workflow_text.strip():
        st.warning("Describe a workflow first.")
    else:
        st.session_state.workflow_text = workflow_text
        with st.spinner("Analyzing..."):
            analysis = analyze_workflow(workflow_text)
            st.session_state.analysis = analysis
        with st.spinner("Drafting adoption plan..."):
            st.session_state.adoption = generate_adoption_plan(
                workflow_text, analysis["opportunity_map"]
            )

analysis = st.session_state.analysis
adoption = st.session_state.adoption

if analysis is None:
    st.stop()

if analysis["meta"]["source"] == "offline" and analysis["meta"].get("note"):
    st.caption(f"ℹ️ {analysis['meta']['note']}")

st.divider()

# ---------------------------------------------------------------------------
# Step 2: AI Opportunity Map
# ---------------------------------------------------------------------------
st.subheader("Opportunity map")

potential_rank = {"High": 4, "Medium-High": 3, "Medium": 2, "Low-Medium": 1, "Low": 0}
potential_color = {
    "High": "🟢", "Medium-High": "🟢", "Medium": "🟡", "Low-Medium": "🟠", "Low": "🔴",
}

for item in analysis["opportunity_map"]:
    badge = potential_color.get(item["automation_potential"], "⚪")
    with st.expander(f"{badge}  **{item['task']}**  ·  {item['category']}  ·  {item['automation_potential']}"):
        st.markdown(f"**Approach:** {item['recommended_approach']}")
        st.markdown(f"**Human role:** {item['human_role']}")

st.divider()

# ---------------------------------------------------------------------------
# Step 3: AI-assisted workflow
# ---------------------------------------------------------------------------
st.subheader("AI-assisted workflow")

steps = analysis["workflow_steps"]
for i, step in enumerate(steps):
    actor = step["actor"]
    icon = "🤖" if actor == "AI" else "🙋"
    tag_color = "blue" if actor == "AI" else "orange"
    st.markdown(f"**{i + 1}.** {icon} :{tag_color}[{actor}] — {step['step']}")
    if i < len(steps) - 1:
        st.markdown("<div style='text-align:center; color:#999;'>↓</div>", unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# Step 4: Implementation Plan
# ---------------------------------------------------------------------------
st.subheader("Implementation plan")

for i, step in enumerate(analysis["implementation_plan"], start=1):
    st.markdown(f"**{i}. {step['step']}**")
    st.caption(step["detail"])

st.divider()

# ---------------------------------------------------------------------------
# Step 5: Before vs After / Business Impact
# ---------------------------------------------------------------------------
st.subheader("Before vs. after")

# The manual-time override applies live, same as runs-per-week and hourly rate,
# rather than only being baked in at the moment "Analyze Workflow" was clicked.
effective_manual_minutes = (
    current_minutes_override if current_minutes_override > 0
    else analysis["estimated_manual_minutes_per_run"]
)

impact = estimate_impact(
    manual_minutes_per_run=effective_manual_minutes,
    ai_assisted_minutes_per_run=analysis["estimated_ai_assisted_minutes_per_run"],
    runs_per_week=runs_per_week,
    hourly_rate=hourly_rate,
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Before", f"{impact['manual_minutes_per_run']} min")
col2.metric("After", f"{impact['ai_assisted_minutes_per_run']} min",
            delta=f"-{impact['minutes_saved_per_run']} min", delta_color="inverse")
col3.metric("Reduction", f"{impact['percent_time_reduction']}%")
col4.metric("Hrs saved / wk", f"{impact['hours_saved_per_week']}")

st.caption(
    f"≈ {impact['hours_saved_per_year']} hrs and ${impact['dollars_saved_per_year']:,.0f} / year, per person."
)

st.divider()

# ---------------------------------------------------------------------------
# Step 6: Adoption Plan
# ---------------------------------------------------------------------------
st.subheader("Adoption plan")

if adoption:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Who:** {adoption['target_users']}")
        st.markdown(f"**Training:** {adoption['training_needed']}")
        st.markdown(f"**Pilot:** {adoption['pilot_plan']}")
    with c2:
        st.markdown("**Risks**")
        for risk in adoption["adoption_risks"]:
            st.markdown(f"- {risk}")
        st.markdown("**Success metrics**")
        for metric in adoption["success_metrics"]:
            st.markdown(f"- {metric}")

st.divider()
st.caption("AI drafts, a human reviews before anything is sent.")
