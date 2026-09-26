# 🧭 FlowAI — AI Workflow Discovery & Adoption Assistant

FlowAI takes a plain-English description of a repetitive work task and turns it into an
AI implementation strategy: what to automate, what stays human, a step-by-step
implementation plan, an estimated time/cost savings, and a rollout plan for getting a
team to actually adopt it.

## Problem

Organizations are adopting AI tools without always understanding **which workflows are
appropriate for AI**, or how to help employees actually adopt them once built.
Most "AI demo" projects stop at "look, it can summarize text" — they skip the harder,
more valuable questions: *Should this be automated? What breaks if the AI is wrong?
How do you get a team to trust and actually use it?*

## Solution

FlowAI analyzes a user's workflow and generates:

1. **AI Opportunity Map** — per-task automation potential, a recommended approach, and
   what must remain human.
2. **AI-Assisted Workflow** — the same workflow re-drawn as a sequence of AI vs. Human
   steps.
3. **Implementation Plan** — concrete steps to actually build the AI-assisted version.
4. **Before vs. After Impact Estimate** — current time per run vs. AI-assisted time per
   run, rolled up into hours and dollars saved per year.
5. **Adoption Plan** — target users, training needed, a pilot plan, adoption risks, and
   success metrics.

## Example

Input:

> "Every Monday I take sales data from Excel, summarize the week's performance,
> identify unusual changes, and email my manager a report."

Output includes things like:

- **Automation potential:** High for data collection/analysis, Low-Medium for the
  actual "email my manager" step (a human should still hit send).
- **Estimated time savings:** roughly 60–70% of the manual time, translated into
  hours/week and dollars/year based on the user's hourly rate.
- **Adoption plan:** a 2-week pilot with a handful of users, trained in a 15–20 minute
  walkthrough, measured by time saved and how often the AI draft needed edits.

## Features

- Workflow analysis (task decomposition)
- AI opportunity identification (automation potential per task)
- Human-vs-AI task allocation
- Implementation planning
- Before/after business impact estimate (time + $ saved)
- Adoption planning (training, pilot, risks, success metrics)
- **Works without an API key** — falls back to a deterministic rule-based analyzer so
  the app is always usable for a demo, and so the core logic is unit-testable without
  mocking an LLM

## Tech Stack

| Layer         | Choice                                   |
|---------------|-------------------------------------------|
| Frontend      | Streamlit                                  |
| Backend       | Python                                     |
| AI            | Claude API (Anthropic), JSON-mode prompting|
| Data handling | Pandas                                     |
| Testing       | pytest                                     |
| Deployment    | Streamlit Community Cloud                  |
| Version control | GitHub                                   |

## Project Structure

```
FlowAI/
├── README.md
├── app.py                     # Streamlit UI
├── requirements.txt
├── .env.example
├── .streamlit/config.toml     # theme
├── src/
│   ├── llm_client.py          # Anthropic API wrapper + JSON parsing/validation
│   ├── workflow_analyzer.py   # task breakdown, opportunity map, workflow steps
│   ├── adoption_planner.py    # training/pilot/risks/success metrics
│   ├── impact_estimator.py    # deterministic before/after time & cost math
│   └── fallback.py            # rule-based offline analysis (no API key needed)
└── tests/
    ├── test_fallback.py
    └── test_impact_estimator.py
```

## Running Locally

```bash
git clone <this-repo>
cd FlowAI
pip install -r requirements.txt

# Optional but recommended — without it, FlowAI runs in offline demo mode
export ANTHROPIC_API_KEY=sk-ant-your-key-here

streamlit run app.py
```

## Running Tests

```bash
pytest tests/ -v
```

## Design Decisions (and why)

**Why a single JSON-mode LLM call instead of chaining several calls per section?**
Cost, latency, and consistency — one call keeps the opportunity map and the workflow
diagram describing the *same* underlying tasks, and Claude's structured JSON output
is validated before use rather than trusted blindly.

**How does this handle bad AI outputs?**
Every LLM response is schema-checked (`_is_valid` in `workflow_analyzer.py` /
`adoption_planner.py`) before it's shown to the user. If the response is missing keys,
isn't valid JSON, or the API call fails outright, FlowAI falls back to
`fallback.py` — a deterministic, keyword-based analyzer — rather than crashing or
silently showing garbage. The UI tells the user when this happened.

**Why is a human review step hard-coded into every workflow?**
Because the app's own thesis is that AI should assist, not replace, judgment calls and
external communication. The offline fallback always appends a human review step, and
the AI prompt explicitly instructs the model to keep at least one.

**Why is the business-impact math not done by the LLM?**
Numbers that go in front of a manager should be simple, checkable arithmetic
(`impact_estimator.py`), not something the model asserts. The AI estimates two time
figures; a human-auditable formula does the rest.

**What would I improve with more time?**
- Let users upload their actual spreadsheet (via Pandas) so the "before" time estimate
  is based on real file size/complexity, not just the text description.
- Persist analyses so a manager could review a team's submitted workflows in one place.
- Add a feedback loop: let users mark whether the AI-assisted estimate was accurate
  after actually trying it, and use that to calibrate future estimates.
- Support OpenAI as an alternate provider behind the same `llm_client` interface.

## What I Learned

*(Fill this in after you've actually built and used it — that's the part an interviewer
will ask about.)*
