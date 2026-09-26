"""
adoption_planner.py

Generates the adoption plan: who should use this, what training is needed,
how to pilot it, what could go wrong, and how to measure success.

This is deliberately a separate module (and separate AI call) from
workflow_analyzer.py because adoption planning is a different kind of
reasoning - organizational/change-management, not task decomposition - and
keeping it separate makes each prompt simpler and each module independently
testable and reusable (e.g. you could swap in a purely template-based
adoption planner without touching the workflow analyzer at all).
"""

from __future__ import annotations

from .fallback import generate_adoption_plan_offline
from .llm_client import ask_claude_for_json, LLMResult

SYSTEM_PROMPT = """You are an AI adoption consultant. Given a description of a work \
workflow and its automation opportunity map, produce a practical rollout plan for \
introducing an AI-assisted version of this workflow into a team.

Respond with ONLY a single valid JSON object, no markdown fences, no commentary:

{
  "target_users": "one sentence naming who should use this first",
  "training_needed": "one sentence describing training format and length",
  "pilot_plan": "one sentence describing a small pilot before full rollout",
  "adoption_risks": ["short risk 1", "short risk 2", "..."],
  "success_metrics": ["short measurable metric 1", "short measurable metric 2", "..."]
}

Keep risks concrete and specific to this workflow (not generic "AI can be wrong" statements). \
Include 2-4 risks and 3-5 success metrics."""

REQUIRED_KEYS = {"target_users", "training_needed", "pilot_plan", "adoption_risks", "success_metrics"}


def _is_valid(data: dict) -> bool:
    if not REQUIRED_KEYS.issubset(data.keys()):
        return False
    if not isinstance(data["adoption_risks"], list) or not data["adoption_risks"]:
        return False
    if not isinstance(data["success_metrics"], list) or not data["success_metrics"]:
        return False
    return True


def generate_adoption_plan(workflow_text: str, opportunity_map: list[dict]) -> dict:
    summary_lines = "\n".join(
        f"- {item['task']} (automation potential: {item['automation_potential']})"
        for item in opportunity_map
    )
    user_prompt = (
        f'Workflow:\n"""\n{workflow_text}\n"""\n\n'
        f"Automation opportunity map:\n{summary_lines}"
    )

    result: LLMResult = ask_claude_for_json(SYSTEM_PROMPT, user_prompt)

    if result.used_ai and _is_valid(result.data):
        data = result.data
        data["meta"] = {"source": "ai"}
        return data

    offline_data = generate_adoption_plan_offline(workflow_text, opportunity_map)
    offline_data["meta"] = {"source": "offline", "note": result.error}
    return offline_data
