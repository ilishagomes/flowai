"""
workflow_analyzer.py

Core analysis module. Takes a plain-English workflow description and
produces:
  1. An "opportunity map" - per-task breakdown of automation potential,
     recommended approach, and what stays human.
  2. A step-by-step AI-assisted workflow (who does each step: AI or Human).
  3. A basic implementation plan.

Design decision: we ask Claude for ALL of this in a single call, as strict
JSON, rather than three separate calls. That keeps latency and cost down
and keeps the three outputs mutually consistent (the workflow steps and the
opportunity map are describing the same tasks). If the AI call fails or
returns something we can't parse, we fall back to fallback.py so the app
still produces a usable (if simpler) result instead of erroring out.
"""

from __future__ import annotations

from typing import Optional

from .fallback import analyze_workflow_offline
from .llm_client import ask_claude_for_json, LLMResult

SYSTEM_PROMPT = """You are an AI workflow consultant helping a nontechnical employee figure out \
where AI can help in a repetitive work task they describe. You are careful, concrete, and never \
overstate what AI can reliably do. You always keep a human in the loop for judgment calls, sending \
communications externally, and anything with real business/financial/legal consequence.

Respond with ONLY a single valid JSON object. No preamble, no markdown fences, no commentary. \
The JSON object must have exactly these keys:

{
  "opportunity_map": [
    {
      "task": "short name of a discrete task in the workflow",
      "category": "one of: Data Collection, Data Analysis, Writing, Formatting, Communication, Judgment, Other",
      "automation_potential": "one of: High, Medium-High, Medium, Low-Medium, Low",
      "recommended_approach": "one short sentence naming a concrete AI approach or tool pattern",
      "human_role": "one short sentence on what a human must still do for this task"
    }
  ],
  "workflow_steps": [
    {"step": "short imperative description of a step in order", "actor": "AI" or "Human"}
  ],
  "implementation_plan": [
    {"step": "short step name", "detail": "one sentence explaining what this involves"}
  ],
  "estimated_manual_minutes_per_run": <integer, current time this workflow takes per run, in minutes>,
  "estimated_ai_assisted_minutes_per_run": <integer, realistic time per run once AI-assisted, including human review>
}

Break the described workflow into 3-7 discrete tasks for the opportunity_map. Always include at \
least one "Human" actor step for review before final delivery in workflow_steps. Be realistic, not \
maximalist, about automation potential - if something involves relationship judgment, sign-off, or \
irreversible external communication, mark it Low or Low-Medium and say so in human_role."""


REQUIRED_KEYS = {
    "opportunity_map", "workflow_steps", "implementation_plan",
    "estimated_manual_minutes_per_run", "estimated_ai_assisted_minutes_per_run",
}


def _is_valid(data: dict) -> bool:
    if not REQUIRED_KEYS.issubset(data.keys()):
        return False
    if not isinstance(data["opportunity_map"], list) or not data["opportunity_map"]:
        return False
    if not isinstance(data["workflow_steps"], list) or not data["workflow_steps"]:
        return False
    if not isinstance(data["implementation_plan"], list) or not data["implementation_plan"]:
        return False
    return True


def analyze_workflow(workflow_text: str) -> dict:
    """
    Main entry point used by the Streamlit app.

    Returns a dict with keys: opportunity_map, workflow_steps, implementation_plan,
    estimated_manual_minutes_per_run, estimated_ai_assisted_minutes_per_run,
    plus a "meta" key describing whether AI or the offline fallback produced it.
    """
    workflow_text = (workflow_text or "").strip()
    if not workflow_text:
        raise ValueError("Workflow description cannot be empty.")

    user_prompt = f'Workflow description from the user:\n"""\n{workflow_text}\n"""'
    result: LLMResult = ask_claude_for_json(SYSTEM_PROMPT, user_prompt)

    if result.used_ai and _is_valid(result.data):
        data = result.data
        data["meta"] = {"source": "ai", "note": None}
        return data

    # Fall back to deterministic offline analysis - either no key, an API
    # error, or the model returned something that failed schema validation.
    offline_data = analyze_workflow_offline(workflow_text)
    note = result.error or "AI response did not match the expected format; used offline analysis instead."
    offline_data["meta"] = {"source": "offline", "note": note}
    return offline_data
