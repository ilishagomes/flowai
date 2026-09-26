"""
fallback.py

Deterministic, rule-based workflow analysis used when the Claude API is
unavailable (no key, network error, malformed response). This keeps FlowAI
usable offline/in a demo with no API key, and is also what makes the app's
behavior predictable enough to unit test without mocking an LLM.

The heuristics here are intentionally simple: split the workflow description
into rough clauses, tag each with a task type (data entry, analysis,
writing, review, communication), and use a lookup table of automation
potential per task type.
"""

from __future__ import annotations

import re

TASK_KEYWORDS = {
    "data_collection": ["collect", "gather", "pull", "export", "download", "upload", "import"],
    "data_analysis": ["analyze", "review data", "identify", "calculate", "compare", "summarize the", "detect"],
    "writing": ["write", "draft", "generate", "create a report", "compose", "summarize"],
    "formatting": ["format", "clean up", "organize", "structure"],
    "communication": ["email", "send", "share", "notify", "present", "message"],
    "judgment": ["decide", "approve", "review", "verify", "check", "escalate", "judge"],
}

# (automation_potential, human_role, default minutes for this clause)
TASK_PROFILE = {
    "data_collection": ("High", "Spot-check for missing/incorrect source data", 20),
    "data_analysis": ("High", "Sanity-check anomalies and interpretations", 30),
    "writing": ("Medium-High", "Edit tone, add context AI can't know", 25),
    "formatting": ("High", "Final visual check", 10),
    "communication": ("Low-Medium", "Approve before sending; own the relationship", 10),
    "judgment": ("Low", "Human makes the actual call", 15),
    "other": ("Medium", "Review output before use", 15),
}


def _split_clauses(workflow_text: str) -> list[str]:
    # Split on commas, "and", "then", periods - good enough for a rough pass.
    parts = re.split(r",| and | then |\.|;", workflow_text, flags=re.IGNORECASE)
    return [p.strip() for p in parts if len(p.strip()) > 3]


def _classify(clause: str) -> str:
    lower = clause.lower()
    for task_type, keywords in TASK_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return task_type
    return "other"


def analyze_workflow_offline(workflow_text: str) -> dict:
    clauses = _split_clauses(workflow_text) or [workflow_text]

    opportunity_map = []
    workflow_steps = []
    total_manual_minutes = 0
    total_ai_minutes = 0

    for clause in clauses:
        task_type = _classify(clause)
        potential, human_role, minutes = TASK_PROFILE[task_type]
        total_manual_minutes += minutes

        is_automatable = potential in ("High", "Medium-High")
        ai_minutes = max(2, minutes // 3) if is_automatable else minutes
        total_ai_minutes += ai_minutes

        opportunity_map.append({
            "task": clause.capitalize(),
            "category": task_type.replace("_", " ").title(),
            "automation_potential": potential,
            "recommended_approach": _approach_for(task_type),
            "human_role": human_role,
        })
        workflow_steps.append({
            "step": clause.capitalize(),
            "actor": "AI" if is_automatable else "Human",
        })

    workflow_steps.append({"step": "Human reviews AI output", "actor": "Human"})
    workflow_steps.append({"step": "Finalize and deliver result", "actor": "Human"})

    return {
        "opportunity_map": opportunity_map,
        "workflow_steps": workflow_steps,
        "implementation_plan": _default_implementation_plan(),
        "estimated_manual_minutes_per_run": total_manual_minutes,
        "estimated_ai_assisted_minutes_per_run": total_ai_minutes + 10,  # +10 for human review overhead
    }


def _approach_for(task_type: str) -> str:
    return {
        "data_collection": "Automated data connector / API pull",
        "data_analysis": "LLM-assisted analysis with anomaly detection",
        "writing": "LLM-drafted summary, human-edited",
        "formatting": "Templated auto-formatting",
        "communication": "AI-drafted message, human sends",
        "judgment": "Human decision, AI provides supporting data only",
        "other": "Case-by-case review",
    }[task_type]


def _default_implementation_plan() -> list[dict]:
    return [
        {"step": "Connect data source", "detail": "Set up the input feed (spreadsheet, database, or API) FlowAI will read from."},
        {"step": "Run AI analysis", "detail": "AI processes the raw input and extracts key figures and patterns."},
        {"step": "Detect trends & anomalies", "detail": "Flag anything unusual or worth a human's attention."},
        {"step": "Generate draft output", "detail": "AI drafts the summary, report, or message."},
        {"step": "Human review", "detail": "A person checks the draft for accuracy, tone, and context before anything goes out."},
        {"step": "Deliver", "detail": "Send, publish, or file the finished output."},
    ]


def generate_adoption_plan_offline(workflow_text: str, opportunity_map: list[dict]) -> dict:
    risky = any(item["automation_potential"] in ("Low", "Low-Medium") for item in opportunity_map)
    return {
        "target_users": "Whoever currently owns this workflow (e.g. analysts, ops, account managers)",
        "training_needed": "15-20 minute walkthrough plus one worked example",
        "pilot_plan": "2-week pilot with 3-5 volunteer users before wider rollout",
        "adoption_risks": [
            "Users may over-trust AI-generated numbers without checking them",
            "Initial resistance from people who see this as replacing their judgment" if risky else
            "Minor workflow disruption while people adjust to the new steps",
        ],
        "success_metrics": [
            "Time saved per run (minutes)",
            "Percentage of AI drafts requiring significant edits",
            "Weekly/active usage rate after rollout",
            "User-reported confidence in AI output (survey)",
        ],
    }
